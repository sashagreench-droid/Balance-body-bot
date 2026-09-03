import content
import bot

# Day 37: remove duplicate service text if it appears in the task,
# and give specific feedback instead of the generic reflection fallback.
item = content.DAY_TASKS.get(37)
if item:
    task, practice, reflection = item

    for marker in (
        "📝 <b>ПРАКТИКА</b>\n\n",
        "📝 <b>ПРАКТИКА</b>\n",
    ):
        practice = practice.replace(marker, "", 1)

    for marker in (
        "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n",
        "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n\n",
        "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».",
    ):
        practice = practice.replace(marker, "", 1)

    for marker in (
        "🌿 <b>Теперь рефлексия</b>\n\n",
        "🌿 Теперь рефлексия\n\n",
    ):
        reflection = reflection.replace(marker, "", 1)

    content.DAY_TASKS[37] = (task, practice, reflection)


def reflection_feedback_day37(day, text, uid=None):
    answer = text.strip()
    return (
        "🌿 Спасибо за ответ ❤️\n\n"
        f"Ты выбрала для себя формат: «{answer}».\n\n"
        "Для утреннего движения это хороший ориентир: зарядка не должна занимать много времени или превращаться в отдельную тренировку. "
        "Если короткий формат легче вписать в твой обычный день, его гораздо проще сделать регулярной привычкой.\n\n"
        "Теперь твоя задача — сохранить именно тот объём, который тебе комфортен, и постепенно сделать его частью своего утра. "
        "Здесь важнее регулярность, чем продолжительность или сложность упражнений."
    )

_original_reflection_feedback = bot.reflection_feedback


def reflection_feedback(day, text, uid=None):
    if day == 37:
        return reflection_feedback_day37(day, text, uid)
    return _original_reflection_feedback(day, text, uid)


bot.reflection_feedback = reflection_feedback
