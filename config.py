"""
Configuration du Bot Telegram d'Analyse d'Écarts
"""
import os
from datetime import datetime

# Token du bot (à remplacer par le vrai token)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'VOTRE_TOKEN_ICI')

# IDs des canaux
SOURCE_CHANNEL_ID = -1003309666471  # Canal source où arrivent les stats
DESTINATION_CHANNEL_ID = -1003725380926  # Canal destination

# Configuration serveur pour Render.com
PORT = int(os.getenv('PORT', 10000))
HOST = '0.0.0.0'

# Fichier de stockage
DATA_FILE = 'ecarts_data.json'

# Catégories à analyser avec leurs patterns de détection
CATEGORIES = {
    '3/2': {
        'patterns': ['3/2', 'La Main Forte du Joueur'],
        'emoji': '🧡'
    },
    '3/3': {
        'patterns': ['3/3', 'Le Jackpot des Trois Cartes'],
        'emoji': '❤️'
    },
    '2/2': {
        'patterns': ['2/2', "L'Équilibre du Tapis"],
        'emoji': '🖤'
    },
    '2/3': {
        'patterns': ['2/3', 'Le Tirage GAGNANT'],
        'emoji': '💚'
    },
    'Victoire Joueur': {
        'patterns': ['VICTOIRE JOUEUR'],
        'emoji': '👤'
    },
    'Victoire Banquier': {
        'patterns': ['VICTOIRE BANQUIER'],
        'emoji': '🏦'
    },
    'Match Nul': {
        'patterns': ['MATCH NUL'],
        'emoji': '⚖️'
    },
    'Pair': {
        'patterns': ['- PAIR (Chronologique)'],
        'emoji': '🔵'
    },
    'Impair': {
        'patterns': ['- IMPAIR (Chronologique)'],
        'emoji': '🔴'
    }
}

def get_current_journee():
    """Retourne le numéro de journée (1h-00h59 = Journée X)"""
    now = datetime.now()
    if now.hour >= 1:
        return f"Journée_{now.strftime('%Y%m%d')}"
    else:
        from datetime import timedelta
        yesterday = now - timedelta(days=1)
        return f"Journée_{yesterday.strftime('%Y%m%d')}"

