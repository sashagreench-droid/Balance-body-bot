import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters

import db
from content import DAYS, DAY_TASKS, SNACKS, LEVELS, BADGES, SYSTEM_FIELDS

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}
TZ = ZoneInfo(os.getenv("BOT_TIMEZONE","UTC"))
REMINDER_HOUR = int(os.getenv("DAILY_REMINDER_HOUR","9"))
ASK_NAME, = range(1)

def day_info(n): return DAYS[n-1]
def task_info(n): return DAY_TASKS[n]
def level_for_day(n):
    for level,(name,a,b) in LEVELS.items():
        if a <= n <= b: return level,name

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ ПРОДОЛЖИТЬ", callback_data="continue")],
        [InlineKeyboardButton("🗺 МОЯ КАРТА", callback_data="map"), InlineKeyboardButton("🧠 МОИ НАВЫКИ", callback_data="skills")],
        [InlineKeyboardButton("🏆 ДОСТИЖЕНИЯ", callback_data="badges"), InlineKeyboardButton("📊 МОЙ ПРОГРЕСС", callback_data="progress")],
        [InlineKeyboardButton("❤️ МОЯ СИСТЕМА", callback_data="system"), InlineKeyboardButton("🥪 ПЕРЕКУСЫ", callback_data="snacks")],
        [InlineKeyboardButton("👩‍🏫 ЗАДАТЬ ТРЕНЕРУ", callback_data="trainer")],
    ])

def back_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")]])

def day_kb(n, status):
    label = "▶️ НАЧАТЬ" if status == "AVAILABLE" else ("▶️ ПРОДОЛЖИТЬ" if status == "IN_PROGRESS" else "↩️ ОТКРЫТЬ ДЕНЬ")
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"startday:{n}")],[InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")]])

def scale_kb(prefix):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=f"{prefix}:{i}") for i in range(1,6)],
        [InlineKeyboardButton(str(i), callback_data=f"{prefix}:{i}") for i in range(6,11)]
    ])

def reflection_buttons():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✍️ ОТВЕТИТЬ",callback_data="reflection_start")],[InlineKeyboardButton("⏭ ПРОПУСТИТЬ",callback_data="reflection_skip")]])

def after_photo_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌿 ПЕРЕЙТИ К РЕФЛЕКСИИ",callback_data="reflection_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")],
        [InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")],
    ])

def hunger_next_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍽️ ЕЩЁ ОДИН ПРИЁМ",callback_data="hunger_start")],
        [InlineKeyboardButton("🌿 ЗАВЕРШИТЬ И ПЕРЕЙТИ К РЕФЛЕКСИИ",callback_data="reflection_start")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")],
    ])

def reflection_feedback(day, text):
    """Short supportive feedback after a user's reflection; it does not judge the answer."""
    t = text.strip().lower()
    if day == 1:
        if any(phrase in t for phrase in ("хотелось изменить", "изменить выбор", "чтобы увид", "тренер увид", "бот увид", "оцен", "стыд", "страшно")):
            return ("Это очень важное наблюдение ❤️\n\n"
                    "Ты заметила не только свой рацион, но и момент, когда появляется желание выглядеть «правильно» для другого человека. "
                    "Сегодня ничего исправлять не нужно. Наоборот — оставляем этот момент таким, какой он был. "
                    "Ты уже тренируешь самостоятельность: замечать реальность, даже когда хочется её отредактировать.")
        if any(phrase in t for phrase in ("удив", "не ожид", "впервые замет", "раньше не замеч")):
            return ("Отличное наблюдение ❤️\n\n"
                    "Именно такие маленькие открытия нам сейчас и нужны. Сегодня не ищем, что с тобой «не так», — просто собираем честную картину своего питания. "
                    "Чем точнее ты замечаешь реальность, тем легче потом самостоятельно принимать решения.")
        return ("Спасибо за честный ответ ❤️\n\n"
                "Сегодня от тебя не требовалось идеального поведения или правильного ответа. "
                "Твоя задача была заметить происходящее без оценки — и ты её выполнила. "
                "Первый шаг к самостоятельности — научиться видеть реальность спокойно.")
    return "Спасибо за честный ответ ❤️ Ты не обязана отвечать идеально — здесь важно замечать себя и постепенно учиться принимать решения самостоятельно."

def completion_text(n, info, badge_text=""):
    next_text = "\n\n🏆 Финал завершен. Ты можешь сама." if n == 49 else f"\n\n➡️ Открыт День {n+1}."
    return f"🎉 <b>День {n} завершен!</b>\n\n+{info[4]} XP{badge_text}{next_text}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.user(update.effective_user.id)
    if u:
        await update.message.reply_text(f"С возвращением, {u['name']} ❤️\n\nДень {u['current_day']} из 49 уже ждёт тебя.", reply_markup=main_kb()); return ConversationHandler.END
    await update.message.reply_text("Привет! ❤️\n\nЭто курс «49 дней → самостоятельность».\n\nКак тебя зовут?"); return ASK_NAME

