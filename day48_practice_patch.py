import bot

# Day 48: replace the abstract checklist with a concrete personal-system exercise.
_original_show_practice = bot.show_practice


async def show_practice_day48(q, context):
    uid = q.from_user.id
    n = bot.db.user(uid)["current_day"]
    if n != 48:
        return await _original_show_practice(q, context)

    text = (
        "📝 <b>ПРАКТИКА — МОЯ СИСТЕМА</b>\n\n"
        "Представь, что через месяц бота уже нет. Тебе нужно самостоятельно решить обычный день.\n\n"
        "Заполни 8 пунктов одним сообщением:\n\n"
        "1️⃣ <b>Белок:</b> что обычно съешь, чтобы набрать белок?\n"
        "2️⃣ <b>Быстрые блюда:</b> назови 2 блюда на случай, когда нет времени готовить.\n"
        "3️⃣ <b>Сладкое:</b> как будешь включать его без запретов и компенсации?\n"
        "4️⃣ <b>Ресторан/гости:</b> по какому принципу выберешь еду?\n"
        "5️⃣ <b>Поездка:</b> что возьмёшь или выберешь, если привычной еды нет?\n"
        "6️⃣ <b>Движение:</b> что реально будешь делать в обычную неделю?\n"
        "7️⃣ <b>Стресс:</b> что сделаешь, если захочется заесть эмоции?\n"
        "8️⃣ <b>Подсчёт:</b> в каких ситуациях он тебе нужен, а когда можно обойтись без него?\n\n"
        "В конце напиши одну фразу: <b>«Моя главная опора — …»</b>.\n\n"
        "Напиши всё одним сообщением. Здесь нет правильных ответов — мы собираем именно твою рабочую систему."
    )
    buttons = [
        [bot.InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО", callback_data="photo")],
        [bot.InlineKeyboardButton("✅ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [bot.InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")]
    ]
    await q.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=bot.InlineKeyboardMarkup(buttons)
    )


bot.show_practice = show_practice_day48
