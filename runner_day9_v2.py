from pathlib import Path

runner_path = Path(__file__).with_name("runner.py")
source = runner_path.read_text(encoding="utf-8")
marker = "\nbot.main()\n"
if marker not in source:
    raise RuntimeError("runner.py: bot.main() marker not found")

# Run the existing runner without its final polling call. This preserves all
# existing Day 8, reflection, and progress fixes.
runner_without_main = source.rsplit(marker, 1)[0] + "\n"
exec(compile(runner_without_main, str(runner_path), "exec"), globals(), globals())

DAY9_QUIZ = [
    {
        "text": (
            "Перед тобой два варианта:\n\n"
            "🥑 Бутерброд с авокадо, творожным сыром и рыбой.\n"
            "🍚 Рис с курицей, мексиканской смесью + конфета.\n\n"
            "Что нужно учитывать, чтобы корректно сравнить их калорийность?"
        ),
        "options": [
            "Только самый калорийный продукт",
            "Состав продуктов и их количество",
            "Только наличие сладкого",
            "Только то, какой вариант кажется полезнее",
        ],
        "correct": 1,
        "feedback": [
            "Один самый калорийный продукт не показывает калорийность всего приёма пищи.",
            "Для сравнения важны весь состав и количество продуктов в порциях.",
            "Наличие сладкого само по себе не определяет калорийность всего приёма пищи.",
            "«Полезнее» и «менее калорийно» — не одно и то же.",
        ],
    },
    {
        "text": "Во втором варианте есть конфета. Можно ли только по этому факту сказать, что весь приём пищи обязательно более калорийный?",
        "options": [
            "Да, всегда",
            "Нет, нужно учитывать весь приём пищи",
            "Да, если конфета сладкая",
            "Нет, потому что конфеты не содержат калорий",
        ],
        "correct": 1,
        "feedback": [
            "Наличие конфеты не позволяет определить калорийность всего приёма пищи без остальных продуктов и их количества.",
            "Общая калорийность зависит от всего состава и количества еды, а не от одного продукта.",
            "Сладкий вкус не является достаточным критерием для сравнения общей калорийности.",
            "Конфеты содержат калории, поэтому этот вариант ответа неверен.",
        ],
    },
    {
        "text": "Какой главный вывод нужно забрать из сегодняшнего задания?",
        "options": [
            "Сладкое всегда мешает похудению",
            "Полезная еда всегда менее калорийная",
            "Калорийность зависит от состава и количества еды",
            "Чем меньше продуктов в тарелке, тем меньше калорий",
        ],
        "correct": 2,
        "feedback": [
            "Сам факт наличия сладкого не определяет результат рациона целиком.",
            "Польза продукта и его калорийность — разные характеристики.",
            "Именно состав и количество еды определяют её общую калорийность.",
            "Количество разных продуктов само по себе не определяет общую калорийность.",
        ],
    },
]


def day9_quiz_keyboard(index):
    return bot.InlineKeyboardMarkup([
        [bot.InlineKeyboardButton(option, callback_data=f"d9q:{index}:{option_index}")]
        for option_index, option in enumerate(DAY9_QUIZ[index]["options"])
    ])


async def day9_show_practice(q, context):
    text = (
        "📝 <b>ПРАКТИКА</b>\n\n"
        "Сегодня сравним два обычных приёма пищи и проверим, как работает калорийность.\n\n"
        "🥑 Бутерброд с авокадо, творожным сыром и рыбой.\n"
        "🍚 Рис с курицей, мексиканской смесью + конфета.\n\n"
        "Пройди мини-тест. Взвешивать еду и считать калории вручную не нужно."
    )
    await q.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup([
            [bot.InlineKeyboardButton("🧠 ПРОЙТИ МИНИ-ТЕСТ", callback_data="d9_start")],
            [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
            [bot.InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
        ]),
    )


async def day9_start(q, context):
    context.user_data["d9_quiz_index"] = 0
    context.user_data["d9_quiz_score"] = 0
    await q.answer()
    await q.message.reply_text(
        "🧠 <b>МИНИ-ТЕСТ — КАЛОРИИ БЕЗ СТРАХА</b>\n\n"
        "3 вопроса. Выбирай ответ, который кажется тебе наиболее правильным.",
        parse_mode="HTML",
    )
    question = DAY9_QUIZ[0]
    await q.message.reply_text(
        f"Вопрос 1 из {len(DAY9_QUIZ)}\n\n{question['text']}",
        reply_markup=day9_quiz_keyboard(0),
    )


async def day9_answer(q, context, index, option):
    current = context.user_data.get("d9_quiz_index")
    if current is None:
        await q.answer("Сначала запусти тест ❤️", show_alert=True)
        return
    if index != current:
        await q.answer("Этот вопрос уже пройден ❤️")
        return

    question = DAY9_QUIZ[index]
    correct = option == question["correct"]
    if correct:
        context.user_data["d9_quiz_score"] = context.user_data.get("d9_quiz_score", 0) + 1
    db.save_answer(q.from_user.id, 9, f"calorie_q{index + 1}", option + 1)
    await q.answer("Записала ❤️")

    explanation = ("✅ Отлично!\n\n" if correct else "💡 Разбираем:\n\n") + question["feedback"][option]
    next_index = index + 1
    if next_index < len(DAY9_QUIZ):
        context.user_data["d9_quiz_index"] = next_index
        await q.message.reply_text(explanation)
        next_question = DAY9_QUIZ[next_index]
        await q.message.reply_text(
            f"Вопрос {next_index + 1} из {len(DAY9_QUIZ)}\n\n{next_question['text']}",
            reply_markup=day9_quiz_keyboard(next_index),
        )
        return

    score = context.user_data.get("d9_quiz_score", 0)
    context.user_data["d9_quiz_index"] = None
    db.save_answer(q.from_user.id, 9, "calorie_quiz_score", score)
    await q.message.reply_text(explanation)
    await q.message.reply_text(
        f"🎉 <b>Тест завершён!</b>\n\nТвой результат: <b>{score}/{len(DAY9_QUIZ)}</b>.\n\n"
        "Главное — понять принцип: калорийность нельзя определить по одному продукту или ярлыку «полезно/вредно». "
        "Важно смотреть на весь приём пищи и его количество.\n\n"
        "Теперь перейди к рефлексии — что стало понятнее после задания?",
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup([
            [bot.InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ", callback_data="reflection_start")],
            [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        ]),
    )


# runner.py has already installed its own menu wrapper at this point.
_original_menu_with_day9 = bot.menu


async def menu_with_day9(update, context):
    q = update.callback_query
    data = q.data if q else ""

    if q and data == "practice":
        u = db.user(q.from_user.id)
        if u and u["current_day"] == 9:
            await q.answer()
            await day9_show_practice(q, context)
            return

    if q and data == "d9_start":
        await day9_start(q, context)
        return

    if q and data.startswith("d9q:"):
        try:
            _, index, option = data.split(":")
            await day9_answer(q, context, int(index), int(option))
        except (ValueError, IndexError):
            await q.answer("Не удалось обработать ответ. Попробуй ещё раз.", show_alert=True)
        return

    await _original_menu_with_day9(update, context)


bot.menu = menu_with_day9
bot.main()
