import runpy
import bot
import db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def calc_activity_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪑 Минимальная", callback_data="calc_activity:1.2")],
        [InlineKeyboardButton("🚶 Лёгкая", callback_data="calc_activity:1.375")],
        [InlineKeyboardButton("🏃 Средняя", callback_data="calc_activity:1.55")],
        [InlineKeyboardButton("🏋️ Высокая", callback_data="calc_activity:1.725")],
    ])


def calc_sex_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👩 Женщина", callback_data="calc_sex:female"),
         InlineKeyboardButton("👨 Мужчина", callback_data="calc_sex:male")],
    ])


def calc_goal_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔻 Снижение веса", callback_data="calc_goal:loss")],
        [InlineKeyboardButton("⚖️ Поддержание", callback_data="calc_goal:maintain")],
        [InlineKeyboardButton("🔺 Набор", callback_data="calc_goal:gain")],
    ])


async def start_calc(q, context):
    context.user_data["calc"] = {}
    await q.message.reply_text(
        "🧮 <b>РАСЧЁТ ОРИЕНТИРА КАЛОРИЙ</b>\n\n"
        "Сначала выберем пол — это нужно для формулы расчёта базового обмена.",
        parse_mode="HTML",
        reply_markup=calc_sex_kb(),
    )


async def calc_sex(q, context, sex):
    context.user_data.setdefault("calc", {})["sex"] = sex
    context.user_data["calc_waiting"] = "age"
    await q.message.reply_text("Сколько тебе полных лет? Напиши число, например: 32")


async def calc_activity(q, context, factor):
    context.user_data.setdefault("calc", {})["activity"] = float(factor)
    context.user_data["calc_waiting"] = None
    await q.message.reply_text("🎯 Теперь выбери цель:", reply_markup=calc_goal_kb())


async def calc_goal(q, context, goal):
    data = context.user_data.get("calc", {})
    data["goal"] = goal
    try:
        age = int(data["age"])
        height = float(data["height"])
        weight = float(data["weight"])
        activity = float(data["activity"])
        sex = data["sex"]
    except (KeyError, TypeError, ValueError):
        await q.message.reply_text("Не удалось собрать все данные ❤️ Давай начнём расчёт заново.")
        context.user_data["calc"] = {}
        context.user_data["calc_waiting"] = None
        return

    # Mifflin–St Jeor: BMR -> approximate daily expenditure -> goal-oriented reference.
    bmr = 10 * weight + 6.25 * height - 5 * age + (-161 if sex == "female" else 5)
    tdee = bmr * activity
    if goal == "loss":
        target = tdee * 0.85
        goal_text = "снижения веса"
    elif goal == "gain":
        target = tdee * 1.10
        goal_text = "набора"
    else:
        target = tdee
        goal_text = "поддержания"

    bmr_r = round(bmr)
    tdee_r = round(tdee)
    target_r = round(target)
    uid = q.from_user.id

    db.save_answer(uid, 10, "calc_sex", sex)
    db.save_answer(uid, 10, "calc_age", age)
    db.save_answer(uid, 10, "calc_height", height)
    db.save_answer(uid, 10, "calc_weight", weight)
    db.save_answer(uid, 10, "calc_activity", activity)
    db.save_answer(uid, 10, "calc_goal", goal)
    db.save_answer(uid, 10, "calc_bmr", bmr_r)
    db.save_answer(uid, 10, "calc_tdee", tdee_r)
    db.save_answer(uid, 10, "calc_target", target_r)

    context.user_data["calc_waiting"] = None
    context.user_data["calc_result"] = target_r

    await q.message.reply_text(
        "📊 <b>ТВОЙ ОРИЕНТИР</b>\n\n"
        f"Базовый обмен: <b>{bmr_r} ккал</b>\n"
        f"Примерный расход с учётом активности: <b>{tdee_r} ккал</b>\n\n"
        f"Для {goal_text}: <b>≈ {target_r} ккал/день</b>\n\n"
        "Это ориентир, а не жёсткая норма. Реальная потребность может отличаться, "
        "поэтому не нужно воспринимать цифру как «разрешённый максимум» или оценку твоего питания.\n\n"
        "Теперь посмотри на эту цифру и ответь себе: насколько она отличается от того, "
        "что ты раньше представляла как свой калораж?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ", callback_data="reflection_start")],
            [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        ]),
    )


