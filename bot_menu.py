import os
import qrcode
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CallbackContext, Updater, CommandHandler
from dotenv import load_dotenv
from db import get_qr_code, get_user_data

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EVENT_ADDRESS = "1234 Event Street, City, Country"
POSTERS = ["poster1.jpg", "poster2.jpg", "poster3.jpg"]

def send_event_address(update: Update, context: CallbackContext) -> None:
    update.callback_query.message.reply_text(f"Адрес мероприятия:\n{EVENT_ADDRESS}")

def send_user_ticket(update: Update, context: CallbackContext) -> None:
    phone = update.callback_query.from_user.phone_number
    qr_code = get_qr_code(phone)
    if qr_code:
        context.bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=qr_code, caption="Ваш билет")
    else:
        update.callback_query.message.reply_text("Не удалось найти ваш QR-код. Пожалуйста, зарегистрируйтесь снова.")

def show_poster(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    poster_index = int(context.user_data.get('poster_index', 0))
    if query.data == 'next':
        poster_index = (poster_index + 1) % len(POSTERS)
    elif query.data == 'prev':
        poster_index = (poster_index - 1) % len(POSTERS)
    context.user_data['poster_index'] = poster_index
    query.answer()
    keyboard = [
        [InlineKeyboardButton("⬅️", callback_data='prev'), InlineKeyboardButton("❌", callback_data='exit'),
         InlineKeyboardButton("➡️", callback_data='next')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_media(media=open(POSTERS[poster_index], 'rb'), reply_markup=reply_markup)

def start_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ваш билет", callback_data='ticket')],
        [InlineKeyboardButton("Адрес мероприятия", callback_data='address')],
        [InlineKeyboardButton("Постеры", callback_data='poster')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

def menu(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data = get_user_data(user_id)

    if user_data:
        # Пользователь зарегистрирован, показ меню
        start_menu(update, context)
    else:
        # Пользователь не зарегистрирован
        update.message.reply_text("Пожалуйста, зарегистрируйтесь, чтобы получить доступ к меню.")
