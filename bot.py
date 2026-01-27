"""
Logique du bot Telegram et formatage des messages
"""
from datetime import datetime
from config import CATEGORIES, get_current_journee

class BotLogic:
    def __init__(self, storage):
        self.storage = storage
    
    def format_bilan(self, analysis_data, total_games, hour_str, comparison=None):
        """Formate le bilan des écarts de manière séduisante"""
        
        sorted_items = sorted(
            analysis_data.items(), 
            key=lambda x: x[1]['max_gap'], 
            reverse=True
        )
        
        message = f"""💐✨ BILAN DES ÉCARTS - ANALYSE COMPLÈTE ✨💐

🕐 Heure d'analyse: **{hour_str}**
📊 Total jeux analysés: **{total_games}**
📅 {get_current_journee().replace('_', ' ')}

"""
        
        for category, data in analysis_data.items():
            gaps_str = str(data['gaps']) if len(str(data['gaps'])) < 50 else str(data['gaps'][:10]) + "..."
            message += f"""{data['emoji']} **{category}**
            
📊 Nombre: {data['count']} numéros 📏 Écarts: {gaps_str} 👉🏻 Max écart: {data['max_gap']}
            
"""
        
        message += """🏆 **RÉCAPITULATIF DES MAX PAR CATÉGORIE** 🏆

"""
        
        for i, (category, data) in enumerate(sorted_items, 1):
            emoji = data['emoji']
            max_gap = data['max_gap']
            
            if max_gap >= 15:
                level = "🔴 CRITIQUE"
                bar = "█" * 10
            elif max_gap >= 10:
                level = "🟠 ÉLEVÉ"
                bar = "█" * 7 + "░" * 3
            elif max_gap >= 5:
                level = "🟡 MODÉRÉ"
                bar = "█" * 5 + "░" * 5
            else:
                level = "🟢 NORMAL"
                bar = "█" * 3 + "░" * 7
            
            comp_indicator = ""
            if comparison and category in comparison:
                comp = comparison[category]
                if comp['status'] == 'same':
                    comp_indicator = " ⚡ (Égal au précédent)"
                elif comp['status'] == 'increased':
                    comp_indicator = " 🔺 (Augmenté)"
                else:
                    comp_indicator = " 🔻 (Diminué)"
            
            message += f"{i}. {emoji} **{category}** | Max: **{max_gap}** | {level}{comp_indicator}\n"
            message += f"   `{bar}`\n\n"
        
        if comparison:
            same_max = [cat for cat, data in comparison.items() if data['status'] == 'same']
            if same_max:
                message += f"⚠️ **Alerte**: Les catégories suivantes ont conservé leur max: {', '.join(same_max)}\n\n"
        
        message += """💡 *Surveillez les catégories 🔴 et 🟠 !*
⏰ Prochaine analyse dans 1 heure pile..."""
        
        return message
    
    def format_historique(self, journee=None):
        """Formate l'historique des écarts"""
        if journee is None:
            journee = get_current_journee()
        
        historique = self.storage.get_historique(journee)
        
        if not historique:
            return f"📭 Aucun historique pour {journee.replace('_', ' ')}"
        
        message = f"""📚 **HISTORIQUE DES ÉCARTS**
📅 {journee.replace('_', ' ')}

"""
        
        for hour in sorted(historique.keys()):
            data = historique[hour]
            gaps_summary = []
            for cat, info in data['gaps'].items():
                emoji = CATEGORIES.get(cat, {}).get('emoji', '🎯')
                gaps_summary.append(f"{emoji}{cat[:3]}:{info['max_gap']}")
            
            message += f"🕐 **{hour}**\n"
            message += f"   {' | '.join(gaps_summary[:5])}\n"
            if len(gaps_summary) > 5:
                message += f"   {' | '.join(gaps_summary[5:])}\n"
            message += "\n"
        
        return message
    
    def format_statut(self, source_id, dest_id):
        """Formate le message de statut"""
        return f"""📊 **STATUT DU BOT**

🎯 Canal Source: `{source_id}`
📤 Canal Destination: `{dest_id if dest_id else 'Non défini'}`

💾 Fichier données: `ecarts_data.json`
📅 Journée active: {get_current_journee().replace('_', ' ')}
"""
        
