import bot
import db
from bju_quiz import QUESTIONS, question_keyboard, result_keyboard

PENDING = "__REFLECTION_PENDING__"

_original_start_reflection = bot.start_reflection
_original_handle_text = bot.handle_text
_original_menu = bot.menu
_original_reflection_feedback = bot.reflection_feedback
_original_show_practice = bot.show_practice


def _has(text, *parts):
    return any(p in text for p in parts)


def reflection_feedback_fixed(day, text, uid=None):
    """Answer-aware reflection feedback without changing the approved course text."""
    t = text.strip().lower()

    if day in (1, 2):
        return _original_reflection_feedback(day, text, uid)

    if day == 3:
        if _has(t, "больш", "огром", "много"):
            return ("Спасибо за честное наблюдение ❤️\n\n"
                    "Ты заметила, что некоторые порции оказались больше, чем ощущались на первый взгляд. "
                    "Сейчас не нужно их уменьшать или исправлять. Важно сначала увидеть свой привычный объём — именно это и тренируем.")
        if _has(t, "мал", "меньш", "не наел", "не хват"):
            return ("Хорошее наблюдение ❤️\n\n"
                    "Ты заметила, что привычная порция может оказаться меньше, чем ожидалось. "
                    "Не нужно делать вывод, что теперь надо есть больше или меньше — просто фиксируем разницу между ощущением и реальностью.")
        return ("Спасибо за наблюдение ❤️\n\n"
                "Сегодня важно было не угадать граммы, а посмотреть на привычный размер порции внимательнее. "
                "Если ожидание и реальность отличались — это уже полезная информация о твоём питании.")

    if day == 4:
        if _has(t, "стыд", "скры", "не хот", "сложно отправ", "трудно отправ", "неудоб"):
            return ("Спасибо, что заметила этот момент ❤️\n\n"
                    "Похоже, сложность была не только в самом фото, но и в желании показать себя «правильно». "
                    "Здесь как раз тренируем обратное: не редактировать реальность ради оценки, а спокойно её видеть.")
        return ("Ты сегодня сделала важную вещь ❤️\n\n"
                "Ты показала рацион без попытки сделать его идеальным. Это позволяет увидеть не отдельный «правильный» день, а настоящую картину, с которой можно работать дальше.")

    if day == 5:
        if _has(t, "стресс", "нерв", "тревог", "пережив", "расстро", "зл", "груст"):
            return ("Ты заметила важную связь ❤️\n\n"
                    "В твоём ответе еда появляется рядом со стрессом или сильными эмоциями. Это не значит, что эмоции нужно «убрать», а еду запретить. "
                    "Сейчас нам важно научиться замечать сам момент: что произошло → что ты почувствовала → захотелось ли что-то съесть.")
        if _has(t, "устал", "усталость", "вечер", "к вечеру", "после работ", "домой"):
            return ("Ты заметила свой вечерний сценарий ❤️\n\n"
                    "Похоже, желание что-то съесть чаще появляется на фоне усталости или в конце дня. "
                    "Пока ничего не меняем — просто наблюдаем, повторяется ли эта связь и что именно тебе хочется в такие моменты.")
        if _has(t, "скуч", "скука", "нечем", "от нечего", "без дел"):
            return ("Вот это полезное наблюдение ❤️\n\n"
                    "Ты заметила, что желание перекусить может появляться не из-за голода, а когда становится скучно или нечем заняться. "
                    "Не нужно запрещать себе еду — сначала учимся различать сам момент и его причину.")
        if _has(t, "голод", "проголод", "долго не", "не ела", "между прием", "между приём"):
            return ("Ты заметила связь с голодом ❤️\n\n"
                    "Это важное отличие: иногда дополнительная еда появляется потому, что организм действительно успел проголодаться. "
                    "Продолжай замечать, насколько сильным был голод и что происходило перед перекусом.")
        if _has(t, "привыч", "автомат", "по времени", "за компанию", "увид", "на кухн", "рядом"):
            return ("Ты заметила автоматический сценарий ❤️\n\n"
                    "Похоже, желание что-то съесть может запускаться привычкой, обстановкой или самим фактом, что еда рядом. "
                    "Сейчас не нужно это ломать — сначала важно увидеть, в каких ситуациях сценарий повторяется.")
        return ("Спасибо за честный ответ ❤️\n\n"
                "Ты уже начала искать не только сам перекус, но и момент, который ему предшествует. "
                "Попробуй дальше замечать три вещи: что происходило перед этим, что ты чувствовала и действительно ли была голодна. Это поможет увидеть свой сценарий без оценки.")

    if _has(t, "стресс", "эмоци", "тревог", "нерв", "зл", "груст", "устал"):
        return ("Ты заметила эмоциональный контекст ❤️\n\n"
                "Это важное наблюдение: ты связала своё поведение с состоянием, в котором находилась. "
                "Не нужно сразу что-то исправлять — сначала посмотрим, повторяется ли эта закономерность.")
    if _has(t, "сложно", "трудно", "не получ", "ошиб", "не смог", "не уме"):
        return ("Спасибо, что написала об этом честно ❤️\n\n"
                "То, что сейчас сложно, тоже является результатом наблюдения. Не нужно делать навык идеально с первого раза — важно понять, где именно возникает трудность, и постепенно её разобрать.")
    if _has(t, "удив", "не ожид", "впервые", "раньше не замеч", "оказыва"):
        return ("Вот это и есть полезная рефлексия ❤️\n\n"
                "Ты обнаружила что-то, чего раньше не замечала. Такие наблюдения важнее «правильного» ответа, потому что именно из них постепенно складывается твоя собственная система.")
    if _has(t, "понял", "стало понят", "теперь знаю", "разобрал", "научил"):
        return ("Отлично ❤️\n\n"
                "Ты смогла перевести сегодняшнее задание из теории в собственное наблюдение. Сохрани это понимание — дальше задача будет не просто знать правило, а уметь применять его самостоятельно.")
    if _has(t, "легк", "просто", "без проблем", "получил", "сделала"):
        return ("Хорошее наблюдение ❤️\n\n"
                "Ты увидела, что этот навык уже получается без сильного напряжения. Это хороший знак: постепенно он может становиться частью твоих обычных решений, а не отдельным заданием курса.")

    return ("Спасибо за честный ответ ❤️\n\n"
            f"Ты заметила: «{text[:180]}». Это и есть материал для сегодняшней рефлексии. "
            "Не нужно сразу делать выводы или что-то исправлять. Сначала учимся замечать свои реальные решения и закономерности — именно так постепенно появляется самостоятельность.")


