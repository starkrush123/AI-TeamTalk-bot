
import configparser
import os
import logging

CONFIG_FILE = "config.ini"
DEFAULT_CONFIG = {
    'Connection': {
        'host': 'localhost',
        'port': '10333',
        'username': 'guest',
        'password': '',
        'nickname': 'PyBot+',
        'channel': '/',
        'channel_password': ''
    },
    'Bot': {
        'client_name': 'AI bot',
        'admin_usernames': '',
        'gemini_api_key': '',
        'gemini_model_name': 'gemini-1.5-flash-latest',
        'status_message': '',
        'reconnect_delay_min': '5',
        'reconnect_delay_max': '15',
        'weather_api_key': '',
        'filtered_words': '',
        'context_history_retention_minutes': '60',
        'context_history_max_messages': '40',
        'context_history_enabled': 'True',
        'debug_logging_enabled': 'False',
        'ai_system_instructions': ''
    }
}

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        logging.warning(f"{CONFIG_FILE} not found. Will prompt for setup.")
        return None

    try:
        config.read(CONFIG_FILE)
        if not config.has_section('Connection') or not config.has_section('Bot'):
            logging.error(f"Config file {CONFIG_FILE} is missing required sections. Please fix or delete it.")
            return None
        
        structured_config = {section: dict(config.items(section)) for section in config.sections()}
        # Ensure context_history_retention_minutes is an integer
        if 'Bot' in structured_config and 'context_history_retention_minutes' in structured_config['Bot']:
            try:
                structured_config['Bot']['context_history_retention_minutes'] = int(structured_config['Bot']['context_history_retention_minutes'])
            except ValueError:
                logging.error("Invalid value for context_history_retention_minutes. Using default.")
                structured_config['Bot']['context_history_retention_minutes'] = int(DEFAULT_CONFIG['Bot']['context_history_retention_minutes'])
        else:
            structured_config['Bot']['context_history_retention_minutes'] = int(DEFAULT_CONFIG['Bot']['context_history_retention_minutes'])

        # Ensure context_history_enabled is a boolean
        if 'Bot' in structured_config and 'context_history_enabled' in structured_config['Bot']:
            structured_config['Bot']['context_history_enabled'] = structured_config['Bot']['context_history_enabled'].lower() == 'true'
        else:
            structured_config['Bot']['context_history_enabled'] = DEFAULT_CONFIG['Bot']['context_history_enabled'].lower() == 'true'

        # Ensure debug_logging_enabled is a boolean
        if 'Bot' in structured_config and 'debug_logging_enabled' in structured_config['Bot']:
            structured_config['Bot']['debug_logging_enabled'] = structured_config['Bot']['debug_logging_enabled'].lower() == 'true'
        else:
            structured_config['Bot']['debug_logging_enabled'] = DEFAULT_CONFIG['Bot']['debug_logging_enabled'].lower() == 'true'

        logging.info(f"Loaded configuration from {CONFIG_FILE}")
        return structured_config
    except configparser.Error as e:
        logging.error(f"Error reading config file {CONFIG_FILE}: {e}. Please fix or delete it.")
        return None

def save_config(structured_config_data):
    config = configparser.ConfigParser()
    
    conn_data = structured_config_data.get('Connection', {})
    bot_data = structured_config_data.get('Bot', {})

    config['Connection'] = {
        'host': conn_data.get('host', DEFAULT_CONFIG['Connection']['host']),
        'port': str(conn_data.get('port', DEFAULT_CONFIG['Connection']['port'])),
        'username': conn_data.get('username', DEFAULT_CONFIG['Connection']['username']),
        'password': conn_data.get('password', ''),
        'nickname': conn_data.get('nickname', DEFAULT_CONFIG['Connection']['nickname']),
        'channel': conn_data.get('channel', DEFAULT_CONFIG['Connection']['channel']),
        'channel_password': conn_data.get('channel_password', '')
    }

    config['Bot'] = {
        'client_name': bot_data.get('client_name', DEFAULT_CONFIG['Bot']['client_name']),
        'admin_usernames': bot_data.get('admin_usernames', ''),
        'gemini_api_key': bot_data.get('gemini_api_key', ''),
        'gemini_model_name': bot_data.get('gemini_model_name', DEFAULT_CONFIG['Bot']['gemini_model_name']),
        'status_message': bot_data.get('status_message', ''),
        'reconnect_delay_min': str(bot_data.get('reconnect_delay_min', DEFAULT_CONFIG['Bot']['reconnect_delay_min'])),
        'reconnect_delay_max': str(bot_data.get('reconnect_delay_max', DEFAULT_CONFIG['Bot']['reconnect_delay_max'])),
        'weather_api_key': bot_data.get('weather_api_key', ''),
        'filtered_words': bot_data.get('filtered_words', ''),
        'context_history_retention_minutes': str(bot_data.get('context_history_retention_minutes', DEFAULT_CONFIG['Bot']['context_history_retention_minutes'])),
        'context_history_enabled': str(bot_data.get('context_history_enabled', DEFAULT_CONFIG['Bot']['context_history_enabled'])),
        'debug_logging_enabled': str(bot_data.get('debug_logging_enabled', DEFAULT_CONFIG['Bot']['debug_logging_enabled'])),
        'ai_system_instructions': bot_data.get('ai_system_instructions', DEFAULT_CONFIG['Bot']['ai_system_instructions'])
    }

    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        logging.info(f"Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        logging.error(f"Error saving configuration to {CONFIG_FILE}: {e}")
