

import sys, threading, signal, logging, argparse, time
from logging.handlers import RotatingFileHandler
from config_manager import load_config, save_config, DEFAULT_CONFIG
from bot import MyTeamTalkBot, TeamTalkError

# This is the server-optimized entry point.
# For GUI, run main_gui.py

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = 'bot.log'
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO) # Set console handler level
    console_handler.setFormatter(log_formatter)
    console_handler.encoding = 'utf-8' # Explicitly set encoding for console output

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

class InteractiveShell(threading.Thread):
    def __init__(self, controller):
        super().__init__(daemon=True)
        self.controller = controller
        self.feature_map = {
            "jcl": "announce_join_leave",
            "chanmsg": "allow_channel_messages",
            "broadcast": "allow_broadcast",
            "geminipm": "allow_gemini_pm",
            "geminichan": "allow_gemini_channel",
            "filter": "filter_enabled",
            "lock": "bot_locked",
            "context_history": "context_history_enabled",
            "debug_logging": "debug_logging_enabled"
        }

    def run(self):
        time.sleep(2) # Wait for bot to likely be running
        print("""
Interactive shell started. Type 'help' for commands.""")
        while not self.controller.exit_event.is_set():
            try:
                cmd_line = input("> ").strip().lower()
                if not cmd_line: continue
                
                parts = cmd_line.split()
                command = parts[0]
                args = parts[1:]

                if command == "help":
                    self.show_help()
                elif command == "status":
                    self.show_status()
                elif command == "toggle":
                    self.toggle_feature(args)
                elif command == "set_retention":
                    self.set_retention(args)
                elif command in ["exit", "quit"]:
                    print("Shutdown requested from shell.")
                    self.controller.exit_event.set()
                    break
                else:
                    print(f"Unknown command: {command}")

            except (EOFError, KeyboardInterrupt):
                # This can happen if the main thread is interrupted
                break
            except Exception as e:
                print(f"Error in shell: {e}")
        print("Interactive shell stopped.")

    def show_help(self):
        print("""--- Bot Interactive Shell Help ---
status              - Show the current status of all features.
toggle <feature>    - Toggle a feature ON or OFF.
  Available features: jcl, chanmsg, broadcast, geminipm, geminichan, filter, lock, context_history, debug_logging
set_retention <minutes> - Set the context history retention period in minutes.
exit / quit         - Stop the bot and exit the application.
help                - Show this help message.""")

    def show_status(self):
        bot = self.controller.bot_instance
        if not bot:
            print("Bot is not currently running.")
            return
        
        print("""
--- Bot Feature Status ---""")
        for short_name, full_name in self.feature_map.items():
            status = "ON" if getattr(bot, full_name, False) else "OFF"
            print(f"{short_name:<12} | {full_name:<25} | {status}")
        print(f"Context History Retention: {bot.context_history_manager.retention_minutes} minutes")
        print(f"Debug Logging: {'ON' if bot.debug_logging_enabled else 'OFF'}")
        print()

    def toggle_feature(self, args):
        if not args:
            print("Usage: toggle <feature_name>")
            return
        
        short_name = args[0]
        feature_key = self.feature_map.get(short_name)
        bot = self.controller.bot_instance

        if not bot:
            print("Bot is not running, cannot toggle features.")
            return
        if not feature_key:
            print(f"Unknown feature: {short_name}. Type 'help' for options.")
            return

        toggle_method_name = f"toggle_{feature_key}"
        toggle_method = getattr(bot, toggle_method_name, None)

        if callable(toggle_method):
            print(f'Toggling "{feature_key}"...')
            toggle_method()
            # Show new status
            new_status = "ON" if getattr(bot, feature_key, False) else "OFF"
            print(f'Feature "{feature_key}" is now {new_status}.')
        else:
            print(f'Error: Could not find toggle method for "{feature_key}"')

    def set_retention(self, args):
        if not args or not args[0].isdigit():
            print("Usage: set_retention <minutes>")
            return
        
        try:
            minutes = int(args[0])
            if minutes < 0:
                print("Retention minutes cannot be negative.")
                return
            
            bot = self.controller.bot_instance
            if not bot:
                print("Bot is not running, cannot set retention.")
                return
            
            bot.context_history_manager.set_retention_minutes(minutes)
            bot.config['Bot']['context_history_retention_minutes'] = str(minutes)
            bot._save_runtime_config()
            print(f"Context history retention set to {minutes} minutes.")
        except Exception as e:
            print(f"Error setting retention: {e}")


