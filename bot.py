import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

import db
from content import DAYS, SNACKS, LEVELS, BADGES

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}
TZ = ZoneInfo(os.getenv("BOT_TIMEZONE","UTC"))
REMINDER_HOUR = int(os.getenv("DAILY_REMINDER_HOUR","9"))

ASK_NAME, REFLECTION, QUESTION = range(3)

def day_info(n):
    return DAYS[n-1]

def level_for_day(n):
    for level,(name,a,b) in LEVELS.items():
        if a <= n <= b:
            return level,name

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ ПРОДОЛЖИТЬ", callback_data="continue")],
        [InlineKeyboardButton("🗺 МОЯ КАРТА", callback_data="map"),
         InlineKeyboardButton("🧠 МОИ НАВЫКИ", callback_data="skills")],
        [InlineKeyboardButton("🏆 ДОСТИЖЕНИЯ", callback_data="badges"),
         InlineKeyboardButton("📊 МОЙ ПРОГРЕСС", callback_data="progress")],
        [InlineKeyboardButton("❤️ МОЯ СИСТЕМА", callback_data="system"),
         InlineKeyboardButton("🥪 ПЕРЕКУСЫ", callback_data="snacks")],
        [InlineKeyboardButton("👩‍🏫 ЗАДАТЬ ТРЕНЕРУ", callback_data="trainer")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.user(update.effective_user.id)
    if u:
        await update.message.reply_text("С возвращением ❤️", reply_markup=main_kb())
        return ConversationHandler.END
    await update.message.reply_text("Привет! ❤️\n\nЭто курс «49 дней → самостоятельность».\nКак тебя зовут?")
    return ASK_NAME

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()[:80]
    db.ensure_user(update.effective_user.id, name)
    await update.message.reply_text(
        f"{name}, начинаем.\n\nТвоя задача — не быть идеальной. Твоя задача — постепенно научиться принимать решения самостоятельно.",
        reply_markup=main_kb()
    )
    return ConversationHandler.END

async def menu(update, context):
    q = update.callback_query
    await q.answer()
    data=q.data
    if data=="continue":
        await show_day(q, context)
    elif data=="map":
        await show_map(q)
    elif data=="skills":
        await show_skills(q)
    elif data=="badges":
        await show_badges(q)
    elif data=="progress":
        await show_progress(q)
    elif data=="system":
        await show_system(q)
    elif data=="snacks":
        await show_snacks(q)
    elif data=="trainer":
        context.user_data["awaiting_question"]=True
        await q.message.reply_text("Напиши вопрос одним сообщением — я передам его тренеру.")
    elif data.startswith("startday:"):
        n=int(data.split(":")[1]); await begin_day(q,n)
    elif data=="practice":
        await q.message.reply_text("Выполни практику из задания дня и нажми «ГОТОВО».",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📷 ОТПРАВИТЬ ФОТО",callback_data="photo")],
                                                                       [InlineKeyboardButton("✅ ГОТОВО",callback_data="donepractice")]]))
    elif data=="donepractice":
        await q.message.reply_text("Отлично. Напиши коротко: что заметила/поняла сегодня?")
        context.user_data["awaiting_reflection"]=True
    elif data=="photo":
        context.user_data["awaiting_photo"]=True
        await q.message.reply_text("Отправь фото отчёта сюда.")
    elif data=="finish":
        await finish_day(q, context)

async def show_day(q, context):
    u=db.user(q.from_user.id); n=u["current_day"]; info=day_info(n); lvl,name=level_for_day(n)
    status=db.day_row(q.from_user.id,n)["status"]
    text=(f"🗓 ДЕНЬ {n} ИЗ 49\n\n<b>{info[1]}</b>\n\n"
          f"Уровень: {name}\n🎯 Навык: {info[3]}\n⭐ Награда: +{info[4]} XP\n\n"
          "Сегодня не нужно делать всё идеально. Сначала разберись, потом действуй.")
    buttons=[]
    if status=="AVAILABLE": buttons.append([InlineKeyboardButton("▶️ НАЧАТЬ",callback_data=f"startday:{n}")])
    elif status=="IN_PROGRESS": buttons.append([InlineKeyboardButton("▶️ ПРОДОЛЖИТЬ",callback_data=f"startday:{n}")])
    else: buttons.append([InlineKeyboardButton("↩️ ОТКРЫТЬ ДЕНЬ",callback_data=f"startday:{n}")])
    await q.message.reply_text(text,parse_mode="HTML",reply_markup=InlineKeyboardMarkup(buttons))

async def begin_day(q,n):
    row=db.day_row(q.from_user.id,n)
    if row["status"]=="LOCKED":
        await q.message.reply_text("Этот день пока закрыт 🔒")
        return
    db.start_day(q.from_user.id,n)
    info=day_info(n)
    text=(f"💡 <b>{info[1]}</b>\n\n"
          f"Сегодня формируем навык:\n<b>{info[3]}</b>\n\n"
          "Сначала коротко разберись с темой, затем выполни действие в реальной жизни.\n\n"
          "Практика: выполни задание дня из контентной базы курса.")
    await q.message.reply_text(text,parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ К ПРАКТИКЕ",callback_data="practice")],
                                            [InlineKeyboardButton("🤔 МНЕ СЛОЖНО",callback_data="trainer")]]))

async def finish_day(q,context):
    u=db.user(q.from_user.id); n=u["current_day"]
    context.user_data["awaiting_reflection"]=True
    await q.message.reply_text("Последний шаг 🌿\n\nЧто ты сегодня заметила, поняла или попробовала?")

