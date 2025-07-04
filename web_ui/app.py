from .core import create_app, init_bot_controller, get_bot_controller
from .auth import auth_bp
from .bot_routes import bot_bp
from .config_routes import config_bp
from .user_routes import user_bp
from .log_routes import log_bp
from .main_routes import main_bp

app = create_app()

# Initialize bot_controller after app is created
with app.app_context():
    init_bot_controller(app)

app.register_blueprint(auth_bp)
app.register_blueprint(bot_bp)
app.register_blueprint(config_bp)
app.register_blueprint(user_bp)
app.register_blueprint(log_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)