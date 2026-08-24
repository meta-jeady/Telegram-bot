import os
import telebot
from groq import Groq
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")
bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)

user_lang = {}

LANGUAGES = {
    "python": ".py", "html": ".html", "css": ".css",
    "js": ".js", "java": ".java", "php": ".php"
}

@bot.message_handler(commands=['start'])
def start(m):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for lang, ext in LANGUAGES.items():
        markup.add(telebot.types.InlineKeyboardButton(f"{lang.upper()} ({ext})", callback_data=lang))
    bot.send_message(m.chat.id, "Fais /start et choisis le langage d'abord", reply_markup=markup)

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
        return bot.send_message(m.chat.id, "Fais /start et choisis le langage d'abord")

    prompt = f"Génère un code complet en {lang} pour : {m.text}. Donne uniquement le code, bien commenté."
    bot.send_chat_action(m.chat.id, 'typing')

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        code = res.choices[0].message.content
        bot.send_message(m.chat.id, f"Voici ton projet en {lang}:\n\n```{lang}\n{code}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(m.chat.id, f"Erreur: {e}")

# Pour que Render ne coupe pas
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

threading.Thread(target=run_flask).start()
bot.infinity_polling()
