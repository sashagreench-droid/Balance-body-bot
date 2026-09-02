import bot

# Explicitly fix the reflection stage for Day 31.
# DAY_TASKS[n] = (task, practice, reflection), so reflection must come from index 2.
_original_start_reflection = bot.start_reflection


async def start_reflection(q, context):
    context.user_data.pop("awaiting_hunger", None)
    context.user_data.pop("awaiting_satiety", None)
    context.user_data["awaiting_reflection"] = True

    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    task, practice, reflection = bot.task_info(n)

    if n == 31:
        await q.message.reply_text(
            "🌿 <b>Теперь рефлексия</b>\n\n"
            "1️⃣ Какое сочетание ты реально готова повторять регулярно?\n"
            "2️⃣ Какое сочетание сильнее всего выручит тебя, когда нет времени или хочется сладкого?\n\n"
            "Напиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.",
            parse_mode="HTML",
        )
        return

    await _original_start_reflection(q, context)


bot.start_reflection = start_reflection
