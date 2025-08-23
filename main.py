import asyncio
import json
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

TOKEN = "8227967518:AAGT5-vanmJeiaAQNh_lSHCYYAHqc-ch1N0"  # 🔑 BotFather token
dp = Dispatcher()

# JSON fayldan testlarni yuklash
with open("test.json", "r", encoding="utf-8") as f:
    tests_data = json.load(f)

# Har bir user uchun sessiya saqlash
user_sessions = {}  # user_id -> {"tests": [...], "index": 0, "score": 0, "mode": "it/dmed/quiz"}

# Asosiy tugmalar
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🖥 IT testlari")],
        [KeyboardButton(text="🏥 DMED testlari")],
        [KeyboardButton(text="🎯 20 talik Quiz")],
    ],
    resize_keyboard=True,
)


# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Salom! 🧪 Quiz botga xush kelibsiz!\nQaysi testni ishlamoqchisiz?",
        reply_markup=main_kb,
    )


# IT testlari
@dp.message(F.text == "🖥 IT testlari")
async def it_test_handler(message: Message):
    user_sessions[message.from_user.id] = {
        "tests": tests_data["it_tests"],
        "index": 0,
        "score": 0,
        "mode": "it",
    }
    await send_next_question(message.bot, message.from_user.id)


# DMED testlari
@dp.message(F.text == "🏥 DMED testlari")
async def dmed_test_handler(message: Message):
    user_sessions[message.from_user.id] = {
        "tests": tests_data["dmed_tests"],
        "index": 0,
        "score": 0,
        "mode": "dmed",
    }
    await send_next_question(message.bot, message.from_user.id)


# 20 talik Quiz
@dp.message(F.text == "🎯 20 talik Quiz")
async def quiz20_handler(message: Message):
    it_random = random.sample(tests_data["it_tests"], 10)
    dmed_random = random.sample(tests_data["dmed_tests"], 10)
    combined = it_random + dmed_random
    random.shuffle(combined)

    user_sessions[message.from_user.id] = {
        "tests": combined,
        "index": 0,
        "score": 0,
        "mode": "quiz20",
    }
    await send_next_question(message.bot, message.from_user.id)


# Savol yuborish (A, B, C, D ko‘rinishida)
async def send_next_question(bot: Bot, user_id: int):
    session = user_sessions.get(user_id)
    if not session:
        return

    if session["index"] >= len(session["tests"]):
        # Test tugadi
        total = len(session["tests"])
        correct = session["score"]
        await bot.send_message(
            user_id,
            f"🏁 Test tugadi!\n✅ To‘g‘ri: {correct}\n❌ Noto‘g‘ri: {total - correct}\nUmumiy: {total}",
        )
        del user_sessions[user_id]
        return

    savol = session["tests"][session["index"]]
    text = f"{session['index']+1}. {savol['savol']}\n\n"

    letters = ["A", "B", "C", "D"]
    variants_text = "\n".join(
        [f"{letters[i]}. {v}" for i, v in enumerate(savol["variantlar"])]
    )
    text += variants_text

    buttons = [
        [InlineKeyboardButton(text=letters[i], callback_data=str(i))]
        for i in range(len(savol["variantlar"]))
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.send_message(user_id, text, reply_markup=kb)


# Javobni tekshirish
@dp.callback_query(F.data)
async def answer_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    session = user_sessions.get(user_id)
    if not session:
        await callback.answer("❗ Sessiya topilmadi")
        return

    savol = session["tests"][session["index"]]
    index = int(callback.data)
    tanlangan = savol["variantlar"][index]
    togri = savol["javob"]

    if tanlangan == togri:
        session["score"] += 1
        await bot.send_message(user_id, "✅ To‘g‘ri!")
    else:
        await bot.send_message(user_id, f"❌ Noto‘g‘ri!\nTo‘g‘ri javob: {togri}")

    session["index"] += 1
    await callback.answer()
    await send_next_question(bot, user_id)


# Botni ishga tushirish
async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
