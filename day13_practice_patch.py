import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 13: clear theory about simple/complex carbohydrates,
# followed by an interactive mini-test instead of a case.

bot.DAYS[12] = (
    13,
    "УГЛЕВОДЫ БЕЗ СТРАХА",
    "ОТЛИЧАЮ ПРОСТЫЕ И СЛОЖНЫЕ УГЛЕВОДЫ",
    "Отличаю простые и сложные углеводы",
    50,
)

DAY13_THEORY = """🧠 НЕБОЛЬШАЯ ТЕОРИЯ

Углеводы — один из основных источников энергии. Их не нужно бояться или исключать из рациона ради похудения.

🍬 ПРОСТЫЕ УГЛЕВОДЫ
Это сахара: например, глюкоза, фруктоза, сахароза и лактоза. Они встречаются в сахаре, сладостях, сладких напитках, фруктах, молоке и других продуктах.

🌾 СЛОЖНЫЕ УГЛЕВОДЫ
Это в основном крахмал и пищевые волокна. Их источники — крупы, хлеб, макароны, картофель, бобовые, овощи и другие растительные продукты.

Главное: «простой» не значит «плохой», а «сложный» не значит «можно есть без ограничений».

Например, фрукт содержит простые сахара, но вместе с ними — воду, клетчатку и другие питательные вещества. А сложный углевод тоже может давать много калорий, если съесть большую порцию.

Для похудения важна общая калорийность рациона. При этом продукты с клетчаткой и более высокой пищевой ценностью часто помогают дольше сохранять сытость.

Сегодня твоя задача — научиться спокойно различать эти группы, а не делить углеводы на «хорошие» и «плохие»."""

DAY13_QUESTIONS = [
    {
        "q": "Какой продукт является очевидным источником простых углеводов?",
        "opts": ["Овсяная крупа", "Сахар", "Чечевица"],
        "correct": 1,
        "explain": "Сахар состоит преимущественно из простого углевода — сахарозы. Овсянка и чечевица в основном дают сложные углеводы, включая крахмал и клетчатку.",
    },
    {
        "q": "Какой вариант лучше всего описывает сложные углеводы?",
        "opts": ["Крахмал и пищевые волокна", "Только добавленный сахар", "Только фруктоза и глюкоза"],
        "correct": 0,
        "explain": "К сложным углеводам относят прежде всего крахмал и пищевые волокна. Добавленный сахар, глюкоза и фруктоза относятся к простым углеводам.",
    },
    {
        "q": "Что вернее сказать про фрукт?",
        "opts": ["Фрукт нельзя есть, потому что в нём есть простой сахар", "Во фрукте есть простые сахара, но это не делает его автоматически «плохим» продуктом", "Фрукт состоит только из сложных углеводов"],
        "correct": 1,
        "explain": "Во фруктах действительно есть простые сахара, но вместе с ними есть вода, клетчатка и другие питательные вещества. Поэтому наличие простых сахаров само по себе не делает продукт плохим.",
    },
    {
        "q": "Что важнее учитывать при похудении?",
        "opts": ["Полностью убрать простые углеводы", "Есть только сложные углеводы", "Смотреть на общую калорийность и состав рациона"],
        "correct": 2,
        "explain": "Для изменения массы тела важен энергетический баланс. При этом состав рациона тоже имеет значение для сытости и качества питания, поэтому не требуется полностью запрещать одну группу углеводов.",
    },
    {
        "q": "Какое утверждение о простых и сложных углеводах верное?",
        "opts": ["Простые всегда вредны, а сложные всегда полезны", "Тип углевода не позволяет автоматически назвать весь продукт хорошим или плохим", "Сложные углеводы можно есть без ограничения по количеству"],
        "correct": 1,
        "explain": "Классификация на простые и сложные описывает тип углевода, а не выносит оценку всему продукту. Количество, состав рациона и контекст тоже имеют значение.",
    },
]


def _day13_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 ПРОЙТИ МИНИ-ТЕСТ", callback_data="day13_test_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])


async def show_practice(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 13:
        return await bot._day13_original_show_practice(q, context)

    context.user_data.pop("day13_quiz_index", None)
    context.user_data.pop("day13_quiz_score", None)
    await q.message.reply_text(
        "📝 <b>ПРАКТИКА</b>\n\n" + DAY13_THEORY +
        "\n\nТеперь проверь себя — 5 коротких вопросов. Здесь нет задачи делить еду на «хорошую» и «плохую»: проверяем, действительно ли ты понимаешь разницу между простыми и сложными углеводами.",
        parse_mode="HTML",
        reply_markup=_day13_keyboard(),
    )


async def _day13_send_question(q, context, index):
    item = DAY13_QUESTIONS[index]
    buttons = [[InlineKeyboardButton(opt, callback_data=f"day13_test:{index}:{i}")] for i, opt in enumerate(item["opts"])]
    await q.message.reply_text(
        f"🧪 <b>МИНИ-ТЕСТ — {index + 1}/{len(DAY13_QUESTIONS)}</b>\n\n{item['q']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _day13_handle_test(q, context, data):
    if data == "day13_test_start":
        context.user_data["day13_quiz_index"] = 0
        context.user_data["day13_quiz_score"] = 0
        await q.answer()
        return await _day13_send_question(q, context, 0)

    if data.startswith("day13_test:"):
        try:
            _, idx_s, choice_s = data.split(":")
            idx = int(idx_s)
            choice = int(choice_s)
        except (ValueError, TypeError):
            await q.answer()
            return

        current = context.user_data.get("day13_quiz_index")
        if current != idx or idx < 0 or idx >= len(DAY13_QUESTIONS):
            await q.answer()
            return

        item = DAY13_QUESTIONS[idx]
        if choice == item["correct"]:
            context.user_data["day13_quiz_score"] = context.user_data.get("day13_quiz_score", 0) + 1
            result = "Верно ❤️"
        else:
            result = "Разберём."

        await q.answer()
        await q.message.reply_text(result + "\n\n" + item["explain"])

        next_idx = idx + 1
        if next_idx < len(DAY13_QUESTIONS):
            context.user_data["day13_quiz_index"] = next_idx
            return await _day13_send_question(q, context, next_idx)

        score = context.user_data.get("day13_quiz_score", 0)
        context.user_data.pop("day13_quiz_index", None)
        context.user_data.pop("day13_quiz_score", None)
        await q.message.reply_text(
            f"🏁 <b>МИНИ-ТЕСТ ЗАВЕРШЁН</b>\n\nТвой результат: <b>{score}/{len(DAY13_QUESTIONS)}</b>.\n\nТеперь напиши одним сообщением:\n👉 Что стало понятнее про простые и сложные углеводы?\n👉 Какие углеводы ты раньше считала «плохими»?\n👉 Что теперь изменится в твоём выборе еды?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ", callback_data="reflection_start")],
                [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
            ]),
        )


bot._day13_original_show_practice = bot.show_practice
bot.show_practice = show_practice

bot._day13_original_menu = bot.menu


async def menu(update, context):
    q = update.callback_query
    data = q.data or ""
    if data == "day13_test_start" or data.startswith("day13_test:"):
        return await _day13_handle_test(q, context, data)
    return await bot._day13_original_menu(update, context)


bot.menu = menu
