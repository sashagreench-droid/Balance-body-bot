from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ApplicationHandlerStop, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters

import bot
import db

# Launch price: 4,990 RUB target, collected in Telegram Stars.
# Two installments: 1,750 Stars + 1,750 Stars.
# The exact RUB value of Stars varies by user's purchase route/region, so the
# bot intentionally displays the price in Stars rather than promising a fixed
# ruble conversion.
PART_STARS = {1: 1750, 2: 1750}
TOTAL_STARS = sum(PART_STARS.values())


def _ensure_payments_table():
    con = db.connect()
    con.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            payload TEXT NOT NULL,
            part INTEGER NOT NULL,
            amount_stars INTEGER NOT NULL,
            currency TEXT NOT NULL,
            telegram_payment_charge_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tg_id, part)
        )
    """)
    con.commit()
    con.close()


def _paid_parts(uid):
    _ensure_payments_table()
    con = db.connect()
    rows = con.execute("SELECT part FROM payments WHERE tg_id=? ORDER BY part", (uid,)).fetchall()
    con.close()
    return {int(r["part"]) for r in rows}


def _course_paid(uid):
    return _paid_parts(uid) == {1, 2}


def _payment_kb(uid):
    paid = _paid_parts(uid)
    buttons = []
    if 1 not in paid:
        buttons.append([InlineKeyboardButton("⭐ ОПЛАТИТЬ 1/2 — 1 750", callback_data="buy:1")])
    elif 2 not in paid:
        buttons.append([InlineKeyboardButton("⭐ ОПЛАТИТЬ 2/2 — 1 750", callback_data="buy:2")])
    else:
        buttons.append([InlineKeyboardButton("▶️ НАЧАТЬ КУРС", callback_data="continue")])
    buttons.append([InlineKeyboardButton("⬅️ В МЕНЮ", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


async def _show_offer(target, uid):
    paid = _paid_parts(uid)
    if paid == {1, 2}:
        await target.reply_text(
            "✅ <b>BALANCE BODY уже оплачен</b>\n\n"
            "Тебе открыт весь курс из 49 дней. Можно начинать с Дня 1 или продолжать с текущего дня.",
            parse_mode="HTML",
            reply_markup=_payment_kb(uid),
        )
        return
    if 1 in paid:
        text = (
            "💳 <b>BALANCE BODY</b>\n\n"
            "Первая часть оплаты получена ❤️\n\n"
            "Осталась вторая часть — <b>1 750 ⭐</b>.\n"
            "После второй оплаты тебе автоматически откроются все 49 дней курса."
        )
    else:
        text = (
            "💳 <b>BALANCE BODY</b>\n\n"
            "49 дней → самостоятельность ❤️\n\n"
            "Ежедневные практики, питание без жестких запретов, работа со сладким, ресторанами, стрессом, движением и срывами.\n\n"
            "Полная стоимость: <b>3 500 ⭐</b>\n"
            "Можно оплатить в два платежа: <b>1 750 ⭐ + 1 750 ⭐</b>.\n\n"
            "Оплата проходит через Telegram Stars."
        )
    await target.reply_text(text, parse_mode="HTML", reply_markup=_payment_kb(uid))


async def _buy_callback(update, context):
    q = update.callback_query
    if not q.data.startswith("buy:"):
        return
    await q.answer()
    uid = q.from_user.id
    part = int(q.data.split(":", 1)[1])
    paid = _paid_parts(uid)
    if part in paid:
        await _show_offer(q.message, uid)
        raise ApplicationHandlerStop
    if part == 2 and 1 not in paid:
        await q.message.reply_text("Сначала нужно оплатить первую часть ❤️", reply_markup=_payment_kb(uid))
        raise ApplicationHandlerStop
    amount = PART_STARS[part]
    payload = f"balance_body_part_{part}"
    await context.bot.send_invoice(
        chat_id=uid,
        title=f"BALANCE BODY — часть {part}/2",
        description="49 дней → самостоятельность. Доступ к курсу после полной оплаты.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(f"BALANCE BODY {part}/2", amount)],
    )
    raise ApplicationHandlerStop


async def _pre_checkout(update, context):
    q = update.pre_checkout_query
    payload = q.invoice_payload
    if payload not in ("balance_body_part_1", "balance_body_part_2"):
        await q.answer(ok=False, error_message="Не удалось проверить заказ. Попробуй ещё раз.")
        return
    part = 1 if payload.endswith("_1") else 2
    if q.currency != "XTR" or q.total_amount != PART_STARS[part]:
        await q.answer(ok=False, error_message="Сумма заказа изменилась. Открой оплату заново.")
        return
    if part == 2 and 1 not in _paid_parts(q.from_user.id):
        await q.answer(ok=False, error_message="Сначала оплати первую часть курса.")
        return
    if part in _paid_parts(q.from_user.id):
        await q.answer(ok=False, error_message="Эта часть уже оплачена.")
        return
    await q.answer(ok=True)


async def _successful_payment(update, context):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    if payload not in ("balance_body_part_1", "balance_body_part_2"):
        return
    part = 1 if payload.endswith("_1") else 2
    uid = update.effective_user.id
    _ensure_payments_table()
    con = db.connect()
    con.execute(
        "INSERT OR IGNORE INTO payments(tg_id,payload,part,amount_stars,currency,telegram_payment_charge_id) VALUES(?,?,?,?,?,?)",
        (uid, payload, part, payment.total_amount, payment.currency, payment.telegram_payment_charge_id),
    )
    con.commit()
    con.close()

    paid = _paid_parts(uid)
    if paid == {1, 2}:
        # The existing course engine starts at day 1 for new users. For an
        # already-progressed user, preserve their current day and simply unlock access.
        u = db.user(uid)
        await update.message.reply_text(
            "🎉 <b>Оплата получена!</b>\n\n"
            "BALANCE BODY полностью оплачен ❤️\n\n"
            f"Тебе открыт курс из 49 дней. Сейчас доступен День {u['current_day'] if u else 1}.",
            parse_mode="HTML",
            reply_markup=bot.main_kb(),
        )
    else:
        await update.message.reply_text(
            "✅ <b>Первая часть оплачена!</b>\n\n"
            "Остался один платеж — 1 750 ⭐. После него откроется весь курс ❤️",
            parse_mode="HTML",
            reply_markup=_payment_kb(uid),
        )


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
        "После полной оплаты доступ к материалам предоставляется автоматически в этом боте.\n\n"
        "Если возникла проблема с оплатой или доступом, используй /paysupport.",
        parse_mode="HTML",
    )


async def _paysupport(update, context):
    await update.message.reply_text(
        "🧾 <b>ПОМОЩЬ ПО ОПЛАТЕ</b>\n\n"
        "Если платеж прошёл, но доступ не открылся, или нужна помощь с возвратом, напиши сюда: @balance_body_support\n\n"
        "Укажи дату платежа и пришли скриншот чека Telegram.",
        parse_mode="HTML",
    )


# Gate the existing course entry points without rewriting the stable course engine.
_real_menu = bot.menu
async def _menu_payment_gate(update, context):
    q = update.callback_query
    if q.data in ("continue",) or q.data.startswith("startday:"):
        uid = q.from_user.id
        if not _course_paid(uid):
            await q.answer()
            await _show_offer(q.message, uid)
            raise ApplicationHandlerStop
    return await _real_menu(update, context)

bot.menu = _menu_payment_gate

_real_main_kb = bot.main_kb
def _main_kb_with_buy():
    kb = _real_main_kb()
    # Keep the original menu and add the purchase entry at the bottom.
    rows = list(kb.inline_keyboard)
    rows.append([InlineKeyboardButton("💳 КУПИТЬ BALANCE BODY", callback_data="buy:offer")])
    return InlineKeyboardMarkup(rows)

bot.main_kb = _main_kb_with_buy

# buy:offer is handled separately because the purchase button itself is a callback.
async def _buy_offer_callback(update, context):
    q = update.callback_query
    if q.data != "buy:offer":
        return
    await q.answer()
    await _show_offer(q.message, q.from_user.id)
    raise ApplicationHandlerStop

_real_run_polling = None

def _install_payment_handlers(self, *args, **kwargs):
    global _real_run_polling
    if _real_run_polling is None:
        _real_run_polling = self.run_polling
    self.add_handler(CommandHandler("buy", _buy_command), group=-6)
    self.add_handler(CommandHandler("terms", _terms), group=-6)
    self.add_handler(CommandHandler("paysupport", _paysupport), group=-6)
    self.add_handler(PreCheckoutQueryHandler(_pre_checkout), group=-6)
    self.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, _successful_payment), group=-6)
    self.add_handler(CallbackQueryHandler(_buy_offer_callback, pattern=r"^buy:offer$"), group=-6)
    self.add_handler(CallbackQueryHandler(_buy_callback, pattern=r"^buy:[12]$"), group=-6)
    return _real_run_polling(*args, **kwargs)

bot.Application.run_polling = _install_payment_handlers

_ensure_payments_table()
