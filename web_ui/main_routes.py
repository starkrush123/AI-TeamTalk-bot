from flask import Blueprint, render_template, flash, redirect, url_for
from .auth import login_required
from .core import get_bot_controller

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    bot_controller = get_bot_controller()
    if not bot_controller.config:
        flash('Configuration file not found or invalid. Please set up your configuration.', 'warning')
        return redirect(url_for('config.setup_config'))
    return render_template('index.html')