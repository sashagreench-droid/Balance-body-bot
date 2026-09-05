import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

_original_show_practice = bot.show_practice


async def show_practice_day47(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 47:
        await _original_show_practice(q, context)
        return

    text = (
        "📝 <b>ПРАКТИКА — СЦЕНАРИЙ «Я РЕШАЮ САМА»</b>\n\n"
        "Представь ситуацию:\n"
        "Ты весь день занята. Нормального обеда не было, вечером тебя зовут в ресторан. "
        "Ты не знаешь заранее, что будет в меню, и сегодня не хочешь считать калории.\n\n"
        "Твоя задача — самостоятельно принять решение, используя навыки курса.\n\n"
        "Ответь одним сообщением:\n"
        "1️⃣ Что выберешь поесть в ресторане?\n"
        "2️⃣ На какой навык курса опираешься?\n"
        "3️⃣ Что сделаешь, если съешь больше, чем планировала?\n"
        "4️⃣ Что сделаешь завтра — без попытки «компенсировать» сегодняшний день?\n\n"
        "Здесь нет единственно правильного меню. Нам важно увидеть твою логику решения."
    )
    buttons = [
        [InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")]
    ]
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))


bot.show_practice = show_practice_day47
