
import wx
import webbrowser

class ConfigDialog(wx.Dialog):
    def __init__(self, parent, title, defaults):
        super(ConfigDialog, self).__init__(parent, title=title, size=(550, 460))

        self.config_data = defaults.copy()
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(5, 5)

        labels = [
            "Server Host:", "Server Port:", "Bot Username:", "Bot Password:",
            "Bot Nickname:", "Initial Status Msg:", "Admin Usernames (comma-sep):",
            "Gemini API Key:", "Weather API Key (OpenWeatherMap):", "Hariku API Key:", "Reconnect Delay (min/max sec):",
            "Context History Retention (minutes):",
            "Enable Debug Logging:"
        ]
        
        self.controls = {}

        key_map = {
            "server host:": "host", "server port:": "port", "bot username:": "username", "bot password:": "password",
            "bot nickname:": "nickname", "initial status msg:": "status_message",
            "admin usernames (comma-sep):": "admin_usernames", "gemini api key:": "gemini_api_key",
            "weather api key (openweathermap)": "weather_api_key",
            "hariku api key:": "hariku_api_key"
        }

        for i, label_text in enumerate(labels):
            if label_text == "Enable Debug Logging:":
                ctrl = wx.CheckBox(panel, label="Enable Debug Logging")
                ctrl.SetValue(defaults.get('debug_logging_enabled', False))
                self.controls['debug_logging_enabled'] = ctrl
                grid.Add(ctrl, pos=(i, 0), span=(1, 2), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)
            else:
                lbl = wx.StaticText(panel, label=label_text)
                grid.Add(lbl, pos=(i, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)

                if "Password" in label_text or "API Key" in label_text:
                    ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
                    key = key_map.get(label_text.lower())
                    if key:
                        ctrl.SetValue(str(defaults.get(key, '')))
                        self.controls[key] = ctrl
                    grid.Add(ctrl, pos=(i, 1), span=(1, 3), flag=wx.EXPAND | wx.RIGHT, border=10)
                elif "Context History Retention" in label_text:
                    ctrl = wx.SpinCtrl(panel, min=0, max=99999, initial=defaults.get('context_history_retention_minutes', 60))
                    self.controls['context_history_retention_minutes'] = ctrl
                    grid.Add(ctrl, pos=(i, 1), span=(1, 3), flag=wx.EXPAND | wx.RIGHT, border=10)
                elif "Reconnect" in label_text:
                    delay_hbox = wx.BoxSizer(wx.HORIZONTAL)
                    self.controls['reconnect_delay_min'] = wx.TextCtrl(panel, value=str(defaults.get('reconnect_delay_min', '5')), size=(50,-1))
                    delay_hbox.Add(self.controls['reconnect_delay_min'], 0, wx.RIGHT, 5)
                    delay_hbox.Add(wx.StaticText(panel, label="/"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
                    self.controls['reconnect_delay_max'] = wx.TextCtrl(panel, value=str(defaults.get('reconnect_delay_max', '15')), size=(50,-1))
                    delay_hbox.Add(self.controls['reconnect_delay_max'], 0)
                    grid.Add(delay_hbox, pos=(i, 1), flag=wx.LEFT, border=0)
                else: # This is for regular TextCtrls
                    ctrl = wx.TextCtrl(panel)
                    key = key_map.get(label_text.lower())
                    if key:
                        ctrl.SetValue(str(defaults.get(key, '')))
                        self.controls[key] = ctrl
                    grid.Add(ctrl, pos=(i, 1), span=(1, 3), flag=wx.EXPAND | wx.RIGHT, border=10)

        grid.AddGrowableCol(1)
        vbox.Add(grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add((-1, 15))

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.btnGetKey = wx.Button(panel, label="Get Gemini API Key")
        self.btnSave = wx.Button(panel, label="Save and Connect", id=wx.ID_OK)
        self.btnCancel = wx.Button(panel, label="Cancel", id=wx.ID_CANCEL)
        self.btnSave.SetDefault()

        hbox3.Add(self.btnGetKey)
        hbox3.AddStretchSpacer()
        hbox3.Add(self.btnCancel, flag=wx.RIGHT, border=5)
        hbox3.Add(self.btnSave)
        vbox.Add(hbox3, flag=wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)

        self.btnGetKey.Bind(wx.EVT_BUTTON, self.OnGetApiKey)
        self.btnSave.Bind(wx.EVT_BUTTON, self.OnSave)
        self.Bind(wx.EVT_CLOSE, lambda evt: self.EndModal(wx.ID_CANCEL))
        self.CenterOnParent()

    def OnGetApiKey(self, event):
        webbrowser.open("[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)")

    def OnSave(self, event):
        try:
            port = int(self.controls['port'].GetValue().strip())
            if not (0 < port < 65536): raise ValueError("Port out of range")
            delay_min = int(self.controls['reconnect_delay_min'].GetValue().strip())
            delay_max = int(self.controls['reconnect_delay_max'].GetValue().strip())
            if delay_min < 0 or delay_max < 0 or delay_min > delay_max: raise ValueError("Invalid reconnect delay")
        except ValueError as e:
            wx.MessageBox(f"Invalid number input for Port or Delay: {e}", "Input Error", wx.OK | wx.ICON_WARNING)
            return

        if not self.controls['host'].GetValue().strip():
             wx.MessageBox("Server Host cannot be empty.", "Input Error", wx.OK | wx.ICON_WARNING); return
        if not self.controls['username'].GetValue().strip():
             wx.MessageBox("Bot Username cannot be empty.", "Input Error", wx.OK | wx.ICON_WARNING); return
        if not self.controls['nickname'].GetValue().strip():
             wx.MessageBox("Bot Nickname cannot be empty.", "Input Error", wx.OK | wx.ICON_WARNING); return

        for key, ctrl in self.controls.items():
            self.config_data[key] = ctrl.GetValue()
        
        self.config_data['port'] = port
        self.config_data['reconnect_delay_min'] = delay_min
        self.config_data['reconnect_delay_max'] = delay_max
        self.config_data['context_history_retention_minutes'] = self.controls['context_history_retention_minutes'].GetValue()
        self.config_data['debug_logging_enabled'] = self.controls['debug_logging_enabled'].GetValue()
        self.EndModal(wx.ID_OK)

    def GetConfigData(self):
        from config_manager import DEFAULT_CONFIG
        structured_data = {
             'Connection': {k: self.config_data.get(k, v) for k, v in DEFAULT_CONFIG['Connection'].items()},
             'Bot': {k: self.config_data.get(k, v) for k, v in DEFAULT_CONFIG['Bot'].items()}
        }
        return structured_data
