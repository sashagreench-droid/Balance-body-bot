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

def back_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")]])

def day_kb(n, status):
    if status == "AVAILABLE": label="▶️ НАЧАТЬ"
    elif status == "IN_PROGRESS": label="▶️ ПРОДОЛЖИТЬ"
    else: label="↩️ ОТКРЫТЬ ДЕНЬ"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"startday:{n}")],[InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.user(update.effective_user.id)
    if u:
        await update.message.reply_text(f"С возвращением, {u['name']} ❤️\n\nДень {u['current_day']} из 49 уже ждёт тебя.", reply_markup=main_kb())
        return ConversationHandler.END
    await update.message.reply_text("Привет! ❤️\n\nЭто курс «49 дней → самостоятельность».\n\nКак тебя зовут?")
    return ASK_NAME

async def got_name(update, context):
    name=update.message.text.strip()[:80]; db.ensure_user(update.effective_user.id,name)
    await update.message.reply_text(f"{name}, начинаем ❤️\n\nТвоя задача — не быть идеальной. Твоя задача — постепенно научиться принимать решения самостоятельно.\n\nПервый шаг — просто наблюдать.",reply_markup=main_kb())
    return ConversationHandler.END

async def menu(update, context):
    q=update.callback_query; await q.answer(); data=q.data
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
    elif data=="donepractice":
        context.user_data["awaiting_reflection"]=True
        n=db.user(q.from_user.id)["current_day"]; await q.message.reply_text("Теперь рефлексия 🌿\n\n"+task_info(n)[2],reply_markup=back_kb())
    elif data=="photo": context.user_data["awaiting_photo"]=True; await q.message.reply_text("Отправь фото отчёта сюда. Если фото не требуется для твоего дня — можешь просто перейти к практике.")
    elif data=="finish": await finish_day(q,context)

async def show_day(q):
    u=db.user(q.from_user.id); n=u["current_day"]; info=day_info(n); lvl,name=level_for_day(n); status=db.day_row(q.from_user.id,n)["status"]
    task,practice,reflection=task_info(n)
    text=(f"🗓 <b>ДЕНЬ {n} ИЗ 49</b>\n\n<b>{info[1]}</b>\n\nУровень: {name}\n🎯 Навык: {info[3]}\n⭐ Награда: +{info[4]} XP\n\n{task}")
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=day_kb(n,status))

