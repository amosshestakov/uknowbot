import os
from dotenv import load_dotenv
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, CallbackContext
from db import init_db, save_user, get_user_data
from bot_menu import start_menu, show_poster
from transliterate import translit
import re

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize database
init_db()

# Stages
GENDER, PHONE, NAME, SELECT_YEAR, SELECT_MONTH, SELECT_DAY = range(6)

# Inline button callback data
MALE, FEMALE = 'male', 'female'


def delete_last_bot_message(context: CallbackContext, chat_id: int) -> None:
    if 'last_bot_message' in context.user_data:
        context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['last_bot_message'])
        del context.user_data['last_bot_message']


def is_russian(text):
    return re.fullmatch(r'[А-Яа-яЁё\s]+', text) is not None


def generate_qr_code(user_name, user_id):
    qr_code_dir = 'qr_codes'
    if not os.path.exists(qr_code_dir):
        os.makedirs(qr_code_dir)
        print(f"Directory {qr_code_dir} created")

    transliterated_name = translit(user_name, 'ru', reversed=True).replace(' ', '_')
    file_path = os.path.join(qr_code_dir, f"{transliterated_name}_qrcode.png")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(f"user_id:{user_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path, format="PNG")

    if os.path.exists(file_path):
        print(f"QR code saved successfully at {file_path}")
    else:
        print(f"Failed to save QR code at {file_path}")

    return file_path


def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    user_data = get_user_data(user_id)

    if user_data:
        user_info = (
            f"Вы уже зарегистрированы.\n"
            f"Имя: {user_data['name']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Пол: {user_data['gender']}\n"
            f"Дата рождения: {user_data['birth_date']}\n"
            f"QR-код: {user_data['qr_code_path']}"
        )
        update.message.reply_text(user_info)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Парень", callback_data=MALE)],
        [InlineKeyboardButton("Девушка", callback_data=FEMALE)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = update.message.reply_text('Укажи свой пол - ты парень или девушка?', reply_markup=reply_markup)
    context.user_data['last_bot_message'] = message.message_id
    return GENDER


def gender(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    delete_last_bot_message(context, query.message.chat_id)

    context.user_data['gender'] = query.data
    message = query.message.reply_text(
        'Отправь свой номер телефона по кнопке ниже. Обещаю, не будем тебя спамить🙏',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton('Отправить номер', request_contact=True)]], one_time_keyboard=True)
    )
    context.user_data['last_bot_message'] = message.message_id
    return PHONE


def phone(update: Update, context: CallbackContext) -> int:
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    delete_last_bot_message(context, update.message.chat_id)
    message = update.message.reply_text('Введите ваше имя и фамилию (например, Иван Иванов):')
    context.user_data['last_bot_message'] = message.message_id
    return NAME


def name(update: Update, context: CallbackContext) -> int:
    name_surname = update.message.text.split()
    delete_last_bot_message(context, update.message.chat_id)
    if len(name_surname) < 2:
        message = update.message.reply_text('Пожалуйста, введите ваше имя и фамилию (например, Иван Иванов):')
        context.user_data['last_bot_message'] = message.message_id
        return NAME

    full_name = ' '.join(name_surname)
    if not is_russian(full_name):
        message = update.message.reply_text('Пожалуйста, введите ваше имя и фамилию на русском языке (например, Иван Иванов):')
        context.user_data['last_bot_message'] = message.message_id
        return NAME

    context.user_data['name'] = full_name

    years = [InlineKeyboardButton(str(year), callback_data=str(year)) for year in range(1930, 2008)]
    years_markup = InlineKeyboardMarkup([years[i:i + 5] for i in range(0, len(years), 5)])

    message = update.message.reply_text('Выберите год своего рождения:', reply_markup=years_markup)
    context.user_data['last_bot_message'] = message.message_id
    return SELECT_YEAR


def select_year(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    delete_last_bot_message(context, query.message.chat_id)

    context.user_data['birth_year'] = query.data

    months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    month_buttons = [InlineKeyboardButton(month, callback_data=str(index + 1)) for index, month in enumerate(months)]
    months_markup = InlineKeyboardMarkup([month_buttons[i:i + 3] for i in range(0, len(month_buttons), 3)])

    message = query.message.reply_text('Выберите месяц своего рождения:', reply_markup=months_markup)
    context.user_data['last_bot_message'] = message.message_id
    return SELECT_MONTH


def select_month(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    delete_last_bot_message(context, query.message.chat_id)

    context.user_data['birth_month'] = query.data

    days = [InlineKeyboardButton(str(day), callback_data=str(day)) for day in range(1, 32)]
    days_markup = InlineKeyboardMarkup([days[i:i + 7] for i in range(0, len(days), 7)])

    message = query.message.reply_text('Выбери день своего рождения:', reply_markup=days_markup)
    context.user_data['last_bot_message'] = message.message_id
    return SELECT_DAY


def select_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    delete_last_bot_message(context, query.message.chat_id)

    context.user_data['birth_day'] = query.data
    birth_date = f"{context.user_data['birth_year']}-{context.user_data['birth_month']}-{context.user_data['birth_day']}"

    user_id = query.message.from_user.id
    qr_code_path = generate_qr_code(context.user_data['name'], user_id)

    if not os.path.exists(qr_code_path):
        query.message.reply_text("Ошибка при создании QR-кода. Попробуйте еще раз.")
        return ConversationHandler.END

    save_user(
        user_id,
        context.user_data['name'],
        context.user_data['phone'],
        context.user_data['gender'],
        birth_date,
        qr_code_path
    )

    user_data = get_user_data(user_id)
    if user_data:
        user_info = (
            f"Имя: {user_data['name']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Пол: {'Мужской' if user_data['gender'] == 'male' else 'Женский'}\n"
            f"Дата рождения: {user_data['birth_date']}\n"
            f"QR-код: {user_data['qr_code_path']}"
        )

        query.message.reply_text(
            'Регистрация завершена! Теперь вы можете использовать меню. Используйте команду /menu для доступа к меню.'
        )
        query.message.reply_text(f"Данные, которые вы ввели:\n{user_info}")
        query.message.reply_photo(photo=open(qr_code_path, 'rb'))

    else:
        query.message.reply_text("Ошибка при получении данных пользователя.")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    delete_last_bot_message(context, update.message.chat_id)
    update.message.reply_text('Отмена регистрации.')
    return ConversationHandler.END


def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [CallbackQueryHandler(gender, pattern=f"^{MALE}$|^{FEMALE}$")],
            PHONE: [MessageHandler(Filters.contact, phone)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            SELECT_YEAR: [CallbackQueryHandler(select_year)],
            SELECT_MONTH: [CallbackQueryHandler(select_month)],
            SELECT_DAY: [CallbackQueryHandler(select_day)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('menu', start_menu))
    dispatcher.add_handler(CallbackQueryHandler(show_poster, pattern='^(prev|next|exit)$'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