async def got_name(update, context):
    name=update.message.text.strip()[:80]; db.ensure_user(update.effective_user.id,name)
    await update.message.reply_text(f"{name}, начинаем ❤️\n\nТвоя задача — не быть идеальной. Твоя задача — постепенно научиться принимать решения самостоятельно.\n\nПервый шаг — просто наблюдать.",reply_markup=main_kb()); return ConversationHandler.END

async def menu(update, context):
    q=update.callback_query; await q.answer(); data=q.data; uid=q.from_user.id
    if data=="home": await q.message.reply_text("Главное меню ❤️",reply_markup=main_kb())
    elif data=="continue": await show_day(q)
    elif data=="map": await show_map(q)
    elif data=="skills": await show_skills(q)
    elif data=="badges": await show_badges(q)
    elif data=="progress": await show_progress(q)
    elif data=="system": await show_system(q)
    elif data.startswith("sys:"): await ask_system(q, data.split(":",1)[1], context)
    elif data=="snacks": await show_snacks(q)
    elif data=="trainer":
        context.user_data["awaiting_question"]=True; await q.message.reply_text("Напиши вопрос одним сообщением — я передам его тренеру.",reply_markup=back_kb())
    elif data.startswith("startday:"): await begin_day(q,int(data.split(":")[1]))
    elif data=="practice": await show_practice(q,context)
    elif data=="photo":
        context.user_data["awaiting_photo"]=True
        await q.message.reply_text("📷 Отправь фото отчёта сюда.\n\nМожно отправить один или несколько снимков — не нужно делать питание идеальным. Просто покажи день таким, какой он был.")
    elif data=="donepractice": await start_reflection(q,context)
    elif data=="hunger_start":
        context.user_data["awaiting_hunger"]=True
        await q.message.reply_text("🍽️ Насколько ты голодна перед едой?\n\n1 — совсем не голодна\n5 — умеренный голод\n10 — очень сильный голод",reply_markup=scale_kb("hunger"))
    elif data.startswith("hunger:"):
        value=int(data.split(":")[1]); db.save_answer(uid,db.user(uid)["current_day"],"hunger_before",value); context.user_data.pop("awaiting_hunger",None); context.user_data["awaiting_satiety"]=True
        await q.message.reply_text("🍽️ А теперь после еды: насколько ты сыта?\n\n1 — совсем не сыта\n5 — комфортно сыта\n10 — переела",reply_markup=scale_kb("satiety"))
    elif data.startswith("satiety:"):
        value=int(data.split(":")[1]); n=db.user(uid)["current_day"]; db.save_answer(uid,n,"satiety_after",value); context.user_data.pop("awaiting_satiety",None)
        await q.message.reply_text("🌿 Записала. Ты можешь отметить ещё один приём пищи, чтобы увидеть несколько эпизодов, или перейти к рефлексии.",reply_markup=hunger_next_kb())
    elif data=="reflection_start":
        context.user_data.pop("awaiting_hunger",None); context.user_data.pop("awaiting_satiety",None); context.user_data["awaiting_reflection"]=True; n=db.user(uid)["current_day"]; await q.message.reply_text("🌿 Теперь рефлексия\n\n"+task_info(n)[2]+"\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.")
    elif data=="reflection_skip": await finish_day(q,context,skipped=True)
    elif data=="finish": await finish_day(q,context)

async def show_day(q):
    u=db.user(q.from_user.id); n=u["current_day"]; info=day_info(n); lvl,name=level_for_day(n); status=db.day_row(q.from_user.id,n)["status"]; task,practice,reflection=task_info(n)
    text=f"🗓 <b>ДЕНЬ {n} ИЗ 49</b>\n\n<b>{info[1]}</b>\n\nУровень: {name}\n🎯 Навык: {info[3]}\n⭐ Награда: +{info[4]} XP\n\n{task}"
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=day_kb(n,status))

