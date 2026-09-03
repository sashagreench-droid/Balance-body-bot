import content

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

# The core bot already adds the PRACTICE heading and the completion instruction.
# Remove them from Day 36 content so they can never appear twice.
practice = practice.replace("📝 <b>ПРАКТИКА</b>\n\n", "", 1)
practice = practice.replace("📝 <b>ПРАКТИКА</b>\n", "", 1)
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n", "\n")
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n\n", "\n")
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n", "")
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».", "")

# start_reflection() already adds the heading and the final instruction.
# Remove both from Day 36's reflection text to avoid duplicates and raw markup.
reflection = reflection.replace("🌿 <b>Теперь рефлексия</b>\n\n", "", 1)
reflection = reflection.replace("🌿 Теперь рефлексия\n\n", "", 1)
reflection = reflection.replace(
    "\n\nНапиши ответ одним сообщением. Я дам тебе короткую обратную связь, а потом мы завершим день.",
    "",
)
reflection = reflection.replace(
    "\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.",
    "",
)

content.DAY_TASKS[36] = (task, practice, reflection)
