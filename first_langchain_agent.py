from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# 1. 定义一个简单的工具函数
def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    weather_data = {
        "北京": "晴天, 25°C",
        "上海": "雨天, 20°C",
        "深圳": "多云, 28°C"
    }
    return weather_data.get(city, f"暂无{city}的天气数据")

# 2. 初始化模型（使用DeepSeek）
model = ChatOpenAI(
    model="deepseek-chat",
    temperature=0,
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1"
)

# 3. 创建Agent
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="你是一个天气助手，只能使用get_weather工具查询天气"
)

# 4. 运行Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "北京今天天气怎么样？"}]
})

print(result["messages"][-1].content)