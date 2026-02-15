from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import os

# === ВСТАВЬ СВОЙ ТОКЕН ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8473700808:AAECogv8XMONhPJQE6oBblOjctgUuJi-MeQ")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "7887918891"))  # твой ID в Telegram

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === Подключённые ПК ===
connected_pcs = {}

# === Команда /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.chat.id != ALLOWED_CHAT_ID:
        await message.answer("🔒 Доступ запрещён!")
        return
    await show_connected_pcs(message)

# === Показать подключённые ПК ===
async def show_connected_pcs(message: types.Message):
    if not connected_pcs:
        await message.answer("❌ ПК в сети не обнаружены.")
        return

    text = "🖥️ Подключённые компьютеры:\n"
    keyboard = []
    for pc_id, info in connected_pcs.items():
        text += f"• {pc_id}: онлайн (IP: {info['ip']})\n"
        keyboard.append([KeyboardButton(text=f"Выбрать {pc_id}")])
    keyboard.append([KeyboardButton(text="🔄 Обновить")])
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer(text, reply_markup=reply_markup)

# === Приём сообщений от ПК ===
@dp.message()
async def handle_message(message: types.Message):
    if message.chat.id == ALLOWED_CHAT_ID:
        # Это от тебя
        text = message.text.lower()
        if text.startswith("выбрать "):
            pc_id = text.replace("выбрать ", "").strip()
            if pc_id in connected_pcs:
                await message.answer(f"✅ Управление передано {pc_id}")
            elif text == "🔄 обновить":
                await show_connected_pcs(message)
            else:
                await message.answer("❌ Такой ПК не найден.")
        return

    # Это сообщение от ПК
    text = message.text
    if "|" in text:
        parts = text.split("|", 2)
        if len(parts) == 3 and parts[1] == "online":
            pc_id = parts[0]
            ip = parts[2]
            connected_pcs[pc_id] = {"ip": ip}
            await bot.send_message(ALLOWED_CHAT_ID, f"✅ {pc_id} подключён (IP: {ip})")

app = Flask(__name__)

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = types.Update(**request.json)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.feed_update(bot, update))
    return {"status": "ok"}

if __name__ == "__main__":
    print("🤖 Бот запущен через Flask webhook...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
