import sys, threading, signal, logging, argparse, time
from bot_controller import ApplicationController, setup_logging

# This is the server-optimized entry point.
# For GUI, run main_gui.py

if __name__ == "__main__":
    setup_logging()
    controller = ApplicationController(nogui_mode=True)
    controller.start()
    sys.exit(0)