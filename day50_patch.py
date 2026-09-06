"""BALANCE BODY — День 50: любимые блюда под себя."""

import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

DAY = 50
COURSE_DAYS = 50
XP = 50
TITLE = "Я ДЕЛАЮ ЛЮБИМЫЕ БЛЮДА ПОД СЕБЯ"
LEVEL_NAME = "АВТОМАТИЗИРУЮ"
SKILL = "Адаптирую любимые блюда под свой рацион"

INFO = (DAY, TITLE, LEVEL_NAME, SKILL, XP)

INTRO = (
    "Когда ты начинаешь считать калории и БЖУ, не нужно переходить на отдельную «диетическую еду».\n\n"
    "Любимые блюда можно оставить в рационе и немного изменить их состав под себя.\n\n"
    "Важно: цель не в том, чтобы сделать пиццу, карбонару или синнабон максимально низкокалорийными. "
    "Цель — научиться вписывать любимую еду в свой рацион так, чтобы она оставалась вкусной и приносила удовольствие."
)

EXAMPLES = (
    "🍕 <b>Пицца</b>\n"
    "Сыр с меньшей жирностью → вместо обычного; ветчина из индейки → вместо пепперони; "
    "соус из греческого йогурта + кетчуп.\n\n"
    "🍝 <b>Карбонара</b>\n"
    "Белковый соус из творога + немного воды/молока и сыра; ветчина из индейки → вместо бекона.\n\n"
    "🥐 <b>Синнабоны</b>\n"
    "Творожное тесто; крем из греческого йогурта + творожного сыра + подсластителя.\n\n"
    "🍔 <b>Бургер</b>\n"
    "Котлета из более постного фарша; йогурт + горчица + кетчуп вместо жирного соуса; сыр можно оставить, овощей добавить больше.\n\n"
    "🌯 <b>Шаурма</b>\n"
    "Курица или индейка; йогуртовый соус; больше овощей; лаваш оставляем.\n\n"
    "🥞 <b>Сладкие панкейки</b>\n"
    "Творожная начинка с какао и подсластителем; сверху можно оставить немного настоящего шоколада.\n\n"
    "🍰 <b>Чизкейк</b>\n"
    "Часть сливочного сыра можно заменить творогом или мягким творогом; сахар — подсластителем; "
    "сливки — греческим йогуртом."
)

PRACTICE = (
    "Вспомни <b>3 блюда</b>, от которых тебе было бы сложнее всего отказаться во время похудения.\n\n"
    "Для каждого блюда ответь:\n"
    "1️⃣ Что мне нравится в нём больше всего?\n"
    "2️⃣ Какие ингредиенты можно изменить, не потеряв основной вкус?\n"
    "3️⃣ Что я хочу оставить без изменений просто потому, что мне это нравится?\n"
    "4️⃣ Как будет выглядеть моя версия этого блюда?\n\n"
    "И закончи фразу:\n"
    "<b>«Теперь я понимаю, что мне не обязательно отказываться от любимой еды. Я могу…»</b>"
)

REFLECTION = (
    "Какое из трёх блюд ты теперь точно можешь оставить в своём рационе?\n"
    "Что именно ты в нём изменишь?\n"
    "И что оставишь без изменений ради вкуса и удовольствия?"
)

TASK = (
    "Сегодня учимся делать привычные блюда удобнее для своего рациона, не превращая их в «диетическую еду».\n\n"
    + INTRO + "\n\n" + EXAMPLES
)

# The base course stores DAYS as a list of tuples.
if isinstance(getattr(bot, "DAYS", None), list):
    while len(bot.DAYS) < DAY:
        bot.DAYS.append((len(bot.DAYS) + 1, "", LEVEL_NAME, "", 50))
    bot.DAYS[DAY - 1] = INFO

if isinstance(getattr(bot, "DAY_TASKS", None), dict):
    bot.DAY_TASKS[DAY] = ("Сегодня учимся адаптировать любимую еду под свой рацион.", PRACTICE, REFLECTION)

# Extend the final level to include the new Day 50.
if isinstance(getattr(bot, "LEVELS", None), dict) and 5 in bot.LEVELS:
    bot.LEVELS[5] = (bot.LEVELS[5][0], bot.LEVELS[5][1], DAY)

