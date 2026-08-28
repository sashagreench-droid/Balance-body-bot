# Interactive Day 8 mini-test: proteins, fats and carbohydrates.

QUESTIONS = [
    {
        "text": "🍗 Куриная грудка — это прежде всего источник:",
        "options": ["🥩 Белка", "🥑 Жиров", "🍚 Углеводов"],
        "correct": 0,
        "explain": "Куриная грудка в первую очередь ценна как источник белка.",
    },
    {
        "text": "🫒 Что из этого в первую очередь относится к источникам жиров?",
        "options": ["🍚 Рис", "🫒 Оливковое масло", "🍗 Куриная грудка"],
        "correct": 1,
        "explain": "Оливковое масло — практически чистый источник жиров.",
    },
    {
        "text": "🍚 Что из этого преимущественно относится к углеводам?",
        "options": ["🥚 Яйца", "🍚 Рис", "🧈 Сливочное масло"],
        "correct": 1,
        "explain": "Рис преимущественно дает углеводы.",
    },
    {
        "text": "🥚 В каком варианте есть сразу несколько макронутриентов?",
        "options": ["🍬 Сахар", "🫒 Оливковое масло", "🥚 Яйца"],
        "correct": 2,
        "explain": "Яйца содержат и белок, и жиры, поэтому продукты не всегда относятся только к одной категории.",
    },
    {
        "text": "💡 Что правильнее сказать о БЖУ?",
        "options": [
            "❌ Один макронутриент нужно исключить",
            "❌ Углеводы мешают похудению",
            "✅ Все три нужны организму, важны их количество и общий рацион",
        ],
        "correct": 2,
        "explain": "Белки, жиры и углеводы выполняют разные функции. Важно не исключать их без причины, а понимать роль и количество.",
    },
]


def question_keyboard(question_index):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    q = QUESTIONS[question_index]
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(option, callback_data=f"bju_answer:{question_index}:{i}")] for i, option in enumerate(q["options"])]
    )


def result_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 ПРОЙТИ ЕЩЁ РАЗ", callback_data="bju_start")],
        [InlineKeyboardButton("➡️ Я ВЫПОЛНИЛА", callback_data="donepractice")],
        [InlineKeyboardButton("🤔 МНЕ СЛОЖНО", callback_data="trainer")],
    ])
