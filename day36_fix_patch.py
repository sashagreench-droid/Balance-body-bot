import content
import bot

# Day 36 must always have exactly three fields:
# task, practice, reflection.
item = content.DAY_TASKS.get(36)
if item and len(item) == 2:
    task, practice = item
    reflection = (
        "1️⃣ Какая из трёх ситуаций окажется для тебя самой лёгкой для внедрения?\n\n"
        "2️⃣ Что обычно мешает тебе больше двигаться в течение дня?\n\n"
        "3️⃣ Какой один вариант ты готова попробовать использовать регулярно?"
    )
    content.DAY_TASKS[36] = (task, practice, reflection)
else:
    task, practice, reflection = item

# The core bot already adds the PRACTICE heading and completion instruction.
# Remove them from Day 36 content so they never appear twice.
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

# start_reflection() already adds the heading and the final instruction.
# Keep only the actual questions in the Day 36 reflection text.
for marker in (
    "🌿 <b>Теперь рефлексия</b>\n\n",
    "🌿 Теперь рефлексия\n\n",
):
    reflection = reflection.replace(marker, "", 1)
for marker in (
    "\n\nНапиши ответ одним сообщением. Я дам тебе короткую обратную связь, а потом мы завершим день.",
    "\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.",
):
    reflection = reflection.replace(marker, "", 1)

content.DAY_TASKS[36] = (task, practice, reflection)

# Day 36 needs specific feedback rather than the generic fallback.
def reflection_feedback_day36(day, text, uid=None):
    answer = text.strip()
    return (
        "🌿 Спасибо, что ответила ❤️\n\n"
        f"Ты выбрала три варианта: «{answer}».\n\n"
        "Вижу, что ты не ставишь себе задачу двигаться максимально много — ты выбрала умеренный подход. "
        "Для бытовой активности это как раз хороший ориентир: не заставлять себя, а находить небольшие возможности, "
        "которые реально вписываются в твой день.\n\n"
        "Теперь выбери из своих вариантов один самый удобный и попробуй повторять его регулярно. "
        "Так движение постепенно станет частью обычного дня, а не отдельной обязанностью."
    )

_original_reflection_feedback = bot.reflection_feedback

def reflection_feedback(day, text, uid=None):
    if day == 36:
        return reflection_feedback_day36(day, text, uid)
    return _original_reflection_feedback(day, text, uid)

bot.reflection_feedback = reflection_feedback
