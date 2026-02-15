"""
Point d'entrée principal du Bot Telegram
"""
import os
import sys
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import (
    API_ID, API_HASH, BOT_TOKEN, PORT, HOST,
    SOURCE_CHANNEL_ID, DESTINATION_CHANNEL_ID,
    ADMIN_ID, ADMIN_USER_IDS,
    MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES,
    get_channels_info, validate_configuration
)
from storage import Storage
from parser import MessageParser
from analyzer import GapAnalyzer
from bot import BotLogic

app = Flask(__name__)

storage = Storage()
parser = MessageParser()
analyzer = GapAnalyzer()
bot_logic = BotLogic(storage)

_channel_status_cache = {
    'source': None,
    'destination': None,
    'last_check': None
}

# ============ FLASK ROUTES ============

@app.route('/')
def home():
    interval = storage.get_interval_minutes()
    auto_send = "Actif" if storage.is_auto_send_enabled() else "Inactif"
    last_send = storage.get_last_auto_send()
    last_send_str = "Jamais"
    if last_send:
        try:
            last_dt = datetime.fromisoformat(last_send)
            last_send_str = last_dt.strftime('%H:%M:%S')
        except:
            pass
    
    validation = validate_configuration()
    status_emoji = "✅" if validation['valid'] else "❌"
    channels = get_channels_info()
    
    source_status = "⏳ Non vérifié"
    dest_status = "⏳ Non vérifié"
    
    if _channel_status_cache['last_check']:
        source_status = "✅ Membre" if _channel_status_cache['source'] else "❌ Non membre"
        dest_status = "✅ Membre" if _channel_status_cache['destination'] else "❌ Non membre"
    
    html_content = f"""
    <h1>{status_emoji} Bot d'Analyse d'Écarts</h1>
    <h3>🔐 Configuration API</h3>
    <ul>
        <li>API ID: <code>{API_ID}</code></li>
        <li>API Hash: <code>{API_HASH[:10]}...</code></li>
        <li>Bot Token: <code>{BOT_TOKEN[:20]}...</code></li>
    </ul>
    <h3>📺 Canaux Configurés</h3>
    <ul>
        <li>Source: <code>{channels['source']}</code> - {source_status}</li>
        <li>Destination: <code>{channels['destination']}</code> - {dest_status}</li>
    </ul>
    <h3>👤 Admin: <code>{ADMIN_ID}</code></h3>
    <h3>⚙️ Paramètres</h3>
    <ul>
        <li>🕐 Heure: {datetime.now().strftime('%H:%M:%S')}</li>
        <li>⏱️ Intervalle: {interval} min ({auto_send})</li>
        <li>📤 Dernier envoi: {last_send_str}</li>
    </ul>
    """
    
    if validation['errors']:
        html_content += "<h3 style='color:red'>❌ Erreurs:</h3><ul>"
        for err in validation['errors']:
            html_content += f"<li style='color:red'>{err}</li>"
        html_content += "</ul>"
    
    if validation['warnings']:
        html_content += "<h3 style='color:orange'>⚠️ Avertissements:</h3><ul>"
        for warn in validation['warnings']:
            html_content += f"<li style='color:orange'>{warn}</li>"
        html_content += "</ul>"
    
    return html_content

@app.route('/health')
def health():
    validation = validate_configuration()
    channels = get_channels_info()
    
    return {
        "status": "healthy" if validation['valid'] else "error",
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "api_configured": API_ID != 0 and API_HASH != "VOTRE_API_HASH",
            "bot_token_configured": BOT_TOKEN != "VOTRE_TOKEN_ICI",
            "admin_configured": ADMIN_ID != 0
        },
        "channels": {
            "source": {
                "id": channels['source'],
                "status": "member" if _channel_status_cache['source'] else "unknown"
            },
            "destination": {
                "id": channels['destination'],
                "status": "member" if _channel_status_cache['destination'] else "unknown"
            }
        },
        "errors": validation['errors'] if validation['errors'] else None
    }

# ============ UTILITAIRES ============

