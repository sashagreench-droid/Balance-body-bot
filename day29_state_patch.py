import bot
import db

# Day 29 reflection state must survive a process restart/redeploy.
# context.user_data alone is in-memory, so a restart between the reflection prompt
# and the user's answer made the bot fall through to "Используй меню ниже ❤️".

_original_start_reflection = bot.start_reflection
_original_handle_text = bot.handle_text


def _reflection_pending(uid, day):
    answers = db.get_day_answers(uid, day)
    for row in reversed(answers):
        if row["kind"] == "reflection_pending":
            return row["value"] == "1"
    return False


async def start_reflection(q, context):
    uid = q.from_user.id
    n = db.user(uid)["current_day"]
    await _original_start_reflection(q, context)
    db.save_answer(uid, n, "reflection_pending", "1")


async def handle_text(update, context):
    uid = update.effective_user.id
    u = db.user(uid)
    if u and u["current_day"] == 29 and _reflection_pending(uid, 29):
        context.user_data["awaiting_reflection"] = True
        try:
            await _original_handle_text(update, context)
        finally:
            db.save_answer(uid, 29, "reflection_pending", "0")
        return
    await _original_handle_text(update, context)


bot.start_reflection = start_reflection
bot.handle_text = handle_text
