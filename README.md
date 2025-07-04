# AI TeamTalk Bot

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)

An advanced TeamTalk bot integrated with Google Gemini AI to provide intelligent chat functionality, moderation, and interactive commands. The bot can be run in a GUI mode (using wxPython) or as a standalone console application.

- **Author**: [starkrush123](https://github.com/starkrush123)

## Key Features

- **TeamTalk Integration**: Connects to a TeamTalk server, joins channels, and interacts with users.
- **Artificial Intelligence (AI)**:
    - Integrated with **Google Gemini** to answer questions in PMs and channels.
    - **Context History**: Remembers previous conversations within a session for more relevant responses.
    - **System Instructions**: Ability to give the AI custom instructions to tailor its behavior.
- **Command System**:
    - Separate commands for private messages (PM) and channel messages.
    - Admin access level for powerful commands.
    - Configurable and blockable command handling.
- **Dual Operation Modes**:
    - **GUI Mode**: A graphical user interface for logging, bot management, and feature toggling.
    - **Console Mode**: Headless operation with an interactive shell for management.
- **Interactive Features**:
    - **Polling System**: Create polls, collect votes, and display results.
    - **Weather Info**: Get current weather conditions for a specific location.
- **Moderation**:
    - **Word Filter**: Automatically moderates channel chat and issues warnings.
    - **User Management**: Kick and ban users from channels.
- **Flexible Configuration**:
    - Initial setup via a GUI dialog or console prompts.
    - Configuration is saved in a `config.ini` file.
    - Many settings can be changed at runtime.

## Requirements

The project requires the following Python dependencies:

- `wxPython`: For the graphical user interface.
- `google-generativeai`: For integration with the Google Gemini API.
- `requests`: For making HTTP requests (e.g., weather service).

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <https://github.com/starkrush123/AI-TeamTalk-bot>>
    cd AI-TeamTalk-Bot
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **TeamTalk SDK**: Ensure the `TeamTalk5.dll` file (or equivalent for your OS) and `TeamTalk5.py` are in the project's root directory.

## Configuration

When you first run the bot, you will be prompted to provide configuration details either through a GUI dialog or console prompts. These settings will be saved to a `config.ini` file.

Here is a breakdown of the configuration sections:

### `[Connection]`
- `host`: The IP address or domain name of the TeamTalk server.
- `port`: The server's TCP port.
- `nickname`: The nickname for the bot.
- `username`: The username for the bot's account (if required).
- `password`: The password for the bot's account (if required).
- `channel`: The target channel path (e.g., `/Public/Channel 1`).
- `channel_password`: The password for the target channel (if required).

### `[Bot]`
- `client_name`: The client name to be displayed in TeamTalk.
- `status_message`: A status message for the bot.
- `admin_usernames`: A comma-separated list of admin usernames.
- `reconnect_delay_min`/`max`: The time range (in seconds) to wait before attempting to reconnect.
- `gemini_api_key`: Your Google Gemini API key.
- `weather_api_key`: Your API key for a weather service.
- `filtered_words`: A comma-separated list of words to filter.
- `ai_system_instructions`: Default instructions for the AI.

## Usage

You can run the bot in either GUI or Console mode.

### GUI Mode (Recommended)

Run `main_gui.py` to start the bot with the graphical user interface.

```bash
python main_gui.py
```
The GUI provides a real-time log, a list of toggleable features, and bot management controls.

### Console Mode

Run `main.py` to start the bot in headless mode.

```bash
python main.py
```
In this mode, the bot will run in your console. You can manage it using the **Interactive Shell**.

## Interactive Shell (Console Mode Only)

When running in console mode, you can use the following commands in the terminal to manage the bot:

- `help`: Displays the help message.
- `status`: Shows the current status of all toggleable features.
- `toggle <feature>`: Toggles a feature ON or OFF. Available features: `jcl`, `chanmsg`, `broadcast`, `geminipm`, `geminichan`, `filter`, `lock`, `context_history`, `debug_logging`.
- `set_retention <minutes>`: Sets the AI context history retention period.
- `exit` / `quit`: Stops the bot and exits the application.

## Command List

### User Commands (Available to everyone)

These commands can be used in a private message (PM) to the bot. Some are also available in channels.

**PM Commands:**
- `h`: Displays a help message with a list of all available commands.
- `c <question>`: Asks a question to the Gemini AI.
- `w <location>`: Gets the current weather for a specific location.
- `info`: Displays information about the bot.
- `whoami`: Shows your username and user ID.
- `!poll <question>; <option1>; <option2>; ...`: Creates a new poll.
- `!vote <poll_id> <option_id>`: Casts a vote in an active poll.
- `!results <poll_id>`: Displays the results of a poll.
- `admins`: Lists all currently online bot admins.
- `users`: Lists all users on the server.
- `uptime`: Shows the bot's current uptime.

**Channel Commands:**
- `/w <location>`: Gets the current weather.
- `/c <question>`: Asks a question to the AI in the channel (if enabled).
- `/instruct <instructions>`: Gives the AI temporary instructions for the next interaction in the channel.

### Admin Commands (Admin Only)

These commands can only be used by users registered as admins.

- `q`: Shuts down the bot.
- `rs`: Restarts the bot.
- `lock`: Locks the bot, ignoring all non-essential commands.
- `block <command>`: Blocks a command from being used.
- `unblock <command>`: Unblocks a command.
- `blocked`: Lists all blocked commands.
- `!setnick <new_nickname>`: Changes the bot's nickname.
- `!setstatus <new_message>`: Changes the bot's status message.
- `!savecfg`: Saves the current configuration to `config.ini`.
- `!addword <word>`: Adds a word to the word filter.
- `!delword <word>`: Removes a word from the word filter.
- `!kick <nickname>`: Kicks a user from the channel.
- `!ban <nickname>`: Bans a user from the channel.
- `!join <channel_path>`: Makes the bot join another channel.
- `!tfilter`: Toggles the word filter ON/OFF.
- `!tjcl`: Toggles join/leave announcements ON/OFF.
- `!tchanmsg`: Allows/disallows the bot from sending messages in the channel.
- `!tbroadcast`: Allows/disallows the bot from sending broadcasts.
- `!tgeminipm`: Toggles the AI in PMs ON/OFF.
- `!tgeminichan`: Toggles the AI in channels ON/OFF.
- `!tgmmode`: Toggles the welcome message mode (template/gemini).
- `!setmodel <model_name>`: Sets the Gemini AI model to use.
- `!models`: Lists all available Gemini models.
- `!setinstructions <instructions>`: Sets the permanent system instructions for the AI.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