def is_admin(user_id):
    """Vérifie si l'utilisateur est admin"""
    return user_id == ADMIN_ID or user_id in ADMIN_USER_IDS

async def check_bot_in_channel(bot, channel_id):
    """
    Vérifie si le bot est membre d'un canal
    Retourne: (success: bool, is_member: bool, error_message: str)
    """
    try:
        chat = await bot.get_chat(channel_id)
        member = await bot.get_chat_member(channel_id, (await bot.get_me()).id)
        can_send = member.status in ['administrator', 'member', 'creator']
        
        return True, can_send, None
        
    except Exception as e:
        error_msg = str(e)
        if "chat not found" in error_msg.lower():
            return False, False, "Canal non trouvé (ID invalide ou bot non membre)"
        elif "user not participant" in error_msg.lower():
            return False, False, "Bot non membre du canal"
        elif "forbidden" in error_msg.lower():
            return False, False, "Bot sans permission d'accès"
        else:
            return False, False, f"Erreur: {error_msg}"

async def update_channel_status_cache(bot):
    """Met à jour le cache du statut des canaux"""
    global _channel_status_cache
    
    print("🔍 Vérification du statut des canaux...")
    
    success_src, is_member_src, error_src = await check_bot_in_channel(bot, SOURCE_CHANNEL_ID)
    if success_src:
        _channel_status_cache['source'] = is_member_src
        print(f"   Source {SOURCE_CHANNEL_ID}: {'✅' if is_member_src else '❌'}")
    else:
        _channel_status_cache['source'] = False
        print(f"   Source {SOURCE_CHANNEL_ID}: ❌ ({error_src})")
    
    success_dest, is_member_dest, error_dest = await check_bot_in_channel(bot, DESTINATION_CHANNEL_ID)
    if success_dest:
        _channel_status_cache['destination'] = is_member_dest
        print(f"   Destination {DESTINATION_CHANNEL_ID}: {'✅' if is_member_dest else '❌'}")
    else:
        _channel_status_cache['destination'] = False
        print(f"   Destination {DESTINATION_CHANNEL_ID}: ❌ ({error_dest})")
    
    _channel_status_cache['last_check'] = datetime.now().isoformat()
    
    return {
        'source': {'ok': success_src, 'member': is_member_src, 'error': error_src},
        'destination': {'ok': success_dest, 'member': is_member_dest, 'error': error_dest}
    }

async def send_bilan_to_destination(context: ContextTypes.DEFAULT_TYPE):
    """Envoie le bilan au canal de destination"""
    try:
        bilan = bot_logic.format_auto_send_bilan()
        if not bilan:
            print("⚠️ Aucune donnée disponible pour l'envoi automatique")
            return False
        
        await context.bot.send_message(
            chat_id=DESTINATION_CHANNEL_ID, 
            text=bilan, 
            parse_mode='Markdown'
        )
        
        storage.update_last_auto_send()
        print(f"✅ Bilan auto envoyé à {DESTINATION_CHANNEL_ID} à {datetime.now().strftime('%H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi auto vers {DESTINATION_CHANNEL_ID}: {e}")
        return False

# ============ COMMANDES PUBLIQUES ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    channels = get_channels_info()
    
    welcome_msg = f"""🌸 **Bot d'Analyse d'Écarts** 🌸

📺 **Canaux configurés:**
• Source: `{channels['source']}`
• Destination: `{channels['destination']}`

📋 **Commandes:**
/start - Démarrer
/statut - Voir la configuration
/verifier - 🔍 Vérifier l'accès aux canaux
/test - Tester l'analyse
/historique - Voir l'historique
/restart - Redémarrer
"""
    
    if is_user_admin:
        welcome_msg += f"""
👑 **Commandes Admin:**
/intervalle <minutes> - Définir l'intervalle
/auto <on/off> - Activer/désactiver l'envoi auto
/envoyer - Forcer l'envoi immédiat
/testenvoi - Tester l'envoi avec données fictives
"""
    
    welcome_msg += f"\n⏰ Envoi auto: **{storage.get_interval_minutes()}** min."
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def statut_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche la configuration complète"""
    channels = get_channels_info()
    interval = storage.get_interval_minutes()
    auto_send = "✅ Activé" if storage.is_auto_send_enabled() else "❌ Désactivé"
    last_send = storage.get_last_auto_send()
    
    last_send_str = "Jamais"
    if last_send:
        try:
            last_dt = datetime.fromisoformat(last_send)
            last_send_str = last_dt.strftime('%H:%M:%S %d/%m/%Y')
        except:
            last_send_str = str(last_send)
    
    # Vérifier si on a des données
    last_data = storage.get_last_parsed_data()
    data_status = "✅ Données disponibles" if last_data else "❌ Aucune donnée reçue"
    
    msg = f"""📊 **Configuration du Bot**

