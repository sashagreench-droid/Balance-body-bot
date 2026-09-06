"""BALANCE BODY — final-course routing for the 50-day version."""

import bot
import db

COURSE_DAYS = 50
FINAL_SENTINEL = COURSE_DAYS + 1

_real_complete_day = db.complete_day
_real_init_db = db.init_db
_real_show_day = bot.show_day
_real_start = bot.start
_real_show_progress = bot.show_progress


def _mark_existing_graduates():
    """Migrate only users who already completed the new Day 50."""
    con = db.connect()
    rows = con.execute("SELECT tg_id FROM days WHERE day=? AND status='COMPLETED'", (COURSE_DAYS,)).fetchall()
    for row in rows:
        con.execute("UPDATE users SET current_day=? WHERE tg_id=?", (FINAL_SENTINEL, row["tg_id"]))
    con.commit()
    con.close()


def _complete_day(tg_id, day, reflection):
    ok = _real_complete_day(tg_id, day, reflection)
    if ok and day == COURSE_DAYS:
        con = db.connect()
        con.execute("UPDATE users SET current_day=? WHERE tg_id=?", (FINAL_SENTINEL, tg_id))
        con.commit()
        con.close()
    return ok


def _init_db():
    _real_init_db()
    con = db.connect()
    rows = con.execute("SELECT tg_id FROM days WHERE day=? AND status='COMPLETED'", (COURSE_DAYS,)).fetchall()
    for row in rows:
        con.execute("UPDATE users SET current_day=? WHERE tg_id=?", (FINAL_SENTINEL, row["tg_id"]))
    con.commit()
    con.close()


db.complete_day = _complete_day
db.init_db = _init_db
_mark_existing_graduates()


async def _final_screen(q):
    uid = q.from_user.id
    u = db.user(uid)
    badges = db.badges(uid)
    badge_line = ""
    if "🍕 Любимая еда — в моей системе" in badges:
        badge_line = "\n🏆 Достижение «Любимая еда — в моей системе» уже получено."
    await q.message.reply_text(
        "🏆 <b>КУРС ЗАВЕРШЁН</b>\n\n"
        "Ты прошла все 50 дней и собрала свою систему.\n\n"
        "Теперь задача не в том, чтобы продолжать курс или искать новые правила. "
        "Твоя задача — пользоваться тем, чему ты научилась: выбирать еду, адаптироваться к обстоятельствам, "
        "двигаться, отдыхать и возвращаться к своему обычному режиму без постоянного контроля.\n\n"
        "❤️ <b>Теперь ты можешь сама.</b>" + badge_line,
        parse_mode="HTML",
        reply_markup=bot.main_kb(),
    )


async def _show_day(q):
    u = db.user(q.from_user.id)
    if u and int(u["current_day"] or 1) >= FINAL_SENTINEL:
        await _final_screen(q)
        return
    await _real_show_day(q)


async def _start(update, context):
    u = db.user(update.effective_user.id)
    if u and int(u["current_day"] or 1) >= FINAL_SENTINEL:
        await update.message.reply_text(
            "🏆 <b>КУРС ЗАВЕРШЁН</b>\n\n"
            "Ты прошла все 50 дней. Теперь у тебя есть своя система — пользуйся ею в реальной жизни без постоянного контроля.\n\n"
            "❤️ <b>Теперь ты можешь сама.</b>",
            parse_mode="HTML",
            reply_markup=bot.main_kb(),
        )
        return
    await _real_start(update, context)


async def _show_progress(q):
    u = db.user(q.from_user.id)
    if u and int(u["current_day"] or 1) >= FINAL_SENTINEL:
        await q.message.reply_text(
            "📊 <b>МОЙ ПРОГРЕСС</b>\n\n"
            "🗓 50/50 дней\n📈 100%\n"
            f"⭐ {u['xp']} XP\n🏆 Достижений: {len(db.badges(q.from_user.id))}\n\n"
            "Курс завершён ❤️",
            parse_mode="HTML",
            reply_markup=bot.back_kb(),
        )
        return
    await _real_show_progress(q)


bot.show_day = _show_day
bot.start = _start
bot.show_progress = _show_progress

_real_menu = bot.menu

async def _menu(update, context):
    q = update.callback_query
    if q.data == "continue":
        u = db.user(q.from_user.id)
        if u and int(u["current_day"] or 1) >= FINAL_SENTINEL:
            await q.answer()
            await _final_screen(q)
            return
    await _real_menu(update, context)

bot.menu = _menu
