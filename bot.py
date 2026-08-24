import os
import telebot
from groq import Groq
from flask import Flask
import threading
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)

user_lang = {}
LANGUAGES = {
    "python": ".py",
    "html": ".html",
    "css": ".css",
    "js": ".js",
    "java": ".java",
    "php": ".php"
}

@bot.message_handler(commands=['start'])
def start(m):
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    for lang, ext in LANGUAGES.items():
        markup.add(telebot.types.InlineKeyboardButton(f"{lang.upper()} ({ext})", callback_data=lang))
    bot.send_message(m.chat.id, "👋 KCØRP DECRYPTOR\n\nChoisis ton langage :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    lang = call.data
    user_lang[call.from_user.id] = lang
    bot.answer_callback_query(call.id, f"{lang} sélectionné")
    bot.send_message(call.message.chat.id, f"✅ {lang.upper()} sélectionné (format {LANGUAGES[lang]})\n\nEnvoie ton projet: ex: je veux créer une calculatrice")

@bot.message_handler(func=lambda m: True)
def handle_project(m):
    lang = user_lang.get(m.from_user.id)
    if not lang:
        return bot.send_message(m.chat.id, "Fais /start et choisis le langage d'abord 👆")

    bot.send_chat_action(m.chat.id, 'typing')

    prompt = f"""
    Tu es un expert développeur {lang}.
    Génère un code COMPLET et FONCTIONNEL pour : {m.text}
    Langage: {lang}
    Donne uniquement le code, bien commenté, prêt à l'emploi.
    Pas d'explication longue, juste le code.
    """

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000
        )
        code = res.choices[0].message.content

        # Envoi avec format code
        if len(code) > 4000:
            # Si code trop long, envoie en 2 parties
            bot.send_message(m.chat.id, f"Voici ton projet en {lang} (partie 1/2):\n\n```{lang}\n{code[:4000]}\n```", parse_mode="Markdown")
            bot.send_message(m.chat.id, f"```{lang}\n{code[4000:]}\n```", parse_mode="Markdown")
        else:
            bot.send_message(m.chat.id, f"Voici ton projet en {lang}:\n\n```{lang}\n{code}\n```", parse_mode="Markdown")

    except Exception as e:
        bot.send_message(m.chat.id, f"Erreur: {e}")

# Flask pour Render
app = Flask(__name__)
@app.route('/')
def home():
    return "KCORP Bot is running ✅"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

# Anti-conflict polling
while True:
    try:
        print("Bot polling started...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Polling error: {e} - retry in 5s")
        time.sleep(5)
