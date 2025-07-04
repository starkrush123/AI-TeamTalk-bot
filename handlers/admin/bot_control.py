
import logging
import wx

def handle_lock(bot, msg_from_id, **kwargs):
    bot.toggle_bot_lock()
    new_state = "ON" if bot.bot_locked else "OFF"
    bot._send_pm(msg_from_id, f"Bot lock is now {new_state}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_block_command(bot, msg_from_id, args_str, **kwargs):
    cmd_to_toggle = args_str.strip().lower()
    if not cmd_to_toggle:
        blocked = ', '.join(sorted(list(bot.blocked_commands))) or 'None'
        bot._send_pm(msg_from_id, f"Usage: block <command>\nCurrently blocked: {blocked}"); return

    if cmd_to_toggle in bot.UNBLOCKABLE_COMMANDS:
        bot._send_pm(msg_from_id, f"Error: Command '{cmd_to_toggle}' cannot be blocked."); return

    if cmd_to_toggle in bot.blocked_commands:
        bot.blocked_commands.remove(cmd_to_toggle)
        feedback = f"Command '{cmd_to_toggle}' has been UNBLOCKED."
    else:
        bot.blocked_commands.add(cmd_to_toggle)
        feedback = f"Command '{cmd_to_toggle}' has been BLOCKED."
    
    bot._send_pm(msg_from_id, feedback)

def handle_restart(bot, msg_from_id, **kwargs):
    bot._send_pm(msg_from_id, "Acknowledged. Restarting bot...")
    bot._mark_stopped_intentionally()
    if bot.main_window:
        wx.CallAfter(bot._initiate_restart)
    else:
        bot._initiate_restart()

def handle_quit(bot, msg_from_id, **kwargs):
    bot._send_pm(msg_from_id, "Acknowledged. Quitting...")
    bot._mark_stopped_intentionally()
    if bot.main_window:
        wx.CallAfter(bot.stop)
    else:
        bot.controller.request_shutdown() # Request application shutdown