# Add a dedicated final badge without changing existing badges.
if isinstance(getattr(bot, "BADGES", None), dict):
    bot.BADGES[DAY] = "🍕 Любимая еда — в моей системе"

_real_level_for_day = bot.level_for_day
def level_for_day(n):
    if n == DAY:
        return 5, LEVEL_NAME
    return _real_level_for_day(n)
bot.level_for_day = level_for_day

_real_completion_text = bot.completion_text
def completion_text(n, info, badge_text=""):
    if n == DAY:
        return (
            f"🎉 <b>День 50 завершен!</b>\n\n"
            f"+{XP} XP{badge_text}\n\n"
            "🏆 Ты дошла до финала и теперь умеешь не отказываться от любимой еды, "
            "а адаптировать её под себя ❤️"
        )
    return _real_completion_text(n, info, badge_text)
bot.completion_text = completion_text

_real_show_day = bot.show_day
async def show_day(q):
    n = bot.db.user(q.from_user.id)["current_day"]
    if n != DAY:
        return await _real_show_day(q)
    status = bot.db.day_row(q.from_user.id, DAY)["status"]
    text = (
        f"🗓 <b>ДЕНЬ {DAY} ИЗ {COURSE_DAYS}</b>\n\n"
        f"<b>{TITLE}</b>\n\n"
        f"Уровень: {LEVEL_NAME}\n🎯 Навык: {SKILL}\n⭐ Награда: +{XP} XP\n\n{TASK}"
    )
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=bot.day_kb(DAY, status))
bot.show_day = show_day

