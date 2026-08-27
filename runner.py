import bot
import db

PENDING = "__REFLECTION_PENDING__"

_original_start_reflection = bot.start_reflection
_original_handle_text = bot.handle_text
_original_menu = bot.menu


async def start_reflection_fixed(q, context):
    uid = q.from_user.id
    u = db.user(uid)
    if u:
        n = u["current_day"]
        con = db.connect()
        con.execute(
            "UPDATE days SET reflection=? WHERE tg_id=? AND day=? AND status='IN_PROGRESS'",
            (PENDING, uid, n),
        )
        con.commit()
        con.close()
    await _original_start_reflection(q, context)


async def handle_text_fixed(update, context):
    uid = update.effective_user.id

    try:
        u = db.user(uid)
        row = db.day_row(uid, u["current_day"]) if u else None
        pending = bool(
            row
            and row["reflection"] == PENDING
            and row["status"] == "IN_PROGRESS"
        )
    except Exception:
        pending = False

    if (
        pending
        and not context.user_data.get("awaiting_question")
        and not context.user_data.get("awaiting_system")
    ):
        context.user_data["awaiting_reflection"] = True

    await _original_handle_text(update, context)


async def menu_fixed(update, context):
    q = update.callback_query

    if q and q.data == "continue":
        await q.answer()
        uid = q.from_user.id

        try:
            u = db.user(uid)

            # Recovery path: if the user already reached the main menu but
            # the active DB has no user row, recreate the minimal course state.
            if not u:
                name = (q.from_user.first_name or "").strip()[:80] or "Участник"
                db.ensure_user(uid, name)
                u = db.user(uid)

            n = int(u["current_day"])
            row = db.day_row(uid, n)
            if not row:
                db.ensure_user(uid, u["name"] or "Участник")

            # "Продолжить" opens the current day directly, without
            # an intermediate "НАЧАТЬ" screen.
            await bot.begin_day(q, n)
        except Exception:
            await q.message.reply_text(
                "Я здесь ❤️ Не удалось открыть день. Попробуй нажать «ПРОДОЛЖИТЬ» ещё раз.",
                reply_markup=bot.main_kb(),
            )
        return

    await _original_menu(update, context)


bot.start_reflection = start_reflection_fixed
bot.handle_text = handle_text_fixed
bot.menu = menu_fixed

bot.main()
