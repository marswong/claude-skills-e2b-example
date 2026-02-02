---
name: weather
description: Query global weather data including current weather, forecasts (1-16 days), hourly forecasts, and air quality (AQI). Use when user asks about weather, temperature, forecast, rain, snow, humidity, or air quality for any city.
---

# Weather 天气查询 Skill

查询全球天气数据，包括实时天气、天气预报、空气质量等。数据源：Open-Meteo（免费，无需 API Key）。

## 快速开始

无需安装额外依赖，直接使用：

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py current Beijing
```

## 功能列表

### 1. 当前天气

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py current Beijing
python3 ~/.claude/skills/weather/scripts/weather_module.py current "New York"
python3 ~/.claude/skills/weather/scripts/weather_module.py current Tokyo --json
```

### 2. 天气预报 (1-16天)

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py forecast Shanghai --days 7
python3 ~/.claude/skills/weather/scripts/weather_module.py forecast London --days 3
```

### 3. 逐小时预报

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py hourly Beijing --hours 24
python3 ~/.claude/skills/weather/scripts/weather_module.py hourly Paris --hours 12
```

### 4. 空气质量 (AQI)

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py aqi Beijing
python3 ~/.claude/skills/weather/scripts/weather_module.py aqi Shanghai --json
```

返回数据：AQI 指数、PM2.5、PM10、O3、NO2、SO2、CO

### 5. 位置搜索

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py search "New York"
python3 ~/.claude/skills/weather/scripts/weather_module.py search "东京"
```

### 6. 使用坐标查询

```bash
python3 ~/.claude/skills/weather/scripts/weather_module.py current --lat 39.9 --lon 116.4
python3 ~/.claude/skills/weather/scripts/weather_module.py forecast --lat 31.2 --lon 121.5 --days 5
```

## Python 模块使用

```python
from weather_module import WeatherClient

client = WeatherClient()

# 当前天气
weather = client.get_current("Beijing")
print(f"温度: {weather['temperature']}°C, 天气: {weather['description']}")

# 天气预报
forecast = client.get_forecast("Shanghai", days=7)
for day in forecast['forecast']:
    print(f"{day['date']}: {day['temp_min']}~{day['temp_max']}°C, {day['description']}")

# 空气质量
aqi = client.get_air_quality("Beijing")
print(f"AQI: {aqi['aqi']} ({aqi['aqi_level']})")
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--days` | 预报天数 (1-16) |
| `--hours` | 小时预报时长 (1-168) |
| `--lat` | 纬度 |
| `--lon` | 经度 |
| `--lang` | 语言 (zh/en) |
| `--json` | JSON 格式输出 |

## 数据说明

- 温度单位：°C
- 风速单位：km/h
- 气压单位：hPa
- 降水单位：mm

---

**费用**: 免费
**数据源**: Open-Meteo API
