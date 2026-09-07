"""BALANCE BODY: payments are confirmed manually, without channel/invite links."""

import bot
import db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationHandlerStop


async def approve_callback(update, context):
    q = update.callback_query
    if q.from_user.id not in set(bot.ADMIN_IDS):
        await q.answer("Нет доступа", show_alert=True)
        return

    await q.answer()
    _, _, uid_text, part_text = q.data.split(":")
    uid, part = int(uid_text), int(part_text)

    # Reuse the payment table created by payment_patch.
    con = db.connect()
    row = con.execute(
        "SELECT * FROM payments WHERE tg_id=? AND part=?",
        (uid, part),
    ).fetchone()
    if not row:
        con.close()
        await q.message.reply_text("Платёж не найден.")
        raise ApplicationHandlerStop

    now = __import__("datetime").datetime.utcnow().isoformat()
    con.execute(
        "UPDATE payments SET status='approved', approved_at=? WHERE tg_id=? AND part=?",
        (now, uid, part),
    )
    con.commit()
    con.close()

    if part == 1:
        text = (
            "✅ <b>Оплата подтверждена!</b> ❤️\n\n"
            "Первая часть курса оплачена.\n"
            "Доступ к курсу открыт.\n\n"
            "Второй платеж — <b>2 495 ₽</b> — станет доступен через 24 дня."
        )
    else:
        text = (
            "✅ <b>Оплата подтверждена!</b> ❤️\n\n"
            "Вторая часть курса оплачена.\n"
            "BALANCE BODY полностью оплачен 🎉\n\n"
            "Теперь тебе открыт весь курс из 50 дней."
        )

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=text,
            parse_mode="HTML",
            reply_markup=bot.main_kb(),
        )
    except Exception:
        pass

    await q.message.reply_text(
        f"✅ Платёж {part}/2 пользователя {uid} подтверждён.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В АДМИН-ПАНЕЛЬ", callback_data="admin:home")]
        ]),
    )
    raise ApplicationHandlerStop


# payment_patch installs its own callback. Replace it after that module is loaded.
if hasattr(bot, "_payment_approve_callback"):
    bot._payment_approve_callback = approve_callback

# payment_patch routes through its module-level callback, so replace the exported name too.
try:
    import payment_patch
    payment_patch._approve_callback = approve_callback
except Exception:
    pass
