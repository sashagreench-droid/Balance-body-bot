import bot
import db

_original_begin_day = bot.begin_day


async def begin_day_debug(q, n):
    uid = q.from_user.id
    try:
        u = db.user(uid)
        row = db.day_row(uid, n) if u else None
        return await _original_begin_day(q, n)
    except Exception as e:
        # Surface the real exception instead of hiding it behind the generic
        # SQLite message in runner.py. This is intentionally diagnostic.
        u = db.user(uid)
        row = db.day_row(uid, n) if u else None
        status = row["status"] if row else "NO_ROW"
        current_day = u["current_day"] if u else "NO_USER"
        db_path = getattr(db, "DB_PATH", "UNKNOWN")
        await q.message.reply_text(
            "🔎 Техническая диагностика\n\n"
            f"Ошибка: {type(e).__name__}: {e}\n"
            f"Пользователь: {uid}\n"
            f"current_day: {current_day}\n"
            f"row day: {n}\n"
            f"status: {status}\n"
            f"SQLite: {db_path}"
        )
        raise


bot.begin_day = begin_day_debug
