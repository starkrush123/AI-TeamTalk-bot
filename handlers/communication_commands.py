
import logging
from TeamTalk5 import ttstr
import TeamTalk5
from datetime import datetime

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

def handle_quote(bot, msg_from_id, channel_id, args_str, msg_type, **kwargs):
    args = args_str.strip().split()
    reply = ""
    
    # Default language and ID
    lang = "en" # Default for random quote
    quote_id = None

    if args:
        first_arg = args[0].lower()
        if first_arg in ["en", "id"]:
            lang = first_arg
            if len(args) > 1 and args[1].isdigit():
                quote_id = int(args[1])
        elif first_arg.isdigit():
            quote_id = int(first_arg)
            lang = "id" # Default to Indonesian if only ID is provided

    if quote_id is not None:
        reply = bot.hariku_service.get_quote_by_id(quote_id, lang)
    else:
        reply = bot.hariku_service.get_random_quote(lang)
    
    if msg_type == TeamTalk5.TextMsgType.MSGTYPE_USER:
        bot._send_pm(msg_from_id, reply)
    else:
        bot._send_channel_message(channel_id, reply)

def handle_event(bot, msg_from_id, channel_id, args_str, msg_type, **kwargs):
    args = args_str.strip().split()
    country_code = "ID" # Default country code
    date_str = None
    reply = ""

    if args:
        # Check if the first argument is a country code (e.g., ID, US)
        if len(args[0]) == 2 and args[0].isalpha():
            country_code = args[0].upper()
            if len(args) > 1:
                date_str = args[1]
        else:
            date_str = args[0]

    if date_str:
        try:
            # Try to parse as YYYY-MM-DD (week)
            datetime.strptime(date_str, '%Y-%m-%d')
            reply = bot.hariku_service.get_events_by_week(country_code, date_str)
        except ValueError:
            try:
                # Try to parse as YYYY-MM (month)
                datetime.strptime(date_str, '%Y-%m')
                reply = bot.hariku_service.get_events_by_month(country_code, date_str)
            except ValueError:
                try:
                    # Try to parse as YYYY (year)
                    datetime.strptime(date_str, '%Y')
                    reply = bot.hariku_service.get_events_by_year(country_code, date_str)
                except ValueError:
                    # If not a date, assume it's a search query
                    reply = bot.hariku_service.search_events(country_code, args_str.strip())
    else:
        # If no date is provided, get today's events
        reply = bot.hariku_service.get_today_events(country_code)

    if msg_type == TeamTalk5.TextMsgType.MSGTYPE_USER:
        bot._send_pm(msg_from_id, reply)
    else:
        bot._send_channel_message(channel_id, reply)
