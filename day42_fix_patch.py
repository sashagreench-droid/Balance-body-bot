import bot
import db

# Day 42 safety fix: some legacy wrappers can raise during the generic
# begin_day renderer because they expect a different day metadata shape.
# Keep the normal renderer for every other day and provide a stable Day 42
# renderer instead of exposing a technical error to the user.
_original_begin_day = bot.begin_day


async def begin_day_fixed(q, n):
    if n != 42:
        return await _original_begin_day(q, n)

    try:
        return await _original_begin_day(q, n)
    except ValueError as e:
        if "too many values to unpack" not in str(e):
            raise

        uid = q.from_user.id
        db.start_day(uid, n)

        day = bot.day_info(n)
        task = bot.task_info(n)
        title = day[1]
        intro = task[0]

        await q.message.reply_text(
            f"💡 <b>ДЕНЬ {n} — {title}</b>\n\n{intro}\n\n"
            "🎯 <b>Сегодня формируем навык:</b>\n"
            "Создаю альтернативы еде как способу отдыха\n\n"
            "Когда будешь готова, переходи к практике.",
            parse_mode="HTML",
            reply_markup=bot.InlineKeyboardMarkup([
                [bot.InlineKeyboardButton("➡️ К ПРАКТИКЕ", callback_data="practice")],
                [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
                [bot.InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
            ]),
        )


bot.begin_day = begin_day_fixed
