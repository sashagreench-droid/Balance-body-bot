import runpy
import content
import bot

# Day 20: plan the next day around the user's individual calorie target.
content.DAY_TASKS[20] = (
    "Сегодня учимся планировать питание под свой калораж, а не есть наугад до сильного голода.",
    "Открой свой индивидуальный ориентир калорий. Составь простой план питания на следующий день под свою калорийность: запиши основные приемы пищи и при необходимости перекус. Ориентируйся на свой обычный рацион и продукты, которые реально будешь есть — задача не в идеальном меню, а в том, чтобы заранее понимать, как распределить калории в течение дня.",
    "Какой у тебя ориентир калорий?\nКак ты распределила калории между приемами пищи?\nЧто оказалось самым удобным или самым сложным при планировании под свой калораж?"
)

# Day 20 gets feedback tied directly to planning around the individual calorie target.
_original_reflection_feedback = bot.reflection_feedback


def reflection_feedback(day, text, uid=None):
    if day == 20:
        return (
            "🌿 Давай посмотрим на твой план\n\n"
            "Сегодня ты не ждала сильного голода, чтобы решить, что есть, а заранее посмотрела на свой калораж и распределила питание под него. "
            "Это и есть навык планирования: калории становятся ориентиром, который помогает принимать решения заранее, а не ограничением.\n\n"
            "Обрати внимание, что в следующем дне можно оставить гибкость: если планы изменятся, рацион можно спокойно скорректировать, не начиная всё заново."
        )
    return _original_reflection_feedback(day, text, uid)


bot.reflection_feedback = reflection_feedback

# Keep all existing patches and production startup logic.
runpy.run_module("day19_patch", run_name="__main__")
