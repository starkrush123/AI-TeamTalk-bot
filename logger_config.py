import logging
import sys
from logging.handlers import RotatingFileHandler
from config_manager import load_config # Import load_config function

# Define a specific logger for the bot application
bot_logger = logging.getLogger('bot_app')

def setup_logging():
    # Load configuration to determine logging level
    config = load_config()
    
    # If config is None (e.g., config.ini not found), default to False for debug_logging_enabled
    debug_logging_enabled = False
    if config and 'Bot' in config and 'debug_logging_enabled' in config['Bot']:
        debug_logging_enabled = config['Bot']['debug_logging_enabled']

    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    log_file = 'bot.log'
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.encoding = 'utf-8'

    # Clear existing handlers from the bot_logger to prevent duplication if called multiple times
    for handler in bot_logger.handlers[:]:
        bot_logger.removeHandler(handler)

    # Set logging level based on config
    if debug_logging_enabled:
        bot_logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        bot_logger.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

    # Attach handlers to the specific bot_logger, not the root logger
    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(console_handler)

    # Set logging level for google.generativeai to INFO
    logging.getLogger('google.generativeai').setLevel(logging.INFO)

    # Set the root logger level to a higher value to suppress unwanted messages
    # from other libraries that might log to the root logger.
    logging.getLogger().setLevel(logging.WARNING)
