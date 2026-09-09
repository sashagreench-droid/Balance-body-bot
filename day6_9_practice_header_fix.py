import bot

# BALANCE BODY — avoid duplicating the "📝 ПРАКТИКА" header.
# The day renderer already adds the practice heading, so the task body must not repeat it.

for day in (6, 9):
    task = list(bot.DAY_TASKS[day])
    if len(task) >= 2:
        task[1] = task[1].lstrip()
        if task[1].startswith("📝 ПРАКТИКА"):
            task[1] = task[1][len("📝 ПРАКТИКА"):].lstrip(" \n")
        bot.DAY_TASKS[day] = tuple(task)