async def handle_text(update,context):
    uid=update.effective_user.id
    text=update.message.text.strip()
    if context.user_data.pop("awaiting_question",False):
        u=db.user(uid); day=u["current_day"]; qid=db.add_question(uid,day,text)
        for admin in ADMIN_IDS:
            try:
                await context.bot.send_message(admin,f"👩‍🏫 Вопрос от {u['name']} (день {day}, ID {qid}):\n{text}")
            except Exception: pass
        await update.message.reply_text("Готово ❤️ Вопрос передан тренеру.",reply_markup=main_kb())
        return
    if context.user_data.pop("awaiting_reflection",False):
        u=db.user(uid); n=u["current_day"]
        if db.complete_day(uid,n,text):
            info=day_info(n); db.add_xp(uid,info[4])
            badge=BADGES.get(n)
            badge_text=""
            if badge and db.add_badge(uid,badge): badge_text=f"\n🏆 Новое достижение: {badge}"
            next_text = "Финал завершен — ты можешь сама 🏆" if n==49 else f"Следующий день: {n+1}"
            await update.message.reply_text(
                f"🎉 <b>День {n} завершен!</b>\n\n+{info[4]} XP{badge_text}\n\n{next_text}",
                parse_mode="HTML", reply_markup=main_kb())
        else:
            await update.message.reply_text("Этот день уже завершен ❤️",reply_markup=main_kb())
        return
    await update.message.reply_text("Используй меню ниже.",reply_markup=main_kb())

async def handle_photo(update,context):
    uid=update.effective_user.id
    if not context.user_data.pop("awaiting_photo",False):
        await update.message.reply_text("Фото получено. Если это отчет по текущему дню, сначала открой практику.")
        return
    u=db.user(uid); n=u["current_day"]; photo=update.message.photo[-1]
    caption=update.message.caption or ""
    db.save_photo(uid,n,photo.file_id,caption)
    for admin in ADMIN_IDS:
        try:
            await context.bot.forward_message(admin,update.effective_chat.id,update.message.message_id)
            await context.bot.send_message(admin,f"📷 Фотоотчет: {u['name']}, день {n}")
        except Exception: pass
    await update.message.reply_text("Фотоотчет сохранен ❤️\nТеперь нажми «ГОТОВО» в задании.")

async def show_map(q):
    uid=q.from_user.id; u=db.user(uid)
    lines=[]
    for level,(name,a,b) in LEVELS.items():
        done=sum(1 for n in range(a,b+1) if db.day_row(uid,n)["status"]=="COMPLETED")
        icon="🟢" if done==(b-a+1) else ("🟡" if done else "🔒")
        lines.append(f"{icon} L{level} — {name}: {done}/{b-a+1}")
    await q.message.reply_text("🗺 <b>МОЯ КАРТА</b>\n\n"+"\n".join(lines),parse_mode="HTML")

async def show_skills(q):
    uid=q.from_user.id; u=db.user(uid)
    done=max(0,u["current_day"]-1)
    text="🧠 <b>МОИ НАВЫКИ</b>\n\n"
    for n,title,level,skill,xp in DAYS:
        status="🟢" if n<=done else "🔒"
        text += f"{status} {skill}\n"
    await q.message.reply_text(text,parse_mode="HTML")

async def show_badges(q):
    b=db.badges(q.from_user.id)
    await q.message.reply_text("🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"+("\n".join("• "+x for x in b) if b else "Пока нет — они будут появляться по ходу курса."),parse_mode="HTML")

async def show_progress(q):
    u=db.user(q.from_user.id)
    done=sum(1 for n in range(1,50) if db.day_row(q.from_user.id,n)["status"]=="COMPLETED")
    await q.message.reply_text(
        f"📊 <b>МОЙ ПРОГРЕСС</b>\n\n🗓 {done}/49 дней\n⭐ {u['xp']} XP\n🎯 Текущий день: {u['current_day']}\n🏆 Достижений: {len(db.badges(q.from_user.id))}",
        parse_mode="HTML")

async def show_system(q):
    await q.message.reply_text(
        "❤️ <b>МОЯ СИСТЕМА</b>\n\n"
        "Здесь постепенно собираются твои личные правила: белок, быстрые приемы пищи, рестораны, поездки, сладкое, движение, стресс и возвращение после неидеального дня.\n\n"
        "В этой MVP-версии раздел подготовлен как точка входа; полноценный редактор личной системы — следующий этап.",
        parse_mode="HTML")

async def show_snacks(q):
    text="🥪 <b>ПЕРЕКУСЫ НА СКОРУЮ РУКУ</b>\n\nЕсли нет времени готовить, не успела взять еду или нужно съесть что-то быстро:\n\n"
    for icon,name,desc in SNACKS:
        text += f"{icon} <b>{name}</b>\n{desc}\n\n"
    await q.message.reply_text(text,parse_mode="HTML")

async def reminders(context):
    now=datetime.now(TZ)
    if now.hour != REMINDER_HOUR:
        return
    con=db.connect()
    rows=con.execute("SELECT * FROM users WHERE current_day < 50").fetchall()
    con.close()
    for u in rows:
        try:
            await context.bot.send_message(u["tg_id"],f"🌿 Добрый день, {u['name']}!\nТвой День {u['current_day']} из 49 ждет тебя.",reply_markup=main_kb())
        except Exception: pass

def main():
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в .env")
    db.init_db()
    app=Application.builder().token(TOKEN).build()
    conv=ConversationHandler(
        entry_points=[CommandHandler("start",start)],
        states={ASK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,got_name)]},
        fallbacks=[CommandHandler("start",start)]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(menu))
    app.add_handler(MessageHandler(filters.PHOTO,handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    if app.job_queue:
        app.job_queue.run_repeating(reminders,interval=60,first=10)
    print("Bot started.")
    app.run_polling()

if __name__=="__main__":
    main()
