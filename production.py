import runpy
import bot
import db

# Initialize the database before loading any patch chain.
db.init_db()

_real_main = bot.main
bot.main = lambda: None
try:
    runpy.run_module("day34_patch", run_name="__main__")
    runpy.run_module("day31_reflection_patch", run_name="__main__")
    runpy.run_module("day29_state_patch", run_name="__main__")
    runpy.run_module("day30_debug_patch", run_name="__main__")
finally:
    bot.main = _real_main

bot.main()