_real_begin_day = bot.begin_day
async def begin_day(q, n):
    if n != DAY:
        return await _real_begin_day(q, n)
    row = bot.db.day_row(q.from_user.id, DAY)
    if not row or row["status"] == "LOCKED":
        await q.message.reply_text("Этот день пока закрыт 🔒")
        return
    bot.db.start_day(q.from_user.id, DAY)
    text = (
        f"💡 <b>ДЕНЬ {DAY} — {TITLE}</b>\n\n{TASK}\n\n"
        f"🎯 Сегодня формируем навык:\n<b>{SKILL}</b>\n\n"
        "Когда будешь готова, переходи к практике."
    )
    buttons = [
        [InlineKeyboardButton("➡️ К ПРАКТИКЕ", callback_data="practice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
    ]
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
bot.begin_day = begin_day

_real_show_practice = bot.show_practice
async def show_practice(q, context):
    n = bot.db.user(q.from_user.id)["current_day"]
    if n != DAY:
        return await _real_show_practice(q, context)
    text = "📝 <b>ПРАКТИКА</b>\n\n" + PRACTICE + "\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА»."
    buttons = [
        [InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ]
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
bot.show_practice = show_practice

_real_start_reflection = bot.start_reflection
async def start_reflection(q, context):
    n = bot.db.user(q.from_user.id)["current_day"]
    if n != DAY:
        return await _real_start_reflection(q, context)
    context.user_data.pop("awaiting_hunger", None)
    context.user_data.pop("awaiting_satiety", None)
    context.user_data["awaiting_reflection"] = True
    await q.message.reply_text(
        "🌿 Теперь рефлексия\n\n" + REFLECTION +
        "\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день."
    )
bot.start_reflection = start_reflection

# Day-specific reflection feedback: react to what the participant actually wrote.
_real_reflection_feedback = bot.reflection_feedback
def reflection_feedback(day, text, uid=None):
    if day != DAY:
        return _real_reflection_feedback(day, text, uid)
    t = text.strip().lower()
    parts = []
    if any(x in t for x in ("пицц", "карбона", "синнабон", "бургер", "шаурм", "панкейк", "чизкейк")):
        parts.append("Ты уже начала смотреть на любимое блюдо не как на «запрещённое», а как на конструктор: можно изменить отдельные ингредиенты и сохранить саму идею блюда.")
    if any(x in t for x in ("сыр", "ветчин", "соус", "творог", "йогурт", "бекон", "пепперон", "сливк", "сахар", "шоколад", "фарш")):
        parts.append("Особенно ценно, что ты выделила конкретные ингредиенты для замены. Именно такой подход помогает адаптировать еду под свои БЖУ, а не отказываться от неё целиком.")
    if any(x in t for x in ("оставлю", "оставить", "не буду менять", "без изменений", "вкус")):
        parts.append("И то, что ты оставляешь часть блюда без изменений ради вкуса, тоже важно: не нужно оптимизировать еду до состояния, в котором она перестаёт тебе нравиться.")
    if any(x in t for x in ("могу", "впис", "адаптир", "замен", "приготов", "сдела")):
        parts.append("Это уже переносимый навык: теперь ты можешь смотреть на любое любимое блюдо и самостоятельно решать, что в нём стоит изменить, а что оставить.")
    if not parts:
        parts.append("Ты тренируешь именно тот навык, ради которого нужен этот день: не выбирать между «любимая еда» и «правильное питание», а искать свой вариант блюда.")
    return "Спасибо за ответ ❤️\n\n" + "\n\n".join(parts)
bot.reflection_feedback = reflection_feedback

_real_show_progress = bot.show_progress
async def show_progress(q):
    uid = q.from_user.id
    u = bot.db.user(uid)
    done = sum(1 for n in range(1, COURSE_DAYS + 1) if bot.db.day_row(uid, n)["status"] == "COMPLETED")
    percent = round(done / COURSE_DAYS * 100)
    await q.message.reply_text(
        f"📊 <b>МОЙ ПРОГРЕСС</b>\n\n🗓 {done}/{COURSE_DAYS} дней\n📈 {percent}%\n⭐ {u['xp']} XP\n🎯 Текущий день: {u['current_day']}\n🏆 Достижений: {len(bot.db.badges(uid))}",
        parse_mode="HTML", reply_markup=bot.back_kb()
    )
bot.show_progress = show_progress

_real_show_map = bot.show_map
async def show_map(q):
    uid = q.from_user.id
    lines = []
    for level, (name, a, b) in bot.LEVELS.items():
        done = sum(1 for n in range(a, b + 1) if bot.db.day_row(uid, n)["status"] == "COMPLETED")
        icon = "🟢" if done == (b - a + 1) else ("🟡" if done else "🔒")
        lines.append(f"{icon} L{level} — {name}: {done}/{b - a + 1}")
    await q.message.reply_text("🗺 <b>МОЯ КАРТА</b>\n\n" + "\n".join(lines), parse_mode="HTML", reply_markup=bot.back_kb())
bot.show_map = show_map

_real_show_skills = bot.show_skills
async def show_skills(q):
    uid = q.from_user.id
    done = sum(1 for n in range(1, COURSE_DAYS + 1) if bot.db.day_row(uid, n)["status"] == "COMPLETED")
    text = "🧠 <b>МОИ НАВЫКИ</b>\n\n"
    for n, title, level, skill, xp in bot.DAYS:
        text += ("🟢 " if n <= done else "🔒 ") + skill + "\n"
    await q.message.reply_text(text, parse_mode="HTML", reply_markup=bot.back_kb())
bot.show_skills = show_skills

_real_reminders = bot.reminders
async def reminders(context):
    now = bot.datetime.now(bot.TZ)
    date_key = now.date().isoformat()
    if now.hour != bot.REMINDER_HOUR:
        return
    con = bot.db.connect()
    rows = con.execute("SELECT * FROM users WHERE current_day<=?", (COURSE_DAYS,)).fetchall()
    con.close()
    for u in rows:
        if not bot.db.claim_reminder(u["tg_id"], date_key):
            continue
        try:
            await context.bot.send_message(
                u["tg_id"],
                f"🌿 Добрый день, {u['name']}!\nТвой День {u['current_day']} из {COURSE_DAYS} ждёт тебя.",
                reply_markup=bot.main_kb()
            )
        except Exception:
            pass
bot.reminders = reminders

# The existing /start conversation uses the function object available when main() builds it.
_real_start = bot.start
async def start(update, context):
    u = bot.db.user(update.effective_user.id)
    if u:
        await update.message.reply_text(
            f"С возвращением, {u['name']} ❤️\n\n"
            f"День {u['current_day']} из {COURSE_DAYS} уже ждёт тебя.",
            reply_markup=bot.main_kb()
        )
        return bot.ConversationHandler.END
    return await _real_start(update, context)
bot.start = start
