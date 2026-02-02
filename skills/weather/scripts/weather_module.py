#!/usr/bin/env python3
"""
Weather Module for ChatGPT Skills
Supports multiple free weather APIs (no API key required)

Data Sources:
- Open-Meteo (default): Free, no API key, global coverage
- wttr.in: Free, simple text/JSON weather

Usage:
    from weather_module import WeatherClient

    client = WeatherClient()

    # Get current weather
    weather = client.get_current("Beijing")
    weather = client.get_current("New York")
    weather = client.get_current(lat=39.9, lon=116.4)

    # Get forecast
    forecast = client.get_forecast("Shanghai", days=7)

    # Get hourly forecast
    hourly = client.get_hourly("Tokyo", hours=24)

Command Line:
    python3 weather_module.py current Beijing
    python3 weather_module.py current "New York"
    python3 weather_module.py forecast Shanghai --days 7
    python3 weather_module.py hourly Tokyo --hours 24
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union


class WeatherClient:
    """Weather data client using free APIs"""

    # Weather code descriptions (WMO codes used by Open-Meteo)
    WMO_CODES = {
        0: ("Clear sky", "晴"),
        1: ("Mainly clear", "晴间多云"),
        2: ("Partly cloudy", "多云"),
        3: ("Overcast", "阴"),
        45: ("Fog", "雾"),
        48: ("Depositing rime fog", "雾凇"),
        51: ("Light drizzle", "小毛毛雨"),
        53: ("Moderate drizzle", "毛毛雨"),
        55: ("Dense drizzle", "大毛毛雨"),
        56: ("Light freezing drizzle", "小冻雨"),
        57: ("Dense freezing drizzle", "冻雨"),
        61: ("Slight rain", "小雨"),
        63: ("Moderate rain", "中雨"),
        65: ("Heavy rain", "大雨"),
        66: ("Light freezing rain", "小冻雨"),
        67: ("Heavy freezing rain", "大冻雨"),
        71: ("Slight snow", "小雪"),
        73: ("Moderate snow", "中雪"),
        75: ("Heavy snow", "大雪"),
        77: ("Snow grains", "雪粒"),
        80: ("Slight rain showers", "小阵雨"),
        81: ("Moderate rain showers", "阵雨"),
        82: ("Violent rain showers", "大阵雨"),
        85: ("Slight snow showers", "小阵雪"),
        86: ("Heavy snow showers", "大阵雪"),
        95: ("Thunderstorm", "雷暴"),
        96: ("Thunderstorm with slight hail", "雷暴伴小冰雹"),
        99: ("Thunderstorm with heavy hail", "雷暴伴冰雹"),
    }

    # Geocoding cache
    _geo_cache = {}

    def __init__(self, lang: str = "zh"):
        """
        Initialize weather client

        Args:
            lang: Language for descriptions ("zh" for Chinese, "en" for English)
        """
        self.lang = lang
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    def _geocode(self, location: str) -> Optional[Dict]:
        """Convert location name to coordinates"""
        if location in self._geo_cache:
            return self._geo_cache[location]

        try:
            params = urllib.parse.urlencode({
                "name": location,
                "count": 1,
                "language": "en"
            })
            url = f"{self.geocoding_url}?{params}"

            req = urllib.request.Request(url, headers={"User-Agent": "WeatherModule/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    geo_data = {
                        "name": result.get("name"),
                        "country": result.get("country"),
                        "admin1": result.get("admin1"),  # State/Province
                        "lat": result.get("latitude"),
                        "lon": result.get("longitude"),
                        "timezone": result.get("timezone")
                    }
                    self._geo_cache[location] = geo_data
                    return geo_data
                return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def _get_weather_description(self, code: int) -> str:
        """Get weather description from WMO code"""
        if code in self.WMO_CODES:
            return self.WMO_CODES[code][1 if self.lang == "zh" else 0]
        return "Unknown"

    def _fetch_weather(self, lat: float, lon: float, params: Dict) -> Optional[Dict]:
        """Fetch weather data from Open-Meteo API"""
        try:
            base_params = {
                "latitude": lat,
                "longitude": lon,
                "timezone": "auto"
            }
            base_params.update(params)

            query = urllib.parse.urlencode(base_params)
            url = f"{self.weather_url}?{query}"

            req = urllib.request.Request(url, headers={"User-Agent": "WeatherModule/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return None

    def get_current(
        self,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Get current weather for a location

        Args:
            location: City name (e.g., "Beijing", "New York")
            lat: Latitude (alternative to location)
            lon: Longitude (alternative to location)

        Returns:
            Dict with current weather data
        """
        # Get coordinates
        if location:
            geo = self._geocode(location)
            if not geo:
                return {"error": f"Location not found: {location}"}
            lat, lon = geo["lat"], geo["lon"]
            location_info = geo
        elif lat is not None and lon is not None:
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}"}
        else:
            return {"error": "Please provide location or lat/lon coordinates"}

        # Fetch current weather
        params = {
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl"
        }

        data = self._fetch_weather(lat, lon, params)
        if not data or "current" not in data:
            return {"error": "Failed to fetch weather data"}

        current = data["current"]

        return {
            "location": location_info.get("name", location),
            "country": location_info.get("country"),
            "province": location_info.get("admin1"),
            "lat": lat,
            "lon": lon,
            "timestamp": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "pressure": current.get("pressure_msl"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "weather_code": current.get("weather_code"),
            "description": self._get_weather_description(current.get("weather_code", 0)),
            "units": {
                "temperature": "°C",
                "wind_speed": "km/h",
                "pressure": "hPa",
                "precipitation": "mm"
            }
        }

    def get_forecast(
        self,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        days: int = 7
    ) -> Optional[Dict]:
        """
        Get daily weather forecast

        Args:
            location: City name
            lat: Latitude
            lon: Longitude
            days: Number of forecast days (1-16)

        Returns:
            Dict with daily forecast data
        """
        days = min(max(1, days), 16)

        # Get coordinates
        if location:
            geo = self._geocode(location)
            if not geo:
                return {"error": f"Location not found: {location}"}
            lat, lon = geo["lat"], geo["lon"]
            location_info = geo
        elif lat is not None and lon is not None:
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}"}
        else:
            return {"error": "Please provide location or lat/lon coordinates"}

        # Fetch forecast
        params = {
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
            "forecast_days": days
        }

        data = self._fetch_weather(lat, lon, params)
        if not data or "daily" not in data:
            return {"error": "Failed to fetch forecast data"}

        daily = data["daily"]
        forecast_days = []

        for i in range(len(daily["time"])):
            forecast_days.append({
                "date": daily["time"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precipitation": daily["precipitation_sum"][i],
                "precipitation_probability": daily["precipitation_probability_max"][i],
                "wind_speed_max": daily["wind_speed_10m_max"][i],
                "weather_code": daily["weather_code"][i],
                "description": self._get_weather_description(daily["weather_code"][i])
            })

        return {
            "location": location_info.get("name", location),
            "country": location_info.get("country"),
            "lat": lat,
            "lon": lon,
            "forecast": forecast_days,
            "units": {
                "temperature": "°C",
                "wind_speed": "km/h",
                "precipitation": "mm"
            }
        }

    def get_hourly(
        self,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        hours: int = 24
    ) -> Optional[Dict]:
        """
        Get hourly weather forecast

        Args:
            location: City name
            lat: Latitude
            lon: Longitude
            hours: Number of forecast hours (1-168)

        Returns:
            Dict with hourly forecast data
        """
        hours = min(max(1, hours), 168)

        # Get coordinates
        if location:
            geo = self._geocode(location)
            if not geo:
                return {"error": f"Location not found: {location}"}
            lat, lon = geo["lat"], geo["lon"]
            location_info = geo
        elif lat is not None and lon is not None:
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}"}
        else:
            return {"error": "Please provide location or lat/lon coordinates"}

        # Fetch hourly data
        params = {
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "forecast_hours": hours
        }

        data = self._fetch_weather(lat, lon, params)
        if not data or "hourly" not in data:
            return {"error": "Failed to fetch hourly data"}

        hourly = data["hourly"]
        hourly_data = []

        for i in range(min(hours, len(hourly["time"]))):
            hourly_data.append({
                "time": hourly["time"][i],
                "temperature": hourly["temperature_2m"][i],
                "humidity": hourly["relative_humidity_2m"][i],
                "precipitation": hourly["precipitation"][i],
                "precipitation_probability": hourly["precipitation_probability"][i],
                "wind_speed": hourly["wind_speed_10m"][i],
                "weather_code": hourly["weather_code"][i],
                "description": self._get_weather_description(hourly["weather_code"][i])
            })

        return {
            "location": location_info.get("name", location),
            "country": location_info.get("country"),
            "lat": lat,
            "lon": lon,
            "hourly": hourly_data,
            "units": {
                "temperature": "°C",
                "wind_speed": "km/h",
                "precipitation": "mm"
            }
        }

    def get_air_quality(
        self,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Get air quality data

        Args:
            location: City name
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with air quality data
        """
        # Get coordinates
        if location:
            geo = self._geocode(location)
            if not geo:
                return {"error": f"Location not found: {location}"}
            lat, lon = geo["lat"], geo["lon"]
            location_info = geo
        elif lat is not None and lon is not None:
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}"}
        else:
            return {"error": "Please provide location or lat/lon coordinates"}

        try:
            params = urllib.parse.urlencode({
                "latitude": lat,
                "longitude": lon,
                "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
                "timezone": "auto"
            })
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?{params}"

            req = urllib.request.Request(url, headers={"User-Agent": "WeatherModule/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

                if "current" not in data:
                    return {"error": "Failed to fetch air quality data"}

                current = data["current"]
                aqi = current.get("us_aqi", 0)

                # AQI category
                if aqi <= 50:
                    aqi_level = ("Good", "优")
                elif aqi <= 100:
                    aqi_level = ("Moderate", "良")
                elif aqi <= 150:
                    aqi_level = ("Unhealthy for Sensitive", "轻度污染")
                elif aqi <= 200:
                    aqi_level = ("Unhealthy", "中度污染")
                elif aqi <= 300:
                    aqi_level = ("Very Unhealthy", "重度污染")
                else:
                    aqi_level = ("Hazardous", "严重污染")

                return {
                    "location": location_info.get("name", location),
                    "country": location_info.get("country"),
                    "lat": lat,
                    "lon": lon,
                    "timestamp": current.get("time"),
                    "aqi": aqi,
                    "aqi_level": aqi_level[1 if self.lang == "zh" else 0],
                    "pm2_5": current.get("pm2_5"),
                    "pm10": current.get("pm10"),
                    "co": current.get("carbon_monoxide"),
                    "no2": current.get("nitrogen_dioxide"),
                    "so2": current.get("sulphur_dioxide"),
                    "o3": current.get("ozone"),
                    "units": {
                        "pm2_5": "μg/m³",
                        "pm10": "μg/m³",
                        "co": "μg/m³",
                        "no2": "μg/m³",
                        "so2": "μg/m³",
                        "o3": "μg/m³"
                    }
                }
        except Exception as e:
            return {"error": f"Air quality fetch error: {e}"}

    def search_location(self, query: str, count: int = 5) -> List[Dict]:
        """
        Search for locations by name

        Args:
            query: Search query
            count: Number of results (1-10)

        Returns:
            List of matching locations
        """
        try:
            params = urllib.parse.urlencode({
                "name": query,
                "count": min(max(1, count), 10),
                "language": "en"
            })
            url = f"{self.geocoding_url}?{params}"

            req = urllib.request.Request(url, headers={"User-Agent": "WeatherModule/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                results = []
                for r in data.get("results", []):
                    results.append({
                        "name": r.get("name"),
                        "country": r.get("country"),
                        "admin1": r.get("admin1"),
                        "lat": r.get("latitude"),
                        "lon": r.get("longitude"),
                        "timezone": r.get("timezone"),
                        "population": r.get("population")
                    })
                return results
        except Exception as e:
            return [{"error": str(e)}]


def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Weather Module - ChatGPT Skills")
    parser.add_argument("command", choices=["current", "forecast", "hourly", "aqi", "search"],
                       help="Command to execute")
    parser.add_argument("location", nargs="?", help="City name or coordinates")
    parser.add_argument("--days", type=int, default=7, help="Forecast days (1-16)")
    parser.add_argument("--hours", type=int, default=24, help="Forecast hours (1-168)")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Language")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    client = WeatherClient(lang=args.lang)

    # Determine location parameters
    loc_params = {}
    if args.lat is not None and args.lon is not None:
        loc_params = {"lat": args.lat, "lon": args.lon}
    elif args.location:
        loc_params = {"location": args.location}
    else:
        print("Error: Please provide a location or --lat/--lon coordinates")
        return

    # Execute command
    if args.command == "current":
        result = client.get_current(**loc_params)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*50}")
            location_str = result['location']
            if result.get('country'):
                location_str += f", {result['country']}"
            print(f"  {location_str}")
            print(f"{'='*50}")
            print(f"  天气: {result['description']}")
            print(f"  温度: {result['temperature']}°C (体感: {result['feels_like']}°C)")
            print(f"  湿度: {result['humidity']}%")
            print(f"  风速: {result['wind_speed']} km/h")
            print(f"  气压: {result['pressure']} hPa")
            if result['precipitation'] > 0:
                print(f"  降水: {result['precipitation']} mm")
            print(f"{'='*50}\n")

    elif args.command == "forecast":
        result = client.get_forecast(**loc_params, days=args.days)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"  {result['location']} - {args.days}天天气预报")
            print(f"{'='*60}")
            for day in result['forecast']:
                print(f"  {day['date']}: {day['description']}")
                print(f"    温度: {day['temp_min']}°C ~ {day['temp_max']}°C")
                print(f"    降水概率: {day['precipitation_probability']}%")
                print()
            print(f"{'='*60}\n")

    elif args.command == "hourly":
        result = client.get_hourly(**loc_params, hours=args.hours)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"  {result['location']} - {args.hours}小时预报")
            print(f"{'='*60}")
            for hour in result['hourly'][:12]:  # Show first 12 hours
                time_str = hour['time'].split('T')[1] if 'T' in hour['time'] else hour['time']
                print(f"  {time_str}: {hour['temperature']}°C, {hour['description']}, "
                      f"降水{hour['precipitation_probability']}%")
            if len(result['hourly']) > 12:
                print(f"  ... (还有 {len(result['hourly']) - 12} 小时)")
            print(f"{'='*60}\n")

    elif args.command == "aqi":
        result = client.get_air_quality(**loc_params)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*50}")
            print(f"  {result['location']} - 空气质量")
            print(f"{'='*50}")
            print(f"  AQI: {result['aqi']} ({result['aqi_level']})")
            print(f"  PM2.5: {result['pm2_5']} μg/m³")
            print(f"  PM10: {result['pm10']} μg/m³")
            print(f"  O3: {result['o3']} μg/m³")
            print(f"{'='*50}\n")

    elif args.command == "search":
        if not args.location:
            print("Error: Please provide a search query")
            return

        results = client.search_location(args.location)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n搜索结果: '{args.location}'")
            print("-" * 40)
            for r in results:
                if "error" in r:
                    print(f"Error: {r['error']}")
                else:
                    print(f"  {r['name']}, {r.get('admin1', '')}, {r['country']}")
                    print(f"    坐标: {r['lat']}, {r['lon']}")
            print()


if __name__ == "__main__":
    main()
