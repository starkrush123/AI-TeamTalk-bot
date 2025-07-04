
import logging
import threading
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

class GeminiService:
    def __init__(self, api_key, context_history_enabled=True, model_name: str = 'gemini-1.5-flash-latest', system_instructions: str = '', welcome_instructions: str = ''):
        self.api_key = api_key
        self._model_name = self._strip_model_prefix(model_name)
        self.model = None
        self._enabled = False
        self.context_history_enabled = context_history_enabled
        self._system_instructions = system_instructions
        self._welcome_instructions = welcome_instructions # New attribute for welcome message instructions
        self._semaphore = threading.Semaphore(5) # Limit to 5 concurrent API calls
        self.init_model()

    def _strip_model_prefix(self, model_name: str) -> str:
        if model_name and model_name.startswith("models/"):
            return model_name[len("models/"):]
        return model_name

    def _add_model_prefix(self, model_name: str) -> str:
        if model_name and not model_name.startswith("models/"):
            return "models/" + model_name
        return model_name

    def init_model(self, model_name: str = None):
        if not GEMINI_AVAILABLE or not self.api_key:
            self._enabled = False
            self.model = None
            self.welcome_model = None
            return

        if model_name: # Allow dynamic model change
            self._model_name = self._strip_model_prefix(model_name)

        try:
            genai.configure(api_key=self.api_key)
            list(genai.list_models()) # Verify API key
            self.model = genai.GenerativeModel(self._model_name, system_instruction=self._system_instructions)
            logging.info(f"Main Gemini model '{self._model_name}' initialized successfully.")
            self._enabled = True
        except Exception as e:
            logging.error(f"Failed to initialize main Gemini model '{self._model_name}' or verify API key: {e}. Main features will be disabled.")
            self.model = None
            self._enabled = False

        # Initialize welcome model separately
        try:
            if self._enabled: # Only try if main model is enabled
                self.welcome_model = genai.GenerativeModel(self._model_name, system_instruction=self._welcome_instructions)
                logging.info(f"Welcome Gemini model '{self._model_name}' initialized successfully.")
            else:
                self.welcome_model = None
        except Exception as e:
            logging.error(f"Failed to initialize welcome Gemini model '{self._model_name}': {e}. Welcome messages will use template.")
            self.welcome_model = None

    def set_system_instructions(self, instructions: str):
        self._system_instructions = instructions
        # Re-initialize only the main model
        if self._enabled and self.model:
            try:
                self.model = genai.GenerativeModel(self._model_name, system_instruction=self._system_instructions)
                logging.info("Main Gemini model system instructions updated.")
            except Exception as e:
                logging.error(f"Failed to update main Gemini model system instructions: {e}")

    def set_welcome_instructions(self, instructions: str):
        self._welcome_instructions = instructions
        # Re-initialize only the welcome model
        if self._enabled and self.welcome_model:
            try:
                self.welcome_model = genai.GenerativeModel(self._model_name, system_instruction=self._welcome_instructions)
                logging.info("Welcome Gemini model system instructions updated.")
            except Exception as e:
                logging.error(f"Failed to update welcome Gemini model system instructions: {e}")

    def is_enabled(self):
        return self._enabled and self.model is not None

    def get_current_model_name(self):
        return self._add_model_prefix(self._model_name)

    def list_available_models(self) -> list[str]:
        if not GEMINI_AVAILABLE or not self.api_key:
            return []
        try:
            genai.configure(api_key=self.api_key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return models
        except Exception as e:
            logging.error(f"Failed to list Gemini models: {e}")
            return []

    def generate_content(self, prompt, history=None):
        if not self.is_enabled():
            return "[Gemini Error] Service not available."

        try:
            with self._semaphore:
                if history and self.context_history_enabled:
                    # Format history for Gemini chat
                    formatted_history = []
                    for msg in history:
                        role = "model" if msg['is_bot'] else "user"
                        if msg['is_bot']:
                            formatted_message = msg['message']
                        else:
                            formatted_message = f"{msg['sender_nick']}: {msg['message']}"
                        formatted_history.append({'role': role, 'parts': [formatted_message]})
                    
                    chat = self.model.start_chat(history=formatted_history)
                    response = chat.send_message(prompt, stream=False, safety_settings=GEMINI_SAFETY_SETTINGS)
                else:
                    response = self.model.generate_content(prompt, stream=False, safety_settings=GEMINI_SAFETY_SETTINGS)
                
                if hasattr(response, 'text') and response.text.strip():
                    return response.text
                elif hasattr(response, 'parts') and response.parts:
                    full_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                    if full_text.strip(): return full_text
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                     return f"[Gemini Error] Request blocked: {response.prompt_feedback.block_reason.name}"
                
                return "[Gemini] (Received an empty response)"
        except Exception as e:
            logging.error(f"Error during Gemini API call: {e}", exc_info=True)
            return "[Bot Error] Error contacting Gemini."

    def generate_simple_content(self, prompt: str, model_to_use=None) -> str:
        if not self.is_enabled():
            return "[Gemini Error] Service not available."
        
        if model_to_use is None:
            model_to_use = self.model

        try:
            with self._semaphore:
                response = model_to_use.generate_content(prompt, stream=False, safety_settings=GEMINI_SAFETY_SETTINGS)
                
                if hasattr(response, 'text') and response.text.strip():
                    return response.text
                elif hasattr(response, 'parts') and response.parts:
                    full_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                    if full_text.strip(): return full_text
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                     return f"[Gemini Error] Request blocked: {response.prompt_feedback.block_reason.name}"
                
                return "[Gemini] (Received an empty response)"
        except Exception as e:
            logging.error(f"Error during Gemini API call: {e}", exc_info=True)
            return "[Bot Error] Error contacting Gemini."

    def generate_welcome_message(self, nickname: str) -> str:
        if not self.is_enabled():
            return ""
        prompt = f"Generate a short, friendly welcome message for a new user named {nickname} joining a chat. Keep it concise and welcoming."
        return self.generate_simple_content(prompt, model_to_use=self.welcome_model)
