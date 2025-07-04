
import logging

def handle_set_gapi(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: gapi <your_gemini_api_key>"); return

    new_api_key = args_str.strip()
    original_api_key = bot.gemini_service.api_key # Store original key

    # Temporarily set and try to initialize with the new key
    bot.gemini_service.api_key = new_api_key
    bot.gemini_service.init_model()

    if bot.gemini_service.is_enabled():
        bot.allow_gemini_pm = True
        bot.allow_gemini_channel = True
        feedback = "Gemini API key updated and initialized successfully."
        bot._save_runtime_config(save_gemini_key=True)
    else:
        # If initialization failed, revert to original key and disable Gemini features
        bot.gemini_service.api_key = original_api_key # Revert API key
        bot.gemini_service.init_model() # Re-initialize with original key
        bot.allow_gemini_pm = False
        bot.allow_gemini_channel = False
        feedback = "Gemini API key provided is invalid or failed to initialize model. Key not saved."
    
    bot._send_pm(msg_from_id, feedback)
    if bot.main_window: bot.main_window.update_feature_list()

def handle_list_gemini_models(bot, msg_from_id, **kwargs):
    if not bot.gemini_service.is_enabled():
        bot._send_pm(msg_from_id, "Gemini service is not enabled. Cannot list models."); return
    
    models = bot.gemini_service.list_available_models()
    if models:
        model_list_str = "Available Gemini Models:\n" + "\n".join(models)
        bot._send_pm(msg_from_id, model_list_str)
    else:
        bot._send_pm(msg_from_id, "No Gemini models found or failed to retrieve list.")

def handle_set_gemini_model(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: set_gemini_model <model_name>"); return
    
    new_model_name = args_str.strip()
    if bot.set_gemini_model(new_model_name):
        bot._send_pm(msg_from_id, f"Gemini model set to '{new_model_name}' successfully.")
    else:
        bot._send_pm(msg_from_id, f"Failed to set Gemini model to '{new_model_name}'. Check model name and API key.")

def handle_set_context_retention(bot, msg_from_id, args_str, **kwargs):
    try:
        retention_minutes = int(args_str.strip())
        if retention_minutes < 0:
            raise ValueError("Retention minutes cannot be negative.")
        
        bot.context_history_manager.set_retention_minutes(retention_minutes)
        bot.config['Bot']['context_history_retention_minutes'] = str(retention_minutes)
        bot._save_runtime_config()
        bot._send_pm(msg_from_id, f"Context history retention set to {retention_minutes} minutes.")
    except ValueError:
        bot._send_pm(msg_from_id, "Usage: set_context_retention <minutes> (e.g., set_context_retention 60)")
    except Exception as e:
        logging.error(f"Error setting context retention: {e}")
        bot._send_pm(msg_from_id, f"[Error] Failed to set context retention: {e}")

def handle_add_word(bot, msg_from_id, args_str, **kwargs):
    word = args_str.strip().lower()
    if not word:
        bot._send_pm(msg_from_id, "Usage: addword <word>"); return
    bot.filtered_words.add(word)
    bot.filter_enabled = True
    bot._save_runtime_config()
    bot._send_pm(msg_from_id, f"Word '{word}' added to filter. Filter enabled.")

def handle_del_word(bot, msg_from_id, args_str, **kwargs):
    word = args_str.strip().lower()
    if not word:
        bot._send_pm(msg_from_id, "Usage: delword <word>"); return
    bot.filtered_words.discard(word)
    if not bot.filtered_words:
        bot.filter_enabled = False
    bot._save_runtime_config()
    bot._send_pm(msg_from_id, f"Word '{word}' removed from filter.")

def handle_set_ai_system_instructions(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: set_ai_system_instructions <instructions>"); return
    instructions = args_str.strip()
    if bot.set_ai_system_instructions(instructions):
        bot._send_pm(msg_from_id, "AI system instructions updated.")
    else:
        bot._send_pm(msg_from_id, "Failed to update AI system instructions.")

def handle_set_welcome_instruction(bot, msg_from_id, args_str, **kwargs):
    if not args_str:
        bot._send_pm(msg_from_id, "Usage: setwelcomeinstruction <instructions>"); return
    instructions = args_str.strip()
    if bot.set_welcome_message_instructions(instructions):
        bot._send_pm(msg_from_id, "Welcome message instructions updated.")
    else:
        bot._send_pm(msg_from_id, "Failed to update welcome message instructions.")
