from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("WeatherServer")

# 免费天气API（OpenWeatherMap需要注册）
# 注册地址：https://openweathermap.org/api
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "af63ce29a653f1c3ecce3394dec1327b")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

@mcp.tool()
def get_weather(city: str, unit: str = "celsius") -> str:
    """
    获取指定城市的当前天气。
    
    参数:
        city: 城市名称（英文或拼音，如 "Beijing"）
        unit: 温度单位，celsius或fahrenheit
    
    返回:
        格式化的天气信息
    """
    try:
        # 转换温度单位
        units = "metric" if unit == "celsius" else "imperial"
        
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units
        }
        
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            return f"查询失败：{data.get('message', '未知错误')}"
        
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        wind_speed = data['wind']['speed']
        
        unit_symbol = "°C" if unit == "celsius" else "°F"
        
        return (
            f"📍 {city} 天气：\n"
            f"🌡️ 温度：{temp}{unit_symbol}\n"
            f"💧 湿度：{humidity}%\n"
            f"🌤️ 天气：{description}\n"
            f"💨 风速：{wind_speed}m/s"
        )
    except requests.exceptions.RequestException as e:
        return f"网络请求失败：{str(e)}"
    except Exception as e:
        return f"处理失败：{str(e)}"

@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """
    获取未来几天的天气预报。
    
    参数:
        city: 城市名称
        days: 预报天数（1-5）
    """
    # 简化版：实际应该调用5天/3小时间隔的API
    return f"{city}未来{days}天预报功能开发中..."

if __name__ == "__main__":
    mcp.run(transport="stdio")