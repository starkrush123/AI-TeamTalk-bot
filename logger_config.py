import logging
import sys
from logging.handlers import RotatingFileHandler

# Define a specific logger for the bot application
bot_logger = logging.getLogger('bot_app')

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    log_file = 'bot.log'
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    console_handler.encoding = 'utf-8'

    # Clear existing handlers from the bot_logger to prevent duplication if called multiple times
    for handler in bot_logger.handlers[:]:
        bot_logger.removeHandler(handler)

    # Attach handlers to the specific bot_logger, not the root logger
    bot_logger.setLevel(logging.INFO) # Set level for the bot's logger
    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(console_handler)

    # Set the root logger level to a higher value to suppress unwanted messages
    # from other libraries that might log to the root logger.
    logging.getLogger().setLevel(logging.WARNING)
