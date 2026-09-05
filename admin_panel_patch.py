import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import bot
import db

ADMIN_IDS = set(bot.ADMIN_IDS)


def _ensure_admin_schema():
    con = db.connect()
    cols = {r["name"] for r in con.execute("PRAGMA table_info(questions)").fetchall()}
    if "answered_at" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN answered_at TEXT")
    if "answer_text" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN answer_text TEXT")
    con.commit()
    con.close()


def _is_admin(uid):
    return int(uid) in ADMIN_IDS


def _admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 НОВЫЕ ВОПРОСЫ", callback_data="admin:questions")],
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin:stats")],
    ])


def _questions_kb(rows):
    buttons = []
    for row in rows[:20]:
        label = f"#{row['id']} · {row['name'] or 'Без имени'} · День {row['day']}"
        buttons.append([InlineKeyboardButton(label[:60], callback_data=f"admin:q:{row['id']}")])
    buttons.append([InlineKeyboardButton("⬅️ В ПАНЕЛЬ", callback_data="admin:home")])
    return InlineKeyboardMarkup(buttons)


async def _admin_start(update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    _ensure_admin_schema()
    con = db.connect()
    total = con.execute("SELECT COUNT(*) AS c FROM questions").fetchone()["c"]
    pending = con.execute("SELECT COUNT(*) AS c FROM questions WHERE answered_at IS NULL").fetchone()["c"]
    users = con.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    con.close()
    await update.message.reply_text(
        "👩‍💼 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"📩 Всего вопросов: {total}\n"
        f"🔔 Без ответа: {pending}",
        parse_mode="HTML",
        reply_markup=_admin_kb(),
    )
    raise ApplicationHandlerStop


async def _admin_callback(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not _is_admin(q.from_user.id):
        return
    await q.answer()
    _ensure_admin_schema()
    data = q.data

    if data == "admin:home":
        await q.message.reply_text("👩‍💼 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>", parse_mode="HTML", reply_markup=_admin_kb())
        raise ApplicationHandlerStop

    if data == "admin:questions":
        con = db.connect()
        rows = con.execute(
            "SELECT q.id,q.tg_id,q.day,q.text,q.created_at,u.name "
            "FROM questions q LEFT JOIN users u ON u.tg_id=q.tg_id "
            "WHERE q.answered_at IS NULL ORDER BY q.id DESC LIMIT 20"
        ).fetchall()
        con.close()
        if not rows:
            await q.message.reply_text("📩 <b>Новых вопросов нет.</b>\n\nВсе обращения обработаны.", parse_mode="HTML", reply_markup=_admin_kb())
        else:
            await q.message.reply_text(
                f"📩 <b>Новые вопросы: {len(rows)}</b>\n\nВыбери вопрос:",
                parse_mode="HTML",
                reply_markup=_questions_kb(rows),
            )
        raise ApplicationHandlerStop

    if data == "admin:stats":
        con = db.connect()
        users = con.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        completed = con.execute("SELECT COUNT(*) AS c FROM users WHERE current_day >= 50").fetchone()["c"]
        pending = con.execute("SELECT COUNT(*) AS c FROM questions WHERE answered_at IS NULL").fetchone()["c"]
        answered = con.execute("SELECT COUNT(*) AS c FROM questions WHERE answered_at IS NOT NULL").fetchone()["c"]
        con.close()
        await q.message.reply_text(
            "📊 <b>СТАТИСТИКА</b>\n\n"
            f"👥 Пользователей: {users}\n"
            f"🏆 Завершили курс: {completed}\n"
            f"📩 Вопросов всего: {pending + answered}\n"
            f"⏳ Ждут ответа: {pending}\n"
            f"✅ Отвечено: {answered}",
            parse_mode="HTML",
            reply_markup=_admin_kb(),
        )
        raise ApplicationHandlerStop

    if data.startswith("admin:q:"):
        qid = int(data.split(":", 2)[2])
        con = db.connect()
        row = con.execute(
            "SELECT q.id,q.tg_id,q.day,q.text,q.created_at,q.answered_at,u.name,u.current_day "
            "FROM questions q LEFT JOIN users u ON u.tg_id=q.tg_id WHERE q.id=?",
            (qid,),
        ).fetchone()
        con.close()
        if not row:
            await q.message.reply_text("Вопрос не найден.", reply_markup=_admin_kb())
            raise ApplicationHandlerStop
        if row["answered_at"]:
            await q.message.reply_text("Этот вопрос уже обработан.", reply_markup=_admin_kb())
            raise ApplicationHandlerStop
        context.user_data["admin_reply_question_id"] = qid
        await q.message.reply_text(
            "📩 <b>ВОПРОС ТРЕНЕРУ</b>\n\n"
            f"👤 {row['name'] or 'Без имени'}\n"
            f"🗓 День: {row['day']}\n"
            f"🆔 Пользователь: <code>{row['tg_id']}</code>\n\n"
            f"💬 {row['text']}\n\n"
            "Напиши ответ следующим сообщением. Он уйдёт пользователю.",
            parse_mode="HTML",
        )
        raise ApplicationHandlerStop


async def _user_question(update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    if _is_admin(update.effective_user.id):
        return
    if not context.user_data.get("awaiting_question"):
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    uid = update.effective_user.id
    user = db.user(uid)
    day = int(user["current_day"] or 1) if user else 1
    qid = db.add_question(uid, day, text)
    context.user_data.pop("awaiting_question", None)

    if not ADMIN_IDS:
        await update.message.reply_text(
            "Я сохранила твой вопрос ❤️\n\n"
            "Сейчас тренер ещё не подключён к уведомлениям. Вопрос не потеряется.",
            reply_markup=bot.back_kb(),
        )
        raise ApplicationHandlerStop

    admin_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ ОТВЕТИТЬ", callback_data=f"admin:q:{qid}")]
    ])
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "📩 <b>НОВЫЙ ВОПРОС ТРЕНЕРУ</b>\n\n"
                    f"👤 {user['name'] if user else 'Без имени'}\n"
                    f"🗓 День: {day}\n"
                    f"🆔 Пользователь: <code>{uid}</code>\n\n"
                    f"💬 {text}"
                ),
                parse_mode="HTML",
                reply_markup=admin_kb,
            )
        except Exception:
            pass

    await update.message.reply_text(
        "Вопрос отправлен тренеру ❤️\n\n"
        "Как только тебе ответят, сообщение придёт сюда.",
        reply_markup=bot.back_kb(),
    )
    raise ApplicationHandlerStop


