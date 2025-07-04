from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash
import threading

import os
import json
from functools import wraps
from datetime import timedelta
from dotenv import load_dotenv

from bot_controller import ApplicationController
from config_manager import load_config, save_config, DEFAULT_CONFIG
from logger_config import setup_logging, bot_logger
from .database import db, User

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

initial_config = load_config()
bot_logger.debug(f"Initial config loaded: {initial_config is not None}")

app.secret_key = os.getenv('SECRET_KEY', 'a_fallback_secret_key_if_env_not_set')
app.permanent_session_lifetime = timedelta(minutes=5)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.logger.propagate = False

global bot_controller
bot_controller = ApplicationController(nogui_mode=True)

setup_logging()

with app.app_context():
    db.create_all()
    log_file_path = os.path.join(os.getcwd(), 'bot.log')
    if os.path.exists(log_file_path):
        try:
            if bot_controller is None or bot_controller.bot_instance is None or not bot_controller.bot_instance._intentional_stop:
                with open(log_file_path, 'w') as f:
                    f.truncate(0)
                bot_logger.info("bot.log cleared on fresh application start.")
        except Exception as e:
            bot_logger.error(f"Error clearing bot.log: {e}")

bot_controller.config = initial_config
bot_logger.debug(f"Bot controller config set: {bot_controller.config is not None}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'super_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['permanent'] = True
            session['username'] = username
            session['role'] = user.role
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

@app.before_request
def check_for_first_user():
    if not User.query.first():
        if request.endpoint and request.endpoint not in ['register', 'static']:
            return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    is_first_user = not User.query.first()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not is_first_user and User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html', is_first_user=is_first_user)
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        if is_first_user:
            new_user.role = 'super_admin'
        
        db.session.add(new_user)
        db.session.commit()
        
        if is_first_user:
            flash('Super admin account created successfully. Please log in.', 'success')
        else:
            flash('Registration successful. Please log in.', 'success')
            
        return redirect(url_for('login'))
        
    return render_template('register.html', is_first_user=is_first_user)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    global bot_controller
    if not bot_controller.config:
        flash('Configuration file not found or invalid. Please set up your configuration.', 'warning')
        return redirect(url_for('setup_config'))
    return render_template('index.html')

@app.route('/setup_config', methods=['GET', 'POST'])
@login_required
def setup_config():
    global bot_controller
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
        return redirect(url_for('index'))

    if bot_controller.config and bot_controller.config.get('Connection', {}).get('host'):
        flash('Configuration already exists. Redirected to main page.', 'info')
        return redirect(url_for('index'))

    return render_template('setup_config.html', default_config=DEFAULT_CONFIG)

@app.route('/status', methods=['GET'])
@login_required
def get_status():
    global bot_controller
    status = {"running": False} # Default status

    try:
        if bot_controller:
            bot_logger.debug("get_status: bot_controller exists.")
            if bot_controller.bot_instance:
                bot_logger.debug("get_status: bot_controller.bot_instance exists.")
                status["running"] = bot_controller.bot_thread.is_alive() if bot_controller.bot_thread else False
                bot_logger.debug(f"get_status: running={status['running']}")
                
                status["logged_in"] = bot_controller.bot_instance._logged_in
                bot_logger.debug(f"get_status: logged_in={status['logged_in']}")
                
                status["in_channel"] = bot_controller.bot_instance._in_channel
                bot_logger.debug(f"get_status: in_channel={status['in_channel']}")

                status["features"] = {
                    "announce_join_leave": bot_controller.bot_instance.announce_join_leave,
                    "allow_channel_messages": bot_controller.bot_instance.allow_channel_messages,
                    "allow_broadcast": bot_controller.bot_instance.allow_broadcast,
                    "allow_gemini_pm": bot_controller.bot_instance.allow_gemini_pm,
                    "allow_gemini_channel": bot_controller.bot_instance.allow_gemini_channel,
                    "filter_enabled": bot_controller.bot_instance.filter_enabled,
                    "bot_locked": bot_controller.bot_instance.bot_locked,
                    "context_history_enabled": bot_controller.bot_instance.context_history_enabled,
                    "debug_logging_enabled": bot_controller.bot_instance.debug_logging_enabled,
                }
                bot_logger.debug(f"get_status: features={status['features']}")
                
                # Ensure config is JSON serializable
                if bot_controller.config:
                    try:
                        json.dumps(bot_controller.config) # Test if serializable
                        status["config"] = bot_controller.config
                        bot_logger.debug("get_status: config is JSON serializable.")
                    except TypeError as e:
                        bot_logger.error(f"get_status: Config is not JSON serializable: {e}", exc_info=True)
                        status["config"] = {"error": "Config not serializable"}
                else:
                    status["config"] = {}
                    bot_logger.debug("get_status: bot_controller.config is None.")
            else:
                bot_logger.debug("get_status: bot_controller.bot_instance is None.")
        else:
            bot_logger.debug("get_status: bot_controller is None.")
    except Exception as e:
        bot_logger.error(f"Error in get_status: {e}", exc_info=True)
        status = {"running": False, "error": str(e)}
    
    return jsonify(status)

@app.route('/start', methods=['POST'])
@login_required
def start_bot():
    global bot_controller
    if not bot_controller:
        return jsonify({"status": "error", "message": "Bot controller not initialized."}), 500

    if bot_controller.bot_thread and bot_controller.bot_thread.is_alive():
        return jsonify({"status": "info", "message": "Bot is already running."})
    
    if not bot_controller.config:
        bot_controller.config = load_config()
        if not bot_controller.config:
            return jsonify({"status": "error", "message": "Bot configuration not found. Please configure first."}), 400

    try:
        bot_controller.start_bot_session()
        return jsonify({"status": "success", "message": "Bot starting..."})
    except Exception as e:
        bot_logger.error(f"Error starting bot: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error starting bot: {e}"}), 500

