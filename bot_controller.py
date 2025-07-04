import sys, threading, signal, logging, time
from logging.handlers import RotatingFileHandler
from config_manager import load_config, save_config, DEFAULT_CONFIG
from bot import MyTeamTalkBot, TeamTalkError

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

    def start(self):
        # Metode ini tidak akan dipanggil langsung oleh web_ui.py
        # Web UI akan memanggil start_bot_session() secara langsung
        self.config = self._load_or_prompt_config()
        if not self.config:
            logging.critical("Configuration failed. Exiting.")
            return

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if self.nogui:
            # Ini adalah mode konsol, tidak relevan untuk Web UI
            logging.info("Starting bot in non-GUI mode. Press Ctrl+C or type 'exit' to stop.")
            while not self.exit_event.is_set():
                self.restart_requested.clear()
                self.start_bot_session()
                
                while self.bot_thread.is_alive() and not self.restart_requested.is_set() and not self.exit_event.is_set():
                    try:
                        self.bot_thread.join(1) 
                    except KeyboardInterrupt:
                        logging.info("KeyboardInterrupt caught in main loop.")
                        self.exit_event.set()

                if self.restart_requested.is_set():
                    logging.info("Bot restart requested. Stopping current bot instance...")
                    if self.bot_instance:
                        self.bot_instance._mark_stopped_intentionally() 
                        self.bot_instance.stop() 
                    if self.bot_thread and self.bot_thread.is_alive():
                        self.bot_thread.join(5) 
                        if self.bot_thread.is_alive():
                            logging.warning("Bot thread did not terminate gracefully after restart request.")
                    logging.info("Restarting bot session...")
                elif not self.exit_event.is_set():
                    logging.warning("Bot thread terminated unexpectedly. Restarting in 15 seconds...")
                    time.sleep(15)
            self.shutdown()
        else:
            # Ini adalah mode GUI, tidak relevan untuk Web UI
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
        logging.warning("Configuration not found. Please configure via Web UI.")
        return None

    def _prompt_for_config_gui(self):
        # Tidak digunakan oleh Web UI
        pass

    def _prompt_for_config_console(self):
        # Tidak digunakan oleh Web UI
        pass

    def start_bot_session(self):
        if self.bot_thread and self.bot_thread.is_alive():
            logging.info("Bot session already running.")
            return
        
        if not self.config:
            logging.error("Cannot start bot: Configuration is not loaded.")
            return

        self.exit_event.clear() # Clear exit event for new session
        self.restart_requested.clear() # Clear restart event

        self.bot_thread = threading.Thread(target=self._bot_thread_func, daemon=True)
        self.bot_thread.start()
        logging.info("New bot session started.")

    def _bot_thread_func(self):
        try:
            self.bot_instance = MyTeamTalkBot(self.config, self)
            # if not self.nogui: # Only set main_window if in GUI mode
            #     self.bot_instance.set_main_window(self.main_gui_window)
            self.bot_instance.start()
        except Exception as e:
            logging.critical(f"Bot thread failed with unhandled exception: {e}", exc_info=True)
        finally:
            logging.info("Bot thread finished execution.")
            self.bot_instance = None

    def request_restart(self):
        logging.info("Restart requested by controller.")
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()
            # Give some time for the bot to stop before restarting
            time.sleep(2) 
        self.restart_requested.set()
        self.exit_event.set() # Signal main loop to exit and potentially restart

    def _signal_handler(self, sig, frame):
        if self.exit_event.is_set():
            logging.warning("Shutdown already in progress.")
            return
        logging.info(f"Signal {sig} received, initiating shutdown...")
        self.exit_event.set()

    def request_shutdown(self):
        logging.info("Shutdown requested by controller.")
        self.exit_event.set()
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()

    def shutdown(self):
        logging.info("Shutdown sequence started.")
        if self.bot_instance:
            self.bot_instance._mark_stopped_intentionally()
            self.bot_instance.stop()
        if self.bot_thread and self.bot_thread.is_alive():
            logging.info("Waiting for bot thread to terminate...")
            self.bot_thread.join(5.0)
        logging.info("Cleanup complete. Exiting.")