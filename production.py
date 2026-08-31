import runpy
import bot

# Load the full patch chain without letting the nested runner start the bot early.
_real_main = bot.main
bot.main = lambda: None
try:
    runpy.run_module("day28_patch", run_name="__main__")
finally:
    bot.main = _real_main

# Start only after Day 28 and all previous patches have been applied.
bot.main()
