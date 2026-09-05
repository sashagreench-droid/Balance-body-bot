import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

_original_menu = bot.menu

async def menu_day45_safe(update, context):
    q = update.callback_query
    try:
        await _original_menu(update, context)
    except Exception as e:
        # Never leave a button silently dead: surface the actual error to the user.
        try:
            await q.message.reply_text(f"⚠️ Не удалось открыть раздел. Ошибка: {type(e).__name__}: {e}")
        except Exception:
            pass

bot.menu = menu_day45_safe

_original_show_practice = bot.show_practice

async def show_practice_day45_safe(q, context):
    try:
        await _original_show_practice(q, context)
    except Exception:
        uid = q.from_user.id
        u = bot.db.user(uid)
        if not u:
            await q.message.reply_text("Не удалось найти твой профиль. Нажми /start.")
            return
        n = int(u["current_day"])
        if n == 45:
            _, practice, _ = bot.task_info(45)
            text = "📝 <b>ПРАКТИКА</b>\n\n" + practice + "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА»."
            buttons = [
                [InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
                [InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
                [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
            ]
            await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            raise

bot.show_practice = show_practice_day45_safe
