
from TeamTalk5 import ttstr, UserRight, BanType, BannedUser

def handle_list_users(bot, msg_from_id, args_str, **kwargs):
    path_str = args_str.strip() or ttstr(bot.target_channel_path)
    chan_id = bot.getChannelIDFromPath(ttstr(path_str)) if path_str else bot._target_channel_id
    if chan_id <= 0: bot._send_pm(msg_from_id, f"Error: Channel not found."); return

    users = sorted(list(bot.getChannelUsers(chan_id) or []), key=lambda u: ttstr(u.szNickname).lower())
    user_list = [f"Users in '{path_str}':"]
    user_list.extend(f"- {ttstr(u.szNickname)} (ID:{u.nUserID}, User:{ttstr(u.szUsername)})" for u in users)
    bot._send_pm(msg_from_id, "\n".join(user_list) if users else f"No users found in '{path_str}'.")

def handle_list_channels(bot, msg_from_id, **kwargs):
    channels = sorted(list(bot.getServerChannels() or []), key=lambda c: ttstr(c.szName).lower())
    chan_list = ["--- Server Channels ---"]
    chan_list.extend(f"- {ttstr(c.szName)} (ID:{c.nChannelID}, Path:{ttstr(bot.getChannelPath(c.nChannelID))})" for c in channels)
    bot._send_pm(msg_from_id, "\n".join(chan_list) if channels else "No channels found.")

def handle_move_user(bot, msg_from_id, args_str, **kwargs):
    if not (bot.my_rights & UserRight.USERRIGHT_MOVE_USERS): bot._send_pm(msg_from_id, "Error: Bot cannot move users."); return
    parts = args_str.split(maxsplit=1)
    if len(parts) < 2: bot._send_pm(msg_from_id, "Usage: move <nick> <channel_path>"); return
    
    nick, chan_path = parts
    user = bot._find_user_by_nick(nick)
    if not user: bot._send_pm(msg_from_id, f"Error: User '{nick}' not found."); return
    chan_id = bot.getChannelIDFromPath(ttstr(chan_path))
    if chan_id <= 0: bot._send_pm(msg_from_id, f"Error: Channel '{chan_path}' not found."); return

    bot.doMoveUser(user.nUserID, chan_id)
    bot._send_pm(msg_from_id, f"Move command sent for '{nick}'.")

def handle_kick_user(bot, msg_from_id, args_str, **kwargs):
    if not (bot.my_rights & UserRight.USERRIGHT_KICK_USERS): bot._send_pm(msg_from_id, "Error: Bot cannot kick users."); return
    if not bot._in_channel: bot._send_pm(msg_from_id, "Error: Bot not in a channel to kick from."); return
    
    nick = args_str.strip()
    user = next((u for u in bot.getChannelUsers(bot._target_channel_id) or [] if ttstr(u.szNickname).lower() == nick.lower()), None)
    if not user: bot._send_pm(msg_from_id, f"Error: User '{nick}' not in my channel."); return

    bot.doKickUser(user.nUserID, bot._target_channel_id)
    bot._send_pm(msg_from_id, f"Kick command sent for '{nick}'.")

def handle_ban_user(bot, msg_from_id, args_str, **kwargs):
    if not (bot.my_rights & UserRight.USERRIGHT_BAN_USERS): bot._send_pm(msg_from_id, "Error: Bot cannot ban users."); return
    
    nick = args_str.strip()
    user = bot._find_user_by_nick(nick)
    if not user: bot._send_pm(msg_from_id, f"Error: User '{nick}' not found."); return

    bot.doBanUserEx(user.nUserID, BanType.BANTYPE_USERNAME)
    bot._send_pm(msg_from_id, f"Ban command sent for user '{ttstr(user.szUsername)}'.")

def handle_unban_user(bot, msg_from_id, args_str, **kwargs):
    if not (bot.my_rights & UserRight.USERRIGHT_BAN_USERS): bot._send_pm(msg_from_id, "Error: Bot cannot unban users."); return
    
    username = args_str.strip()
    if not username: bot._send_pm(msg_from_id, "Usage: unban <username>"); return
    
    ban_entry = BannedUser(); ban_entry.szUsername = ttstr(username); ban_entry.uBanTypes = BanType.BANTYPE_USERNAME
    bot.doUnBanUserEx(ban_entry)
    bot._send_pm(msg_from_id, f"Unban command sent for user '{username}'.")

def handle_list_admins(bot, msg_from_id, **kwargs):
    configured_admins = set(bot.admin_usernames_config)
    online_users = bot.getServerUsers() or []
    online_usernames = {ttstr(u.szUsername).lower() for u in online_users}
    online_nicknames = {ttstr(u.szNickname).lower(): ttstr(u.szUsername).lower() for u in online_users}

    admin_status_messages = ["--- Admin Status ---"]

    # Check configured admins
    for admin_username in sorted(list(configured_admins)):
        status = "Offline"
        if admin_username in online_usernames:
            status = "Online"
        admin_status_messages.append(f"- {admin_username} (Configured): {status}")
    
    # Check if any online user is an admin by nickname but not by username (less reliable)
    for online_nick, online_user in online_nicknames.items():
        if online_user not in configured_admins and online_nick in configured_admins:
             admin_status_messages.append(f"- {online_nick} (Online by Nick, not Configured by User): Online")

    if not configured_admins:
        admin_status_messages.append("No admin usernames configured in bot settings.")

    bot._send_pm(msg_from_id, "\n".join(admin_status_messages))
