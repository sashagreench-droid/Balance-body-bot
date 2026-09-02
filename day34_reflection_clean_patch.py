import re
import bot

# The bot adds the reflection heading and the final reply instruction itself.
# Keep Day 34's custom questions, but remove embedded HTML/duplicate wrapper text.
_previous_feedback = bot.reflection_feedback


def reflection_feedback(day, text, uid=None):
    result = _previous_feedback(day, text, uid)
    if day != 34:
        return result

    result = re.sub(r"</?b>", "", result)
    result = result.replace("🌿 Теперь рефлексия\n\n", "")
    result = result.replace(
        "Напиши ответ одним сообщением. Я дам тебе короткую обратную связь, а потом мы завершим день.",
        "",
    ).rstrip()
    return result


bot.reflection_feedback = reflection_feedback
