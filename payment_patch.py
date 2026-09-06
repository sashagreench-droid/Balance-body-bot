import os
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationHandlerStop, CommandHandler, CallbackQueryHandler

import bot
import db

# BALANCE BODY: manual transfer payments.
# First payment: 2,495 RUB. Second payment: 2,495 RUB, due 24 days after the first.
PART_RUB = {1: 2495, 2: 2495}
SECOND_PAYMENT_DELAY_DAYS = 24
PAYMENT_DETAILS = os.getenv("PAYMENT_DETAILS", "Реквизиты оплаты пока не настроены.").strip()
COURSE_CHANNEL_ID = os.getenv("COURSE_CHANNEL_ID", "").strip()


def _ensure_payments_table():
    con = db.connect()
    con.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            part INTEGER NOT NULL,
            amount_rub INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            invite_link TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT,
            UNIQUE(tg_id, part)
        )
    """)
    # Add fields when upgrading the previous Stars-payment table.
    cols = {r["name"] for r in con.execute("PRAGMA table_info(payments)").fetchall()}
    if "amount_rub" not in cols:
        con.execute("ALTER TABLE payments ADD COLUMN amount_rub INTEGER")
        con.execute("UPDATE payments SET amount_rub=2495 WHERE amount_rub IS NULL")
    if "status" not in cols:
        con.execute("ALTER TABLE payments ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
    if "invite_link" not in cols:
        con.execute("ALTER TABLE payments ADD COLUMN invite_link TEXT")
    if "approved_at" not in cols:
        con.execute("ALTER TABLE payments ADD COLUMN approved_at TEXT")
    con.commit()
    con.close()


def _rows(uid):
    _ensure_payments_table()
    con = db.connect()
    rows = con.execute("SELECT * FROM payments WHERE tg_id=? ORDER BY part", (uid,)).fetchall()
    con.close()
    return rows


def _paid_parts(uid):
    return {int(r["part"]) for r in _rows(uid) if (r["status"] or "") == "approved"}


def _payment_date(uid, part=1):
    for row in _rows(uid):
        if int(row["part"]) != part:
            continue
        for field in ("approved_at", "created_at"):
            value = row[field]
            if value:
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    pass
    return None


def _second_payment_available(uid):
    first = _payment_date(uid, 1)
    return bool(first and datetime.utcnow() >= first + timedelta(days=SECOND_PAYMENT_DELAY_DAYS))


def _payment_kb(uid):
    paid = _paid_parts(uid)
    buttons = []
    if 1 not in paid:
        buttons.append([InlineKeyboardButton("💳 ОПЛАТИТЬ 1/2 — 2 495 ₽", callback_data="buy:1")])
    elif 2 not in paid:
        if _second_payment_available(uid):
            buttons.append([InlineKeyboardButton("💳 ОПЛАТИТЬ 2/2 — 2 495 ₽", callback_data="buy:2")])
        else:
            first = _payment_date(uid, 1)
            available = first + timedelta(days=SECOND_PAYMENT_DELAY_DAYS) if first else None
            date_text = available.strftime("%d.%m.%Y") if available else "через 24 дня"
            buttons.append([InlineKeyboardButton(f"⏳ ВТОРОЙ ПЛАТЕЖ С {date_text}", callback_data="buy:wait")])
    else:
        buttons.append([InlineKeyboardButton("▶️ НАЧАТЬ КУРС", callback_data="continue")])
    buttons.append([InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


async def _show_offer(target, uid):
    paid = _paid_parts(uid)
    if paid == {1, 2}:
        await target.reply_text(
            "🎉 <b>BALANCE BODY полностью оплачен</b>\n\n"
            "Тебе открыт весь курс из 49 дней ❤️",
            parse_mode="HTML",
            reply_markup=_payment_kb(uid),
        )
        return

    if 1 in paid:
        first = _payment_date(uid, 1)
        available = first + timedelta(days=SECOND_PAYMENT_DELAY_DAYS) if first else None
        if _second_payment_available(uid):
            text = (
                "💳 <b>BALANCE BODY</b>\n\n"
                "Прошло 24 дня с первой оплаты ❤️\n\n"
                "Теперь доступен второй платеж — <b>2 495 ₽</b>.\n"
                "После подтверждения оплаты доступ к продолжению курса откроется."
            )
        else:
            date_text = available.strftime("%d.%m.%Y") if available else "через 24 дня"
            text = (
                "💳 <b>BALANCE BODY</b>\n\n"
                "Первая часть оплаты получена ❤️\n\n"
                "Второй платеж — <b>2 495 ₽</b> — доступен через 24 дня после первой оплаты.\n"
                f"📅 Дата второго платежа: <b>{date_text}</b>"
            )
    else:
        text = (
            "💳 <b>BALANCE BODY</b>\n\n"
            "<b>49 дней → самостоятельность ❤️</b>\n\n"
            "Ежедневные практики, питание без жестких запретов, работа со сладким, ресторанами, стрессом, движением и срывами.\n\n"
            "Стоимость курса: <b>4 990 ₽</b>.\n"
            "Оплата в два этапа: <b>2 495 ₽ + 2 495 ₽</b>.\n"
            "Второй платеж — через <b>24 дня</b> после первой оплаты.\n\n"
            "Оплата переводом. Нажми кнопку оплаты, чтобы получить реквизиты."
        )
    await target.reply_text(text, parse_mode="HTML", reply_markup=_payment_kb(uid))


async def _buy_callback(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    part = int(q.data.split(":", 1)[1])
    paid = _paid_parts(uid)

    if part in paid:
        await _show_offer(q.message, uid)
        raise ApplicationHandlerStop

    if part == 2:
        if 1 not in paid:
            await q.message.reply_text("Сначала нужно оплатить первую часть ❤️", reply_markup=_payment_kb(uid))
            raise ApplicationHandlerStop
        if not _second_payment_available(uid):
            await q.message.reply_text("Второй платеж станет доступен через 24 дня после первой оплаты ❤️", reply_markup=_payment_kb(uid))
            raise ApplicationHandlerStop

    _ensure_payments_table()
    con = db.connect()
    cols = {r["name"] for r in con.execute("PRAGMA table_info(payments)").fetchall()}
    values = {"tg_id": uid, "part": part, "amount_rub": PART_RUB[part], "status": "pending", "created_at": datetime.utcnow().isoformat()}
    # Compatibility with the old Stars schema, if it is still present in the Railway DB.
    if "payload" in cols:
        values["payload"] = f"manual_transfer_part_{part}"
    if "amount_stars" in cols:
        values["amount_stars"] = 0
    if "currency" in cols:
        values["currency"] = "RUB"
    if "telegram_payment_charge_id" in cols:
        values["telegram_payment_charge_id"] = None
    fields = list(values)
    placeholders = ",".join("?" for _ in fields)
    sql = f"INSERT OR REPLACE INTO payments({','.join(fields)}) VALUES({placeholders})"
    con.execute(sql, tuple(values[f] for f in fields))
    con.commit()
    con.close()

    await q.message.reply_text(
        "💳 <b>ОПЛАТА BALANCE BODY</b>\n\n"
        f"Часть: <b>{part}/2</b>\n"
        f"Сумма: <b>{PART_RUB[part]:,} ₽</b>\n\n"
        f"<b>Реквизиты:</b>\n{PAYMENT_DETAILS}\n\n"
        "После перевода обязательно нажми «Я ОПЛАТИЛА» — я передам запрос тренеру для проверки поступления.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Я ОПЛАТИЛА", callback_data=f"payment:paid:{part}")],
            [InlineKeyboardButton("⬅️ К ОПЛАТЕ", callback_data="buy:offer")],
        ]),
    )
    raise ApplicationHandlerStop


async def _paid_callback(update, context):
    q = update.callback_query
    uid = q.from_user.id
    part = int(q.data.split(":", 2)[2])
    await q.answer("Запрос отправлен тренеру ❤️")

    _ensure_payments_table()
    con = db.connect()
    row = con.execute("SELECT * FROM payments WHERE tg_id=? AND part=?", (uid, part)).fetchone()
    con.close()
    if not row:
        await q.message.reply_text("Сначала нажми кнопку оплаты ❤️", reply_markup=_payment_kb(uid))
        raise ApplicationHandlerStop

    for admin_id in set(bot.ADMIN_IDS):
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🔔 <b>ПОЛЬЗОВАТЕЛЬ СООБЩИЛ ОБ ОПЛАТЕ</b>\n\n"
                    f"👤 Пользователь: <code>{uid}</code>\n"
                    f"💳 Часть: <b>{part}/2</b>\n"
                    f"💵 Сумма: <b>{PART_RUB[part]:,} ₽</b>\n\n"
                    "Проверь поступление перевода и подтверди оплату."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data=f"payment:approve:{uid}:{part}")]
                ]),
            )
        except Exception:
            pass

    await q.message.reply_text(
        "Отлично ❤️ Я передала информацию тренеру.\n\n"
        "Доступ откроется после проверки перевода.",
        reply_markup=bot.back_kb(),
    )
    raise ApplicationHandlerStop


async def _approve_callback(update, context):
    q = update.callback_query
    if q.from_user.id not in set(bot.ADMIN_IDS):
        await q.answer("Нет доступа", show_alert=True)
        return
    await q.answer()
    _, _, uid_text, part_text = q.data.split(":")
    uid, part = int(uid_text), int(part_text)
    _ensure_payments_table()

    con = db.connect()
    row = con.execute("SELECT * FROM payments WHERE tg_id=? AND part=?", (uid, part)).fetchone()
    if not row:
        con.close()
        await q.message.reply_text("Платёж не найден.")
        raise ApplicationHandlerStop

    now = datetime.utcnow().isoformat()
    con.execute("UPDATE payments SET status='approved', approved_at=? WHERE tg_id=? AND part=?", (now, uid, part))
    con.commit()
    con.close()

    invite = None
    if COURSE_CHANNEL_ID:
        try:
            chat_id = int(COURSE_CHANNEL_ID) if COURSE_CHANNEL_ID.lstrip("-").isdigit() else COURSE_CHANNEL_ID
            invite_obj = await context.bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"BALANCE BODY {uid} часть {part}",
                member_limit=1,
            )
            invite = invite_obj.invite_link
            con = db.connect()
            con.execute("UPDATE payments SET invite_link=? WHERE tg_id=? AND part=?", (invite, uid, part))
            con.commit()
            con.close()
        except Exception:
            invite = None

    text = "✅ <b>Оплата подтверждена!</b> ❤️\n\n"
    if part == 1:
        text += "Первая часть курса оплачена. Второй платеж — <b>2 495 ₽</b> — будет доступен через 24 дня.\n\n"
    else:
        text += "Вторая часть курса оплачена. BALANCE BODY полностью оплачен 🎉\n\n"

    if invite:
        text += "🔐 <b>Персональная ссылка на закрытый канал:</b>\n\n" + invite + "\n\nСсылка рассчитана на одно использование."
    elif COURSE_CHANNEL_ID:
        text += "⚠️ Оплата подтверждена, но персональную ссылку создать не удалось. Проверь, что бот добавлен администратором закрытого канала с правом приглашать пользователей."
    else:
        text += "ℹ️ Закрытый канал ещё не подключён. После добавления COURSE_CHANNEL_ID бот сможет выдавать персональные ссылки."

    try:
        await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML", reply_markup=bot.main_kb())
    except Exception:
        pass

    await q.message.reply_text(
        f"✅ Платёж {part}/2 пользователя {uid} подтверждён.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В АДМИН-ПАНЕЛЬ", callback_data="admin:home")]]),
    )
    raise ApplicationHandlerStop


async def _buy_wait_callback(update, context):
    q = update.callback_query
    await q.answer("Второй платеж станет доступен через 24 дня после первой оплаты.", show_alert=True)
    raise ApplicationHandlerStop


async def _buy_command(update, context):
    uid = update.effective_user.id
    if not db.user(uid):
        await update.message.reply_text("Сначала нажми /start и зарегистрируйся ❤️")
        return
    await _show_offer(update.message, uid)


async def _terms(update, context):
    await update.message.reply_text(
        "📄 <b>УСЛОВИЯ ПОКУПКИ</b>\n\n"
        "BALANCE BODY — цифровой образовательный курс из 49 дней.\n\n"
        "Стоимость: 4 990 ₽, оплата двумя платежами по 2 495 ₽.\n"
        "Второй платеж доступен через 24 дня после первого.\n\n"
        "Доступ предоставляется после подтверждения оплаты.\n\n"
        "Если возникла проблема с оплатой или доступом, используй /paysupport.",
        parse_mode="HTML",
    )


async def _paysupport(update, context):
    await update.message.reply_text(
        "🧾 <b>ПОМОЩЬ ПО ОПЛАТЕ</b>\n\n"
        "Если ты оплатила переводом, нажала «Я оплатила», но доступ ещё не открыт — дождись проверки тренером.\n\n"
        "Если нужна помощь, напиши через кнопку «ЗАДАТЬ ТРЕНЕРУ» в боте.",
        parse_mode="HTML",
    )


# First payment unlocks the bot course immediately. After 24 days the second payment is required.
_real_menu = bot.menu
async def _menu_payment_gate(update, context):
    q = update.callback_query
    if q.data in ("continue",) or q.data.startswith("startday:"):
        uid = q.from_user.id
        paid = _paid_parts(uid)
        if not paid:
            await q.answer()
            await _show_offer(q.message, uid)
            raise ApplicationHandlerStop
        if 1 in paid and 2 not in paid and _second_payment_available(uid):
            await q.answer()
            await q.message.reply_text(
                "⏳ <b>Время второго платежа</b>\n\n"
                "Прошло 24 дня с первой оплаты. Чтобы продолжить BALANCE BODY, оплати вторую часть — <b>2 495 ₽</b>.",
                parse_mode="HTML",
                reply_markup=_payment_kb(uid),
            )
            raise ApplicationHandlerStop
    return await _real_menu(update, context)

bot.menu = _menu_payment_gate

_real_main_kb = bot.main_kb
def _main_kb_with_buy():
    kb = _real_main_kb()
    rows = list(kb.inline_keyboard)
    rows.append([InlineKeyboardButton("💳 КУПИТЬ BALANCE BODY", callback_data="buy:offer")])
    return InlineKeyboardMarkup(rows)

bot.main_kb = _main_kb_with_buy


async def _buy_offer_callback(update, context):
    q = update.callback_query
    await q.answer()
    await _show_offer(q.message, q.from_user.id)
    raise ApplicationHandlerStop


_ORIGINAL_RUN_POLLING = bot.Application.run_polling


def _install_payment_handlers(self, *args, **kwargs):
    self.add_handler(CommandHandler("buy", _buy_command), group=-6)
    self.add_handler(CommandHandler("terms", _terms), group=-6)
    self.add_handler(CommandHandler("paysupport", _paysupport), group=-6)
    self.add_handler(CallbackQueryHandler(_buy_offer_callback, pattern=r"^buy:offer$"), group=-6)
    self.add_handler(CallbackQueryHandler(_buy_callback, pattern=r"^buy:[12]$"), group=-6)
    self.add_handler(CallbackQueryHandler(_buy_wait_callback, pattern=r"^buy:wait$"), group=-6)
    self.add_handler(CallbackQueryHandler(_paid_callback, pattern=r"^payment:paid:[12]$"), group=-6)
    self.add_handler(CallbackQueryHandler(_approve_callback, pattern=r"^payment:approve:\d+:[12]$"), group=-6)
    return _ORIGINAL_RUN_POLLING(self, *args, **kwargs)


bot.Application.run_polling = _install_payment_handlers
_ensure_payments_table()
