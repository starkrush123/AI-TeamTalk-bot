
import sys, time, random, re, wx
import logging # Re-add logging import for constants
from TeamTalk5 import (
    TeamTalk, TeamTalkError, TextMsgType, UserRight, TT_STRLEN,
    ttstr, buildTextMessage, ClientError, ClientFlags
)
from config_manager import save_config
from handlers import command_handler
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from context_history_manager import ContextHistoryManager
from logger_config import bot_logger # Import the named logger


class MyTeamTalkBot(TeamTalk):
    def __init__(self, config_dict, controller=None):
        super().__init__()
        self.logger = bot_logger # Use the named logger
        self.config = config_dict
        self.controller = controller
        conn_conf, bot_conf = self.config.get('Connection', {}), self.config.get('Bot', {})

        self.host, self.tcp_port = ttstr(conn_conf.get('host')), int(conn_conf.get('port'))
        self.udp_port, self.nickname = self.tcp_port, ttstr(conn_conf.get('nickname'))
        self.status_message, self.username = ttstr(bot_conf.get('status_message')), ttstr(conn_conf.get('username'))
        self.password, self.target_channel_path = ttstr(conn_conf.get('password')), ttstr(conn_conf.get('channel'))
        self.channel_password, self.client_name = ttstr(conn_conf.get('channel_password')), ttstr(bot_conf.get('client_name'))

        self.reconnect_delay_min = int(bot_conf.get('reconnect_delay_min'))
        self.reconnect_delay_max = int(bot_conf.get('reconnect_delay_max'))

        self.filtered_words = {w.strip().lower() for w in bot_conf.get('filtered_words','').split(',') if w.strip()}
        self.admin_usernames_config = [n.strip().lower() for n in bot_conf.get('admin_usernames','').split(',') if n.strip()]

        self._logged_in = self._in_channel = self._running = self._intentional_stop = self.bot_locked = False
        self._my_user_id = self._target_channel_id = self._join_cmd_id = -1
        self._start_time = 0; self.my_rights = UserRight.USERRIGHT_NONE
        self.admin_user_ids, self.blocked_commands = set(), set()
        self._all_users_cache = [] # Cache for all users
        self._text_message_buffer, self.polls, self.warning_counts = {}, {}, {}
        self.next_poll_id = 1; self.main_window = None

        self.announce_join_leave = self.allow_channel_messages = self.allow_broadcast = True
        self.allow_gemini_pm = self.allow_gemini_channel = True
        self.welcome_message_mode, self.filter_enabled = "template", bool(self.filtered_words)
        self.UNBLOCKABLE_COMMANDS = {'h','q','rs','block','unblock','info','whoami','rights','lock','tfilter','tgmmode'}

        self.context_history_enabled = bot_conf.get('context_history_enabled', True)
        self.debug_logging_enabled = bot_conf.get('debug_logging_enabled', False) # New attribute for debug logging
        self.ai_system_instructions = bot_conf.get('ai_system_instructions', '') # New attribute for AI system instructions
        self.welcome_message_instructions = bot_conf.get('welcome_message_instructions', '') # New attribute for welcome message instructions
        self.gemini_service = GeminiService(
            api_key=bot_conf.get('gemini_api_key'),
            context_history_enabled=self.context_history_enabled,
            model_name=bot_conf.get('gemini_model_name', 'gemini-1.5-flash-latest'),
            system_instructions=self.ai_system_instructions,
            welcome_instructions=self.welcome_message_instructions
        )
        self.weather_service = WeatherService(bot_conf.get('weather_api_key'))
        self.context_history_manager = ContextHistoryManager(
            retention_minutes=bot_conf.get('context_history_retention_minutes', 60),
            max_messages=bot_conf.get('context_history_max_messages', 20)
        )
        if not self.gemini_service.is_enabled(): self.allow_gemini_pm = self.allow_gemini_channel = False
        self._apply_debug_logging_setting() # Apply initial setting

    def set_gemini_model(self, new_model_name):
        self._log_to_gui(f"Attempting to set Gemini model to: {new_model_name}")
        self.gemini_service.init_model(new_model_name)
        if self.gemini_service.is_enabled() and self.gemini_service.get_current_model_name() == new_model_name:
            self.config['Bot']['gemini_model_name'] = new_model_name
            self._save_runtime_config()
            self._log_to_gui(f"Gemini model successfully set to {new_model_name}.")
            return True
        else:
            self._log_to_gui(f"Failed to set Gemini model to {new_model_name}. Current model: {self.gemini_service.get_current_model_name()}")
            return False

    def set_ai_system_instructions(self, instructions):
        self.ai_system_instructions = instructions
        self.config['Bot']['ai_system_instructions'] = instructions
        self._save_runtime_config()
        self.gemini_service.set_system_instructions(instructions)
        return True

    def set_welcome_message_instructions(self, instructions):
        self.welcome_message_instructions = instructions
        self.config['Bot']['welcome_message_instructions'] = instructions
        self._save_runtime_config()
        self.gemini_service.set_welcome_instructions(instructions)
        return True

    def set_main_window(self, window): self.main_window = window; self._log_to_gui("GUI window linked.")
    def _log_to_gui(self, msg):
        if self.main_window and hasattr(wx, 'CallAfter'):
            wx.CallAfter(self.main_window.log_message, msg)
        else:
            # When in non-GUI mode, just log to the standard logger
            self.logger.info(f"[Bot] {msg}")
    def _send_pm(self, to_id, msg): self._send_text_message(msg, TextMsgType.MSGTYPE_USER, nToUserID=to_id)
    def _send_channel_message(self, chan_id, msg): return self._send_text_message(msg, TextMsgType.MSGTYPE_CHANNEL, nChannelID=chan_id)
    def _send_broadcast(self, msg): return self._send_text_message(msg, TextMsgType.MSGTYPE_BROADCAST)

    def _send_text_message(self, message, msg_type, **kwargs):
        if not message: return False
        is_chan = msg_type == TextMsgType.MSGTYPE_CHANNEL
        if (is_chan and (self.bot_locked or not self.allow_channel_messages)) or \
           (msg_type == TextMsgType.MSGTYPE_BROADCAST and (self.bot_locked or not self.allow_broadcast)):
            return False
        
        # Determine recipient for context history
        user_id = None
        if msg_type == TextMsgType.MSGTYPE_USER and 'nToUserID' in kwargs:
            user_id = str(kwargs['nToUserID'])
        elif msg_type == TextMsgType.MSGTYPE_CHANNEL and 'nChannelID' in kwargs:
            user_id = str(kwargs['nChannelID'])

        # Split the message into chunks that fit within TeamTalk's message length limit
        # TeamTalk's buildTextMessage also splits, but this pre-splitting handles very long messages more robustly
        message_chunks = self._split_message(message, max_len=TT_STRLEN - 1) # Use TT_STRLEN from TeamTalk5

        for chunk in message_chunks:
            # buildTextMessage returns an iterable of textmessage objects
            for msg_part_obj in buildTextMessage(ttstr(chunk), msg_type, **kwargs):
                if self.doTextMessage(msg_part_obj) == 0: # doTextMessage expects a textmessage object
                    self._log_to_gui(f"[Error] Failed to send message part.");
                    return False

        if user_id:
            self.context_history_manager.add_message(user_id, message, self.nickname, is_bot=True)
        return True

    def _split_message(self, message, max_len=512):
        """Splits a message into chunks no longer than max_len."""
        if not message: return []
        if len(message) <= max_len: return [message]

        chunks = []
        current_chunk = ""
        words = message.split(' ')
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= max_len:
                if current_chunk: current_chunk += ' '
                current_chunk += word
            else:
                chunks.append(current_chunk)
                current_chunk = word
        if current_chunk: chunks.append(current_chunk)
        return chunks

    def _update_admin_ids(self):
        all_users = self.getServerUsers() or []
        self._all_users_cache = all_users # Update the cache
        self.admin_user_ids = {u.nUserID for u in all_users if ttstr(u.szUsername).lower() in self.admin_usernames_config}
        if ttstr(self.username).lower() in self.admin_usernames_config: self.admin_user_ids.add(self._my_user_id)
        self._log_to_gui(f"Resolved Admin IDs: {self.admin_user_ids or 'None'}")

    def _is_admin(self, user_id): return user_id in self.admin_user_ids
    def _find_user_by_nick(self, nick):
        target_nick = ttstr(nick).lower()
        try:
            return next((u for u in self.getServerUsers() if ttstr(u.szNickname).lower() == target_nick), None)
        except TeamTalkError as e:
            if e.errnum != ClientError.CMDERR_NOT_LOGGEDIN: self.logger.error(f"SDK error in _find_user_by_nick: {e}"); return None
    def _save_runtime_config(self, save_gemini_key=False):
        self._log_to_gui("Saving runtime config..."); self.config['Bot']['filtered_words'] = ','.join(sorted(list(self.filtered_words)))
        self.config['Connection']['nickname'] = ttstr(self.nickname); self.config['Bot']['status_message'] = ttstr(self.status_message)
        if save_gemini_key: self.config['Bot']['gemini_api_key'] = self.gemini_service.api_key
        save_config(self.config)
    def _mark_stopped_intentionally(self): self._intentional_stop = True

    def stop(self):
        if not self._running: return
        self._log_to_gui("Stop requested."); self._running = False; time.sleep(0.1)
        try:
            if self.getFlags() & ClientFlags.CLIENT_CONNECTED:
                if self._logged_in: self.doLogout()
                self.disconnect()
        except TeamTalkError: pass
        finally: self.closeTeamTalk(); self._tt = None

    def start(self):
        self._log_to_gui(f"Initializing bot session..."); self._start_time = time.time()
        self._intentional_stop = False; self._running = True
        try:
            if not self.connect(self.host, self.tcp_port, self.udp_port): self._running = False; return
            self._log_to_gui("Connection started. Entering event loop.")
            while self._running: self.runEventLoop(100)
        except TeamTalkError as e: self._log_to_gui(f"[SDK Critical] Connection error: {e.errmsg}"); self._running = False
        finally: self.stop()

    def _initiate_restart(self):
        self._log_to_gui("--- BOT RESTART SEQUENCE INITIATED ---")
        if self.controller:
            self.controller.request_restart()
        else:
            self._log_to_gui("[CRITICAL] No controller found! Cannot restart.")

    def onConnectSuccess(self): self._log_to_gui("Connected. Logging in..."); self.doLogin(self.nickname, self.username, self.password, self.client_name)
    def onConnectFailed(self): self._log_to_gui("[Error] Connection failed."); self._handle_reconnect()
    def onConnectionLost(self): self._log_to_gui("[Error] Connection lost."); self._logged_in = self._in_channel = False; self._handle_reconnect()
    def _handle_reconnect(self):
        if self._running and not self._intentional_stop:
            delay = random.randint(self.reconnect_delay_min, self.reconnect_delay_max)
            self._log_to_gui(f"Reconnecting in {delay}s..."); time.sleep(delay)
            if self._running and not self._intentional_stop:
                self._initiate_restart()

    def onCmdError(self, cmd_id, err):
        self._log_to_gui(f"[Cmd Error {cmd_id}] {err.nErrorNo} - {ttstr(err.szErrorMsg)}")
        if err.nErrorNo in [ClientError.CMDERR_INVALID_ACCOUNT, ClientError.CMDERR_SERVER_BANNED]: self._mark_stopped_intentionally()

    def onCmdMyselfLoggedIn(self, user_id, user_acc):
        self._logged_in, self._my_user_id, self.my_rights = True, user_id, user_acc.uUserRights
        self._log_to_gui(f"Login success! My ID: {user_id}, Rights: {self.my_rights:#010x}")
        if self.main_window: wx.CallAfter(self.main_window.Show); wx.CallAfter(self.main_window.SetTitle, f"Bot - {ttstr(self.nickname)}"); wx.CallAfter(self.main_window.update_feature_list)
        if self.status_message: self.doChangeStatus(0, self.status_message)
        self._update_admin_ids()
        chan_id = self.getChannelIDFromPath(self.target_channel_path) or self.getRootChannelID()
        if chan_id > 0: self._target_channel_id = chan_id; self._join_cmd_id = self.doJoinChannelByID(chan_id, self.channel_password)
    
    def onCmdMyselfLoggedOut(self): self._log_to_gui("Logged out."); self._logged_in = False
    
    def onCmdUserJoinedChannel(self, user):
        if user.nUserID == self._my_user_id: self._in_channel = True; self._log_to_gui(f"Joined channel ID: {user.nChannelID}")
        else:
            self._update_admin_ids() # Update admin IDs when a user joins
            if self.announce_join_leave and user.nChannelID == self.getMyChannelID():
                welcome_msg = self.gemini_service.generate_welcome_message(ttstr(user.szNickname)) if self.welcome_message_mode == "gemini" and self.gemini_service.is_enabled() else f"Welcome, {ttstr(user.szNickname)}!"
                self._send_channel_message(user.nChannelID, welcome_msg)
    
    def onCmdUserLeftChannel(self, chan_id, user):
        if user.nUserID == self._my_user_id: self._in_channel = False; self._log_to_gui("Left channel.")
    
    def onCmdUserTextMessage(self, textmessage):
        if textmessage.nFromUserID == self._my_user_id or not self._logged_in: return
        key = (textmessage.nFromUserID, textmessage.nMsgType, textmessage.nChannelID)
        self._text_message_buffer[key] = self._text_message_buffer.get(key, "") + ttstr(textmessage.szMessage)
        if textmessage.bMore: return
        full_msg = self._text_message_buffer.pop(key, "")
        if not full_msg: return
        
        # Add incoming message to context history
        if textmessage.nMsgType == TextMsgType.MSGTYPE_USER:
            sender_nick = ttstr(self.getUser(textmessage.nFromUserID).szNickname)
            self.context_history_manager.add_message(str(textmessage.nFromUserID), full_msg, sender_nick, is_bot=False)

        log_prefix = ""
        if textmessage.nMsgType == TextMsgType.MSGTYPE_CHANNEL: log_prefix=f"[{ttstr(self.getChannelPath(textmessage.nChannelID))}]"
        elif textmessage.nMsgType == TextMsgType.MSGTYPE_USER: log_prefix="[PM]"
        self._log_to_gui(f"{log_prefix} <{ttstr(self.getUser(textmessage.nFromUserID).szNickname)}> {full_msg}")
        
        command_handler.handle_message(self, textmessage, full_msg)

    def onCmdUserUpdate(self, user):
        if user and user.nUserID == self._my_user_id:
            if ttstr(user.szNickname) != self.nickname or ttstr(user.szStatusMsg) != self.status_message:
                self.nickname = ttstr(user.szNickname); self.status_message = ttstr(user.szStatusMsg)
                self._log_to_gui(f"My info updated: Nick='{self.nickname}', Status='{self.status_message}'")
                self._save_runtime_config()
        self._update_admin_ids() # Update admin IDs when a user updates

    def toggle_feature(self, attr_name, on_msg, off_msg):
        setattr(self, attr_name, not getattr(self, attr_name))
        new_state = getattr(self, attr_name)
        self._log_to_gui(f"[Toggle] {on_msg if new_state else off_msg}")
        return new_state
    def toggle_announce_join_leave(self): self.toggle_feature('announce_join_leave', "JCL ON", "JCL OFF")
    def toggle_allow_channel_messages(self): self.toggle_feature('allow_channel_messages', "Chan Msgs ON", "Chan Msgs OFF")
    def toggle_allow_broadcast(self): self.toggle_feature('allow_broadcast', "Broadcasts ON", "Broadcasts OFF")
    def toggle_allow_gemini_pm(self): self.toggle_feature('allow_gemini_pm', "Gemini PM ON", "Gemini PM OFF")
    def toggle_allow_gemini_channel(self): self.toggle_feature('allow_gemini_channel', "Gemini Chan ON", "Gemini Chan OFF")
    def toggle_bot_lock(self): self.toggle_feature('bot_locked', "Bot Lock ON", "Bot Lock OFF")
    def toggle_filter_enabled(self):
        if not self.filter_enabled and not self.filtered_words:
            self._log_to_gui("[Warn] Cannot enable filter: no words defined."); return
        self.toggle_feature('filter_enabled', "Filter ON", "Filter OFF")

    def toggle_context_history_enabled(self):
        self.toggle_feature('context_history_enabled', "Context History ON", "Context History OFF")

    def _apply_debug_logging_setting(self):
        if self.debug_logging_enabled:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Debug logging is now ON.")
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.info("Debug logging is now OFF.")

    def toggle_debug_logging(self):
        self.debug_logging_enabled = not self.debug_logging_enabled
        self._apply_debug_logging_setting()
        self.config['Bot']['debug_logging_enabled'] = str(self.debug_logging_enabled)
        self._save_runtime_config()
