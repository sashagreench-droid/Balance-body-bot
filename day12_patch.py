import os
import runpy
import bot
import db

IMAGE_PATH = os.path.join(os.path.dirname(__file__), "protein_cheat.svg")


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