async def begin_day(q,n):
    row=db.day_row(q.from_user.id,n)
    if not row or row["status"]=="LOCKED": await q.message.reply_text("Этот день пока закрыт 🔒"); return
    db.start_day(q.from_user.id,n); info=day_info(n); task,practice,reflection=task_info(n)
    text=f"💡 <b>ДЕНЬ {n} — {info[1]}</b>\n\n{task}\n\n🎯 Сегодня формируем навык:\n<b>{info[3]}</b>\n\nКогда будешь готова, переходи к практике."
    buttons=[[InlineKeyboardButton("➡️ К ПРАКТИКЕ",callback_data="practice")],[InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")],[InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")]]
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def show_practice(q,context):
    uid=q.from_user.id; n=db.user(uid)["current_day"]; _,practice,_=task_info(n)
    if n == 2:
        text="📝 <b>ПРАКТИКА</b>\n\nПеред несколькими приемами пищи отметь свой голод, а после еды — сытость.\n\nНе оценивай себя. Просто фиксируй ощущения.\n\nМожно сделать несколько отметок в течение дня — после каждой пары бот предложит либо записать ещё один приём пищи, либо перейти к рефлексии."
        buttons=[[InlineKeyboardButton("🍽️ ОТМЕТИТЬ ГОЛОД",callback_data="hunger_start")],[InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")]]
    else:
        text=f"📝 <b>ПРАКТИКА</b>\n\n{practice}\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА»."
        buttons=[[InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО",callback_data="photo")],[InlineKeyboardButton("✅ Я ВЫПОЛНИЛА",callback_data="donepractice")],[InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")]]
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def start_reflection(q,context):
    context.user_data.pop("awaiting_hunger",None); context.user_data.pop("awaiting_satiety",None); context.user_data["awaiting_reflection"]=True; n=db.user(q.from_user.id)["current_day"]; await q.message.reply_text("🌿 Теперь рефлексия\n\n"+task_info(n)[2]+"\n\nНапиши ответ одним сообщением. Я сначала дам тебе короткую обратную связь, а потом мы завершим день.")

async def finish_day(q,context,skipped=False):
    context.user_data.pop("awaiting_reflection",None); n=db.user(q.from_user.id)["current_day"]; info=day_info(n)
    if skipped:
        feedback = "🌿 Рефлексию можно пропустить. Это не ошибка. Главное — ты прошла практику и продолжаешь двигаться дальше ❤️"
        reflection = "Пропущено"
    else:
        feedback = "🌿 Спасибо за честный ответ ❤️"
        reflection = ""
    if db.complete_day(q.from_user.id,n,reflection):
        db.add_xp(q.from_user.id,info[4]); badge=BADGES.get(n); badge_text=""
        if badge and db.add_badge(q.from_user.id,badge): badge_text=f"\n🏆 Новое достижение: {badge}"
        await q.message.reply_text(feedback + "\n\n" + completion_text(n,info,badge_text),parse_mode="HTML",reply_markup=main_kb())
    else: await q.message.reply_text("Этот день уже завершен ❤️",reply_markup=main_kb())

async def handle_text(update,context):
    uid=update.effective_user.id; text=update.message.text.strip()
    if context.user_data.pop("awaiting_question",False):
        u=db.user(uid); day=u["current_day"]; qid=db.add_question(uid,day,text)
        for admin in ADMIN_IDS:
            try: await context.bot.send_message(admin,f"👩‍🏫 Вопрос от {u['name']} (день {day}, ID {qid}):\n{text}")
            except Exception: pass
        await update.message.reply_text("Готово ❤️ Вопрос передан тренеру.",reply_markup=main_kb()); return
    field=context.user_data.pop("awaiting_system",None)
    if field:
        db.set_system_item(uid,field,text); await update.message.reply_text("Сохранила ❤️\n\nТвою систему можно дополнять в любой момент.",reply_markup=main_kb()); return
    if context.user_data.pop("awaiting_reflection",False):
        u=db.user(uid); n=u["current_day"]; info=day_info(n)
        if db.complete_day(uid,n,text):
            feedback = reflection_feedback(n,text)
            db.add_xp(uid,info[4]); badge=BADGES.get(n); badge_text=""
            if badge and db.add_badge(uid,badge): badge_text=f"\n🏆 Новое достижение: {badge}"
            await update.message.reply_text(feedback + "\n\n" + completion_text(n,info,badge_text),parse_mode="HTML",reply_markup=main_kb())
        else: await update.message.reply_text("Этот день уже завершен ❤️",reply_markup=main_kb())
        return
    await update.message.reply_text("Используй меню ниже ❤️",reply_markup=main_kb())

async def handle_photo(update,context):
    uid=update.effective_user.id
    if not context.user_data.pop("awaiting_photo",False): await update.message.reply_text("Фото получено ❤️ Если это фотоотчет по текущему дню, открой практику."); return
    u=db.user(uid); n=u["current_day"]; photo=update.message.photo[-1]; caption=update.message.caption or ""; db.save_photo(uid,n,photo.file_id,caption)
    for admin in ADMIN_IDS:
        try: await context.bot.forward_message(admin,update.effective_chat.id,update.message.message_id); await context.bot.send_message(admin,f"📷 Фотоотчет: {u['name']}, день {n}")
        except Exception: pass
    await update.message.reply_text("Фотоотчет сохранен ❤️\n\nЯ получила его. Сегодня ничего не нужно исправлять — нам важно увидеть реальный день таким, какой он был.\n\nКогда будешь готова, перейди к рефлексии: я помогу тебе разобрать наблюдение и дам короткую обратную связь.",reply_markup=after_photo_kb())

async def show_map(q):
    uid=q.from_user.id; lines=[]
    for level,(name,a,b) in LEVELS.items():
        done=sum(1 for n in range(a,b+1) if db.day_row(uid,n)["status"]=="COMPLETED"); icon="🟢" if done==(b-a+1) else ("🟡" if done else "🔒"); lines.append(f"{icon} L{level} — {name}: {done}/{b-a+1}")
    await q.message.reply_text("🗺 <b>МОЯ КАРТА</b>\n\n"+"\n".join(lines),parse_mode="HTML",reply_markup=back_kb())

async def show_skills(q):
    uid=q.from_user.id; done=sum(1 for n in range(1,50) if db.day_row(uid,n)["status"]=="COMPLETED"); text="🧠 <b>МОИ НАВЫКИ</b>\n\n"
    for n,title,level,skill,xp in DAYS: text += ("🟢 " if n<=done else "🔒 ")+skill+"\n"
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=back_kb())