async def start_reflection_fixed(q, context):
    uid = q.from_user.id
    u = db.user(uid)
    if u:
        n = u["current_day"]
        con = db.connect()
        con.execute(
            "UPDATE days SET reflection=? WHERE tg_id=? AND day=? AND status='IN_PROGRESS'",
            (PENDING, uid, n),
        )
        con.commit()
        con.close()
    await _original_start_reflection(q, context)


async def handle_text_fixed(update, context):
    uid = update.effective_user.id

    try:
        u = db.user(uid)
        row = db.day_row(uid, u["current_day"]) if u else None
        pending = bool(
            row
            and row["reflection"] == PENDING
            and row["status"] == "IN_PROGRESS"
        )
    except Exception:
        pending = False

    if (
        pending
        and not context.user_data.get("awaiting_question")
        and not context.user_data.get("awaiting_system")
    ):
        context.user_data["awaiting_reflection"] = True

    await _original_handle_text(update, context)


async def show_practice_fixed(q, context):
    """Day 8 uses an interactive BJU test as its practice."""
    uid = q.from_user.id
    n = db.user(uid)["current_day"]

    if n != 8:
        await _original_show_practice(q, context)
        return

    text = (
        "📝 <b>ПРАКТИКА</b>\n\n"
        "Пройди короткий мини-тест на распределение продуктов по БЖУ.\n\n"
        "Твоя задача — не набрать идеальный результат, а проверить, насколько ты уже различаешь белки, жиры и углеводы."
    )
    buttons = [
        [bot.InlineKeyboardButton("📝 ПРОЙТИ МИНИ-ТЕСТ", callback_data="bju_start")],
        [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ]
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=bot.InlineKeyboardMarkup(buttons))


