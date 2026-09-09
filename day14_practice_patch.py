import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 14: short theory first, then an interactive control mini-test.

bot.DAYS[13] = (
    14,
    "КОНТРОЛЬНАЯ: Я ПОНИМАЮ СВОЮ ЕДУ",
    "РАЗБИРАЮСЬ В БЖУ",
    "Связываю продукты с БЖУ и калориями",
    100,
)

DAY14_THEORY = """🧠 НЕБОЛЬШАЯ ТЕОРИЯ

За последние дни мы разобрали калории, белки, жиры и углеводы. Теперь соединяем всё в одну картину.

🥩 БЕЛКИ
Помогают строить и восстанавливать ткани. Источники: мясо, птица, рыба, яйца, творог, йогурт, бобовые.

🥑 ЖИРЫ
Нужны организму и при этом дают много энергии: 1 г жира ≈ 9 ккал. Источники: масла, орехи, сыр, жирная рыба, авокадо.

🍚 УГЛЕВОДЫ
Один из основных источников энергии: 1 г углеводов ≈ 4 ккал. Источники: крупы, хлеб, картофель, фрукты, сладости.

🔥 КАЛОРИИ
Белки и углеводы дают примерно по 4 ккал на грамм, жиры — примерно 9 ккал. Поэтому продукт с большим количеством жира может быть значительно калорийнее даже при небольшой порции.

Например, орехи полезны и питательны, но калорийны из-за высокого содержания жиров. А фрукт содержит углеводы и при этом обычно имеет меньшую калорийность на ту же массу.

Важно: по одному продукту нельзя решить, «хороший» он или «плохой». Мы смотрим на состав, количество и весь рацион.

Сегодня задача — проверить, умеешь ли ты уже связывать продукт → БЖУ → калорийность и принимать решение без запретов."""

DAY14_QUESTIONS = [
    {
        "q": "В тарелке: куриная грудка, рис и овощи. Что здесь в первую очередь является источником белка?",
        "opts": ["Куриная грудка", "Рис", "Овощи", "Все продукты дают примерно одинаково белка"],
        "correct": 0,
        "explain": "Куриная грудка — основной белковый компонент этой тарелки. Рис и овощи тоже могут содержать немного белка, но в меньшем количестве.",
    },
    {
        "q": "Почему 20 г жира дают больше калорий, чем 20 г белка?",
        "opts": ["В жире примерно 9 ккал на 1 г, а в белке около 4 ккал", "В белке нет калорий", "Жир всегда увеличивает вес сильнее белка", "Потому что жир нельзя использовать как энергию"],
        "correct": 0,
        "explain": "1 г жира даёт примерно 9 ккал, а 1 г белка — около 4 ккал. Поэтому при одинаковом весе жир даёт больше энергии.",
    },
    {
        "q": "Ты выбираешь между двумя завтраками: овсянка с ягодами или яйца с овощами. Как правильнее оценивать их при похудении?",
        "opts": ["Один из них автоматически запрещён", "Нужно смотреть только на углеводы", "Сравнить состав, порцию и калорийность в контексте всего рациона", "Выбирать только тот, где меньше продуктов"],
        "correct": 2,
        "explain": "При похудении не нужно делить еду на разрешённую и запрещённую. Важно учитывать состав, размер порции, калорийность и то, как блюдо вписывается в общий рацион.",
    },
    {
        "q": "Какой вывод о продукте будет наиболее полезным?",
        "opts": ["В нём есть жиры — значит, его нельзя есть", "В нём есть углеводы — значит, он мешает похудению", "В нём есть белок — значит, можно есть без ограничений", "У продукта есть определённый состав и калорийность, а значение имеет его количество и место в рационе"],
        "correct": 3,
        "explain": "Наличие одного макронутриента не делает продукт автоматически хорошим или плохим. Важны количество и общая картина питания.",
    },
    {
        "q": "Ты видишь десерт на 300 ккал. Что это означает?",
        "opts": ["Что после него нельзя есть весь день", "Что десерт обязательно помешает похудению", "Что порция даёт около 300 ккал и её можно учитывать в общей картине рациона", "Что 300 ккал нужно обязательно отработать тренировкой"],
        "correct": 2,
        "explain": "300 ккал — это информация об энергетической ценности порции. Сам по себе десерт не отменяет возможность похудеть: значение имеет общий рацион и количество энергии.",
    },
]


