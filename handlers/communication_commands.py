
import logging
from TeamTalk5 import ttstr
import TeamTalk5

def handle_weather(bot, msg_from_id, channel_id, args_str, msg_type, **kwargs):
    location = args_str.strip()
    if not location:
        reply = "Usage: w <location> OR /w <location>"
    else:
        reply = bot.weather_service.get_weather(location)
    
    if msg_type == TeamTalk5.TextMsgType.MSGTYPE_USER: # PM command
        bot._send_pm(msg_from_id, reply)
    else: # Channel command
        bot._send_channel_message(channel_id, reply)

def handle_channel_text(bot, msg_from_id, sender_nick, args_str, **kwargs):
    if not bot._in_channel:
        bot._send_pm(msg_from_id, "Error: Bot is not in a channel."); return
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: ct <message>"); return

    if bot._send_channel_message(bot._target_channel_id, f"<{sender_nick}> {args_str}"):
        bot._send_pm(msg_from_id, "Message sent to channel.")
    else:
        bot._send_pm(msg_from_id, "Failed to send message (check rights/lock status).")

def handle_broadcast_message(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: bm <message>"); return
    if bot._send_broadcast(ttstr(args_str)):
        bot._send_pm(msg_from_id, "Broadcast sent.")
    else:
        bot._send_pm(msg_from_id, "Failed to send broadcast (check rights/lock status).")
