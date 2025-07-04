import time
import sys
import os
from TeamTalk5 import UserRight, TT_STRLEN, ttstr, LOADED_TT_LIB
from utils import format_uptime

from TeamTalk5 import UserRight, TT_STRLEN, ttstr
from utils import format_uptime
from . import ai_commands, poll_commands, communication_commands
from .admin import bot_control, config_management, feature_toggles, user_management, channel_management, ai_instructions

def handle_help(bot, msg_from_id, **kwargs):
    is_admin = bot._is_admin(msg_from_id)
    help_lines = ["""--- Bot Commands (Send via PM) ---"""]

    # Standard User Commands
    help_lines.append("- h: Show this help.")
    help_lines.append("- ping: Check if the bot is responding.")
    help_lines.append("- info: Display bot status and server info.")
    help_lines.append("- whoami: Show your user info.")
    help_lines.append("- rights: Show the bot's permissions.")
    help_lines.append("- cn <new_nick>: Change bot's nickname.")
    help_lines.append("- cs <new_status>: Change bot's status.")
    help_lines.append("- w <location>: Get weather (also /w in channel).")
    help_lines.append("- ct <msg>: Send a message to bot's channel.")
    help_lines.append("- bm <msg>: Send a broadcast message.")
    help_lines.append("- c <q>: Ask Gemini AI via PM.")
    help_lines.append("- /c <q>: Ask Gemini AI in bot's channel.")
    help_lines.append("- poll \"Q\" \"A\" \"B\": Create a poll.")
    help_lines.append("- vote <id> <num>: Vote in a poll.")
    help_lines.append("- results <id>: Show poll results.")

    if is_admin:
        help_lines.append("\n--- Admin Commands ---")
        help_lines.append("- gapi: Set Gemini API key.")
        help_lines.append("- list_gemini_models / lgm: List available Gemini models.")
        help_lines.append("- set_gemini_model <model_name> / sgm <model_name>: Set the active Gemini model.")
        help_lines.append("- addword <word>: Adds a word to the word filter.")
        help_lines.append("- delword <word>: Removes a word from the word filter.")
        help_lines.append("- set_context_retention: Set context history retention.")
        help_lines.append("- jcl: Toggle join/leave announcements.")
        help_lines.append("- tg_chanmsg: Toggle channel messages.")
        help_lines.append("- tg_broadcast: Toggle broadcast messages.")
        help_lines.append("- tg_gemini_pm: Toggle Gemini PM.")
        help_lines.append("- tg_gemini_chan: Toggle Gemini channel messages.")
        help_lines.append("- tgmmode: Toggle welcome message mode.")
        help_lines.append("- tfilter: Toggle filter.")
        help_lines.append("- tg_context_history: Toggle context history.")
        help_lines.append("- tg_debug_logging: Toggle debug logging.")
        help_lines.append("- lock: Lock/unlock bot.")
        help_lines.append("- block / unblock: Block/unblock commands.")
        help_lines.append("- rs: Restart bot.")
        help_lines.append("- q: Quit bot.")
        help_lines.append("- listusers: List all users.")
        help_lines.append("- listchannels: List all channels.")
        help_lines.append("- move: Move user to channel.")
        help_lines.append("- kick: Kick user.")
        help_lines.append("- ban: Ban user.")
        help_lines.append("- unban: Unban user.")
        help_lines.append("- instruct: Set AI system instructions.")
        help_lines.append("- jc: Join channel.")
        help_lines.append("- ct: Send message to bot's channel.")
        help_lines.append("- bm: Send broadcast message.")
    

    bot._send_pm(msg_from_id, "\n".join(help_lines))

def handle_ping(bot, msg_from_id, **kwargs):
    bot._send_pm(msg_from_id, "Pong!")

def handle_info(bot, msg_from_id, **kwargs):
    uptime_str = format_uptime(time.time() - bot._start_time if bot._start_time > 0 else -1)
    
    gemini_status = "ENABLED" if bot.gemini_service.is_enabled() else "DISABLED"
    debug_logging_status = "ENABLED" if bot.config['Bot']['debug_logging_enabled'] else "DISABLED"
    context_history_status = "ENABLED" if bot.config['Bot']['context_history_enabled'] else "DISABLED"
    gemini_api_key_status = "SET" if bot.config['Bot']['gemini_api_key'] else "NOT SET"

    server_name, server_version = "N/A", "N/A"
    try:
        props = bot.getServerProperties()
        if props:
            server_name = ttstr(props.szServerName)
            server_version = ttstr(props.szServerVersion)
    except Exception: pass

    info_lines = [
        f"--- Bot Info ---",
        f"Name: {ttstr(bot.nickname)}",
        f"Uptime: {uptime_str}",
        f"Current Channel: {ttstr(bot.getChannelPath(bot.getMyChannelID())) if bot._in_channel else 'Not in channel'}",
        f"Target Channel: {ttstr(bot.target_channel_path)}",
        f"Locked: {'YES' if bot.bot_locked else 'NO'}",
        f"--- System Info ---",
        f"Operating System: {sys.platform}",
        f"Python Version: {sys.version.split(' ')[0]}",
        f"TeamTalk Library: {LOADED_TT_LIB}",
        f"--- Features ---",
        f"Gemini AI: {gemini_status} (Model: {bot.gemini_service.get_current_model_name()})\n        AI System Instructions: {bot.ai_system_instructions if bot.ai_system_instructions else 'Not set'}",
        f"Announce Join/Leave: {'ON' if bot.announce_join_leave else 'OFF'}",
        f"Allow Channel Messages: {'ON' if bot.allow_channel_messages else 'OFF'}",
        f"Allow Broadcasts: {'ON' if bot.allow_broadcast else 'OFF'}",
        f"Allow Gemini PM: {'ON' if bot.allow_gemini_pm else 'OFF'}",
        f"Allow Gemini Channel: {'ON' if bot.allow_gemini_channel else 'OFF'}",
        f"Welcome Message Mode: {bot.welcome_message_mode.upper()}",
        f"Filter Enabled: {'ON' if bot.filter_enabled else 'OFF'}",
        f"Debug Logging: {debug_logging_status}",
        f"Context History: {context_history_status}",
        f"Gemini API Key: {gemini_api_key_status}",
        f"--- Server Info ---",
        f"Name: {server_name} ({ttstr(bot.host)})",
        f"Version: {server_version}",
    ]
    bot._send_pm(msg_from_id, "\n".join(info_lines))

