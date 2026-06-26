import requests
from plugins.plugin_base import Plugin
import re
import json
import os
from datetime import datetime

class weatherPlugin(Plugin):   
    def coords_from_loc(self, loc):
        geocodeurl = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "M.A.R.V.I.N. v1.0 (goldtitaniumalloy72@gmail.com)"
        }
        params = {
            "q": loc,
            "format": "json",
            "limit": 1
        }
    
        response = requests.get(geocodeurl, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
    
        if not results:
            raise ValueError(f"location'{loc}' not found.")
    
        lat = float(results[0]["lat"])
        long = float(results[0]["lon"])
    
        return lat, long
    
    def can_handle(self, message: str) -> bool:
        return "[WEATHER]" in message and "[/WEATHER]" in message
    
    def handle(self, message, apiKey="apikey", savedDataPath="/home/pi/marvin/plugins/plugin_info/weather_saved.json") -> list[str]:
        pattern = r"\[WEATHER\](.*?)\[/WEATHER\]"
        calc_blocks = re.findall(pattern, message, re.DOTALL)

        url = "https://api.tomorrow.io/v4/weather/realtime?location={}, {}&apikey={}"
        
        weather_code_map = {
            0: "Unknown",
            1000: "Clear",
            1001: "Cloudy",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            3000: "Light Wind",
            3001: "Wind",
            3002: "Strong Wind",
            4000: "Drizzle",
            4001: "Rain",
            4200: "Light Rain",
            4201: "Heavy Rain",
            5000: "Snow",
            5001: "Flurries",
            5100: "Light Snow",
            5101: "Heavy Snow",
            6000: "Freezing Drizzle",
            6001: "Freezing Rain",
            6200: "Light Freezing Rain",
            6201: "Heavy Freezing Rain",
            7000: "Ice Pellets",
            7101: "Heavy Ice Pellets",
            7102: "Light Ice Pellets",
            8000: "Thunderstorm"
        }
    
        results = []
        
        if os.path.exists(savedDataPath):
            with open(savedDataPath, "r") as file:
                saved_data = json.load(file)
        
        for block in calc_blocks:
            try:
                if saved_data.get(block.strip(), "NA") != "NA":
                    long = saved_data[block.strip()]["long"]
                    lat = saved_data[block.strip()]["lat"]
                else:
                    lat, long = self.coords_from_loc(block)
            except ValueError:
                print("\033[38;2;255;60;60mcould not find location!\nskipping...\033[0m")
                results.append(f"error: could not find {block}")
                continue
            except KeyError:
                print("\033[38;2;255;60;60mlocation not saved!\nskipping...\033[0m")
                results.append(f"error: could not find {block}")
                continue
                
            data = requests.get(url.format(lat, long, apiKey)).json()
            
            values = data["data"]["values"]
            location = data["location"]
            time = data["data"]["time"]
            
            
            weather_overall = weather_code_map.get(values.get('weatherCode', '0'), 'unknown')
            current_datetime = datetime.now().strftime('%m/%d/%Y, %H:%M:%S)
            summary = (
                f"the current time is {current_datetime}"
                f"the current weather in {block}(lat: {lat}, long: {long}) is:\n{weather_overall}\n"
                f"temperature: {values['temperature']} degrees Celcius\n"
                f"apparentTemperature: {values['temperatureApparent']} degrees Celcius\n"
                f"humidity: {values.get('humidity', 'NA')}%\n"
                f"cloudCover: {values.get('cloudCover', 'NA')}%\n"
                f"wind direction: {values.get('windDirection', 0)} degrees clockwise from north\n"
                f"wind speed: {values.get('windSpeed', 0)} metres/s\n"
                f"rain intensity: {values.get('rainIntensity', 'NA')} mm/hr\n"
            )
            
            results.append(summary)
            
        return results


