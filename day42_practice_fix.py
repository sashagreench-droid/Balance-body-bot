import bot
import db

# Day 42 — dedicated practice renderer.
# This bypasses legacy day wrappers and reads the practice payload safely.
_original_show_practice = bot.show_practice


async def show_practice_fixed(q, context):
    await q.answer()
    uid = q.from_user.id
    u = db.user(uid)
    if not u:
        await q.message.reply_text("Не удалось найти профиль. Нажми /start ❤️")
        return

    n = u["current_day"]
    if n != 42:
        return await _original_show_practice(q, context)

    item = bot.DAY_TASKS.get(42)
    if not item or len(item) < 3:
        await q.message.reply_text("Не удалось загрузить практику Дня 42. Попробуй ещё раз ❤️")
        return

    practice = item[1]
    text = "📝 <b>ПРАКТИКА</b>\n\n" + practice + "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА»."
    buttons = [
        [bot.InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [bot.InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ]
    await q.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup(buttons),
    )


bot.show_practice = show_practice_fixed