async def bju_start(q, context):
    context.user_data["bju_quiz_index"] = 0
    context.user_data["bju_quiz_score"] = 0
    context.user_data["bju_quiz_answers"] = []
    await q.message.reply_text(
        "🧠 <b>МИНИ-ТЕСТ БЖУ</b>\n\n5 вопросов. Выбирай тот вариант, который кажется тебе наиболее правильным.",
        parse_mode="HTML",
    )
    await q.message.reply_text(
        f"Вопрос 1 из {len(QUESTIONS)}\n\n{QUESTIONS[0]['text']}",
        reply_markup=question_keyboard(0),
    )


async def bju_answer(q, context, question_index, option_index):
    current = context.user_data.get("bju_quiz_index")
    if current is None:
        await q.answer("Сначала запусти тест ❤️", show_alert=True)
        return
    if question_index != current:
        await q.answer("Этот вопрос уже пройден ❤️")
        return

    question = QUESTIONS[question_index]
    correct = option_index == question["correct"]
    if correct:
        context.user_data["bju_quiz_score"] = context.user_data.get("bju_quiz_score", 0) + 1

    context.user_data.setdefault("bju_quiz_answers", []).append({
        "question": question_index + 1,
        "option": option_index + 1,
        "correct": correct,
    })
    db.save_answer(q.from_user.id, 8, f"bju_q{question_index + 1}", option_index + 1)
    await q.answer("Верно ❤️" if correct else "Записала ❤️")

    prefix = "✅ Верно!" if correct else "💡 Посмотри на объяснение:"
    feedback = f"{prefix}\n\n{question['explain']}"
    next_index = question_index + 1

    if next_index < len(QUESTIONS):
        context.user_data["bju_quiz_index"] = next_index
        await q.message.reply_text(feedback)
        await q.message.reply_text(
            f"Вопрос {next_index + 1} из {len(QUESTIONS)}\n\n{QUESTIONS[next_index]['text']}",
            reply_markup=question_keyboard(next_index),
        )
        return

    score = context.user_data.get("bju_quiz_score", 0)
    context.user_data["bju_quiz_index"] = None
    db.save_answer(q.from_user.id, 8, "bju_quiz_score", score)

    if score == len(QUESTIONS):
        level_text = "Отлично — ты уверенно различаешь БЖУ."
    elif score >= 3:
        level_text = "Хороший результат — основа уже есть. Ошибки можно спокойно разобрать."
    else:
        level_text = "Это нормально — тест как раз показал, что стоит закрепить."

    await q.message.reply_text(
        feedback +
        f"\n\n🎉 <b>Тест завершён!</b>\n\nРезультат: <b>{score}/{len(QUESTIONS)}</b>\n{level_text}\n\nТеперь переходи к завершению практики.",
        parse_mode="HTML",
        reply_markup=result_keyboard(),
    )


async def menu_fixed(update, context):
    q = update.callback_query
    data = q.data if q else ""

    if data == "bju_start":
        await q.answer()
        await bju_start(q, context)
        return

    if data.startswith("bju_answer:"):
        parts = data.split(":")
        if len(parts) != 3:
            await q.answer("Не удалось прочитать ответ.", show_alert=True)
            return
        await bju_answer(q, context, int(parts[1]), int(parts[2]))
        return

    if data == "continue":
        await q.answer()
        uid = q.from_user.id

        try:
            u = db.user(uid)
            if not u:
                await q.message.reply_text(
                    "Не могу найти твой прогресс ❤️ Данные курса не должны сбрасываться при перезапуске. "
                    "Проверь постоянное хранилище SQLite в Railway, а затем нажми «ПРОДОЛЖИТЬ» ещё раз.",
                    reply_markup=bot.main_kb(),
                )
                return

            n = int(u["current_day"])
            row = db.day_row(uid, n)
            if not row:
                await q.message.reply_text(
                    "Не могу найти текущий день в базе ❤️ Проверь постоянное хранилище SQLite в Railway.",
                    reply_markup=bot.main_kb(),
                )
                return

            await bot.begin_day(q, n)
        except Exception:
            await q.message.reply_text(
                "Я здесь ❤️ Не удалось открыть сохранённый день. Проверь постоянное хранилище SQLite в Railway и попробуй «ПРОДОЛЖИТЬ» ещё раз.",
                reply_markup=bot.main_kb(),
            )
        return

    await _original_menu(update, context)


bot.start_reflection = start_reflection_fixed
bot.handle_text = handle_text_fixed
bot.menu = menu_fixed
bot.reflection_feedback = reflection_feedback_fixed
bot.show_practice = show_practice_fixed

bot.main()
