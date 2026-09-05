import bot
import db

# Day 49 is the end of the course. Persist a sentinel value (50) so
# the generic "continue" action can never reopen Day 49 after graduation.
_real_complete_day = db.complete_day
_real_init_db = db.init_db
_real_show_day = bot.show_day
_real_start = bot.start
_real_show_progress = bot.show_progress


def _complete_day(tg_id, day, reflection):
    ok = _real_complete_day(tg_id, day, reflection)
    if ok and day == 49:
        con = db.connect()
        con.execute("UPDATE users SET current_day=50 WHERE tg_id=?", (tg_id,))
        con.commit()
        con.close()
    return ok


def _init_db():
    _real_init_db()
    # Restore the completed-course sentinel after the legacy DB initializer
    # clamps current_day to 49.
    con = db.connect()
    rows = con.execute(
        "SELECT tg_id FROM days WHERE day=49 AND status='COMPLETED'"
    ).fetchall()
    for row in rows:
        con.execute("UPDATE users SET current_day=50 WHERE tg_id=?", (row["tg_id"],))
    con.commit()
    con.close()


db.complete_day = _complete_day
db.init_db = _init_db


async def _final_screen(q):
    uid = q.from_user.id
    u = db.user(uid)
    badges = db.badges(uid)
    badge_line = ""
    if "🏆 Я сама" in badges:
        badge_line = "\n🏆 Достижение «Я сама» уже получено."
    await q.message.reply_text(
        "🏆 <b>КУРС ЗАВЕРШЁН</b>\n\n"
        "Ты прошла все 49 дней и собрала свою систему.\n\n"
        "Теперь задача не в том, чтобы продолжать курс или искать новые правила. "
        "Твоя задача — пользоваться тем, чему ты научилась: выбирать еду, адаптироваться к обстоятельствам, "
        "двигаться, отдыхать и возвращаться к своему обычному режиму без постоянного контроля.\n\n"
        "❤️ <b>Теперь ты можешь сама.</b>" + badge_line,
        parse_mode="HTML",
        reply_markup=bot.main_kb(),
    )


async def _show_day(q):
    u = db.user(q.from_user.id)
    if u and int(u["current_day"] or 1) >= 50:
        await _final_screen(q)
        return
    await _real_show_day(q)


async def _start(update, context):
    u = db.user(update.effective_user.id)
    if u and int(u["current_day"] or 1) >= 50:
        await update.message.reply_text(
            "🏆 <b>КУРС ЗАВЕРШЁН</b>\n\n"
            "Ты прошла все 49 дней. Теперь у тебя есть своя система — пользуйся ею в реальной жизни без постоянного контроля.\n\n"
            "❤️ <b>Теперь ты можешь сама.</b>",
            parse_mode="HTML",
            reply_markup=bot.main_kb(),
        )
        return
    await _real_start(update, context)


async def _show_progress(q):
    u = db.user(q.from_user.id)
    if u and int(u["current_day"] or 1) >= 50:
        await q.message.reply_text(
            "📊 <b>МОЙ ПРОГРЕСС</b>\n\n"
            "🗓 49/49 дней\n📈 100%\n"
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

# Intercept the menu's Continue action for graduates. The callback handler
# resolves bot.show_day dynamically, so the final screen is shown instead of Day 49.
_real_menu = bot.menu

async def _menu(update, context):
    q = update.callback_query
    if q.data == "continue":
        u = db.user(q.from_user.id)
        if u and int(u["current_day"] or 1) >= 50:
            await q.answer()
            await _final_screen(q)
            return
    await _real_menu(update, context)

bot.menu = _menu
