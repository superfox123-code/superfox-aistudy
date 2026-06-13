from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

# 实验1：基础工具
@tool
def calculator(expression: str) -> str:
    """计算数学表达式，如'2+3*4'"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"

# 实验2：自定义名称和描述
@tool("web_search", description="搜索网络信息，适用于实时数据查询")
def search(query: str) -> str:
    """搜索功能（模拟）"""
    return f"关于'{query}'的搜索结果：示例结果1、示例结果2"

# 实验3：复杂输入（使用Pydantic）
class WeatherInput(BaseModel):
    location: str = Field(description="城市名称")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius", 
        description="温度单位"
    )

@tool(args_schema=WeatherInput)
def get_weather_advanced(location: str, units: str = "celsius") -> str:
    """获取天气（高级版）"""
    temp = 25 if units == "celsius" else 77
    return f"{location}天气：{temp}°{'C' if units=='celsius' else 'F'}"

# 测试
print(calculator.invoke("10+20"))
print(search.invoke("LangChain教程"))
print(get_weather_advanced.invoke({"location": "北京", "units": "celsius"}))