class ApplicationController:
    def __init__(self, nogui_mode):
        self.nogui = nogui_mode
        self.bot_instance = None
        self.bot_thread = None
        self.config = None
        self.app_instance = None
        self.main_gui_window = None
        self.exit_event = threading.Event()
        self.restart_requested = threading.Event()

    def start(self):
        self.config = self._load_or_prompt_config()
        if not self.config:
            logging.critical("Configuration failed. Exiting.")
            return

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if self.nogui:
            self._run_console_mode()
        else:
            # This path is taken when main.py is called by main_gui.py
            # It expects wx to be available and will run the GUI mode.
            self._run_gui_mode()

    def _load_or_prompt_config(self):
        loaded_config = load_config()
        if loaded_config:
            return loaded_config
        
        if not self.nogui:
            config = self._prompt_for_config_gui()
        else:
            config = self._prompt_for_config_console()
        
        if config: # Only save if config was successfully obtained
            save_config(config)
        return config

    def _prompt_for_config_gui(self):
        try:
            import wx
            from gui.config_dialog import ConfigDialog
        except ImportError:
            logging.critical("wxPython or GUI modules not found. Cannot prompt for config in GUI mode.")
            return None

        # Create a dummy app if not already created by _run_gui_mode
        if not self.app_instance:
            self.app_instance = wx.App(False)

        dialog = ConfigDialog(None, "Bot Configuration", DEFAULT_CONFIG)
        if dialog.ShowModal() == wx.ID_OK:
            user_config = dialog.GetConfigData()
            dialog.Destroy()
            return user_config
        else:
            dialog.Destroy()
            logging.warning("Configuration cancelled by user in GUI dialog.")
            return None

    def _prompt_for_config_console(self):
        print("Initial configuration not found. Please provide the following details:")
        config = {}
        for section, settings in DEFAULT_CONFIG.items():
            config[section] = {}
            print(f"--- {section} ---")
            for key, default_value in settings.items():
                prompt_text = f"{key} [{default_value}]: "
                user_input = input(prompt_text)
                config[section][key] = user_input if user_input else default_value
        return config

    def _run_console_mode(self):
        logging.info("Starting bot in non-GUI mode. Press Ctrl+C or type 'exit' to stop.")
        
        shell = InteractiveShell(self)
        shell.start()

        while not self.exit_event.is_set():
            self.restart_requested.clear()
            self.start_bot_session()
            
            while self.bot_thread.is_alive() and not self.restart_requested.is_set() and not self.exit_event.is_set():
                try:
                    self.bot_thread.join(1) # Wait for bot thread to finish or for restart/exit signal
                except KeyboardInterrupt:
                    logging.info("KeyboardInterrupt caught in main loop.")
                    self.exit_event.set()

            if self.restart_requested.is_set():
                logging.info("Bot restart requested. Stopping current bot instance...")
                if self.bot_instance:
                    self.bot_instance._mark_stopped_intentionally() # Mark as intentional stop
                    self.bot_instance.stop() # Ensure the bot instance stops
                if self.bot_thread and self.bot_thread.is_alive():
                    self.bot_thread.join(5) # Give it some time to stop gracefully
                    if self.bot_thread.is_alive():
                        logging.warning("Bot thread did not terminate gracefully after restart request.")
                logging.info("Restarting bot session...")
            elif not self.exit_event.is_set():
                logging.warning("Bot thread terminated unexpectedly. Restarting in 15 seconds...")
                time.sleep(15)
        
        self.shutdown()

    def _run_gui_mode(self):
        # This method is called when main.py is launched by main_gui.py
        # It expects wx to be available.
        try:
            import wx
            from gui.config_dialog import ConfigDialog
            from gui.main_window import MainBotWindow
        except ImportError:
            logging.critical("wxPython or GUI modules not found. Cannot run in GUI mode.")
            self.exit_event.set()
            return

        if not self.app_instance:
            self.app_instance = wx.App(False)
        self.main_gui_window = MainBotWindow(None, "TeamTalk Bot", self)
        self.main_gui_window.Show() # Show the window
        self.start_bot_session()
        self.app_instance.MainLoop()
        self.shutdown()

    def start_bot_session(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
        self.bot_thread = threading.Thread(target=self._bot_thread_func, daemon=True)
        self.bot_thread.start()
        logging.info("New bot session started.")

    def _bot_thread_func(self):
        try:
            self.bot_instance = MyTeamTalkBot(self.config, self)
            if not self.nogui: # Only set main_window if in GUI mode
                self.bot_instance.set_main_window(self.main_gui_window)
            self.bot_instance.start()
        except Exception as e:
            logging.critical(f"Bot thread failed with unhandled exception: {e}", exc_info=True)
        finally:
            logging.info("Bot thread finished execution.")
            self.bot_instance = None

    def request_restart(self):
        logging.info("Restart requested by bot.")
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()
        self.restart_requested.set()

    def _signal_handler(self, sig, frame):
        if self.exit_event.is_set():
            logging.warning("Shutdown already in progress.")
            return
        logging.info(f"Signal {sig} received, initiating shutdown...")
        self.exit_event.set()

    def request_shutdown(self):
        logging.info("Shutdown requested by bot.")
        self.exit_event.set()

    def shutdown(self):
        logging.info("Shutdown sequence started.")
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()
        if self.bot_thread and self.bot_thread.is_alive():
            logging.info("Waiting for bot thread to terminate...")
            self.bot_thread.join(5.0)
        logging.info("Cleanup complete. Exiting.")

if __name__ == "__main__":
    setup_logging()
    controller = ApplicationController(nogui_mode=True)
    controller.start()
    sys.exit(0)

