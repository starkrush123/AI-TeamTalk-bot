
from TeamTalk5 import ttstr

def handle_join_channel(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: jc <channel_path>[|password]"); return

    parts = args_str.split('|', 1)
    chan_path, chan_pass = ttstr(parts[0].strip()), ttstr(parts[1]) if len(parts) > 1 else ttstr("")
    chan_id = bot.getChannelIDFromPath(chan_path)
    
    if chan_id <= 0:
        bot._send_pm(msg_from_id, f"Error: Channel '{chan_path}' not found."); return

    bot.target_channel_path = chan_path
    bot.channel_password = chan_pass
    bot._target_channel_id = chan_id
    
    if bot.doJoinChannelByID(chan_id, chan_pass) == 0:
        bot._send_pm(msg_from_id, f"Error sending join command for '{chan_path}'.")
    else:
        bot._send_pm(msg_from_id, f"Join command sent for '{chan_path}'.")
