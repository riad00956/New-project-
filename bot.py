import os
import logging
import asyncio
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Text
from dotenv import load_dotenv

load_dotenv()

# Load secrets
BOT_TOKEN = os.getenv("7938369063:AAH2kBm0jnbMNhJH6pUux7JBkHVTEYfBjnc")
OPENAI_API_KEY = os.getenv("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")

# Set up OpenAI
openai.api_key = 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

# Set up bot
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# --- States ---
class Form(StatesGroup):
    waiting_for_question = State()
    waiting_for_image_prompt = State()

# --- Keyboards ---
async def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💬 Ask Anything", callback_data="ask_gpt"),
        InlineKeyboardButton("🎨 Generate Image", callback_data="generate_image")
    )
    return markup

# --- Command Handlers ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Hi! I'm your AI assistant 🤖\nWhat would you like to do?", reply_markup=await main_menu())

# --- Callback Query Handlers ---
@dp.callback_query_handler(Text(startswith="ask_gpt"))
async def ask_gpt_start(callback: types.CallbackQuery):
    await callback.message.answer("🧠 What would you like to ask me?")
    await Form.waiting_for_question.set()
    await callback.answer()

@dp.callback_query_handler(Text(startswith="generate_image"))
async def image_prompt_start(callback: types.CallbackQuery):
    await callback.message.answer("🎨 What image do you want me to create?")
    await Form.waiting_for_image_prompt.set()
    await callback.answer()

# --- GPT Text Response ---
@dp.message_handler(state=Form.waiting_for_question)
async def handle_question(message: types.Message, state: FSMContext):
    await message.answer("Thinking... 🤔")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response.choices[0].message['content']
        await message.answer(answer)
    except Exception as e:
        await message.answer("⚠️ Error while generating response.")
        logging.error(e)
    await state.finish()

# --- Image Generator ---
@dp.message_handler(state=Form.waiting_for_image_prompt)
async def handle_image_prompt(message: types.Message, state: FSMContext):
    await message.answer("Creating image... 🖼️")
    try:
        image_response = openai.Image.create(
            prompt=message.text,
            n=1,
            size="512x512"
        )
        image_url = image_response['data'][0]['url']
        await message.answer_photo(photo=image_url)
    except Exception as e:
        await message.answer("⚠️ Failed to generate image.")
        logging.error(e)
    await state.finish()

# --- Run Bot ---
if __name__ == '__main__':
    print("Bot is running...")
    executor.start_polling(dp, skip_updates=True)
