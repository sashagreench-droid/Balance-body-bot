import bot
import db

PENDING = "__REFLECTION_PENDING__"

_original_start_reflection = bot.start_reflection
_original_handle_text = bot.handle_text


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
    pending = False
    try:
        u = db.user(uid)
        row = db.day_row(uid, u["current_day"]) if u else None
        pending = bool(
            row
            and row["reflection"] == PENDING
            and row["status"] == "IN_PROGRESS"
        )
    except Exception:
        pass

    if (
        pending
        and not context.user_data.get("awaiting_question")
        and not context.user_data.get("awaiting_system")
    ):
        context.user_data["awaiting_reflection"] = True

    await _original_handle_text(update, context)


bot.start_reflection = start_reflection_fixed
bot.handle_text = handle_text_fixed

bot.main()
