
import logging
import threading
try:
    import google.generativeai as genai
    from google.generativeai.types import StopCandidateException
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
    def __init__(self, api_key, context_history_enabled=True, model_name: str = 'gemini-1.5-flash-latest', system_instructions: str = '', welcome_instructions: str = '', hariku_service=None):
        self.api_key = api_key
        self._model_name = self._strip_model_prefix(model_name)
        self.model = None
        self._enabled = False
        self.context_history_enabled = context_history_enabled
        self._system_instructions = system_instructions
        self._welcome_instructions = welcome_instructions # New attribute for welcome message instructions
        self._semaphore = threading.Semaphore(5) # Limit to 5 concurrent API calls
        self.hariku_service = hariku_service
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
            self.model = genai.GenerativeModel(self._model_name, system_instruction=self._system_instructions, tools=self._get_hariku_tools())
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
                self.model = genai.GenerativeModel(self._model_name, system_instruction=self._system_instructions, tools=self._get_hariku_tools())
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

    def _get_hariku_tools(self):
        tools = []
        if self.hariku_service and self.hariku_service.is_enabled():
            tools.append(self.hariku_service.get_random_quote)
            tools.append(self.hariku_service.get_today_events)
            tools.append(self.hariku_service.get_quote_by_id)
            tools.append(self.hariku_service.get_events_by_date)
            tools.append(self.hariku_service.get_events_by_week)
            tools.append(self.hariku_service.get_events_by_month)
            tools.append(self.hariku_service.get_events_by_year)
            tools.append(self.hariku_service.search_events)
        return tools

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
                
                if response.candidates and response.candidates[0].content.parts:
                    logging.debug(f"Gemini response parts: {response.candidates[0].content.parts}")
                    full_text_from_parts = ""

                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            fc = part.function_call
                            if not fc.name:
                                logging.warning("Gemini requested an empty function call name. Skipping tool execution.")
                                continue

                            logging.info(f"Gemini requested function call: {fc.name} with args {fc.args}")
                            if self.hariku_service:
                                try:
                                    func = getattr(self.hariku_service, fc.name)
                                    args_dict = {key: getattr(fc.args, key) for key in fc.args.keys()}
                                    tool_result = func(**args_dict)
                                    logging.info(f"Hariku tool result: {tool_result}")
                                    return tool_result
                                except AttributeError:
                                    logging.error(f"HarikuService does not have method: {fc.name}")
                                    return f"[Gemini Error] Requested tool '{fc.name}' not found."
                                except Exception as tool_e:
                                    logging.error(f"Error executing Hariku tool {fc.name}: {tool_e}", exc_info=True)
                                    return f"[Gemini Error] Failed to execute tool '{fc.name}': {tool_e}"
                            else:
                                return "[Gemini Error] Hariku service not available to execute tool."
                        elif hasattr(part, 'text'):
                            full_text_from_parts += part.text

                    if full_text_from_parts.strip():
                        return full_text_from_parts
                
                # Fallback to response.text if no parts or no relevant content in parts
                if hasattr(response, 'text') and response.text.strip():
                    return response.text.strip()

                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                     return f"[Gemini Error] Request blocked: {response.prompt_feedback.block_reason.name}"

                return "[Gemini] (Received an empty response or unhandled content)"
        except StopCandidateException as e:
            logging.error(f"Gemini StopCandidateException: {e}")
            if e.candidate and e.candidate.function_calls:
                for fc in e.candidate.function_calls:
                    logging.error(f"Malformed function call: {fc.name} with args {fc.args}")
            return "[Gemini Error] Failed to execute tool. Please check logs for details."
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
                
                if response.candidates and response.candidates[0].content.parts:
                    logging.debug(f"Gemini response parts: {response.candidates[0].content.parts}")
                    full_text_from_parts = ""

                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            fc = part.function_call
                            if not fc.name:
                                logging.warning("Gemini requested an empty function call name. Skipping tool execution.")
                                continue

                            logging.info(f"Gemini requested function call: {fc.name} with args {fc.args}")
                            if self.hariku_service:
                                try:
                                    func = getattr(self.hariku_service, fc.name)
                                    args_dict = {key: getattr(fc.args, key) for key in fc.args.keys()}
                                    tool_result = func(**args_dict)
                                    logging.info(f"Hariku tool result: {tool_result}")
                                    return tool_result
                                except AttributeError:
                                    logging.error(f"HarikuService does not have method: {fc.name}")
                                    return f"[Gemini Error] Requested tool '{fc.name}' not found."
                                except Exception as tool_e:
                                    logging.error(f"Error executing Hariku tool {fc.name}: {tool_e}", exc_info=True)
                                    return f"[Gemini Error] Failed to execute tool '{fc.name}': {tool_e}"
                            else:
                                return "[Gemini Error] Hariku service not available to execute tool."
                        elif hasattr(part, 'text'):
                            full_text_from_parts += part.text

                    if full_text_from_parts.strip():
                        return full_text_from_parts
                
                # Fallback to response.text if no parts or no relevant content in parts
                if hasattr(response, 'text') and response.text.strip():
                    return response.text.strip()

                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                     return f"[Gemini Error] Request blocked: {response.prompt_feedback.block_reason.name}"

                return "[Gemini] (Received an empty response or unhandled content)"
        except StopCandidateException as e:
            logging.error(f"Gemini StopCandidateException: {e}")
            if e.candidate and e.candidate.function_calls:
                for fc in e.candidate.function_calls:
                    logging.error(f"Malformed function call: {fc.name} with args {fc.args}")
            return "[Gemini Error] Failed to execute tool. Please check logs for details."
        except Exception as e:
            logging.error(f"Error during Gemini API call: {e}", exc_info=True)
            return "[Bot Error] Error contacting Gemini."

    def generate_welcome_message(self, nickname: str) -> str:
        if not self.is_enabled():
            return ""
        prompt = f"Generate a short, friendly welcome message for a new user named {nickname} joining a chat. Keep it concise and welcoming."
        return self.generate_simple_content(prompt, model_to_use=self.welcome_model)
