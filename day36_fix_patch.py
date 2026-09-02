import content

# Day 36 was temporarily written as a 2-item tuple, while the core bot
# expects every DAY_TASKS entry to contain: task, practice, reflection.
# Normalize it here so opening Day 36 cannot fail with
# "expected 3, got 2".
item = content.DAY_TASKS.get(36)
if item and len(item) == 2:
    task, practice = item
    reflection = (
        "🌿 <b>Теперь рефлексия</b>\n\n"
        "1️⃣ Какая из трёх ситуаций окажется для тебя самой лёгкой для внедрения?\n\n"
        "2️⃣ Что обычно мешает тебе больше двигаться в течение дня?\n\n"
        "3️⃣ Какой один вариант ты готова попробовать использовать регулярно?\n\n"
        "Напиши ответ одним сообщением. Я дам тебе короткую обратную связь, а потом мы завершим день."
    )
    content.DAY_TASKS[36] = (task, practice, reflection)
