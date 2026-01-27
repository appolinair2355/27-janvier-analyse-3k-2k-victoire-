"""
Gestion du stockage JSON des écarts
"""
import json
import os
from datetime import datetime
from config import DATA_FILE, get_current_journee

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
                'source_channel': -1003309666471,
                'dest_channel': -1003725380926,
                'last_analysis': None
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
    
    def set_dest_channel(self, channel_id):
        """Définit le canal de destination"""
        self.data['config']['dest_channel'] = channel_id
        self.save_data()
    
    def get_dest_channel(self):
        """Récupère le canal de destination"""
        return self.data['config']['dest_channel']
    
    def get_source_channel(self):
        """Récupère le canal source"""
        return self.data['config']['source_channel']
          
