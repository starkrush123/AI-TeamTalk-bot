
def handle_toggle_jcl(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('announce_join_leave', "Join/Leave Announce ON", "Join/Leave Announce OFF")
    bot._send_pm(msg_from_id, f"Join/Leave Announce is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_chanmsg(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('allow_channel_messages', "Allow Channel Msgs ON", "Allow Channel Msgs OFF")
    bot._send_pm(msg_from_id, f"Allow Channel Messages is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_broadcast(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('allow_broadcast', "Allow Broadcasts ON", "Allow Broadcasts OFF")
    bot._send_pm(msg_from_id, f"Allow Broadcasts is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_gemini_pm(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('allow_gemini_pm', "Allow Gemini PM ON", "Allow Gemini PM OFF")
    bot._send_pm(msg_from_id, f"Allow Gemini PM is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_gemini_chan(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('allow_gemini_channel', "Allow Gemini Channel ON", "Allow Gemini Channel OFF")
    bot._send_pm(msg_from_id, f"Allow Gemini Channel is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_welcome_mode(bot, msg_from_id, **kwargs):
    if bot.welcome_message_mode == "template":
        if not bot.gemini_service.is_enabled():
            bot._send_pm(msg_from_id, "Error: Cannot switch to Gemini mode, AI not available.")
            return
        bot.welcome_message_mode = "gemini"
        feedback = "Welcome message mode set to: Gemini."
    else:
        bot.welcome_message_mode = "template"
        feedback = "Welcome message mode set to: Template."
    bot._send_pm(msg_from_id, feedback)

def handle_toggle_filter(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('filter_enabled', "Word Filter ON", "Word Filter OFF")
    bot._send_pm(msg_from_id, f"Word Filter is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_context_history(bot, msg_from_id, **kwargs):
    state = bot.toggle_feature('context_history_enabled', "Context History ON", "Context History OFF")
    bot._send_pm(msg_from_id, f"Context History is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()

def handle_toggle_debug_logging(bot, msg_from_id, **kwargs):
    bot.toggle_debug_logging()
    state = bot.debug_logging_enabled
    bot._send_pm(msg_from_id, f"Debug Logging is now {'ON' if state else 'OFF'}.")
    if bot.main_window: bot.main_window.update_feature_list()