async def _admin_answer(update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user or not _is_admin(update.effective_user.id):
        return
    qid = context.user_data.get("admin_reply_question_id")
    if not qid:
        return
    text = (update.message.text or "").strip()
    if not text:
        return

    con = db.connect()
    row = con.execute(
        "SELECT q.id,q.tg_id,q.day,q.text,u.name FROM questions q LEFT JOIN users u ON u.tg_id=q.tg_id WHERE q.id=? AND q.answered_at IS NULL",
        (qid,),
    ).fetchone()
    if not row:
        con.close()
        context.user_data.pop("admin_reply_question_id", None)
        await update.message.reply_text("Этот вопрос уже обработан или не найден.", reply_markup=_admin_kb())
        raise ApplicationHandlerStop

    con.execute("UPDATE questions SET answered_at=?, answer_text=? WHERE id=?", (datetime.utcnow().isoformat(), text, qid))
    con.commit()
    con.close()
    context.user_data.pop("admin_reply_question_id", None)

    try:
        await context.bot.send_message(
            chat_id=row["tg_id"],
            text=f"👩‍🏫 <b>Ответ тренера</b>\n\n{text}",
            parse_mode="HTML",
            reply_markup=bot.main_kb(),
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю.", reply_markup=_admin_kb())
    except Exception:
        await update.message.reply_text("⚠️ Ответ сохранён, но отправить его пользователю не удалось.", reply_markup=_admin_kb())
    raise ApplicationHandlerStop


def install_admin_handlers(application):
    _ensure_admin_schema()
    application.add_handler(CommandHandler("admin", _admin_start), group=-3)
    application.add_handler(CallbackQueryHandler(_admin_callback, pattern=r"^admin:"), group=-3)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _admin_answer), group=-3)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _user_question), group=-2)


_real_run_polling = Application.run_polling


def _run_polling(self, *args, **kwargs):
    install_admin_handlers(self)
    return _real_run_polling(self, *args, **kwargs)


Application.run_polling = _run_polling
