import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 16: make the portion practice concrete.
# The original task was too vague, so the participant now follows a clear
# 3-step exercise: estimate -> compare with visual cues -> optionally check.

DAY16_PRACTICE = """📝 <b>ПРАКТИКА</b>

Сегодня не нужно угадывать граммы. Учимся видеть размер порции без весов.

Возьми <b>3 обычные порции</b> еды, которые ты реально ешь в течение дня.

<b>Шаг 1.</b> Положи еду так, как положила бы обычно — без весов.

<b>Шаг 2.</b> Перед едой оцени каждую порцию:
• белковый продукт — примерно с ладонь;
• гарнир/крупа/картофель — примерно с кулак или горсть;
• жирный продукт (сыр, орехи, масло) — небольшая порция, ориентиром может быть большой палец.

Это <b>не строгие нормы</b>, а визуальные ориентиры, чтобы постепенно перестать зависеть от весов.

<b>Шаг 3.</b> Если есть возможность, после своей оценки один раз взвесь порцию и сравни результат с тем, что ты представляла.

Например: ты положила себе рис, курицу и сыр. Сначала оценила порции на глаз → потом взвесила → заметила, где ошиблась.

<b>Твоя задача — не сделать порцию «идеальной», а понять, насколько хорошо ты уже умеешь оценивать её визуально.</b>

После 3 порций нажми «Я ВЫПОЛНИЛА»."""


def _day16_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])


_original_show_practice = bot.show_practice


async def show_practice(q, context):
    uid = q.from_user.id
    u = bot.db.user(uid)
    if not u or u["current_day"] != 16:
        return await _original_show_practice(q, context)

    await q.message.reply_text(
        DAY16_PRACTICE,
        parse_mode="HTML",
        reply_markup=_day16_keyboard(),
    )


bot.show_practice = show_practice
