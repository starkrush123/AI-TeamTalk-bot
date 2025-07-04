import sys, threading, signal, time
from config_manager import load_config, save_config, DEFAULT_CONFIG
from bot import MyTeamTalkBot, TeamTalkError
from logger_config import bot_logger, setup_logging # Import from new module

# InteractiveShell dihapus karena tidak relevan untuk Web UI

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
        self.logger = bot_logger # Use the named logger

    def start(self):
        # Metode ini tidak akan dipanggil langsung oleh web_ui.py
        # Web UI akan memanggil start_bot_session() secara langsung
        self.config = self._load_or_prompt_config()
        if not self.config:
            self.logger.critical("Configuration failed. Exiting.")
            return

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if self.nogui:
            # Ini adalah mode konsol, tidak relevan untuk Web UI
            self.logger.info("Starting bot in non-GUI mode. Press Ctrl+C or type 'exit' to stop.")
            while not self.exit_event.is_set():
                self.restart_requested.clear()
                self.start_bot_session()
                
                while self.bot_thread.is_alive() and not self.restart_requested.is_set() and not self.exit_event.is_set():
                    try:
                        self.bot_thread.join(1) 
                    except KeyboardInterrupt:
                        self.logger.info("KeyboardInterrupt caught in main loop.")
                        self.exit_event.set()

                if self.restart_requested.is_set():
                    self.logger.info("Bot restart requested. Stopping current bot instance...")
                    if self.bot_instance:
                        self.bot_instance._mark_stopped_intentionally() 
                        self.bot_instance.stop() 
                    if self.bot_thread and self.bot_thread.is_alive():
                        self.bot_thread.join(5) 
                        if self.bot_thread.is_alive():
                            self.logger.warning("Bot thread did not terminate gracefully after restart request.")
                    self.logger.info("Restarting bot session...")
                elif not self.exit_event.is_set():
                    self.logger.warning("Bot thread terminated unexpectedly. Restarting in 15 seconds...")
                    time.sleep(15)
            self.shutdown()
        else:
            # Ini adalah mode GUI, tidak relevan untuk Web UI
            try:
                import wx
                from gui.config_dialog import ConfigDialog
                from gui.main_window import MainBotWindow
            except ImportError:
                self.logger.critical("wxPython or GUI modules not found. Cannot run in GUI mode.")
                self.exit_event.set()
                return

            if not self.app_instance:
                self.app_instance = wx.App(False)
            self.main_gui_window = MainBotWindow(None, "TeamTalk Bot", self)
            self.main_gui_window.Show() 
            self.start_bot_session()
            self.app_instance.MainLoop()
            self.shutdown()

    def _load_or_prompt_config(self):
        loaded_config = load_config()
        if loaded_config:
            return loaded_config
        
        # Untuk Web UI, kita tidak akan meminta konfigurasi di sini
        # Konfigurasi harus dimuat atau diatur melalui API
        self.logger.warning("Configuration not found. Please configure via Web UI.")
        return None

    def _prompt_for_config_gui(self):
        # Tidak digunakan oleh Web UI
        pass

    def _prompt_for_config_console(self):
        # Tidak digunakan oleh Web UI
        pass

    def start_bot_session(self):
        if self.bot_thread and self.bot_thread.is_alive():
            self.logger.info("Bot session already running.")
            return
        
        if not self.config:
            self.logger.error("Cannot start bot: Configuration is not loaded.")
            return

        self.exit_event.clear() # Clear exit event for new session
        self.restart_requested.clear() # Clear restart event

        self.bot_thread = threading.Thread(target=self._bot_thread_func, daemon=True)
        self.bot_thread.start()
        self.logger.info("New bot session started.")

    def _bot_thread_func(self):
        try:
            self.bot_instance = MyTeamTalkBot(self.config, self)
            # if not self.nogui: # Only set main_window if in GUI mode
            #     self.bot_instance.set_main_window(self.main_gui_window)
            self.bot_instance.start()
        except Exception as e:
            self.logger.critical(f"Bot thread failed with unhandled exception: {e}", exc_info=True)
        finally:
            self.logger.info("Bot thread finished execution.")
            self.bot_instance = None

    def request_restart(self):
        
        if self.restart_requested.is_set():
            self.logger.warning("Restart is already in progress.")
            return

        self.logger.info("Restart requested by controller.")
        self.restart_requested.set()

        def restart_thread_func():
            if self.bot_instance:
                self.logger.info("Stopping bot instance...")
                self.bot_instance._mark_stopped_intentionally()
                self.bot_instance.stop()
            
            if self.bot_thread and self.bot_thread.is_alive():
                self.logger.info("Waiting for bot thread to terminate...")
                self.bot_thread.join(10.0) # Wait up to 10 seconds
                if self.bot_thread.is_alive():
                    self.logger.error("Bot thread did not terminate gracefully. Restart aborted.")
                    self.restart_requested.clear()
                    return

            self.logger.info("Bot stopped. Restarting in 3 seconds...")
            time.sleep(3)

            # Start a new bot session
            self.logger.info("Starting new bot session...")
            self.start_bot_session()
            self.restart_requested.clear()
            self.logger.info("Bot restart process completed.")

        restart_thread = threading.Thread(target=restart_thread_func, daemon=True)
        restart_thread.start()

    def _signal_handler(self, sig, frame):
        if self.exit_event.is_set():
            self.logger.warning("Shutdown already in progress.")
            return
        self.logger.info(f"Signal {sig} received, initiating shutdown...")
        self.exit_event.set()

    def request_shutdown(self):
        self.logger.info("Shutdown requested by controller.")
        self.exit_event.set()
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()

    def shutdown(self):
        self.logger.info("Shutdown sequence started.")
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()
        if self.bot_thread and self.bot_thread.is_alive():
            self.logger.info("Waiting for bot thread to terminate...")
            self.bot_thread.join(5.0)
        self.logger.info("Cleanup complete. Exiting.")