def _day14_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 ПРОЙТИ МИНИ-ТЕСТ", callback_data="day14_test_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])


async def show_practice(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 14:
        return await bot._day14_original_show_practice(q, context)

    context.user_data.pop("day14_quiz_index", None)
    context.user_data.pop("day14_quiz_score", None)
    await q.message.reply_text(
        "📝 <b>ПРАКТИКА</b>\n\n" + DAY14_THEORY +
        "\n\nТеперь проверь себя — 5 коротких вопросов. После каждого ответа ты сразу увидишь разбор.",
        parse_mode="HTML",
        reply_markup=_day14_keyboard(),
    )


async def _day14_send_question(q, context, index):
    item = DAY14_QUESTIONS[index]
    buttons = [[InlineKeyboardButton(opt, callback_data=f"day14_test:{index}:{i}")] for i, opt in enumerate(item["opts"])]
    await q.message.reply_text(
        f"🧪 <b>МИНИ-ТЕСТ — {index + 1}/{len(DAY14_QUESTIONS)}</b>\n\n{item['q']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _day14_handle_test(q, context, data):
    if data == "day14_test_start":
        context.user_data["day14_quiz_index"] = 0
        context.user_data["day14_quiz_score"] = 0
        await q.answer()
        return await _day14_send_question(q, context, 0)

    if data.startswith("day14_test:"):
        try:
            _, idx_s, choice_s = data.split(":")
            idx = int(idx_s)
            choice = int(choice_s)
        except (ValueError, TypeError):
            await q.answer()
            return

        current = context.user_data.get("day14_quiz_index")
        if current != idx or idx < 0 or idx >= len(DAY14_QUESTIONS):
            await q.answer()
            return

        item = DAY14_QUESTIONS[idx]
        if choice == item["correct"]:
            context.user_data["day14_quiz_score"] = context.user_data.get("day14_quiz_score", 0) + 1
            result = "Верно ❤️"
        else:
            result = "Разбираем этот момент ❤️"

        await q.answer()
        await q.message.reply_text(result + "\n\n" + item["explain"])

        next_idx = idx + 1
        if next_idx < len(DAY14_QUESTIONS):
            context.user_data["day14_quiz_index"] = next_idx
            return await _day14_send_question(q, context, next_idx)

        score = context.user_data.get("day14_quiz_score", 0)
        context.user_data.pop("day14_quiz_index", None)
        context.user_data.pop("day14_quiz_score", None)
        await q.message.reply_text(
            f"🏁 <b>КОНТРОЛЬНАЯ ЗАВЕРШЕНА</b>\n\nТвой результат: <b>{score}/{len(DAY14_QUESTIONS)}</b>.\n\nТеперь напиши одним сообщением:\n👉 Какой продукт или блюдо ты теперь лучше понимаешь по БЖУ?\n👉 Что стало понятнее про калорийность?\n👉 Есть ли продукт, который ты раньше считала «плохим», а теперь смотришь на него спокойнее?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ", callback_data="reflection_start")],
                [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
            ]),
        )


bot._day14_original_show_practice = bot.show_practice
bot.show_practice = show_practice

bot._day14_original_menu = bot.menu

async def menu(update, context):
    q = update.callback_query
    data = q.data or ""
    if data == "day14_test_start" or data.startswith("day14_test:"):
        return await _day14_handle_test(q, context, data)
    return await bot._day14_original_menu(update, context)

bot.menu = menu
