from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode


# Ініціалізація змінних
admin_chat_id = "-1002099677956"  # Telegram ID чату адміністратора
channel_id = "-1002039222512"  # Telegram ID каналу для публікацій
token = "6961512157:AAFAKECDyKXMQf_KAbvmJZQbmMlFTYT9d9c"  # Ваш реальний токен бота

# Словник для збереження статусу постів і ID користувачів
posts_status = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        'Привіт! \n\n'
        '- Напиши обʼяву про роботу або пошук роботи\n'
        '- Додай одне зображення\n'
        '- Відправ повідомлення і буде тобі щастя\n\n'
        '😈'
    )
    await update.message.reply_text(welcome_text)

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.caption if update.message.photo else update.message.text
    photo = update.message.photo[-1].file_id if update.message.photo else None
    
    posts_status[update.message.message_id] = {
        "status": "pending",
        "user_id": update.message.from_user.id,
        "text": text,
        "photo": photo,
    }
    
    keyboard_admin = [
        [InlineKeyboardButton("Схвалити", callback_data=f'approve_{update.message.message_id}'),
         InlineKeyboardButton("Відхилити", callback_data=f'reject_{update.message.message_id}')]
    ]
    reply_markup_admin = InlineKeyboardMarkup(keyboard_admin)
    if photo:
        await context.bot.send_photo(chat_id=admin_chat_id, photo=photo, caption=text, reply_markup=reply_markup_admin)
    else:
        await context.bot.send_message(chat_id=admin_chat_id, text=text, reply_markup=reply_markup_admin)
    await update.message.reply_text("Дякую за повідомлення, воно скоро з'явиться на каналі")

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action, message_id_str = query.data.split('_')
    message_id = int(message_id_str)
    message_info = posts_status.get(message_id)

    if not message_info:
        await context.bot.send_message(chat_id=admin_chat_id, text="Повідомлення не знайдено або вже було оброблено.")
        return

    user_id = message_info["user_id"]

    try:
        if action == 'approve' and message_info["status"] == "pending":
            if message_info["photo"]:
                await context.bot.send_photo(chat_id=channel_id, photo=message_info["photo"], caption=message_info["text"])
            else:
                await context.bot.send_message(chat_id=channel_id, text=message_info["text"])
            posts_status[message_id]["status"] = "approved"
            await context.bot.send_message(chat_id=user_id, text="Ваш пост опубліковано.")
        elif action == 'reject' and message_info["status"] == "pending":
            posts_status[message_id]["status"] = "rejected"
            await context.bot.send_message(chat_id=user_id, text="Ваш пост відхилено.")
    except BadRequest as e:
        print(f"Виникла помилка: {e}")

async def handle_write_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=query.from_user.id, text="Будь ласка, надішліть свій наступний пост.")

def main():
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, submit))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, submit))  # Оновлення для обробки фото
    application.add_handler(CallbackQueryHandler(handle_approval, pattern='^(approve|reject)_'))
    application.add_handler(CallbackQueryHandler(handle_write_more, pattern='^write_more$'))

    application.run_polling()

if __name__ == '__main__':
    main()