async def show_practice_patch(q, context):
    uid = q.from_user.id
    n = db.user(uid)["current_day"]
    if n != 10:
        return False
    await q.message.reply_text(
        "📝 <b>ПРАКТИКА</b>\n\n"
        "Рассчитай свой индивидуальный ориентир калорийности.\n\n"
        "Пройди короткий расчёт: пол → возраст → рост → вес → активность → цель.\n\n"
        "Твоя задача — не получить «идеальную» цифру, а понять свой ориентир и увидеть его как инструмент, а не наказание.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧮 РАССЧИТАТЬ МОЙ ОРИЕНТИР", callback_data="calc_start")],
            [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        ]),
    )
    return True


_original_show_practice = bot.show_practice


async def show_practice(q, context):
    if await show_practice_patch(q, context):
        return
    await _original_show_practice(q, context)


bot.show_practice = show_practice


_original_reflection_feedback = bot.reflection_feedback


def reflection_feedback(day, text, uid=None):
    if day == 12:
        t = text.strip().lower()
        if any(p in t for p in ("йогурт", "яйц", "яйцо", "творог", "сыр", "куриц", "рыб", "лосос", "индейк", "мяс", "белок")):
            return (
                "Хороший выбор ❤️\n\n"
                "Йогурт и яйца — понятные и удобные источники белка, которые легко встроить в обычный день. "
                "Особенно ценно, что ты сразу назвала конкретные продукты, а не просто «что-нибудь белковое». "
                "Теперь у тебя уже есть 2 простых варианта, к которым можно обращаться, когда нужно добрать белок."
            )
        return (
            "Хороший ответ ❤️\n\n"
            "Ты уже начала формировать свою личную белковую базу. "
            "Главное сейчас — не искать идеальные продукты, а выбрать те источники белка, которые тебе действительно удобно есть регулярно."
        )
    return _original_reflection_feedback(day, text, uid)


bot.reflection_feedback = reflection_feedback


_original_menu = bot.menu


async def menu(update, context):
    q = update.callback_query
    data = q.data if q else ""
    if data == "calc_start":
        await q.answer()
        await start_calc(q, context)
        return
    if data.startswith("calc_sex:"):
        await q.answer()
        await calc_sex(q, context, data.split(":", 1)[1])
        return
    if data.startswith("calc_activity:"):
        await q.answer()
        await calc_activity(q, context, data.split(":", 1)[1])
        return
    if data.startswith("calc_goal:"):
        await q.answer()
        await calc_goal(q, context, data.split(":", 1)[1])
        return
    await _original_menu(update, context)


bot.menu = menu


_original_handle_text = bot.handle_text


async def handle_text(update, context):
    waiting = context.user_data.get("calc_waiting")
    if waiting:
        text = update.message.text.strip().replace(",", ".")
        try:
            if waiting == "age":
                value = int(float(text))
                if not 10 <= value <= 100:
                    raise ValueError
                context.user_data.setdefault("calc", {})["age"] = value
                context.user_data["calc_waiting"] = "height"
                await update.message.reply_text("Какой у тебя рост в сантиметрах? Например: 168")
                return
            if waiting == "height":
                value = float(text)
                if not 100 <= value <= 230:
                    raise ValueError
                context.user_data.setdefault("calc", {})["height"] = value
                context.user_data["calc_waiting"] = "weight"
                await update.message.reply_text("Какой у тебя вес в килограммах? Например: 65")
                return
            if waiting == "weight":
                value = float(text)
                if not 30 <= value <= 250:
                    raise ValueError
                context.user_data.setdefault("calc", {})["weight"] = value
                context.user_data["calc_waiting"] = "activity"
                await update.message.reply_text(
                    "Теперь выбери свой обычный уровень активности:",
                    reply_markup=calc_activity_kb(),
                )
                return
        except ValueError:
            label = {"age": "возраст", "height": "рост", "weight": "вес"}[waiting]
            await update.message.reply_text(f"Похоже, я не распознала {label} ❤️ Напиши только число.")
            return
    await _original_handle_text(update, context)


bot.handle_text = handle_text


runpy.run_module("runner", run_name="__main__")
