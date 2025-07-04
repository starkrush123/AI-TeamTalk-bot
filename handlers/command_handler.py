import logging
import re
from TeamTalk5 import TextMsgType, ttstr, UserRight

from . import user_commands, ai_commands, poll_commands, communication_commands
from .admin import bot_control, config_management, feature_toggles, user_management, channel_management, ai_instructions

COMMAND_MAP_PM = user_commands.COMMAND_MAP_PM
ADMIN_COMMANDS = user_commands.ADMIN_COMMANDS

COMMAND_MAP_CHANNEL = {
    "h": user_commands.handle_help,
    "w": communication_commands.handle_weather,
    "c": ai_commands.handle_channel_ai,
    "poll": poll_commands.handle_poll_create,
    "vote": poll_commands.handle_vote,
    "results": poll_commands.handle_results,
    "instruct": ai_instructions.handle_instruct_command,
}

def handle_message(bot, textmessage, full_message_text):
    msg_from_id = textmessage.nFromUserID
    msg_type = textmessage.nMsgType
    msg_channel_id = textmessage.nChannelID
    
    sender_nick = f"UserID_{msg_from_id}"
    try:
        sender_user = bot.getUser(msg_from_id)
        if sender_user and sender_user.nUserID == msg_from_id:
            sender_nick = ttstr(sender_user.szNickname)
    except Exception: pass

    log_and_process(bot, msg_type, msg_from_id, msg_channel_id, sender_nick, full_message_text)

def log_and_process(bot, msg_type, msg_from_id, msg_channel_id, sender_nick, full_message_text):
    process_commands = False
    
    if msg_type == TextMsgType.MSGTYPE_CHANNEL:
        if bot._in_channel: # Process if bot is in *any* channel
            process_commands = True
    elif msg_type == TextMsgType.MSGTYPE_USER:
        process_commands = True
    else: return

    if not process_commands: return
    
    if msg_type == TextMsgType.MSGTYPE_CHANNEL and check_word_filter(bot, msg_from_id, msg_channel_id, sender_nick, full_message_text):
        return

    parts = full_message_text.strip().split(maxsplit=1)
    command_word = parts[0].lower() if parts else ""
    args_str = parts[1] if len(parts) > 1 else ""

    # For channel messages, remove leading '/' if present
    if msg_type == TextMsgType.MSGTYPE_CHANNEL and command_word.startswith('/'):
        command_word = command_word[1:]

    if not command_word: return
    
    if bot.bot_locked and command_word not in bot.UNBLOCKABLE_COMMANDS:
        if msg_type == TextMsgType.MSGTYPE_USER: bot._send_pm(msg_from_id, f"Command ignored; bot is locked."); return
    if command_word in bot.blocked_commands and command_word not in ['block', 'unblock']:
        if msg_type == TextMsgType.MSGTYPE_USER: bot._send_pm(msg_from_id, f"Command '{command_word}' is blocked."); return

    handler_func = None
    if msg_type == TextMsgType.MSGTYPE_USER:
        handler_func = user_commands.ALL_COMMANDS.get(command_word)
    elif msg_type == TextMsgType.MSGTYPE_CHANNEL:
        handler_func = COMMAND_MAP_CHANNEL.get(command_word)

    if handler_func:
        if command_word in ADMIN_COMMANDS and not bot._is_admin(msg_from_id):
            bot._send_pm(msg_from_id, f"Error: You are not authorized to use '{command_word}'.")
            logging.warning(f"Unauthorized admin command '{command_word}' by {sender_nick}.")
            return
        
        try:
            handler_func(bot=bot, msg_from_id=msg_from_id, args_str=args_str, channel_id=msg_channel_id, sender_nick=sender_nick, command=command_word, msg_type=msg_type)
        except Exception as e:
            logging.error(f"Error executing command '{command_word}': {e}", exc_info=True)
            bot._send_pm(msg_from_id, f"An unexpected error occurred executing '{command_word}'.")

def check_word_filter(bot, user_id, channel_id, user_nick, message):
    if not bot.filter_enabled or not bot.filtered_words: return False
    
    msg_lower = message.lower()
    found_bad_word = next((word for word in bot.filtered_words if re.search(r'\b' + re.escape(word) + r'\b', msg_lower, re.IGNORECASE)), None)
    
    if found_bad_word:
        bot.warning_counts[user_id] = bot.warning_counts.get(user_id, 0) + 1
        warning_msg = f"Warning {bot.warning_counts[user_id]}/3 for {user_nick}: Please avoid inappropriate language."
        bot._send_channel_message(channel_id, warning_msg)

        if bot.warning_counts[user_id] >= 3:
            if bot.my_rights & UserRight.USERRIGHT_KICK_USERS:
                bot.doKickUser(user_id, channel_id)
                bot._send_channel_message(channel_id, f"User {user_nick} kicked after 3 warnings.")
            else:
                bot._send_channel_message(channel_id, f"{user_nick} has 3 warnings, but bot cannot kick.")
            bot.warning_counts[user_id] = 0
        return True
    return False