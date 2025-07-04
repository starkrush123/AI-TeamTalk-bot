from web_ui.app import app
import logging

if __name__ == '__main__':
    logging.info("Starting Flask Web UI...")
    app.run(host='0.0.0.0', port=5000, debug=True)
