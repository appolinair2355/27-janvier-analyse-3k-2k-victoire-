"""
Logique du bot et formatage des messages
"""
from datetime import datetime
from config import CATEGORIES, get_current_journee, get_channels_info

class BotLogic:
    def __init__(self, storage):
        self.storage = storage
    
    def format_statut(self, source, dest):
        """Formate le message de statut"""
        interval = self.storage.get_interval_minutes()
        auto_send = "✅ Activé" if self.storage.is_auto_send_enabled() else "❌ Désactivé"
        
        return f"""📊 **Statut du Bot**

🎯 **Canal Source:** `{source}`
📤 **Canal Destination:** `{dest}`
⏱️ **Intervalle d'envoi:** `{interval} minutes`
🤖 **Envoi automatique:** {auto_send}

📅 **Journée:** {get_current_journee().replace('_', ' ')}
🕐 **Heure actuelle:** {datetime.now().strftime('%H:%M:%S')}"""
    
    def format_bilan(self, analysis, total_games, hour_str, comparison=None):
        """Formate le bilan des écarts"""
        lines = [
            "🌸 **BILAN DES ÉCARTS** 🌸",
            f"⏰ {hour_str} | 🎲 {total_games} jeux",
            ""
        ]
        
        # Ajouter chaque catégorie
        for category_name, data in analysis.items():
            emoji = data['emoji']
            max_gap = data['max_gap']
            count = data['count']
            lines.append(f"{emoji} **{category_name}** → Écart max: **{max_gap}** ({count} tirages)")
        
        # Ajouter comparaison si disponible
        if comparison:
            lines.append("")
            lines.append("📈 **Évolution vs précédent:**")
            increased = sum(1 for v in comparison.values() if v['status'] == 'increased')
            decreased = sum(1 for v in comparison.values() if v['status'] == 'decreased')
            same = sum(1 for v in comparison.values() if v['status'] == 'same')
            lines.append(f"↗️ {increased} en hausse | ↘️ {decreased} en baisse | ➡️ {same} stable")
        
        return "\n".join(lines)
    
    def format_historique(self):
        """Formate l'historique de la journée"""
        journee = get_current_journee()
        historique = self.storage.get_historique(journee)
        
        lines = [
            f"📚 **Historique - {journee.replace('_', ' ')}**",
            ""
        ]
        
        if not historique:
            lines.append("Aucune analyse enregistrée aujourd'hui.")
            return "\n".join(lines)
        
        for hour in sorted(historique.keys()):
            data = historique[hour]
            gaps = data.get('gaps', {})
            total_categories = len(gaps)
            max_gaps = [str(v.get('max_gap', 0)) for v in gaps.values()]
            lines.append(f"🕐 **{hour}** - {total_categories} catégories")
            lines.append(f"   Écarts max: {', '.join(max_gaps[:5])}{'...' if len(max_gaps) > 5 else ''}")
        
        return "\n".join(lines)
    
    def format_auto_send_bilan(self):
        """Formate le bilan pour l'envoi automatique (utilise dernières données connues)"""
        last_data = self.storage.get_last_parsed_data()
        
        if not last_data:
            return None
        
        gaps_data = last_data.get('gaps', {})
        timestamp = last_data.get('timestamp', datetime.now().isoformat())
        
        # Reconstruire le format analysis attendu
        analysis = {}
        for cat_name, cat_data in gaps_data.items():
            analysis[cat_name] = {
                'emoji': CATEGORIES.get(cat_name, {}).get('emoji', '⚪'),
                'max_gap': cat_data.get('max_gap', 0),
                'count': len(cat_data.get('gaps', [])) + 1,
                'gaps': cat_data.get('gaps', [])
            }
        
        # Calculer total_games approximatif
        total_games = sum(d['count'] for d in analysis.values()) // 3
        
        hour_str = datetime.fromisoformat(timestamp).strftime('%H:%M') if isinstance(timestamp, str) else datetime.now().strftime('%H:%M')
        
        return self.format_bilan(analysis, total_games, hour_str)
    
    def format_interval_update(self, new_interval):
        """Confirme la mise à jour de l'intervalle"""
        return f"""✅ **Configuration mise à jour**

⏱️ Nouvel intervalle d'envoi: **{new_interval} minutes**

Le bilan sera envoyé automatiquement toutes les {new_interval} minutes au canal destinataire."""
    
    def format_auto_send_status(self, enabled):
        """Confirme l'activation/désactivation de l'envoi auto"""
        status = "activé" if enabled else "désactivé"
        emoji = "✅" if enabled else "❌"
        return f"{emoji} Envoi automatique **{status}**."