🔐 **API:** Configurée (ID: `{API_ID}`)
🤖 **Bot:** Actif
👤 **Admin:** `{ADMIN_ID}`

📺 **Canaux:**
• Source: `{channels['source']}`
• Destination: `{channels['destination']}`

📊 **Données:** {data_status}

⚙️ **Paramètres:**
• Intervalle: **{interval}** minutes
• Envoi auto: {auto_send}
• Dernier envoi: {last_send_str}

🕐 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def verifier_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔍 Vérifie si le bot a accès aux canaux configurés
    Affiche ✅ si membre, ❌ si non
    """
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "⏳ Vérification des canaux en cours... (réservé admin)", 
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "🔍 **Vérification des canaux en cours...**\n"
        "Cela peut prendre quelques secondes.", 
        parse_mode='Markdown'
    )
    
    results = await update_channel_status_cache(context.bot)
    
    channels = get_channels_info()
    
    source_emoji = "✅" if results['source']['member'] else "❌"
    dest_emoji = "✅" if results['destination']['member'] else "❌"
    
    source_detail = ""
    if not results['source']['ok'] and results['source']['error']:
        source_detail = f"\n   _{results['source']['error']}_"
    
    dest_detail = ""
    if not results['destination']['ok'] and results['destination']['error']:
        dest_detail = f"\n   _{results['destination']['error']}_"
    
    msg = f"""🔍 **Résultat de la Vérification**

📥 **Canal Source:**
{source_emoji} `{channels['source']}`
{source_detail}

📤 **Canal Destination:**
{dest_emoji} `{channels['destination']}`
{dest_detail}

💡 **Conseils si ❌:**
• Vérifiez que les IDs sont corrects
• Ajoutez le bot comme admin dans les canaux
• Assurez-vous que le bot n'est pas bloqué
• Pour les canaux privés, utilisez le format `-100XXXXXXXXXX`
"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_data = {
        'total_games': 60,
        'categories': {
            '3/2': [1330, 1342, 1352, 1361, 1366, 1370, 1374, 1375],
            '3/3': [1322, 1323, 1325, 1329, 1332, 1335, 1337, 1338, 1340, 1349],
            '2/2': [1321, 1324, 1326, 1327, 1328, 1331, 1336, 1339],
            '2/3': [1333, 1334, 1343, 1344, 1347, 1360],
            'Victoire Joueur': [1322, 1330, 1333, 1335, 1336],
            'Victoire Banquier': [1321, 1323, 1325, 1326, 1327],
            'Match Nul': [1324, 1332],
            'Pair': [1321, 1323, 1324, 1326],
            'Impair': [1322, 1325, 1328]
        }
    }
    
    analysis = analyzer.analyze_all_categories(test_data)
    hour_str = datetime.now().strftime('%H:%M')
    msg = bot_logic.format_bilan(analysis, test_data['total_games'], hour_str)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def historique_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = bot_logic.format_historique()
    await update.message.reply_text(msg, parse_mode='Markdown')

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Redémarrage...", parse_mode='Markdown')
    try:
        storage.save_data()
        await update.message.reply_text("✅ Bot redémarré!", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}", parse_mode='Markdown')

