from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .auth import login_required, super_admin_required
from config_manager import load_config, save_config, DEFAULT_CONFIG
from logger_config import bot_logger
from .core import get_bot_controller

config_bp = Blueprint('config', __name__)

@config_bp.route('/setup_config', methods=['GET', 'POST'])
@login_required
def setup_config():
    bot_controller = get_bot_controller()
    if request.method == 'POST':
        new_config_data = {}
        for key, value in request.form.items():
            section, option = key.split('_', 1)
            if section not in new_config_data:
                new_config_data[section] = {}
            new_config_data[section][option] = value

        bot_logger.debug(f"DEBUG: new_config_data from form: {new_config_data}")

        current_config = DEFAULT_CONFIG
        
        for section, settings in new_config_data.items():
            if section in current_config:
                for key, value in settings.items():
                    if value == 'on':
                        current_config[section][key] = 'True'
                    elif key in DEFAULT_CONFIG.get(section, {}) and DEFAULT_CONFIG[section][key].lower() in ['true', 'false']:
                        current_config[section][key] = 'False'
                    else:
                        if section == 'Connection' and key == 'host' and value.endswith('localhost') and value != 'localhost':
                            current_config[section][key] = value.rstrip('localhost')
                        else:
                            current_config[section][key] = value
            else:
                current_config[section] = settings

        bot_logger.debug(f"DEBUG: current_config before save in setup_config: {current_config}")
        save_config(current_config)
        bot_controller.config = current_config
        flash('Configuration saved successfully.', 'success')
        return redirect(url_for('main.index'))

    if bot_controller.config and bot_controller.config.get('Connection', {}).get('host'):
        flash('Configuration already exists. Redirected to main page.', 'info')
        return redirect(url_for('main.index'))

    return render_template('setup_config.html', default_config=DEFAULT_CONFIG)

@config_bp.route('/config', methods=['GET', 'POST'])
@login_required
@super_admin_required
def manage_config():
    bot_controller = get_bot_controller()
    if request.method == 'GET':
        if bot_controller and bot_controller.config:
            return jsonify(bot_controller.config)
        else:
            config = load_config()
            if config:
                return jsonify(config)
            return jsonify({"status": "error", "message": "Configuration not loaded."}), 404
    elif request.method == 'POST':
        new_config_data = request.get_json()

        bot_logger.debug(f"DEBUG: new_config_data from JSON in manage_config: {new_config_data}")

        current_config = bot_controller.config if bot_controller.config else load_config() or DEFAULT_CONFIG
        bot_logger.debug(f"DEBUG: current_config before merge in manage_config: {current_config}")
        
        for section, settings in new_config_data.items():
            if section in current_config:
                for key, value in settings.items():
                    current_config[section][key] = value
            else:
                current_config[section] = settings

        bot_logger.debug(f"DEBUG: current_config after merge in manage_config: {current_config}")

        save_config(current_config)
        bot_controller.config = current_config
        
        if bot_controller.bot_thread and bot_controller.bot_thread.is_alive():
            bot_logger.info("Bot is running, initiating restart to apply new configuration.")
            bot_controller.request_restart()
            return jsonify({"status": "success", "message": 'Configuration updated and bot restart initiated.'})
        else:
            return jsonify({"status": "success", "message": 'Configuration updated.'})