import runpy
import content
import bot

# Day 19: quickly build a balanced meal from the foods already available at home.
content.DAY_TASKS[19] = (
    "Сегодня учимся собирать полноценный прием пищи даже тогда, когда дома осталось всего несколько продуктов.",
    "Представь, что до следующей закупки осталось несколько продуктов из того, что уже есть дома. Выбери из них те, из которых можно быстро собрать сбалансированный прием пищи за 5–10 минут. Прикинь, где здесь белок, источник углеводов, овощи/фрукты и жиры. Собери блюдо и, если хочешь, отправь фото.",
    "Какие продукты у тебя остались дома?\nЧто ты из них собрала?\nЗа счет чего твой прием пищи получился сбалансированным?"
)

# Day 19 gets a specific reflection feedback instead of the generic response.
_original_reflection_feedback = bot.reflection_feedback


def reflection_feedback(day, text, uid=None):
    if day == 19:
        return (
            "🌿 Теперь посмотрим на твой выбор\n\n"
            "Ты использовала продукты, которые уже были дома, вместо того чтобы искать «идеальные» ингредиенты. "
            "И это как раз тот навык, который мы сегодня тренируем: собирать нормальный сбалансированный прием пищи из того, что есть под рукой.\n\n"
            "Даже если получилось не идеально — ты уже можешь посмотреть на свой прием пищи и понять, "
            "чего в нем достаточно, а чего можно добавить в следующий раз."
        )
    return _original_reflection_feedback(day, text, uid)


bot.reflection_feedback = reflection_feedback

# Keep all existing patches and production startup logic.
runpy.run_module("day18_patch", run_name="__main__")
