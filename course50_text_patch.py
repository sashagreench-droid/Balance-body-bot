import bot
from telegram.ext import ConversationHandler

# BALANCE BODY: update the public onboarding text to the actual 50-day course.
_real_start = bot.start

async def start(update, context):
    u = bot.db.user(update.effective_user.id)
    if u:
        return await _real_start(update, context)

    await update.message.reply_text(
        "Привет! ❤️\n\n"
        "Это курс «50 дней → самостоятельность».\n\n"
        "Как тебя зовут?"
    )
    return bot.ASK_NAME

bot.start = start
