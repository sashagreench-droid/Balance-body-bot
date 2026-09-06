from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationHandlerStop, CallbackQueryHandler

import bot
import db
import payment_patch


# BALANCE BODY: receipt tracking for manual transfer payments.
# The bot does not issue the tax receipt itself; this flag lets the admin mark
# that the receipt was issued in the tax app after the transfer was confirmed.


def _ensure_receipt_schema():
    payment_patch._ensure_payments_table()
    con = db.connect()
    cols = {r["name"] for r in con.execute("PRAGMA table_info(payments)").fetchall()}
    if "receipt_issued_at" not in cols:
        con.execute("ALTER TABLE payments ADD COLUMN receipt_issued_at TEXT")
    con.commit()
    con.close()


async def _receipt_callback(update, context):
    q = update.callback_query
    if q.from_user.id not in set(bot.ADMIN_IDS):
        await q.answer("Нет доступа", show_alert=True)
        return

    await q.answer("Чек отмечен как выдан 🧾")
    try:
        _, _, uid_text, part_text = q.data.split(":")
        uid, part = int(uid_text), int(part_text)
    except Exception:
        await q.message.reply_text("Не удалось определить платеж.")
        raise ApplicationHandlerStop

    _ensure_receipt_schema()
    now = datetime.utcnow().isoformat()
    con = db.connect()
    row = con.execute("SELECT * FROM payments WHERE tg_id=? AND part=?", (uid, part)).fetchone()
    if not row:
        con.close()
        await q.message.reply_text("Платёж не найден.")
        raise ApplicationHandlerStop

    con.execute(
        "UPDATE payments SET receipt_issued_at=? WHERE tg_id=? AND part=?",
        (now, uid, part),
    )
    con.commit()
    con.close()

    await q.message.reply_text(
        f"🧾 <b>Чек отмечен как выдан</b>\n\n"
        f"Пользователь: <code>{uid}</code>\n"
        f"Платёж: <b>{part}/2</b>\n"
        f"Дата: <b>{datetime.utcnow().strftime('%d.%m.%Y %H:%M')}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В АДМИН-ПАНЕЛЬ", callback_data="admin:home")]
        ]),
    )
    raise ApplicationHandlerStop


# Wrap the payment approval function so that after the payment is approved,
# the admin also gets a clear one-tap receipt tracking action.
_original_approve = payment_patch._approve_callback


async def _approve_with_receipt(update, context):
    try:
        return await _original_approve(update, context)
    except ApplicationHandlerStop:
        q = update.callback_query
        try:
            _, _, uid_text, part_text = q.data.split(":")
            uid, part = int(uid_text), int(part_text)
            await q.message.reply_text(
                "🧾 <b>Не забудь выдать чек</b>\n\n"
                f"Пользователь: <code>{uid}</code>\n"
                f"Платёж: <b>{part}/2</b> — <b>2 495 ₽</b>\n\n"
                "После выдачи чека в «Мой налог» нажми кнопку ниже, чтобы сохранить отметку в боте.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🧾 ЧЕК ВЫДАН", callback_data=f"payment:receipt:{uid}:{part}")]
                ]),
            )
        except Exception:
            pass
        raise


payment_patch._approve_callback = _approve_with_receipt


# Register the receipt handler before the payment patch's polling wrapper starts.
_previous_run_polling = bot.Application.run_polling


def _install_receipt_handlers(self, *args, **kwargs):
    _ensure_receipt_schema()
    self.add_handler(
        CallbackQueryHandler(_receipt_callback, pattern=r"^payment:receipt:\d+:[12]$"),
        group=-7,
    )
    return _previous_run_polling(self, *args, **kwargs)


bot.Application.run_polling = _install_receipt_handlers
_ensure_receipt_schema()