async def begin_day(q,n):
    row=db.day_row(q.from_user.id,n)
    if not row or row["status"]=="LOCKED": await q.message.reply_text("Этот день пока закрыт 🔒"); return
    db.start_day(q.from_user.id,n); info=day_info(n); task,practice,reflection=task_info(n)
    text=(f"💡 <b>ДЕНЬ {n} — {info[1]}</b>\n\n{task}\n\n🎯 Сегодня формируем навык:\n<b>{info[3]}</b>\n\nКогда будешь готова, переходи к практике.")
    buttons=[[InlineKeyboardButton("➡️ К ПРАКТИКЕ",callback_data="practice")],[InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")],[InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")]]
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def show_practice(q,context):
    n=db.user(q.from_user.id)["current_day"]; info=day_info(n); task,practice,reflection=task_info(n)
    buttons=[[InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО",callback_data="photo")],[InlineKeyboardButton("✅ Я ВЫПОЛНИЛА",callback_data="donepractice")],[InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")]]
    await q.message.reply_text(f"📝 <b>ПРАКТИКА</b>\n\n{practice}\n\nКогда закончишь — нажми «Я ВЫПОЛНИЛА».",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def finish_day(q,context):
    context.user_data["awaiting_reflection"]=True; n=db.user(q.from_user.id)["current_day"]
    await q.message.reply_text("Последний шаг 🌿\n\n"+task_info(n)[2])

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
        u=db.user(uid); n=u["current_day"]
        if db.complete_day(uid,n,text):
            info=day_info(n); db.add_xp(uid,info[4]); badge=BADGES.get(n); badge_text=""
            if badge and db.add_badge(uid,badge): badge_text=f"\n🏆 Новое достижение: {badge}"
            if n==49:
                next_text="\n\n🏆 Финал завершен. Ты можешь сама."
            else: next_text=f"\n\n➡️ Открыт День {n+1}."
            await update.message.reply_text(f"🎉 <b>День {n} завершен!</b>\n\n+{info[4]} XP{badge_text}{next_text}",parse_mode="HTML",reply_markup=main_kb())
        else: await update.message.reply_text("Этот день уже завершен ❤️",reply_markup=main_kb())
        return
    await update.message.reply_text("Используй меню ниже ❤️",reply_markup=main_kb())

async def handle_photo(update,context):
    uid=update.effective_user.id
    if not context.user_data.pop("awaiting_photo",False):
        await update.message.reply_text("Фото получено ❤️ Если это фотоотчет по текущему дню, открой практику."); return
    u=db.user(uid); n=u["current_day"]; photo=update.message.photo[-1]; caption=update.message.caption or ""
    db.save_photo(uid,n,photo.file_id,caption)
    for admin in ADMIN_IDS:
        try:
            await context.bot.forward_message(admin,update.effective_chat.id,update.message.message_id)
            await context.bot.send_message(admin,f"📷 Фотоотчет: {u['name']}, день {n}")
        except Exception: pass
    await update.message.reply_text("Фотоотчет сохранен ❤️\nТеперь возвращайся к практике и нажми «Я ВЫПОЛНИЛА».",reply_markup=main_kb())

async def show_map(q):
    uid=q.from_user.id; lines=[]
    for level,(name,a,b) in LEVELS.items():
        done=sum(1 for n in range(a,b+1) if db.day_row(uid,n)["status"]=="COMPLETED")
        icon="🟢" if done==(b-a+1) else ("🟡" if done else "🔒"); lines.append(f"{icon} L{level} — {name}: {done}/{b-a+1}")
    await q.message.reply_text("🗺 <b>МОЯ КАРТА</b>\n\n"+"\n".join(lines),parse_mode="HTML",reply_markup=back_kb())

async def show_skills(q):
    uid=q.from_user.id; done=sum(1 for n in range(1,50) if db.day_row(uid,n)["status"]=="COMPLETED")
    text="🧠 <b>МОИ НАВЫКИ</b>\n\n"
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
    buttons=[]
    for key,label in SYSTEM_FIELDS: buttons.append([InlineKeyboardButton(label,callback_data=f"sys:{key}")])
    buttons.append([InlineKeyboardButton("⬅️ В МЕНЮ",callback_data="home")])
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def ask_system(q,field,context):
    label=next((label for key,label in SYSTEM_FIELDS if key==field),field); context.user_data["awaiting_system"]=field
    await q.message.reply_text(f"{label}\n\nНапиши, что ты хочешь сохранить в этом разделе. Это можно будет изменить позже.")

async def show_snacks(q):
    text="🥪 <b>ПЕРЕКУСЫ НА СКОРУЮ РУКУ</b>\n\nЕсли нет времени готовить, не успела взять еду или нужно съесть что-то быстро:\n\n"
    for icon,name,desc in SNACKS: text += f"{icon} <b>{name}</b>\n{desc}\n\n"
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=back_kb())

async def reminders(context):
    now=datetime.now(TZ)
    if now.hour != REMINDER_HOUR: return
    con=db.connect(); rows=con.execute("SELECT * FROM users WHERE current_day<=49").fetchall(); con.close()
    for u in rows:
        try: await context.bot.send_message(u["tg_id"],f"🌿 Добрый день, {u['name']}!\nТвой День {u['current_day']} из 49 ждёт тебя.",reply_markup=main_kb())
        except Exception: pass

def main():
    if not TOKEN: raise RuntimeError("Не задан BOT_TOKEN в .env")
    db.init_db(); app=Application.builder().token(TOKEN).build()
    conv=ConversationHandler(entry_points=[CommandHandler("start",start)],states={ASK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,got_name)]},fallbacks=[CommandHandler("start",start)])
    app.add_handler(conv); app.add_handler(CallbackQueryHandler(menu)); app.add_handler(MessageHandler(filters.PHOTO,handle_photo)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    if app.job_queue: app.job_queue.run_repeating(reminders,interval=60,first=10)
    print("Bot started."); app.run_polling()

if __name__=="__main__": main()