# ============ COMMANDES ADMIN ============

async def intervalle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Commande réservée aux administrateurs.", parse_mode='Markdown')
        return
    
    if not context.args:
        current = storage.get_interval_minutes()
        await update.message.reply_text(
            f"⏱️ Intervalle actuel: **{current}** minutes\n\n"
            f"Usage: `/intervalle <minutes>`\n"
            f"Min: {MIN_INTERVAL_MINUTES} | Max: {MAX_INTERVAL_MINUTES}",
            parse_mode='Markdown'
        )
        return
    
    try:
        new_interval = int(context.args[0])
        
        if new_interval < MIN_INTERVAL_MINUTES or new_interval > MAX_INTERVAL_MINUTES:
            await update.message.reply_text(
                f"❌ Intervalle invalide. Entre {MIN_INTERVAL_MINUTES} et {MAX_INTERVAL_MINUTES} minutes.",
                parse_mode='Markdown'
            )
            return
        
        storage.set_interval_minutes(new_interval)
        msg = bot_logic.format_interval_update(new_interval)
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un nombre valide.", parse_mode='Markdown')

async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Commande réservée aux administrateurs.", parse_mode='Markdown')
        return
    
    if not context.args:
        status = storage.is_auto_send_enabled()
        status_str = "activé" if status else "désactivé"
        await update.message.reply_text(
            f"🤖 Envoi automatique: **{status_str}**\n\n"
            f"Usage: `/auto <on/off>`",
            parse_mode='Markdown'
        )
        return
    
    arg = context.args[0].lower()
    if arg in ['on', 'true', '1', 'oui']:
        storage.set_auto_send_enabled(True)
        await update.message.reply_text(bot_logic.format_auto_send_status(True), parse_mode='Markdown')
    elif arg in ['off', 'false', '0', 'non']:
        storage.set_auto_send_enabled(False)
        await update.message.reply_text(bot_logic.format_auto_send_status(False), parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Usage: `/auto <on/off>`", parse_mode='Markdown')

async def envoyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force l'envoi immédiat du bilan vers DESTINATION_CHANNEL_ID"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Commande réservée aux administrateurs.", parse_mode='Markdown')
        return
    
    channels = get_channels_info()
    
    # Vérifier d'abord si on a des données
    last_data = storage.get_last_parsed_data()
    
    if not last_data:
        await update.message.reply_text(
            f"""❌ **Aucune donnée disponible**

📤 Impossible d'envoyer le bilan vers `{channels['destination']}`

💡 **Raison:** Le bot n'a pas encore reçu de message "STATISTIQUES COMPLÈTES" du canal source.

✅ **Solutions:**
1. Attendez que le canal source `{channels['source']}` envoie des statistiques
2. Utilisez `/test` pour voir un exemple de bilan
3. Utilisez `/testenvoi` pour tester l'envoi avec des données fictives

🔍 Vérifiez aussi: `/verifier` pour confirmer que le bot est dans les canaux""",
            parse_mode='Markdown'
        )
        return
    
    # On a des données, procéder à l'envoi
    await update.message.reply_text(
        f"📤 Envoi du bilan vers `{channels['destination']}`...\n"
        f"📊 Dernière donnée reçue: {last_data.get('timestamp', 'inconnue')[:16]}", 
        parse_mode='Markdown'
    )
    
    success = await send_bilan_to_destination(context)
    
    if success:
        await update.message.reply_text("✅ Bilan envoyé avec succès!", parse_mode='Markdown')
    else:
        await update.message.reply_text(
            """❌ **Échec de l'envoi**

🔧 Causes possibles:
• Bot retiré du canal destination
• Canal destination inexistant ou inaccessible
• Problème de réseau

🔍 Faites `/verifier` pour diagnostiquer""",
            parse_mode='Markdown'
        )

async def testenvoi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teste l'envoi avec des données fictives vers le canal destination"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Commande réservée aux administrateurs.", parse_mode='Markdown')
        return
    
    channels = get_channels_info()
    
    await update.message.reply_text(
        f"🧪 **Test d'envoi vers** `{channels['destination']}`\n"
        f"Utilisation de données fictives...", 
        parse_mode='Markdown'
    )
    
    # Créer des données de test
    test_data = {
        'total_games': 60,
        'categories': {
            '3/2': [1330, 1342, 1352, 1361, 1366, 1370, 1374, 1375],
            '3/3': [1322, 1323, 1325, 1329, 1332, 1335, 1337, 1338, 1340, 1349],
            '2/2': [1321, 1324, 1326, 1327, 1328, 1331, 1336, 1339],
            '2/3': [1333, 1334, 1343, 1344, 1347, 1360],
            'Victoire Joueur': [1322, 1330, 1333, 1335, 1336],
            'Victoire Banquier': [1321, 1323, 1325, 1326, 1327],
            'Match Nul': [1324, 1332],
            'Pair': [1321, 1323, 1324, 1326],
            'Impair': [1322, 1325, 1328]
        }
    }
    
    try:
        analysis = analyzer.analyze_all_categories(test_data)
        hour_str = datetime.now().strftime('%H:%M')
        bilan_msg = bot_logic.format_bilan(analysis, test_data['total_games'], hour_str)
        
        # Envoyer au canal destination
        await context.bot.send_message(
            chat_id=DESTINATION_CHANNEL_ID,
            text=bilan_msg + "\n\n🧪 *Message de test*", 
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            f"""✅ **Test réussi!**

📤 Bilan de test envoyé vers `{channels['destination']}`

✅ Le canal destination est accessible
✅ Le bot a les permissions d'envoi

📝 Prochaine étape: Attendez les vraies données du canal source `{channels['source']}`""",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"""❌ **Test échoué**

💥 Erreur: `{str(e)}`

🔍 Causes possibles:
• Bot non membre du canal destination
• ID du canal incorrect
• Canal inexistant

💡 Faites `/verifier` pour diagnostiquer""",
            parse_mode='Markdown'
        )

# ============ GESTION MESSAGES CANAL ============

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traite les messages du canal source configuré"""
    if not update.channel_post:
        return
    
    if update.channel_post.chat_id != SOURCE_CHANNEL_ID:
        return
    
    message_text = update.channel_post.text
    
    print(f"\n{'='*50}")
    print(f"📥 MESSAGE REÇU à {datetime.now().strftime('%H:%M:%S')}")
    print(f"📍 Canal: {update.channel_post.chat_id}")
    print(f"📝 Début: {message_text[:100]}...")
    print(f"{'='*50}\n")
    
    if not message_text or 'STATISTIQUES COMPLÈTES' not in message_text:
        print("❌ Message ignoré: ne contient pas 'STATISTIQUES COMPLÈTES'")
        return
    
    # DEBUG: Sauvegarder le message brut pour analyse
    try:
        with open('last_message_debug.txt', 'w', encoding='utf-8') as f:
            f.write(message_text)
        print("💾 Message sauvegardé dans last_message_debug.txt")
    except Exception as e:
        print(f"⚠️ Impossible de sauvegarder: {e}")
    
    parsed_data = parser.parse_message(message_text)
    
    if not parsed_data:
        print("❌ ÉCHEC DU PARSING - Message incomplet ou format non reconnu")
        print("💡 Vérifiez que toutes les catégories sont présentes dans le message")
        return
    
    print(f"✅ PARSING RÉUSSI: {len(parsed_data['categories'])} catégories")
    
    # Suite du traitement
    analysis = analyzer.analyze_all_categories(parsed_data)
    now = datetime.now()
    hour_str = now.strftime('%H:%M')
    hour_key = now.strftime('%H:00')
    
    previous_data = storage.get_previous_hour_data(hour_key)
    comparison = None
    if previous_data:
        comparison = analyzer.compare_with_previous(analysis, previous_data)
    
    gaps_data = {cat: {'max_gap': data['max_gap'], 'gaps': data['gaps']} 
                 for cat, data in analysis.items()}
    storage.save_analysis(hour_key, gaps_data)
    
    bilan_msg = bot_logic.format_bilan(analysis, parsed_data['total_games'], hour_str, comparison)
    
    try:
        await context.bot.send_message(
            chat_id=DESTINATION_CHANNEL_ID,
            text=bilan_msg, 
            parse_mode='Markdown'
        )
        print(f"✅ Bilan envoyé vers {DESTINATION_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Erreur envoi vers {DESTINATION_CHANNEL_ID}: {e}")

# ============ SCHEDULER ============

async def auto_send_scheduler(context: ContextTypes.DEFAULT_TYPE):
    print(f"⏰ Scheduler démarré - Intervalle: {storage.get_interval_minutes()} min - Destination: {DESTINATION_CHANNEL_ID}")
    
    while True:
        try:
            if storage.is_auto_send_enabled():
                last_send_str = storage.get_last_auto_send()
                interval = storage.get_interval_minutes()
                
                should_send = False
                
                if not last_send_str:
                    should_send = storage.get_last_parsed_data() is not None
                else:
                    try:
                        last_send = datetime.fromisoformat(last_send_str)
                        next_send = last_send + timedelta(minutes=interval)
                        should_send = datetime.now() >= next_send
                    except:
                        should_send = True
                
                if should_send:
                    await send_bilan_to_destination(context)
            
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"❌ Erreur scheduler: {e}")
            await asyncio.sleep(60)

# ============ DÉMARRAGE ============

def run_flask():
    app.run(host=HOST, port=PORT, threaded=True)

def main():
    validation = validate_configuration()
    
    print("=" * 50)
    print("🤖 BOT D'ANALYSE D'ÉCARTS")
    print("=" * 50)
    
    if validation['errors']:
        print("\n❌ ERREURS DE CONFIGURATION:")
        for err in validation['errors']:
            print(f"   {err}")
        print("\n⚠️  Le bot risque de ne pas fonctionner correctement!\n")
    elif validation['warnings']:
        print("\n⚠️  AVERTISSEMENTS:")
        for warn in validation['warnings']:
            print(f"   {warn}")
        print()
    
    channels = get_channels_info()
    print(f"📺 Canaux configurés:")
    print(f"   Source:      {channels['source']}")
    print(f"   Destination: {channels['destination']}")
    print(f"👤 Admin:       {ADMIN_ID}")
    print(f"🔐 API:         ID {API_ID} configurée")
    print()
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print(f"🚀 Serveur web démarré sur port {PORT}")
    
    asyncio.run(run_bot())

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commandes publiques
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("statut", statut_command))
    application.add_handler(CommandHandler("verifier", verifier_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("historique", historique_command))
    application.add_handler(CommandHandler("restart", restart_command))
    
    # Commandes admin
    application.add_handler(CommandHandler("intervalle", intervalle_command))
    application.add_handler(CommandHandler("auto", auto_command))
    application.add_handler(CommandHandler("envoyer", envoyer_command))
    application.add_handler(CommandHandler("testenvoi", testenvoi_command))
    
    # Handler canal source
    application.add_handler(MessageHandler(
        filters.Chat(chat_id=SOURCE_CHANNEL_ID) & filters.TEXT, 
        handle_channel_message
    ))
    
    print(f"🤖 Bot Telegram démarré")
    print(f"⏱️  Intervalle auto: {storage.get_interval_minutes()} min")
    print(f"🤖 Envoi auto: {'Activé' if storage.is_auto_send_enabled() else 'Désactivé'}")
    print(f"🔍 Commande /verifier disponible pour tester les canaux")
    print()
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Vérification initiale des canaux (silencieuse)
    try:
        await update_channel_status_cache(application.bot)
    except Exception as e:
        print(f"⚠️  Impossible de vérifier les canaux au démarrage: {e}")
    
    # Démarrer scheduler
    scheduler_task = asyncio.create_task(auto_send_scheduler(application))
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        scheduler_task.cancel()
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt...")
        storage.save_data()
        sys.exit(0)
