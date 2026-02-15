"""
Configuration du Bot Telegram d'Analyse d'Écarts
"""
import os
from datetime import datetime

# ==========================================
# CONFIGURATION API TELEGRAM (OBLIGATOIRE)
# ==========================================

# API ID et Hash (depuis https://my.telegram.org)
API_ID = 29177661
API_HASH = "a8639172fa8d35dbfd8ea46286d349ab"

# Token du bot (depuis @BotFather)
BOT_TOKEN = "7928036679:AAGJyBYLy7FPPTNBygP_pqXjIXVMNOpYPJk"

# ==========================================
# CONFIGURATION DES CANAUX (OBLIGATOIRE)
# ==========================================

# ID du canal source où arrivent les statistiques
SOURCE_CHANNEL_ID = -1003309666471

# ID du canal de destination où envoyer les bilans
DESTINATION_CHANNEL_ID = -1003725380926

# ==========================================
# CONFIGURATION ADMINISTRATEUR
# ==========================================

# ID Telegram de l'administrateur (depuis @userinfobot)
ADMIN_ID = 1190237801

# Liste des IDs admin (pour compatibilité avec le code existant)
ADMIN_USER_IDS = [ADMIN_ID]

# ==========================================
# CONFIGURATION SERVEUR
# ==========================================

PORT = int(os.getenv('PORT', 10000))
HOST = '0.0.0.0'

# Fichier de stockage
DATA_FILE = 'ecarts_data.json'

# ==========================================
# CONFIGURATION INTERVALLES
# ==========================================

DEFAULT_INTERVAL_MINUTES = int(os.getenv('DEFAULT_INTERVAL', 30))
MIN_INTERVAL_MINUTES = 5
MAX_INTERVAL_MINUTES = 1440

# ==========================================
# CATÉGORIES D'ANALYSE
# ==========================================

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
    
    # Vérification API
    if API_ID == 0 or API_HASH == "VOTRE_API_HASH":
        errors.append("❌ API_ID ou API_HASH non configuré")
    
    if BOT_TOKEN == "VOTRE_TOKEN_ICI" or not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN non configuré")
    
    # Vérification canaux
    if not str(SOURCE_CHANNEL_ID).startswith('-100'):
        errors.append(f"❌ SOURCE_CHANNEL_ID invalide: {SOURCE_CHANNEL_ID}")
    
    if not str(DESTINATION_CHANNEL_ID).startswith('-100'):
        errors.append(f"❌ DESTINATION_CHANNEL_ID invalide: {DESTINATION_CHANNEL_ID}")
    
    # Vérification admin
    if ADMIN_ID == 0:
        warnings.append("⚠️ ADMIN_ID non configuré")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
