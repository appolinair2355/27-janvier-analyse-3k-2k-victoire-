"""
Configuration du Bot Telegram d'Analyse d'Écarts
"""
import os
from datetime import datetime

# ==========================================
# CONFIGURATION API TELEGRAM (OBLIGATOIRE)
# ==========================================

API_ID = 29177661
API_HASH = "a8639172fa8d35dbfd8ea46286d349ab"
BOT_TOKEN = "7815360317:AAGsrFzeUZrHOjujf5aY2UjlBj4GOblHSig"

# ==========================================
# CONFIGURATION DES CANAUX (OBLIGATOIRE)
# ==========================================

SOURCE_CHANNEL_ID = -1003309666471
DESTINATION_CHANNEL_ID = -1003725380926

# ==========================================
# CONFIGURATION ADMINISTRATEUR
# ==========================================

ADMIN_ID = 1190237801
ADMIN_USER_IDS = [ADMIN_ID]

# ==========================================
# CONFIGURATION SERVEUR
# ==========================================

PORT = int(os.getenv('PORT', 10000))
HOST = '0.0.0.0'
DATA_FILE = 'ecarts_data.json'

# ==========================================
# CONFIGURATION INTERVALLES
# ==========================================

DEFAULT_INTERVAL_MINUTES = int(os.getenv('DEFAULT_INTERVAL', 30))
MIN_INTERVAL_MINUTES = 5
MAX_INTERVAL_MINUTES = 1440

# ==========================================
# CATÉGORIES À ANALYSER (ADAPTÉ AU FORMAT RÉEL)
# ==========================================

CATEGORIES = {
    # Victoires
    'Victoire Joueur': {
        'patterns': ['VICTOIRE JOUEUR', 'Liste des numéros - VICTOIRE JOUEUR'],
        'emoji': '👤'
    },
    'Victoire Banquier': {
        'patterns': ['VICTOIRE BANQUIER', 'Liste des numéros - VICTOIRE BANQUIER'],
        'emoji': '🏦'
    },
    'Match Nul': {
        'patterns': ['MATCH NUL', 'Liste des numéros - MATCH NUL'],
        'emoji': '⚖️'
    },
    # Pair/Impair
    'Pair': {
        'patterns': ['PAIR (Chronologique)', 'Liste des numéros - PAIR'],
        'emoji': '🔵'
    },
    'Impair': {
        'patterns': ['IMPAIR (Chronologique)', 'Liste des numéros - IMPAIR'],
        'emoji': '🔴'
    },
    # Paires détaillées
    '3/2': {
        'patterns': ['3/2', '💪 3/2'],
        'emoji': '🧡'
    },
    '3/3': {
        'patterns': ['3/3', '🔥 3/3'],
        'emoji': '❤️'
    },
    '2/2': {
        'patterns': ['2/2', '🎯 2/2'],
        'emoji': '🖤'
    },
    '2/3': {
        'patterns': ['2/3', '🍀 2/3'],
        'emoji': '💚'
    }
}

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def get_current_journee():
    """Retourne le numéro de journée (1h-00h59 = Journée X)"""
    now = datetime.now()
    if now.hour >= 1:
        return f"Journée_{now.strftime('%Y%m%d')}"
    else:
        from datetime import timedelta
        yesterday = now - timedelta(days=1)
        return f"Journée_{yesterday.strftime('%Y%m%d')}"


def get_channels_info():
    """Retourne les informations des canaux configurés"""
    return {
        'source': SOURCE_CHANNEL_ID,
        'destination': DESTINATION_CHANNEL_ID,
        'source_str': str(SOURCE_CHANNEL_ID),
        'destination_str': str(DESTINATION_CHANNEL_ID)
    }


def validate_configuration():
    """Valide la configuration complète"""
    errors = []
    warnings = []
    
    if API_ID == 0 or API_HASH == "VOTRE_API_HASH":
        errors.append("❌ API_ID ou API_HASH non configuré")
    
    if BOT_TOKEN == "VOTRE_TOKEN_ICI" or not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN non configuré")
    
    if not str(SOURCE_CHANNEL_ID).startswith('-100'):
        errors.append(f"❌ SOURCE_CHANNEL_ID invalide: {SOURCE_CHANNEL_ID}")
    
    if not str(DESTINATION_CHANNEL_ID).startswith('-100'):
        errors.append(f"❌ DESTINATION_CHANNEL_ID invalide: {DESTINATION_CHANNEL_ID}")
    
    if ADMIN_ID == 0:
        warnings.append("⚠️ ADMIN_ID non configuré")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