def handle_whoami(bot, msg_from_id, sender_nick, **kwargs):
    try:
        user = bot.getUser(msg_from_id)
        if not user: raise ValueError("Could not get user info")
        admin_status = "Yes" if bot._is_admin(msg_from_id) else "No"
        bot._send_pm(msg_from_id, f"Nick: {sender_nick}\nID: {user.nUserID}\nUser: {ttstr(user.szUsername)}\nAdmin: {admin_status}")
    except Exception as e:
        bot._send_pm(msg_from_id, f"Error getting your info: {e}")

def handle_rights(bot, msg_from_id, **kwargs):
    rights_map = {v: k for k, v in UserRight.__dict__.items() if k.startswith('USERRIGHT_')}
    output = [f"My Permissions ({bot.my_rights:#010x}):"]
    output.extend(f"- {flag_name.replace('USERRIGHT_', '')}" for flag_val, flag_name in rights_map.items() if bot.my_rights & flag_val)
    bot._send_pm(msg_from_id, "\n".join(output))

def handle_change_nick(bot, msg_from_id, args_str, **kwargs):
    if not args_str: bot._send_pm(msg_from_id, "Usage: cn <new_nickname>"); return
    new_nick = ttstr(args_str)
    if len(new_nick) > TT_STRLEN: bot._send_pm(msg_from_id, "Error: Nickname too long."); return
    bot.doChangeNickname(new_nick)
    bot._send_pm(msg_from_id, f"Nickname change to '{new_nick}' requested.")

def handle_change_status(bot, msg_from_id, args_str, **kwargs):
    new_status = ttstr(args_str)
    if len(new_status) > TT_STRLEN: bot._send_pm(msg_from_id, "Error: Status too long."); return
    bot.doChangeStatus(0, new_status)
    bot._send_pm(msg_from_id, "Status change requested.")

COMMAND_MAP_PM = {
    # User Commands
    "h": handle_help,
    "ping": handle_ping,
    "info": handle_info,
    "whoami": handle_whoami,
    "rights": handle_rights,
    "cn": handle_change_nick,
    "cs": handle_change_status,
    # Communication Commands
    "w": communication_commands.handle_weather,
    # AI Commands
    "c": ai_commands.handle_pm_ai,
    # Poll Commands
    "poll": poll_commands.handle_poll_create,
    "vote": poll_commands.handle_vote,
    "results": poll_commands.handle_results,
    "instruct": ai_instructions.handle_instruct_command,
}

ADMIN_COMMANDS = {
    # Admin - Bot Control
    "lock": bot_control.handle_lock,
    "block": bot_control.handle_block_command,
    "unblock": bot_control.handle_block_command,
    "rs": bot_control.handle_restart,
    "q": bot_control.handle_quit,
    # Admin - Config Management
    "gapi": config_management.handle_set_gapi,
    "list_gemini_models": config_management.handle_list_gemini_models,
    "lgm": config_management.handle_list_gemini_models,
    "set_gemini_model": config_management.handle_set_gemini_model,
    "sgm": config_management.handle_set_gemini_model,
    "addword": config_management.handle_add_word,
    "delword": config_management.handle_del_word,
    "set_context_retention": config_management.handle_set_context_retention,
    # Admin - Feature Toggles
    "jcl": feature_toggles.handle_toggle_jcl,
    "tg_chanmsg": feature_toggles.handle_toggle_chanmsg,
    "tg_broadcast": feature_toggles.handle_toggle_broadcast,
    "tg_gemini_pm": feature_toggles.handle_toggle_gemini_pm,
    "tg_gemini_chan": feature_toggles.handle_toggle_gemini_chan,
    "tgmmode": feature_toggles.handle_toggle_welcome_mode,
    "tfilter": feature_toggles.handle_toggle_filter,
    "tg_context_history": feature_toggles.handle_toggle_context_history,
    "tg_debug_logging": feature_toggles.handle_toggle_debug_logging,
    # Admin - User Management
    "listusers": user_management.handle_list_users,
    "listchannels": user_management.handle_list_channels,
    "move": user_management.handle_move_user,
    "kick": user_management.handle_kick_user,
    "ban": user_management.handle_ban_user,
    "unban": user_management.handle_unban_user,
    "instruct": ai_instructions.handle_instruct_command,
    # Admin - Channel Management
    "jc": channel_management.handle_join_channel,
    "ct": communication_commands.handle_channel_text,
    "bm": communication_commands.handle_broadcast_message,
}

# Combine all commands for easy lookup in command_handler
ALL_COMMANDS = {**COMMAND_MAP_PM, **ADMIN_COMMANDS}