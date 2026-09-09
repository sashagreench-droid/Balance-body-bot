import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 8: short theory first, then an interactive BJU mini-test.

bot.DAYS[7] = (
    8,
    "ЧТО НА САМОМ ДЕЛЕ ДАЁТ КАЛОРИИ?",
    "РАЗБИРАЮСЬ В БЖУ",
    "Понимаю роль белков, жиров и углеводов",
    100,
)

DAY8_THEORY = """🧠 НЕБОЛЬШАЯ ТЕОРИЯ

Калории — это энергия из еды. На вес влияет не только то, какие продукты ты выбираешь, но и сколько энергии в итоге получает организм.

БЖУ — это три основных макронутриента:

🥩 БЕЛКИ
Нужны для построения и восстановления тканей, а также помогают дольше сохранять сытость.

🥑 ЖИРЫ
Участвуют в работе клеток, нервной системы и усвоении жирорастворимых витаминов. Они более калорийны: 1 г жира ≈ 9 ккал.

🍚 УГЛЕВОДЫ
Один из основных источников энергии для организма, особенно при физической активности. 1 г углеводов ≈ 4 ккал.

Белок тоже даёт около 4 ккал на 1 г.

Важно: ни один из этих нутриентов не делает продукт автоматически «хорошим» или «плохим». Один и тот же продукт может вписываться в рацион по-разному в зависимости от количества и общей картины питания.

Сегодня тебе не нужно считать свои БЖУ. Сначала разберёмся, действительно ли ты понимаешь, что они означают."""

DAY8_QUESTIONS = [
    {
        "q": "Что такое калории в контексте питания?",
        "opts": [
            "Количество белка в продукте",
            "Количество энергии, которое даёт еда",
            "Количество углеводов в порции",
        ],
        "correct": 1,
        "explain": "Калории показывают энергетическую ценность еды. Они не являются отдельным нутриентом вроде белка или углеводов.",
    },
    {
        "q": "Какой макронутриент наиболее калорийный на 1 грамм?",
        "opts": [
            "Белок",
            "Углеводы",
            "Жиры",
        ],
        "correct": 2,
        "explain": "1 г жира даёт примерно 9 ккал, тогда как белок и углеводы — примерно по 4 ккал.",
    },
    {
        "q": "Какое утверждение про белок наиболее верное?",
        "opts": [
            "Белок нужен только тем, кто тренируется",
            "Белок участвует в построении и восстановлении тканей",
            "Белок полностью заменяет углеводы в организме",
        ],
        "correct": 1,
        "explain": "Белок нужен организму независимо от тренировок и участвует, в частности, в построении и восстановлении тканей.",
    },
    {
        "q": "Как лучше относиться к жирам и углеводам в обычном рационе?",
        "opts": [
            "Исключать их, если хочется похудеть",
            "Считать их «плохими» продуктами",
            "Учитывать их количество и общую картину рациона",
        ],
        "correct": 2,
        "explain": "И жиры, и углеводы выполняют важные функции. Для рациона важна не идея полного запрета, а их количество и общий баланс питания.",
    },
    {
        "q": "Что важнее всего понять сегодня перед началом подсчёта БЖУ?",
        "opts": [
            "Какой продукт содержит только белок",
            "Что БЖУ — это разные макронутриенты, которые дают энергию и выполняют разные функции",
            "Что нужно есть только продукты с низкой калорийностью",
        ],
        "correct": 1,
        "explain": "БЖУ — это белки, жиры и углеводы. Они дают энергию и выполняют разные функции, поэтому задача не в том, чтобы выбрать один «правильный» макронутриент.",
    },
]


def _day8_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 ПРОЙТИ МИНИ-ТЕСТ", callback_data="day8_test_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])


async def show_practice(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 8:
        return await bot._day8_original_show_practice(q, context)

    context.user_data.pop("day8_quiz_index", None)
    context.user_data.pop("day8_quiz_score", None)
    await q.message.reply_text(
        "📝 <b>ПРАКТИКА</b>\n\n" + DAY8_THEORY +
        "\n\nТеперь проверь себя — 5 коротких вопросов. Не ищи идеальный результат: нам важно понять, что уже понятно, а что стоит разобрать ещё раз.",
        parse_mode="HTML",
        reply_markup=_day8_keyboard(),
    )


async def _day8_send_question(q, context, index):
    item = DAY8_QUESTIONS[index]
    buttons = [[InlineKeyboardButton(opt, callback_data=f"day8_test:{index}:{i}")] for i, opt in enumerate(item["opts"])]
    await q.message.reply_text(
        f"🧪 <b>МИНИ-ТЕСТ — {index + 1}/{len(DAY8_QUESTIONS)}</b>\n\n{item['q']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _day8_handle_test(q, context, data):
    if data == "day8_test_start":
        context.user_data["day8_quiz_index"] = 0
        context.user_data["day8_quiz_score"] = 0
        await q.answer()
        return await _day8_send_question(q, context, 0)

    if data.startswith("day8_test:"):
        try:
            _, idx_s, choice_s = data.split(":")
            idx = int(idx_s)
            choice = int(choice_s)
        except (ValueError, TypeError):
            await q.answer()
            return

        current = context.user_data.get("day8_quiz_index")
        if current != idx or idx < 0 or idx >= len(DAY8_QUESTIONS):
            await q.answer()
            return

        item = DAY8_QUESTIONS[idx]
        if choice == item["correct"]:
            context.user_data["day8_quiz_score"] = context.user_data.get("day8_quiz_score", 0) + 1
            result = "Верно ❤️"
        else:
            result = "Почти — сейчас разберём."

        await q.answer()
        await q.message.reply_text(result + "\n\n" + item["explain"])

        next_idx = idx + 1
        if next_idx < len(DAY8_QUESTIONS):
            context.user_data["day8_quiz_index"] = next_idx
            return await _day8_send_question(q, context, next_idx)

        score = context.user_data.get("day8_quiz_score", 0)
        context.user_data.pop("day8_quiz_index", None)
        context.user_data.pop("day8_quiz_score", None)
        await q.message.reply_text(
            f"🏁 <b>МИНИ-ТЕСТ ЗАВЕРШЁН</b>\n\nТвой результат: <b>{score}/{len(DAY8_QUESTIONS)}</b>.\n\nТеперь напиши одним сообщением:\n👉 Что из БЖУ стало понятнее?\n👉 Что осталось непонятным?\n👉 Нужно ли тебе вообще считать БЖУ прямо сейчас? Почему?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ", callback_data="reflection_start")],
                [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
            ]),
        )


# Keep the existing show_practice for every other day.
bot._day8_original_show_practice = bot.show_practice
bot.show_practice = show_practice

# Handle the Day 8 test before the generic menu dispatcher.
bot._day8_original_menu = bot.menu

async def menu(update, context):
    q = update.callback_query
    data = q.data or ""
    if data == "day8_test_start" or data.startswith("day8_test:"):
        return await _day8_handle_test(q, context, data)
    return await bot._day8_original_menu(update, context)

bot.menu = menu
