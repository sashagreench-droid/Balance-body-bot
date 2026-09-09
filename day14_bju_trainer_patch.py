import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# BALANCE BODY — День 14: personal BJU check + trainer review.
# The participant first records her current BJU, then sends a personal photo.
# Both are forwarded to the trainer for correction.

DAY14_TEXT = """📝 <b>КОНТРОЛЬНАЯ: РАЗБИРАЮ МОЁ ТЕКУЩЕЕ БЖУ</b>

Сегодня не проверяем теорию по учебнику. Мы смотрим именно на <b>твоё текущее БЖУ</b> и передаём его тренеру на проверку.

<b>Шаг 1. Посмотри, какие цифры БЖУ ты сейчас используешь.</b>

Если у тебя уже есть рассчитанная норма или цель — возьми её. Если ты пока не знаешь свои цифры, напиши об этом: тренер поможет определить их.

Пришли одним сообщением:
• калории — … ккал
• белки — … г
• жиры — … г
• углеводы — … г

Если каких-то цифр нет — просто напиши «не знаю».

<b>Шаг 2. Посмотри на свой рацион.</b>

Ответь себе:
• получается ли у тебя регулярно добирать белок?
• не приходится ли слишком сильно урезать жиры или углеводы?
• удобно ли тебе держать эти цифры в обычной жизни?
• есть ли постоянный голод, усталость или желание «доесть» вечером?

Не пытайся сегодня подогнать рацион под идеальные цифры. Нам нужна <b>реальная картина</b>.

<b>Шаг 3. Отправь своё фото.</b>

После того как внесёшь БЖУ, я попрошу отправить фото. Оно вместе с твоими цифрами уйдёт тренеру.

Тренер посмотрит твою ситуацию и при необходимости <b>скорректирует БЖУ</b>. Самостоятельно менять цифры до проверки не нужно.

❤️ Задача дня — не угадать идеальное БЖУ, а получить персональную корректировку под себя."""


def _kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 ВНЕСТИ МОЁ ТЕКУЩЕЕ БЖУ", callback_data="day14_bju_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
        [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
    ])


async def show_practice(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 14:
        return await bot._day14_bju_original_show_practice(q, context)

    context.user_data.pop("day14_bju", None)
    context.user_data.pop("awaiting_day14_bju_photo", None)
    await q.message.reply_text(DAY14_TEXT, parse_mode="HTML", reply_markup=_kb())


async def menu(update, context):
    q = update.callback_query
    data = q.data or ""
    if data == "day14_bju_start":
        await q.answer()
        context.user_data["awaiting_day14_bju"] = True
        await q.message.reply_text(
            "📊 Напиши своё текущее БЖУ одним сообщением.\n\n"
            "Например:\n"
            "Калории — 1800 ккал\n"
            "Белки — 120 г\n"
            "Жиры — 60 г\n"
            "Углеводы — 190 г\n\n"
            "Если ты не знаешь какую-то цифру — напиши «не знаю».",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤔 НЕ ЗНАЮ СВОЁ БЖУ", callback_data="day14_bju_unknown")],
                [InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")],
            ]),
        )
        return

    if data == "day14_bju_unknown":
        await q.answer()
        context.user_data.pop("awaiting_day14_bju", None)
        context.user_data["day14_bju"] = "Не знает текущую норму БЖУ"
        context.user_data["awaiting_day14_bju_photo"] = True
        await q.message.reply_text(
            "Хорошо ❤️ Тогда тренер посмотрит твою ситуацию и поможет определить подходящие цифры.\n\n"
            "Теперь отправь своё фото одним сообщением. После этого я передам тренеру твои данные на проверку.",
        )
        return

    return await bot._day14_bju_original_menu(update, context)


async def handle_text(update, context):
    if context.user_data.pop("awaiting_day14_bju", False):
        text = (update.message.text or "").strip()
        if not text:
            await update.message.reply_text("Напиши цифры БЖУ одним сообщением или нажми «НЕ ЗНАЮ СВОЁ БЖУ».")
            context.user_data["awaiting_day14_bju"] = True
            return

        context.user_data["day14_bju"] = text[:2000]
        context.user_data["awaiting_day14_bju_photo"] = True
        await update.message.reply_text(
            "Приняла ❤️\n\n"
            "Теперь отправь своё фото одним сообщением.\n\n"
            "Я передам тренеру вместе:\n"
            "📊 твоё текущее БЖУ\n"
            "📷 твоё фото\n\n"
            "Тренер проверит данные и при необходимости скорректирует БЖУ."
        )
        return

    return await bot._day14_bju_original_handle_text(update, context)


async def handle_photo(update, context):
    if context.user_data.pop("awaiting_day14_bju_photo", False):
        uid = update.effective_user.id
        u = bot.db.user(uid)
        bju = context.user_data.get("day14_bju", "Не указано")
        photo = update.message.photo[-1]

        # Save the photo in the normal course photo table as well.
        caption = update.message.caption or ""
        bot.db.save_photo(uid, 14, photo.file_id, caption)

        for admin in bot.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin,
                    f"📊 <b>ПРОВЕРКА БЖУ — ДЕНЬ 14</b>\n\n"
                    f"Участница: {u['name']}\n"
                    f"ID: {uid}\n\n"
                    f"Текущее БЖУ:\n{bju}\n\n"
                    f"Пожалуйста, проверь БЖУ и при необходимости скорректируй его.",
                    parse_mode="HTML",
                )
                await context.bot.send_photo(
                    admin,
                    photo.file_id,
                    caption=f"📷 Фото участницы {u['name']} — День 14, проверка БЖУ",
                )
            except Exception:
                pass

        # Complete the control day after the full package has been sent.
        info = bot.day_info(14)
        if bot.db.complete_day(uid, 14, f"БЖУ на проверку тренеру: {bju}"):
            bot.db.add_xp(uid, info[4])
            badge = bot.BADGES.get(14)
            badge_text = ""
            if badge and bot.db.add_badge(uid, badge):
                badge_text = f"\n🏆 Новое достижение: {badge}"
            await update.message.reply_text(
                "✅ <b>Данные отправлены тренеру</b>\n\n"
                "Я передала тренеру твоё текущее БЖУ и фото. ❤️\n\n"
                "Тренер проверит цифры и при необходимости скорректирует их под тебя. "
                "До проверки ничего специально менять не нужно.\n\n"
                + bot.completion_text(14, info, badge_text),
                parse_mode="HTML",
                reply_markup=bot.main_kb(),
            )
        else:
            await update.message.reply_text(
                "Я передала тренеру твоё БЖУ и фото ❤️ Тренер сможет проверить и скорректировать цифры.",
                reply_markup=bot.main_kb(),
            )
        context.user_data.pop("day14_bju", None)
        return

    return await bot._day14_bju_original_handle_photo(update, context)


bot._day14_bju_original_show_practice = bot.show_practice
bot.show_practice = show_practice

bot._day14_bju_original_menu = bot.menu
bot.menu = menu

bot._day14_bju_original_handle_text = bot.handle_text
bot.handle_text = handle_text

bot._day14_bju_original_handle_photo = bot.handle_photo
bot.handle_photo = handle_photo
