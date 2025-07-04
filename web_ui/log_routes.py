from flask import Blueprint, request
import os
from .auth import login_required
from logger_config import bot_logger

log_bp = Blueprint('log', __name__)

@log_bp.route('/logs', methods=['GET'])
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
