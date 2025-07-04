
import logging
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self._enabled = REQUESTS_AVAILABLE and bool(self.api_key)
        self.base_url = "[http://api.openweathermap.org/data/2.5/weather](http://api.openweathermap.org/data/2.5/weather)?"

    def is_enabled(self):
        return self._enabled

    def get_weather(self, location):
        if not self.is_enabled():
            return "[Bot] Weather feature is disabled (check API key/library)."

        complete_url = self.base_url + "appid=" + self.api_key + "&q=" + location + "&units=metric"
        
        try:
            response = requests.get(complete_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("cod") != 200 and data.get("cod") != "200":
                return f"[Weather Error] {data.get('message', 'Unknown API error')}."

            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            sys_info = data.get("sys", {})

            temp = main.get("temp", "N/A")
            feels_like = main.get("feels_like", "N/A")
            humidity = main.get("humidity", "N/A")
            description = weather.get("description", "N/A").capitalize()
            wind_speed = wind.get("speed", "N/A")
            city_name = data.get("name", location)
            country = sys_info.get("country", "")

            wind_kmh = f"{wind_speed * 3.6:.1f} km/h" if isinstance(wind_speed, (int, float)) else "N/A"

            return (f"Weather in {city_name}, {country}: {description}. "
                    f"Temp: {temp}°C (Feels like: {feels_like}°C). "
                    f"Humidity: {humidity}%. Wind: {wind_kmh}.")

        except requests.exceptions.Timeout:
             return f"[Weather Error] Request timed out for '{location}'."
        except requests.exceptions.RequestException:
            return f"[Weather Error] Could not fetch weather for '{location}'. Check location."
        except Exception as e:
             logging.error(f"Unexpected weather error for {location}: {e}", exc_info=True)
             return f"[Weather Error] An unexpected error occurred."
