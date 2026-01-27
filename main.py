"""
Point d'entrée principal du Bot Telegram
"""
import os
import sys
import asyncio
import threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN, PORT, HOST, SOURCE_CHANNEL_ID, get_current_journee
from storage import Storage
from parser import MessageParser
from analyzer import GapAnalyzer
from bot import BotLogic

app = Flask(__name__)

storage = Storage()
parser = MessageParser()
analyzer = GapAnalyzer()
bot_logic = BotLogic(storage)

@app.route('/')
def home():
    return f"""
    <h1>🤖 Bot d'Analyse d'Écarts Actif</h1>
    <p>🕐 Heure: {datetime.now().strftime('%H:%M:%S')}</p>
    <p>📅 {get_current_journee().replace('_', ' ')}</p>
    <p>🎯 Source: {storage.get_source_channel()}</p>
    <p>📤 Dest: {storage.get_dest_channel()}</p>
    <p>✅ Port: {PORT}</p>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============ COMMANDES ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """🌸 **Bienvenue sur le Bot d'Analyse d'Écarts** 🌸

Je surveille les statistiques et analyse les écarts entre numéros.

📋 **Commandes:**
/start - Démarrer
/statut - Voir les IDs des canaux
/test - Tester l'analyse
/historique - Voir l'historique
/restart - Redémarrer

⏰ Analyse automatique à chaque heure pile.
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def statut_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source = storage.get_source_channel()
    dest = storage.get_dest_channel()
    msg = bot_logic.format_statut(source, dest)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_data = {
        'total_games': 60,
        'categories': {
            '3/2': [1330, 1342, 1352, 1361, 1366, 1370, 1374, 1375],
            '3/3': [1322, 1323, 1325, 1329, 1332, 1335, 1337, 1338, 1340, 1349, 1350, 1351, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1362, 1363, 1369, 1372, 1377, 1378, 1379],
            '2/2': [1321, 1324, 1326, 1327, 1328, 1331, 1336, 1339, 1341, 1345, 1346, 1348, 1367, 1368, 1373, 1376, 1380],
            '2/3': [1333, 1334, 1343, 1344, 1347, 1360, 1364, 1365, 1371],
            'Victoire Joueur': [1322, 1330, 1333, 1335, 1336, 1339, 1341, 1343, 1344, 1345, 1347, 1349, 1351, 1355, 1358, 1362, 1363, 1364, 1367, 1369, 1371, 1373, 1375, 1377, 1378, 1379, 1380],
            'Victoire Banquier': [1321, 1323, 1325, 1326, 1327, 1328, 1329, 1331, 1334, 1337, 1338, 1340, 1342, 1346, 1348, 1350, 1352, 1353, 1356, 1357, 1359, 1360, 1361, 1365, 1366, 1370, 1374, 1376],
            'Match Nul': [1324, 1332, 1354, 1368, 1372],
            'Pair': [1321, 1323, 1324, 1326, 1327, 1331, 1332, 1334, 1335, 1337, 1338, 1340, 1341, 1344, 1348, 1349, 1350, 1353, 1354, 1357, 1359, 1362, 1365, 1367, 1368, 1369, 1370, 1372, 1376, 1377, 1378],
            'Impair': [1322, 1325, 1328, 1329, 1330, 1333, 1336, 1339, 1342, 1343, 1345, 1346, 1347, 1351, 1352, 1355, 1356, 1358, 1360, 1361, 1363, 1364, 1366, 1371, 1373, 1374, 1375, 1379, 1380]
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

# ============ GESTION MESSAGES CANAL ============

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat_id == SOURCE_CHANNEL_ID:
        message_text = update.channel_post.text
        
        if not message_text or 'STATISTIQUES COMPLÈTES' not in message_text:
            return
        
        print(f"📥 Message reçu à {datetime.now().strftime('%H:%M')}")
        
        parsed_data = parser.parse_message(message_text)
        if not parsed_data:
            print("⚠️ Message incomplet")
            return
        
        print(f"✅ {len(parsed_data['categories'])} catégories trouvées")
        
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
        
        dest_channel = storage.get_dest_channel()
        if dest_channel:
            try:
                await context.bot.send_message(chat_id=dest_channel, text=bilan_msg, parse_mode='Markdown')
                print(f"✅ Bilan envoyé")
            except Exception as e:
                print(f"❌ Erreur envoi: {e}")

# ============ DÉMARRAGE CORRIGÉ ============

def run_flask():
    app.run(host=HOST, port=PORT, threaded=True)

def main():
    """Fonction principale synchrone"""
    # Lancer Flask dans un thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print(f"🚀 Serveur web démarré sur port {PORT}")
    
    # Créer la boucle asyncio et exécuter le bot
    asyncio.run(run_bot())

async def run_bot():
    """Fonction async pour le bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("statut", statut_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("historique", historique_command))
    application.add_handler(CommandHandler("restart", restart_command))
    
    application.add_handler(MessageHandler(
        filters.Chat(chat_id=SOURCE_CHANNEL_ID) & filters.TEXT, 
        handle_channel_message
    ))
    
    print(f"🤖 Bot Telegram démarré")
    print(f"🎯 Source: {SOURCE_CHANNEL_ID}")
    print(f"📤 Dest: {storage.get_dest_channel()}")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Garder le bot en vie
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt...")
        storage.save_data()
        sys.exit(0)
    
