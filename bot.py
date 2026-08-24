import os, threading, tempfile, requests
import telebot
from telebot import types
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("GROQ_KEY")
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)
user_data = {}

EXT = {
    "python": "py",
    "html": "html",
    "css": "css",
    "javascript": "js",
    "java": "java",
    "php": "php",
    "csharp": "cs",
    "c": "c",
    "sql": "sql",
    "flutter": "dart"
}

def ai(lang, prompt):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {AI_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.15,
            "messages": [
                {"role": "system", "content": f"Tu es expert {lang}. Génère code propre, sans erreur, production-ready. Uniquement code brut sans ```"},
                {"role": "user", "content": f"Crée {prompt} en {lang}. Code complet fonctionnel."}
            ]
        }, timeout=60).json()
    return r['choices'][0]['message']['content'].replace("```","").strip()

def menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🐍 Python (.py)", callback_data="L_python"),
        types.InlineKeyboardButton("🌐 HTML (.html)", callback_data="L_html"),
        types.InlineKeyboardButton("🎨 CSS (.css)", callback_data="L_css"),
        types.InlineKeyboardButton("⚡ JS (.js)", callback_data="L_javascript"),
        types.InlineKeyboardButton("☕ Java (.java)", callback_data="L_java"),
        types.InlineKeyboardButton("🐘 PHP (.php)", callback_data="L_php"),
    )
    return m

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id,
        "🤖 **DXS REGEN PRO**\n\n"
        ".......\n"
        "**De quoi as-tu besoin, choisis le langage selon ton besoin** 👇",
        reply_markup=menu()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith('L_'))
def pick(call):
    bot.answer_callback_query(call.id)
    lang = call.data.replace("L_","")
    user_data[call.from_user.id] = lang
    bot.send_message(call.message.chat.id,
        f"✅ **{lang.upper()}** sélectionné (format `.{EXT.get(lang,'txt')}`)\n\n"
        f"Envoie ton projet: `je veux créer une calculatrice`")

@bot.message_handler(func=lambda m: True)
def gen(m):
    if m.text.startswith('/'): return
    lang = user_data.get(m.from_user.id)
    if not lang:
        bot.reply_to(m, "Fais /start et choisis le langage d'abord", reply_markup=menu())
        return

    prompt = m.text
    ext = EXT.get(lang, "txt")
    wait = bot.send_message(m.chat.id, f"⏳ Génération en **{lang.upper()}** format `.{ext}`...")

    code = ai(lang, prompt)
    code_final = code + f"\n\n// DEV kco4p tech - {lang}.{ext}"

    # Si > 4000 caractères ->.txt + preview, sinon vrai format
    if len(code) > 4000:
        file_name = f"{prompt[:15]}.{ext}.txt"
        caption = f"✅ Code **{lang.upper()}** (trop long, en.txt)\n📋 `{prompt}`\n📄 Format original: `.{ext}`\n\nColle sur.txt\nDEV kco4p tech 🚀"
    else:
        file_name = f"{prompt[:15].replace(' ','_')}.{ext}"
        caption = f"✅ Code **{lang.upper()}** prêt\n📋 `{prompt}`\n📄 Format: `.{ext}`\n\nDEV kco4p tech 🚀"

    path = os.path.join(tempfile.gettempdir(), file_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code_final)

    with open(path, "rb") as f:
        bot.send_document(m.chat.id, f, caption=caption)

    # Aperçu code si pas trop long
    if len(code) < 3500:
        bot.send_message(m.chat.id, f"```{lang}\n{code[:3500]}\n```")

    os.remove(path)
    bot.delete_message(m.chat.id, wait.message_id)

@app.route('/')
def health(): return "FORMAT AUTO BOT RUNNING"
def run(): bot.infinity_polling()
if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
