from flask import Flask
import os
from datetime import timedelta
from dotenv import load_dotenv

from bot_controller import ApplicationController
from config_manager import load_config, DEFAULT_CONFIG
from logger_config import setup_logging, bot_logger
from .database import db

load_dotenv()

_bot_controller_instance = None

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    initial_config = load_config()
    bot_logger.debug(f"Initial config loaded: {initial_config is not None}")

    app.secret_key = os.getenv('SECRET_KEY', 'a_fallback_secret_key_if_env_not_set')
    app.permanent_session_lifetime = timedelta(minutes=5)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.logger.propagate = False

    setup_logging()

    with app.app_context():
        db.create_all()
        log_file_path = os.path.join(os.getcwd(), 'bot.log')
        if os.path.exists(log_file_path):
            try:
                pass # Temporarily disable log clearing on app start for modularization
            except Exception as e:
                bot_logger.error(f"Error clearing bot.log: {e}")
    
    return app

def init_bot_controller(app):
    global _bot_controller_instance
    if _bot_controller_instance is None:
        _bot_controller_instance = ApplicationController(nogui_mode=True)
        initial_config = load_config() # Reload config to ensure it's fresh
        _bot_controller_instance.config = initial_config
        bot_logger.debug(f"Bot controller config set: {_bot_controller_instance.config is not None}")
    return _bot_controller_instance

def get_bot_controller():
    global _bot_controller_instance
    if _bot_controller_instance is None:
        # This case should ideally not happen if init_bot_controller is called correctly
        # but as a fallback, we can try to initialize it here (though it might lack app context)
        bot_logger.warning("get_bot_controller called before initialization. Attempting fallback initialization.")
        _bot_controller_instance = ApplicationController(nogui_mode=True)
        _bot_controller_instance.config = load_config() # Load config as fallback
    return _bot_controller_instance