@app.route('/stop', methods=['POST'])
@login_required
def stop_bot():
    global bot_controller
    if bot_controller and bot_controller.bot_thread and bot_controller.bot_thread.is_alive():
        bot_logger.info("Web UI: Stop request received.")
        bot_controller.request_shutdown()
        bot_controller.bot_thread.join(5) 
        if not bot_controller.bot_thread.is_alive():
            bot_logger.info("Web UI: Bot thread successfully stopped.")
            return jsonify({"status": "success", "message": "Bot stopping..."})
        else:
            bot_logger.warning("Web UI: Bot thread did not stop gracefully within 5 seconds.")
            return jsonify({"status": "warning", "message": "Bot is shutting down, but may take longer."})
    return jsonify({"status": "info", "message": "Bot is not running."})

@app.route('/restart', methods=['POST'])
@login_required
def restart_bot():
    global bot_controller
    if not bot_controller:
        return jsonify({"status": "error", "message": "Bot controller not initialized."}), 500

    if bot_controller.bot_thread and bot_controller.bot_thread.is_alive():
        if bot_controller.restart_requested.is_set():
             return jsonify({"status": "info", "message": "Bot restart is already in progress."})
        
        bot_logger.info("Web UI: Restart request received.")
        bot_controller.request_restart()
        return jsonify({"status": "success", "message": "Bot restart initiated."})
    else:
        bot_logger.info("Web UI: Bot is not running, starting instead.")
        bot_controller.start_bot_session()
        return jsonify({"status": "success", "message": "Bot is not running, starting now..."})


@app.route('/toggle_feature/<feature_name>', methods=['POST'])
@login_required
def toggle_feature(feature_name):
    global bot_controller
    if not bot_controller or not bot_controller.bot_instance:
        return jsonify({"status": "error", "message": "Bot is not running."}), 400

    feature_map = {
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
    
    full_feature_name = feature_map.get(feature_name)
    if not full_feature_name:
        return jsonify({"status": "error", "message": f"Unknown feature: {feature_name}"}), 400

    toggle_method_name = f"toggle_{full_feature_name}"
    toggle_method = getattr(bot_controller.bot_instance, toggle_method_name, None)

    if callable(toggle_method):
        toggle_method()
        new_status = getattr(bot_controller.bot_instance, full_feature_name, False)
        return jsonify({"status": "success", "message": f"Feature {full_feature_name} is now {'ON' if new_status else 'OFF'}.", "new_state": new_status})
    else:
        return jsonify({"status": "error", "message": f"Toggle method for {full_feature_name} not found."}), 500

@app.route('/config', methods=['GET', 'POST'])
@login_required
@super_admin_required
def manage_config():
    global bot_controller
    if request.method == 'GET':
        if bot_controller and bot_controller.config:
            return jsonify(bot_controller.config)
        else:
            config = load_config()
            if config:
                return jsonify(config)
            return jsonify({"status": "error", "message": "Configuration not loaded."}), 404
    elif request.method == 'POST':
        if not bot_controller:
            setup_logging()
            bot_controller = ApplicationController(nogui_mode=True)
        
        new_config_data = {}
        for key, value in request.form.items():
            section, option = key.split('_', 1)
            if section not in new_config_data:
                new_config_data[section] = {}
            new_config_data[section][option] = value

        bot_logger.debug(f"DEBUG: new_config_data from JSON in manage_config: {new_config_data}")

        current_config = bot_controller.config if bot_controller.config else load_config() or DEFAULT_CONFIG
        bot_logger.debug(f"DEBUG: current_config before merge in manage_config: {current_config}")
        
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

        bot_logger.debug(f"DEBUG: current_config after merge in manage_config: {current_config}")

        save_config(current_config)
        bot_controller.config = current_config
        
        if bot_controller.bot_thread and bot_controller.bot_thread.is_alive():
            bot_logger.info("Bot is running, initiating restart to apply new configuration.")
            bot_controller.request_restart()
            if bot_controller.bot_thread.is_alive():
                return jsonify({"status": "success", "message": 'Configuration updated and bot restarted successfully.'})
            else:
                return jsonify({"status": "warning", "message": 'Configuration updated. Bot restart initiated, but status is unclear.'})
        else:
            return jsonify({"status": "success", "message": 'Configuration updated.'})

@app.route('/logs', methods=['GET'])
@login_required
def get_logs():
    log_file_path = os.path.join(os.getcwd(), 'bot.log')
    if os.path.exists(log_file_path):
        limit = request.args.get('limit', type=int, default=500)
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs = "".join(lines[-limit:])
            return logs, 200, {'Content-Type': 'text/plain'}
        except Exception as e:
            bot_logger.error(f"Error reading log file: {e}", exc_info=True)
            return "Error reading logs.", 500
    return "No logs found.", 404

@app.route('/users', methods=['GET'])
@login_required
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "username": user.username, "role": user.role} for user in users])

@app.route('/users', methods=['POST'])
@login_required
@super_admin_required
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'admin') # Default to 'admin' if not provided

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Username already exists."}), 400

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "message": "User added successfully.", "user": {"id": new_user.id, "username": new_user.username, "role": new_user.role}}), 201

@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@super_admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_password = data.get('password')

    if new_password:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({"status": "success", "message": "User password updated successfully."}), 200
    return jsonify({"status": "error", "message": "No password provided for update."}), 400

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == session.get('username'):
        return jsonify({"status": "error", "message": "Cannot delete currently logged in user."}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"status": "success", "message": "User deleted successfully."}), 200