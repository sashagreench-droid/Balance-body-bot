import runpy
import content
import bot
import db

# Load the complete Day 35 content first.
runpy.run_module("day35_patch", run_name="__main__")

# The core bot already adds the PRACTICE heading and the completion instruction.
# Remove those parts from the day-specific text so they are not duplicated.
task, practice, reflection = content.DAY_TASKS[35]
practice = practice.replace("📝 <b>ПРАКТИКА</b>\n\n", "", 1)
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».\n", "\n")
practice = practice.replace("\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».", "")
content.DAY_TASKS[35] = (task, practice, reflection)

# The original start_reflection message did not set parse_mode, so HTML tags
# such as <b> were shown literally. Keep the same flow, but render HTML.
async def start_reflection_html(q, context):
    context.user_data.pop("awaiting_hunger", None)
    context.user_data.pop("awaiting_satiety", None)
    context.user_data["awaiting_reflection"] = True
    n = db.user(q.from_user.id)["current_day"]
    await q.message.reply_text(
        "🌿 Теперь рефлексия\n\n" + content.DAY_TASKS[n][2] +
        "\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.",
        parse_mode="HTML",
    )

bot.start_reflection = start_reflection_html