async def show_badges(q):
    b=db.badges(q.from_user.id); await q.message.reply_text("🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"+("\n".join("• "+x for x in b) if b else "Пока нет — они будут появляться по ходу курса."),parse_mode="HTML",reply_markup=back_kb())

async def show_progress(q):
    uid=q.from_user.id; u=db.user(uid); done=sum(1 for n in range(1,50) if db.day_row(uid,n)["status"]=="COMPLETED"); percent=round(done/49*100)
    await q.message.reply_text(f"📊 <b>МОЙ ПРОГРЕСС</b>\n\n🗓 {done}/49 дней\n📈 {percent}%\n⭐ {u['xp']} XP\n🎯 Текущий день: {u['current_day']}\n🏆 Достижений: {len(db.badges(uid))}",parse_mode="HTML",reply_markup=back_kb())

async def show_system(q):
    items=db.system_items(q.from_user.id); text="❤️ <b>МОЯ СИСТЕМА</b>\n\nЭто твоя личная инструкция. Она собирается по ходу курса.\n\n"
    for key,label in SYSTEM_FIELDS: text += f"{label}: {items.get(key,'—')}\n"
    buttons=[[InlineKeyboardButton(label,callback_data=f"sys:{key}")] for key,label in SYSTEM_FIELDS]; buttons.append([InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")])
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def ask_system(q,field,context):
    label=next((label for key,label in SYSTEM_FIELDS if key==field),field); context.user_data["awaiting_system"]=field; await q.message.reply_text(f"{label}\n\nНапиши, что ты хочешь сохранить в этом разделе. Это можно будет изменить позже.")

async def show_snacks(q):
    text="🥪 <b>ПЕРЕКУСЫ НА СКОРУЮ РУКУ</b>\n\nЕсли нет времени готовить, не успела взять еду или нужно съесть что-то быстро:\n\n"+"\n".join(f"{icon} <b>{name}</b>\n{desc}" for icon,name,desc in SNACKS)
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=back_kb())

async def reminders(context):
    now=datetime.now(TZ); date_key=now.date().isoformat()
    if now.hour != REMINDER_HOUR: return
    con=db.connect(); rows=con.execute("SELECT * FROM users WHERE current_day<=49").fetchall(); con.close()
    for u in rows:
        if not db.claim_reminder(u["tg_id"],date_key): continue
        try: await context.bot.send_message(u["tg_id"],f"🌿 Добрый день, {u['name']}!\nТвой День {u['current_day']} из 49 ждёт тебя.",reply_markup=main_kb())
        except Exception: pass

def main():
    if not TOKEN: raise RuntimeError("Не задан BOT_TOKEN")
    db.init_db(); app=Application.builder().token(TOKEN).build()
    conv=ConversationHandler(entry_points=[CommandHandler("start",start)],states={ASK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,got_name)]},fallbacks=[])
    app.add_handler(conv); app.add_handler(CallbackQueryHandler(menu)); app.add_handler(MessageHandler(filters.PHOTO,handle_photo)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    if app.job_queue: app.job_queue.run_repeating(reminders,interval=60,first=5)
    app.run_polling()

if __name__ == "__main__": main()
