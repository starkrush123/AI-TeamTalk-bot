
import wx

class MainBotWindow(wx.Frame):
    def __init__(self, parent, title, controller):
        super(MainBotWindow, self).__init__(parent, title=title, size=(850, 550))
        self.controller = controller
        self.feature_map = {}

        panel = wx.Panel(self)
        main_hbox = wx.BoxSizer(wx.HORIZONTAL)

        log_vbox = wx.BoxSizer(wx.VERTICAL)
        log_vbox.Add(wx.StaticText(panel, label="Bot Log:"), 0, wx.LEFT | wx.TOP, 5)
        self.logDisplay = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        log_vbox.Add(self.logDisplay, 1, wx.EXPAND | wx.ALL, 5)
        main_hbox.Add(log_vbox, 1, wx.EXPAND)

        features_vbox = wx.BoxSizer(wx.VERTICAL)
        features_vbox.Add(wx.StaticText(panel, label="Bot Features (Double-click to toggle):"), 0, wx.LEFT | wx.TOP, 5)
        self.feature_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VRULES)
        self.feature_list.InsertColumn(0, "Feature", width=200)
        self.feature_list.InsertColumn(1, "Status", width=100)
        features_vbox.Add(self.feature_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.context_retention_label = wx.StaticText(panel, label="Context Retention: N/A")
        features_vbox.Add(self.context_retention_label, 0, wx.LEFT | wx.BOTTOM, 5)
        
        features_vbox.Add(wx.StaticText(panel, label="Channel Message:"), 0, wx.LEFT | wx.TOP, 5)
        self.channel_msg_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.send_channel_msg_btn = wx.Button(panel, label="Send Channel Msg")
        controls_hbox = wx.BoxSizer(wx.HORIZONTAL)
        controls_hbox.Add(self.channel_msg_input, 1, wx.RIGHT, 5)
        controls_hbox.Add(self.send_channel_msg_btn, 0)
        features_vbox.Add(controls_hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        features_vbox.Add(wx.StaticText(panel, label="Broadcast Message:"), 0, wx.LEFT | wx.TOP, 5)
        self.broadcast_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.send_broadcast_btn = wx.Button(panel, label="Send Broadcast")
        controls_hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        controls_hbox2.Add(self.broadcast_input, 1, wx.RIGHT, 5)
        controls_hbox2.Add(self.send_broadcast_btn, 0)
        features_vbox.Add(controls_hbox2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        main_hbox.Add(features_vbox, 1, wx.EXPAND)

        bottom_vbox = wx.BoxSizer(wx.VERTICAL)
        bottom_vbox.Add(main_hbox, 1, wx.EXPAND | wx.ALL, 5)
        self.btnDisconnect = wx.Button(panel, label="Disconnect and Exit")
        bottom_vbox.Add(self.btnDisconnect, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.TOP, 10)
        panel.SetSizer(bottom_vbox)

        self.btnDisconnect.Bind(wx.EVT_BUTTON, self.OnDisconnect)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.feature_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnFeatureToggle)
        self.send_channel_msg_btn.Bind(wx.EVT_BUTTON, self.OnSendChannelMessage)
        self.channel_msg_input.Bind(wx.EVT_TEXT_ENTER, self.OnSendChannelMessage)
        self.send_broadcast_btn.Bind(wx.EVT_BUTTON, self.OnSendBroadcast)
        self.broadcast_input.Bind(wx.EVT_TEXT_ENTER, self.OnSendBroadcast)
        
        self.Center()

    def log_message(self, message):
        if self.logDisplay:
            wx.CallAfter(self.logDisplay.AppendText, message + "\n")

    def update_feature_list(self):
        wx.CallAfter(self._update_feature_list_internal)

    def _update_feature_list_internal(self):
        if not self.feature_list: return
        current_bot = self.controller.bot_instance
        self.feature_list.DeleteAllItems()
        self.feature_map.clear()
        
        is_bot_running = current_bot is not None
        self.channel_msg_input.Enable(is_bot_running)
        self.send_channel_msg_btn.Enable(is_bot_running)
        self.broadcast_input.Enable(is_bot_running)
        self.send_broadcast_btn.Enable(is_bot_running)

        if not is_bot_running: return

        features = {
            "announce_join_leave": "Join/Leave Announce", "allow_channel_messages": "Channel Messages",
            "allow_broadcast": "Broadcast Messages", "allow_gemini_pm": "Gemini AI (PM)",
            "allow_gemini_channel": "Gemini AI (Channel /c)", "filter_enabled": "Word Filter",
            "bot_locked": "Bot Locked", "context_history_enabled": "Context History",
            "debug_logging_enabled": "Debug Logging"
        }

        for idx, (key, name) in enumerate(features.items()):
            status_str = "ON" if getattr(current_bot, key, False) else "OFF"
            self.feature_list.InsertItem(idx, name)
            self.feature_list.SetItem(idx, 1, status_str)
            self.feature_map[idx] = key
        
        # Add context history retention minutes display
        self.context_retention_label.SetLabel(f"Context Retention: {current_bot.context_history_manager.retention_minutes} min")

    def OnFeatureToggle(self, event):
        idx = event.GetIndex()
        feature_key = self.feature_map.get(idx)
        current_bot = self.controller.bot_instance
        if not current_bot or not feature_key: return

        self.log_message(f"[GUI Action] Toggling feature: {feature_key}")
        toggle_method_name = f"toggle_{feature_key}"
        toggle_method = getattr(current_bot, toggle_method_name, None)

        if callable(toggle_method):
            toggle_method()
            self.update_feature_list()
        else:
            self.log_message(f"[GUI Error] Unknown toggle method '{toggle_method_name}'")

    def OnSendChannelMessage(self, event):
        current_bot = self.controller.bot_instance
        message = self.channel_msg_input.GetValue().strip()
        if not current_bot or not message: return

        if not current_bot._in_channel or current_bot._target_channel_id <= 0:
             self.log_message("[GUI Error] Cannot send: Bot is not in a channel."); return
        
        self.log_message(f"[GUI Send Chan] {message}")
        if current_bot._send_channel_message(current_bot._target_channel_id, f"{message}"):
            self.channel_msg_input.SetValue("")
        else:
            self.log_message("[GUI Error] Failed to send channel message.")

    def OnSendBroadcast(self, event):
        current_bot = self.controller.bot_instance
        message = self.broadcast_input.GetValue().strip()
        if not current_bot or not message: return
        
        self.log_message(f"[GUI Send Broadcast] {message}")
        if current_bot._send_broadcast(f"{message}"):
            self.broadcast_input.SetValue("")
        else:
            self.log_message("[GUI Error] Failed to send broadcast.")
    
    def OnDisconnect(self, event):
        self.log_message("Disconnect button clicked. Stopping bot...")
        self.controller.shutdown()
        self.Close()

    def OnCloseWindow(self, event):
        self.log_message("Main window closing. Stopping bot...")
        self.controller.shutdown()
        self.Destroy()

