import telebot 
from groq import Groq 
from flask import Flask, request
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

histories = {}

@bot.message_handler(commands=['start'])
def start(message):
	histories[message.chat.id] = []
	bot.send_message(message.chat.id, "Привет! Я AI бот. Задай мне любой вопрос 🤖")

@bot.message_handler(commands=['clear'])
def clear(message):
	histories[message.chat.id] = []
	bot.send_message(message.chat.id, "История очищена! Начинаем заново 🔄")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
	chat_id = message.chat.id 

	if chat_id not in histories:
		histories[chat_id] = []

	histories[chat_id].append({
		"role": "user",
		"content": message.text
	})

	bot.send_message(chat_id, "Думаю... ⏳")

	response = client.chat.completions.create(
		model="llama-3.3-70b-versatile",
		messages=[
			{"role": "system", "content": """Ты философский собеседник - эрудит и полемист. 
			Когда пользователь делится своими взглядами или идеями, ты:
			1. Сразу называешь конкретных философов с похожими взглядами
			2. Обязательно приводишь противоположную философсую позицию 
			3. Задаёшь один острый провокационный вопрос в конце
			4. Споришь, не соглашаешься слепо
			5. Не предлагаешь психологичсекую помощь - это философский диалог, а не терапия
			6. Говоришь живо, как умный друг - без занудства и Wikipedia стиля

			Отвечай на русском языке. Будь краток - не более 150 слов"""}
		] + histories[chat_id]
	)

	answer = response.choices[0].message.content

	histories[chat_id].append({
		"role": "assistant",
		"content": answer
	})

	bot.send_message(chat_id, answer)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
	update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
	bot.process_new_updates([update])
	return 'ok', 200

@app.route('/')
def index():
	return 'AI бот работает!', 200