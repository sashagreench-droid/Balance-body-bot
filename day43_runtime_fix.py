import bot
import db
from content import DAYS, DAY_TASKS

# Day 43 runtime compatibility fix.
# Some legacy navigation code expects a 3-item day tuple, while the current
# DAYS entries contain 5 fields. Keep the legacy flow untouched for all other
# days, but render Day 43 directly so Continue/Start never hits the bad unpack.
_original_menu = bot.menu


def _day43_header():
    info = DAYS[42]
    title = info[0]
    task = DAY_TASKS[43]
    intro = task[0]
    skill = info[3]
    return (
        f"💡 <b>ДЕНЬ 43 — {title}</b>\n\n"
        f"{intro}\n\n"
        f"🎯 Сегодня формируем навык:\n<b>{skill}</b>\n\n"
        "Когда будешь готова, переходи к практике."
    )


def _day43_practice():
    return DAY_TASKS[43][1]


async def _send_day43(q):
    await q.message.reply_text(
        _day43_header(),
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup([
            [bot.InlineKeyboardButton("➡️ К ПРАКТИКЕ", callback_data="practice43")],
            [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
            [bot.InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
        ]),
    )


async def _send_practice43(q):
    await q.message.reply_text(
        "📝 <b>ПРАКТИКА</b>\n\n" + _day43_practice() +
        "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».",
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup([
            [bot.InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
            [bot.InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
            [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        ]),
    )


async def menu_fixed(update, context):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    u = db.user(uid)

    if data in ("continue", "startday:43") and u and int(u["current_day"]) == 43:
        await q.answer()
        row = db.day_row(uid, 43)
        if row and row["status"] == "AVAILABLE":
            db.start_day(uid, 43)
        await _send_day43(q)
        return

    if data == "practice43" and u and int(u["current_day"]) == 43:
        await q.answer()
        await _send_practice43(q)
        return

    await _original_menu(update, context)


bot.menu = menu_fixed
