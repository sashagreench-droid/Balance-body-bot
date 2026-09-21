import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 19: make the quick-meal practice concrete.

DAY19_PRACTICE = """📝 <b>ПРАКТИКА</b>

Сегодня тренируем навык быстро собрать полноценный прием пищи из того, что уже есть дома.

<b>Шаг 1. Открой холодильник и шкаф.</b>
Выбери продукты, которые уже есть дома. Ничего специально покупать не нужно.

<b>Шаг 2. Собери прием пищи из 4 элементов:</b>
• 🥩 <b>Белок</b> — яйца, творог, йогурт, курица, рыба, сыр, бобовые;
• 🍚 <b>Углеводы</b> — хлеб, крупа, картофель, макароны, фрукты;
• 🥒 <b>Овощи или фрукты</b> — любые, которые есть дома;
• 🥑 <b>Источник жиров</b> — масло, орехи, авокадо, сыр или другой продукт, который уже содержит жиры.

<b>Шаг 3. Собери блюдо за 5–10 минут.</b>
Например:
• яйца + хлеб + овощи + сыр;
• творог/йогурт + фрукт + хлеб/овсянка + орехи;
• тунец/курица + готовая крупа + овощи + немного масла.

<b>Шаг 4. Проверь себя.</b>
Перед тем как нажать «Я ВЫПОЛНИЛА», напиши:
1) какой белок выбрала;
2) какие углеводы;
3) какие овощи/фрукты;
4) какой источник жиров.

💡 <b>Задача не в идеальном блюде.</b> Нужно научиться быстро собирать нормальный прием пищи из доступных продуктов, даже когда нет времени готовить.

Когда закончишь — нажми «Я ВЫПОЛНИЛА»."""


def _day19_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])


_original_show_practice = bot.show_practice


async def show_practice(q, context):
    uid = q.from_user.id
    u = bot.db.user(uid)
    if not u or u["current_day"] != 19:
        return await _original_show_practice(q, context)

    await q.message.reply_text(
        DAY19_PRACTICE,
        parse_mode="HTML",
        reply_markup=_day19_keyboard(),
    )


bot.show_practice = show_practice
