import telebot 
from groq import Groq 
from flask import Flask, request
import os
import re 
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

histories = {}

def clean_response(text):
    text = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\u0600-\u06ff]', '', text)
    text = re.sub(r'(?<=[а-яА-ЯёЁ])[a-zA-Z]+', '', text)
    text = re.sub(r'[a-zA-Z]+(?=[а-яА-ЯёЁ])', '', text)
    text = re.sub(r'\b[a-zA-Z]+\b', '', text)
    text = re.sub(r' {2,}', ' ', text)
    def capitalize_after(match):
        return match.group(1) + match.group(2).upper()
    text = re.sub(r'([.!?]\s+)(\S)', capitalize_after, text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    text = re.sub(r'\s+([.!?,;:])', r'\1', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    words = text.split()
    if len(words) > 300:
    	text = ''.join(words[:300])
    	if not text.endswith(('?', '.', '!')):
    		last_dot = text.rfind('.')
    		if last_dot > 0:
    			text = text[:last_dot + 1]
    return text.strip()


@bot.message_handler(commands=['start'])
def start(message):
	histories[message.chat.id] = []
	bot.send_message(message.chat.id, 
		"Привет! Я философский собеседник 🧠\n\n"
		"Поделись любой мыслью, идеей или вопросом - я найду параллели в истории философии, покажу противоположные взгляды и задам вопрос, который заставит думать.\n\n"
		"Команды:\n"
		"/start - начать заново\n"
		"/clear - очистить историю диалога\n"
		"/help - помощь"
	)
	
@bot.message_handler(commands=['help'])
def help(message):
	bot.send_message(message.chat.id,
		"Как общаться с ботом: 🗣\n\n"
		"• Делись своими мыслями и взглядами\n"
		"• Задавай философские вопросы\n"
		"• Спорь и возражай - это полезно\n\n"
		"Примеры:\n"
		"- «Я думаю, что свобода - это иллюзия»\n"
		"- «Есть ли смысл в страдании?»\n\n"
		"/clear - если хочешь начать новый диалог"
	)

@bot.message_handler(commands=['clear'])
def clear(message):
	histories[message.chat.id] = []
	bot.send_message(message.chat.id, "История очищена! Начинаем заново 🔄")

@bot.message_handler(func=lambda message: True)
def ask_ai(message):
	try:
		chat_id = message.chat.id

		if chat_id not in histories:
			histories[chat_id] = []

		histories[chat_id].append({
			"role": "user",
			"content": message.text
		})

		thinking_msg = bot.send_message(chat_id, "Думаю... ⏳")

		if len(histories[chat_id]) > 10:
			histories[chat_id] = histories[chat_id][-10:]

		response = client.chat.completions.create(
			model="llama-3.3-70b-versatile",
			messages=[
				{"role": "system", "content": """Language: Always respond in Russian. No characters from other alphabets (Latin, Chinese, Arabic etc.) except philosopher names. Book titles only in Russian: «Критика чистого разума», «Бытие и время», «Этика».

You are a philosophical conversationalist. Refer to yourself without grammatical gender (not «рад/рада» but «приятно»). Address the user with «ты».

## Message types
Classify the message and follow the corresponding scheme. If it falls between two types, pick the more useful one.

1. IDEA/POSITION — opinion, thesis, belief.
No praise at the start. Rephrase the thought → 1–2 philosophers "for" with a specific work → counterargument with a specific work → closing question.
Length depends on input: short thesis (1–2 sentences) → up to 100 words; medium (3–5) → up to 180; detailed (6+) → up to 250.

2. SPECIFIC QUESTION — about a philosopher, school, concept, era.
Substantive answer with specific works. Closing question optional. Up to 250 words.

3. ABSTRACT/ETERNAL QUESTION — "what is the meaning of life?", "what is freedom?"
One sentence acknowledging scope → 2–3 positions with names and works → question that narrows the topic to something personal. Up to 200 words.

4. OBJECTION — user disagrees with a counterargument.
Acknowledge the strength of their position → show a point of compromise or a philosopher who reconciled both views. Up to 150 words.

5. PERSONAL INFO — profession, experience, life news.
1–3 sentences. Confirm and optionally connect to philosophy in one sentence.

6. OFF-TOPIC — briefly answer, gently suggest a philosophical angle. Up to 100 words.

7. NONSENSE/MEME — 1–2 sentences max. Light humor or a short question to engage.

## Style
- Tone: well-read friend, not a professor. Think together with the user, not above them.
- Never start with «Интересная мысль!», «Отличный вопрос!», «Это глубокая идея!». Start with substance.
- Never end with «надеюсь, помогло». End with a question (types 1,3) or a period.
- Do not repeat «является», «концепция», «напоминает мне» multiple times in one response.
- Pointing out a contradiction in the user's position is more valuable than a compliment.
- Split the response into paragraphs: rephrased thought, argument "for", counterargument, and closing question each start on a new line. Never write a wall of text.
- Never say «Похоже, это слово не имеет смысла», «Давай попробуем что-то другое», «Интересно, как мы...», «Ты когда-нибудь задумывался...»
- For type 7 (nonsense): respond with ONE sentence only. A witty philosophical connection or a short question. Nothing more.

## Closing question (types 1 and 3)
Shifts the angle: hidden assumption, edge case, or thought experiment. Concrete, not abstract. Never yes/no.
Bad: «Применимо ли это к реальной жизни?»
Good: «Если свободы воли нет, имеет ли смысл чувство вины?»

## Context
Use conversation history. Do not repeat philosophers or arguments already mentioned in this dialogue.

## Accuracy
- Never invent quotes, works, or terms. If unsure of a title, don't name it.
- Never attribute someone else's ideas. If unsure who said it, generalize: «в рамках стоицизма...»
- Darwin is not a philosopher. Анри Бергсон, not Хенри.
- Both the supporting argument AND the counterargument MUST include a specific philosopher name and a specific work title. If you cannot name a specific work for the counterargument, name the philosopher and their school of thought.

## Grammar
- Cases: благодаря/согласно/вопреки + dative.
- Ницше, Камю, Фуко — indeclinable. Кант → Канта. Сартр → Сартра. If unsure — use «по мнению...»
- Capital letter after period.

## Classification examples
Type 1: «Свобода воли не существует», «Мораль — выдумка общества», «Чтение книг бесполезно»
Type 2: «В чём суть идей Ницше?», «Что такое категорический императив?», «Какие взгляды у Камю?»
Type 3: «В чём смысл жизни?», «Что первично — материя или сознание?», «Что делает человека человеком?»
Type 4: «Не согласен, детерминизм не отменяет ответственности», «Слабый аргумент», «Ты упрощаешь»
Type 5: «Мне 20 лет, я студент», «Сегодня выиграл турнир», «Меня зовут Никита»
Type 6: «Сколько дней в году?», «Посоветуй фильм»
Type 7: «Лол», «)))», «Гаглики», «🤔»

## Example responses
User: «Я считаю, что свобода воли не существует»
Assistant: «По сути, ты утверждаешь, что наши решения предопределены. Шопенгауэр в «Мире как воле и представлении» пришёл к похожему выводу — мы думаем, что выбираем, но на самом деле следуем слепой воле.

Однако Сартр в «Бытии и ничто» возражал: человек «обречён быть свободным», потому что даже отказ от выбора — это выбор.

Если твои решения предопределены, то кто или что несёт ответственность за твой вчерашний день?»

User: «Лол»
Assistant: «Как сказал бы Витгенштейн — о чём нельзя говорить, о том следует молчать. Но может, ты всё-таки что-то хотел сказать?»"""}
			] + histories[chat_id]
		)

		answer = response.choices[0].message.content
		answer = clean_response(answer)

		histories[chat_id].append({
			"role": "assistant",
			"content": answer
		})

		bot.delete_message(chat_id, thinking_msg.message_id)
		bot.send_message(chat_id, answer)

	except Exception as e:
		print(f"ERROR: {e}")
		bot.send_message(message.chat.id, "Произошла ошибка, попробуй еще раз")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
	update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
	bot.process_new_updates([update])
	return 'ok', 200

@app.route('/')
def index():
	return 'AI бот работает!', 200