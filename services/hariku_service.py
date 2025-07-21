import logging
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

hariku_logger = logging.getLogger(__name__)
hariku_logger.setLevel(logging.INFO)

class HarikuService:
    def __init__(self, api_key):
        self.api_key = api_key
        self._enabled = REQUESTS_AVAILABLE and bool(self.api_key)
        hariku_logger.info(f"HarikuService initialized. Requests available: {REQUESTS_AVAILABLE}, API Key present: {bool(self.api_key)}, Enabled: {self._enabled}")
        self.base_url_quotes = "https://www.techlabs.lol/hariku/quotes/"
        self.base_url_calendar = "https://www.techlabs.lol/hariku/calendar/"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def is_enabled(self):
        return self._enabled

    def get_random_quote(self, lang="en"):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_quotes}{lang}/random"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            hariku_logger.info(f"Hariku API raw response: {data}")
            if data and data.get('quote_text'):
                return f"\"{data['quote_text']}\" - {data.get('author', 'Unknown')}"
            return "[Hariku API] Could not retrieve a quote."
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for random quote: {e}")
            return f"[Hariku API Error] Failed to fetch quote: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_random_quote: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_today_events(self, country_code="ID"):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
            
        url = f"{self.base_url_calendar}{country_code}/today"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for today in {country_code}."

            events = [f"- {event.get('event_name')}" for event in data]
            if not events:
                return f"No events found for today in {country_code}."

            return f"Today's Events in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for today's events: {e}")
            return f"[Hariku API Error] Failed to fetch events: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_today_events: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_quote_by_id(self, quote_id, lang="ID"):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_quotes}{lang}/id/{quote_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            hariku_logger.info(f"Hariku API raw response for ID {quote_id}: {data}")
            if data and data.get("quote_text"):
                return f"\"{data['quote_text']}\" - {data.get('author', 'Unknown')}"
            return f"[Hariku API] Could not retrieve quote with ID {quote_id}."
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for quote ID {quote_id}: {e}")
            return f"[Hariku API Error] Failed to fetch quote by ID: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_quote_by_id: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_events_by_date(self, country_code, date_str):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_calendar}{country_code}/date/{date_str}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for {date_str} in {country_code}."

            events = [f"- {event.get('event_name')}" for event in data]
            if not events:
                return f"No events found for {date_str} in {country_code}."

            return f"Events on {date_str} in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for events on {date_str}: {e}")
            return f"[Hariku API Error] Failed to fetch events: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_events_by_date: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_events_by_week(self, country_code, date_str):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_calendar}{country_code}/week/{date_str}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for the week starting {date_str} in {country_code}."

            events = [f"- {event.get('event_name')} ({event.get('event_full_date', 'N/A')})" for event in data]
            if not events:
                return f"No events found for the week starting {date_str} in {country_code}."

            return f"Events for the week starting {date_str} in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for events for the week starting {date_str}: {e}")
            return f"[Hariku API Error] Failed to fetch events: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_events_by_week: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_events_by_month(self, country_code, month_str):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_calendar}{country_code}/month/{month_str}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for {month_str} in {country_code}."

            events = [f"- {event.get('event_name')} ({event.get('event_full_date', 'N/A')})" for event in data]
            if not events:
                return f"No events found for {month_str} in {country_code}."

            return f"Events for {month_str} in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for events for {month_str}: {e}")
            return f"[Hariku API Error] Failed to fetch events: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_events_by_month: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def get_events_by_year(self, country_code, year_str):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_calendar}{country_code}/year/{year_str}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for {year_str} in {country_code}."

            events = [f"- {event.get('event_name')} ({event.get('event_full_date') or 'N/A'})" for event in data]
            if not events:
                return f"No events found for {year_str} in {country_code}."

            return f"Events for {year_str} in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for events for {year_str}: {e}")
            return f"[Hariku API Error] Failed to fetch events: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in get_events_by_year: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def search_events(self, country_code, query):
        if not self.is_enabled():
            return "[Bot] Hariku service is disabled (check API key/library)."
        
        url = f"{self.base_url_calendar}{country_code}/search?q={query}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return f"No events found for '{query}' in {country_code}."

            events = [f"- {event.get('event_name')} ({event.get('event_full_date') or 'N/A'})" for event in data]
            if not events:
                return f"No events found for '{query}' in {country_code}."

            return f"Search results for '{query}' in {country_code}:\n" + "\n".join(events)
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API request error for search query '{query}': {e}")
            return f"[Hariku API Error] Failed to fetch search results: {e}"
        except Exception as e:
            hariku_logger.error(f"Unexpected error in search_events: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."

    def validate_api_key(self, api_key):
        if not REQUESTS_AVAILABLE:
            hariku_logger.warning("Requests library not available, cannot validate Hariku API key.")
            return False
        
        temp_headers = {"Authorization": f"Bearer {api_key}"}
        test_url = f"{self.base_url_quotes}en/random"
        try:
            response = requests.get(test_url, headers=temp_headers, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            hariku_logger.error(f"Hariku API key validation failed: {e}")
            return False
        except Exception as e:
            hariku_logger.error(f"Unexpected error during Hariku API key validation: {e}", exc_info=True)
            return "[Hariku API Error] An unexpected error occurred."
