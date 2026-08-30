import os
import runpy
import bot
import db

IMAGE_PATH = os.path.join(os.path.dirname(__file__), "protein_cheat.svg")

# Day 15: make the practice concrete so the participant knows exactly what to change.
bot.DAY_TASKS[15] = (
    "Сегодня не запрещаем любимые продукты — учимся немного менять прием пищи.",
    "Выбери ОДИН обычный прием пищи сегодня (завтрак, обед или ужин). Оставь в нем любимый продукт, но сделай одну небольшую корректировку: например, уменьши его порцию и добавь источник белка/овощи; или оставь прежнюю порцию и убери один лишний калорийный компонент. Задача — не сделать прием пищи «идеальным», а увидеть, как небольшое изменение меняет его состав и сытость.",
    "Какой прием пищи ты выбрала?\nЧто именно изменила?\nУдалось ли оставить любимый продукт без полного запрета?"
)


async def send_day12_bonus(context, chat_id):
    caption = (
        "📌 Забери себе шпаргалку ❤️\n\n"
        "Здесь ещё больше простых источников белка, которые можно использовать в обычном рационе.\n\n"
        "Сохрани её, чтобы не искать идеи каждый раз заново."
    )
    try:
        with open(IMAGE_PATH, "rb") as document:
            await context.bot.send_document(chat_id=chat_id, document=document, caption=caption)
    except Exception:
        # Не мешаем завершению дня, если Telegram временно не принял материал.
        pass


_original_finish_day = bot.finish_day


async def finish_day(q, context, skipped=False):
    n = db.user(q.from_user.id)["current_day"]
    await _original_finish_day(q, context, skipped)
    if n == 12:
        await send_day12_bonus(context, q.from_user.id)


bot.finish_day = finish_day


_original_handle_text = bot.handle_text


async def handle_text(update, context):
    uid = update.effective_user.id
    n = db.user(uid)["current_day"]
    await _original_handle_text(update, context)
    if n == 12 and db.user(uid)["current_day"] == 13:
        await send_day12_bonus(context, uid)


bot.handle_text = handle_text

# Keep all existing Day 10 calculator logic and the current production runner.
runpy.run_path(os.path.join(os.path.dirname(__file__), "day10_patch.py"), run_name="__main__")
