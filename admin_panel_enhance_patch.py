from html import escape

import bot
import db
import admin_panel_patch as admin
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationHandlerStop


def _admin_kb_enhanced():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 НОВЫЕ ВОПРОСЫ", callback_data="admin:questions")],
        [InlineKeyboardButton("📚 ВСЕ ВОПРОСЫ", callback_data="admin:all_questions")],
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin:stats")],
    ])


def _questions_kb_enhanced(rows, prefix="admin:q:"):
    buttons = []
    for row in rows[:20]:
        name = (row["name"] or "Без имени")[:22]
        label = f"#{row['id']} · {name} · День {row['day']}"
        buttons.append([InlineKeyboardButton(label[:60], callback_data=f"admin:q:{row['id']}")])
    buttons.append([InlineKeyboardButton("⬅️ В ПАНЕЛЬ", callback_data="admin:home")])
    return InlineKeyboardMarkup(buttons)


async def _admin_callback_enhanced(update, context):
    q = update.callback_query
    if not admin._is_admin(q.from_user.id):
        return
    await q.answer()
    admin._ensure_admin_schema()
    data = q.data

    if data == "admin:home":
        await q.message.reply_text("👩‍💼 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>", parse_mode="HTML", reply_markup=_admin_kb_enhanced())
        raise ApplicationHandlerStop

    if data in ("admin:questions", "admin:all_questions"):
        con = db.connect()
        where = "" if data == "admin:all_questions" else "WHERE q.answered_at IS NULL"
        rows = con.execute(
            "SELECT q.id,q.tg_id,q.day,q.text,q.created_at,q.answered_at,u.name "
            "FROM questions q LEFT JOIN users u ON u.tg_id=q.tg_id "
            f"{where} ORDER BY q.id DESC LIMIT 20"
        ).fetchall()
        con.close()
        title = "Все вопросы" if data == "admin:all_questions" else "Новые вопросы"
        if not rows:
            text = "📩 <b>Новых вопросов нет.</b>" if data == "admin:questions" else "📚 <b>Вопросов пока нет.</b>"
            await q.message.reply_text(text, parse_mode="HTML", reply_markup=_admin_kb_enhanced())
        else:
            await q.message.reply_text(
                f"📩 <b>{title}: {len(rows)}</b>\n\nВыбери обращение:",
                parse_mode="HTML", reply_markup=_questions_kb_enhanced(rows)
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
            parse_mode="HTML", reply_markup=_admin_kb_enhanced()
        )
        raise ApplicationHandlerStop

    if data.startswith("admin:q:"):
        qid = int(data.split(":", 2)[2])
        con = db.connect()
        row = con.execute(
            "SELECT q.id,q.tg_id,q.day,q.text,q.created_at,q.answered_at,u.name,u.current_day "
            "FROM questions q LEFT JOIN users u ON u.tg_id=q.tg_id WHERE q.id=?",
            (qid,)
        ).fetchone()
        con.close()
        if not row:
            await q.message.reply_text("Вопрос не найден.", reply_markup=_admin_kb_enhanced())
            raise ApplicationHandlerStop
        if row["answered_at"]:
            await q.message.reply_text("Этот вопрос уже обработан.", reply_markup=_admin_kb_enhanced())
            raise ApplicationHandlerStop
        context.user_data["admin_reply_question_id"] = qid
        name = escape(row["name"] or "Без имени")
        question = escape(row["text"] or "")
        await q.message.reply_text(
            "📩 <b>ВОПРОС ТРЕНЕРУ</b>\n\n"
            f"👤 <b>{name}</b>\n"
            f"📍 Сейчас на дне: <b>{row['current_day'] or row['day']}</b>\n"
            f"📝 Вопрос из дня: <b>{row['day']}</b>\n"
            f"🆔 Пользователь: <code>{row['tg_id']}</code>\n\n"
            f"💬 {question}\n\n"
            "✍️ Напиши ответ следующим сообщением — он сразу уйдёт пользователю.",
            parse_mode="HTML"
        )
        raise ApplicationHandlerStop


# Replace the callback before admin_panel_patch installs its handler.
admin._admin_callback = _admin_callback_enhanced
admin._admin_kb = _admin_kb_enhanced
admin._questions_kb = _questions_kb_enhanced
