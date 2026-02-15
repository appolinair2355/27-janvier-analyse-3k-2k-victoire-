"""
Gestion du stockage JSON des écarts
"""
import json
import os
from datetime import datetime
from config import DATA_FILE, get_current_journee, DEFAULT_INTERVAL_MINUTES

class Storage:
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self):
        """Charge les données depuis le fichier JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.init_data()
        return self.init_data()
    
    def init_data(self):
        """Initialise la structure des données"""
        return {
            'historique': {},
            'config': {
                'last_analysis': None,
                'interval_minutes': DEFAULT_INTERVAL_MINUTES,
                'auto_send_enabled': True,
                'last_auto_send': None
            }
        }
    
    def save_data(self):
        """Sauvegarde les données dans le fichier JSON"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def save_analysis(self, hour, gaps_data):
        """Sauvegarde une analyse d'heure"""
        journee = get_current_journee()
        
        if journee not in self.data['historique']:
            self.data['historique'][journee] = {}
        
        self.data['historique'][journee][hour] = {
            'timestamp': datetime.now().isoformat(),
            'gaps': gaps_data
        }
        
        self.data['config']['last_analysis'] = datetime.now().isoformat()
        self.save_data()
    
    def get_previous_hour_data(self, current_hour):
        """Récupère les données de l'heure précédente"""
        journee = get_current_journee()
        
        if journee not in self.data['historique']:
            return None
        
        hours = sorted(self.data['historique'][journee].keys())
        try:
            idx = hours.index(current_hour)
            if idx > 0:
                prev_hour = hours[idx - 1]
                return self.data['historique'][journee][prev_hour]
        except ValueError:
            pass
        
        return None
    
    def get_historique(self, journee=None):
        """Récupère l'historique d'une journée"""
        if journee is None:
            journee = get_current_journee()
        return self.data['historique'].get(journee, {})
    
    def get_interval_minutes(self):
        """Récupère l'intervalle d'envoi en minutes"""
        return self.data['config'].get('interval_minutes', DEFAULT_INTERVAL_MINUTES)
    
    def set_interval_minutes(self, minutes):
        """Définit l'intervalle d'envoi en minutes"""
        self.data['config']['interval_minutes'] = minutes
        self.save_data()
    
    def is_auto_send_enabled(self):
        """Vérifie si l'envoi automatique est activé"""
        return self.data['config'].get('auto_send_enabled', True)
    
    def set_auto_send_enabled(self, enabled):
        """Active/désactive l'envoi automatique"""
        self.data['config']['auto_send_enabled'] = enabled
        self.save_data()
    
    def get_last_auto_send(self):
        """Récupère le timestamp du dernier envoi automatique"""
        return self.data['config'].get('last_auto_send')
    
    def update_last_auto_send(self):
        """Met à jour le timestamp du dernier envoi automatique"""
        self.data['config']['last_auto_send'] = datetime.now().isoformat()
        self.save_data()
    
    def get_last_parsed_data(self):
        """Récupère les dernières données parsées pour l'envoi automatique"""
        journee = get_current_journee()
        if journee in self.data['historique']:
            hours = sorted(self.data['historique'][journee].keys())
            if hours:
                last_hour = hours[-1]
                return self.data['historique'][journee][last_hour]
        return None
