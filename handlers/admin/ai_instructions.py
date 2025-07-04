
import logging
from TeamTalk5 import TextMsgType

def handle_instruct_command(bot, msg_from_id, args_str, channel_id=None, **kwargs):
    if not bot._is_admin(msg_from_id):
        bot._send_pm(msg_from_id, "You are not authorized to use this command.")
        return

    message_type = TextMsgType.MSGTYPE_CHANNEL if channel_id else TextMsgType.MSGTYPE_USER

    if not args_str:
        response = "Usage: instruct <your system instructions here>"
        if message_type == TextMsgType.MSGTYPE_USER:
            bot._send_pm(msg_from_id, response)
        elif message_type == TextMsgType.MSGTYPE_CHANNEL:
            bot._send_channel_message(channel_id, response)
        return

    instructions = args_str.strip()
    bot.set_ai_system_instructions(instructions)

    response = "AI system instructions have been updated and saved."
    if message_type == TextMsgType.MSGTYPE_USER:
        bot._send_pm(msg_from_id, response)
    elif message_type == TextMsgType.MSGTYPE_CHANNEL:
        bot._send_channel_message(channel_id, response)
    logging.info(f"Admin {bot.getUser(msg_from_id).szNickname} updated AI system instructions.")
