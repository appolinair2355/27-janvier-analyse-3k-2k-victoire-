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
            
