import runpy
import bot
import db

# Initialize the database before loading any patch chain.
db.init_db()

_real_main = bot.main
bot.main = lambda: None
try:
    # Load patches from oldest to newest so the newest day-specific
    # handlers stay outermost and do not get bypassed by older wrappers.
    runpy.run_module("day29_state_patch", run_name="__main__")
    runpy.run_module("day31_reflection_patch", run_name="__main__")
    runpy.run_module("day34_reflection_clean_patch", run_name="__main__")
    runpy.run_module("day35_cleanup_patch", run_name="__main__")
    runpy.run_module("day36_patch", run_name="__main__")
    runpy.run_module("day36_fix_patch", run_name="__main__")
    runpy.run_module("day37_patch", run_name="__main__")
    runpy.run_module("day37_fix_patch", run_name="__main__")
    runpy.run_module("day38_patch", run_name="__main__")
    runpy.run_module("day39_patch", run_name="__main__")
    runpy.run_module("day40_patch", run_name="__main__")
    runpy.run_module("day41_patch", run_name="__main__")
    runpy.run_module("day42_patch", run_name="__main__")
    runpy.run_module("day42_fix_patch", run_name="__main__")
    runpy.run_module("day42_practice_fix", run_name="__main__")
    runpy.run_module("day30_debug_patch", run_name="__main__")
finally:
    bot.main = _real_main

bot.main()
