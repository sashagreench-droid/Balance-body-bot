import runpy
import bot
import db

# Initialize and repair the persistent SQLite database BEFORE any patch is loaded.
# This is important because production.py temporarily disables bot.main().
db.init_db()

# Load the full patch chain without letting the nested runner start the bot early.
_real_main = bot.main
bot.main = lambda: None
try:
    runpy.run_module("day30_patch", run_name="__main__")
    runpy.run_module("day29_state_patch", run_name="__main__")
finally:
    bot.main = _real_main

# Start only after all patches and DB repair have been applied.
bot.main()
