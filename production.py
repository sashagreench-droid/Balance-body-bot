import runpy
import bot
import db

db.init_db()

_real_main = bot.main
bot.main = lambda: None
try:
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
    runpy.run_module("day43_patch", run_name="__main__")
    runpy.run_module("day43_runtime_fix", run_name="__main__")
    runpy.run_module("day44_patch", run_name="__main__")
    runpy.run_module("day44_feedback_fix", run_name="__main__")
    runpy.run_module("day45_patch", run_name="__main__")
    runpy.run_module("day45_runtime_fix", run_name="__main__")
    runpy.run_module("day30_debug_patch", run_name="__main__")
finally:
    bot.main = _real_main

bot.main()
