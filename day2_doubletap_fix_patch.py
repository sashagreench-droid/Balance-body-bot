import bot

# BALANCE BODY — prevent duplicate Day 2 hunger/satiety messages when a
# Telegram button is tapped twice quickly or a stale callback is delivered.
# The original flow already stores awaiting_hunger/awaiting_satiety, so use
# those flags as a small idempotency guard.

_original_menu = bot.menu


async def menu(update, context):
    q = update.callback_query
    data = q.data or ""

    if data == "hunger_start":
        # Once the first tap has opened the hunger scale, a second tap on the
        # same old button must not start the flow again.
        if context.user_data.get("awaiting_hunger"):
            await q.answer()
            return

    elif data.startswith("hunger:"):
        # The first accepted hunger value clears this flag. Any repeated or
        # stale tap must therefore be ignored.
        if not context.user_data.get("awaiting_hunger"):
            await q.answer()
            return

    elif data.startswith("satiety:"):
        # Same protection for the satiety scale.
        if not context.user_data.get("awaiting_satiety"):
            await q.answer()
            return

    return await _original_menu(update, context)


bot.menu = menu
