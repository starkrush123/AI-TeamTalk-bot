# AI TeamTalk Bot

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)

An advanced TeamTalk bot integrated with Google Gemini AI to provide intelligent chat functionality, moderation, and interactive commands. The bot can be run in a GUI mode (using wxPython) or as a standalone console application, and now features a web-based control panel.

- **Author**: [starkrush123](https://github.com/starkrush123)

## Key Features

- **TeamTalk Integration**: Connects to a TeamTalk server, joins channels, and interacts with users.
- **Web-based Control Panel (Web UI)**: Manage your bot remotely via a modern, responsive web interface.
    - **Secure Authentication**: User management system with database-backed authentication (SQLite by default).
    - **Tabbed Interface**: Organized control panel with dedicated tabs for Status, Settings, User Management, and Logs.
- **Artificial Intelligence (AI)**:
    - Integrated with **Google Gemini** to answer questions in PMs and channels.
    - **Context History**: Remembers previous conversations within a session for more relevant responses.
    - **System Instructions**: Ability to give the AI custom instructions to tailor its behavior.
- **Hariku API Integration**:
    - Hariku is a keyboard-focused daily companion designed to help you manage your time with intention and clarity. It integrates essential tools such as a personal journal, to-do lists, daily quotes, date insights, and updates into one seamless space. For more information, visit the [Hariku homepage](https://www.techlabs.lol/hariku/index.php). It is developed by **TechLabs**.
    - The bot is now fully integrated with Gemini AI, allowing users to interact with Hariku services (such as getting quotes and event information) using natural language queries. The Gemini AI will intelligently call the relevant Hariku functions based on your requests. Please note that this integration is still under active development, and the AI may sometimes return incorrect tool call responses.
- **Command System**:
    - Separate commands for private messages (PM) and channel messages.
    - Admin access level for powerful commands.
    - Configurable and blockable command handling.
- **Multi Operation Modes**:
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
    - Many settings can be changed at runtime, now primarily via the Web UI.

## Requirements

The project requires the following Python dependencies:

- `wxPython`: For the graphical user interface.
- `google-generativeai`: For integration with the Google Gemini API.
- `requests`: For making HTTP requests (e.g., weather service).
- `SQLAlchemy`: For database ORM.
- `Flask-SQLAlchemy`: Flask extension for SQLAlchemy.

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <https://github.com/starkrush123/AI-TeamTalk-bot>
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
**It is highly recommended to manage configuration via the Web UI for ease of use and remote access.**

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
- `hariku_api_key`: Your Hariku API key.
- `filtered_words`: A comma-separated list of words to filter.
- `ai_system_instructions`: Default instructions for the AI.

## Usage

You can run the bot in GUI, Console, or Web UI mode.

### Web UI Mode (Recommended for remote management)

Run `web_ui.py` to start the web-based control panel.

```bash
python web_ui.py
```
Open your web browser and navigate to `http://127.0.0.1:5000/`.

#### First-Time Setup: Creating a Super Admin

The first time you run the Web UI, you will be redirected to a registration page. The first user account created will automatically be assigned the **Super Admin** role. This account will have full control over the bot, including user management and system configuration.

#### User Roles

The control panel has two distinct user roles:

-   **Super Admin**:
    -   Can start, stop, and restart the bot.
    -   Can toggle all operational features.
    -   Can view logs.
    -   Can manage all bot settings and configuration.
    -   Can add, edit, and remove other users (both Admins and Super Admins).
-   **Admin**:
    -   Can start, stop, and restart the bot.
    -   Can toggle all operational features.
    -   Can view logs.
    -   **Cannot** manage users or change the bot's core configuration.

You can manage bot status, features, configuration, and users through the intuitive web interface after logging in.

### GUI Mode

Run `main_gui.py` to start the bot with the graphical user interface.

```bash
python main_gui.py
```
The GUI provides a real-time log, a list of toggleable features, and bot management controls.

### Console Mode (Headless)

Run `main.py` to start the bot in headless mode.

```bash
python main.py
```
In this mode, the bot will run in your console without an interactive shell. Management is primarily done via the Web UI.

## Command List

### User Commands (Available to everyone)

These commands can be used in a private message (PM) to the bot. Some are also available in channels as noted.

- `h`: Displays this help message.
- `ping`: Checks if the bot is responding.
- `info`: Displays bot status and server info.
- `whoami`: Shows your user info.
- `rights`: Shows the bot's permissions.
- `cn <new_nick>`: Changes the bot's nickname.
- `cs <new_status>`: Changes the bot's status message.
- `w <location>`: Gets the current weather (also available as `/w <location>` in channels).
- `c <question>`: Asks the Gemini AI a question via PM.
- `/c <question>`: Asks the Gemini AI a question in the bot's current channel (if enabled).
- `quote`: Retrieves a random quote from the Hariku API. (Also accessible via natural language queries to Gemini AI, e.g., "Tell me a random quote.")
- `event`: Retrieves event information from the Hariku API. (Also accessible via natural language queries to Gemini AI, e.g., "What events are happening today?")
- `poll "Question" "Option A" "Option B" ...`: Creates a new poll.
- `vote <poll_id> <option_number>`: Casts a vote in an active poll.
- `results <poll_id>`: Displays the results of a poll.

### Admin Commands (Admin Only)

These commands can only be used by users registered as admins in the bot's config.

#### Bot Control & Toggles
- `q`: Shuts down the bot.
- `rs`: Restarts the bot.
- `lock`: Locks the bot, ignoring all non-admin commands.
- `block <command>`: Blocks a user command.
- `unblock <command>`: Unblocks a user command.
- `jcl`: Toggles join/leave announcements ON/OFF.
- `tg_chanmsg`: Toggles the bot's ability to send messages in the channel.
- `tg_broadcast`: Toggles the bot's ability to send broadcast messages.
- `tfilter`: Toggles the word filter ON/OFF.

#### AI & Configuration
- `gapi <api_key>`: Sets the Gemini API key.
- `harikuapi <api_key>`: Sets the Hariku API key.
- `list_gemini_models` / `lgm`: Lists available Gemini models.
- `set_gemini_model <model_name>` / `sgm <model_name>`: Sets the active Gemini model.
- `instruct <instructions>`: Sets the permanent system instructions for the AI.
- `setwelcomeinstruction <instructions>`: Sets the instructions for the AI-powered welcome message.
- `tg_gemini_pm`: Toggles the AI in PMs ON/OFF.
- `tg_gemini_chan`: Toggles the AI in channels ON/OFF.
- `tgmmode`: Toggles the welcome message mode (template vs. Gemini).
- `tg_context_history`: Toggles the context history feature ON/OFF.
- `set_context_retention <minutes>`: Sets the AI context history retention period.
- `tg_debug_logging`: Toggles debug logging ON/OFF.

#### Moderation & User Management
- `addword <word>`: Adds a word to the word filter.
- `delword <word>`: Removes a word from the word filter.
- `listusers [channel_path]`: Lists users in the specified channel (or current channel if none specified).
- `listchannels`: Lists all channels on the server.
- `admins`: Lists all configured bot admins and their online status.
- `kick <nickname>`: Kicks a user from the bot's current channel.
- `ban <nickname>`: Bans a user from the server.
- `unban <username>`: Unban a user from the server.
- `move <nickname> <channel_path>`: Moves a user to the specified channel.

#### Communication & Channel
- `jc <channel_path>[|password]`: Makes the bot join another channel.
- `ct <message>`: Sends a message to the bot's current channel.
- `bm <message>`: Sends a broadcast message to the entire server.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.