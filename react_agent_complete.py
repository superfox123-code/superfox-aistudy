from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

# ========== 定义3个工具 ==========

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入应为数学公式，如 '2+3*4' 或 'sqrt(16)'"""
    try:
        # 安全的eval，只允许数学运算
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow, "sqrt": __import__('math').sqrt}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """获取指定城市的实时天气。输入城市名称，如 '北京'、'上海'"""
    weather_db = {
        "北京": "晴天，温度25°C，湿度45%",
        "上海": "小雨，温度22°C，湿度80%",
        "深圳": "多云，温度28°C，湿度65%",
        "广州": "雷阵雨，温度30°C，湿度85%"
    }
    return weather_db.get(city, f"暂无{city}的天气数据，请尝试查询：北京、上海、深圳、广州")

@tool
def search_info(topic: str) -> str:
    """搜索一般信息。输入想查询的主题，如 'LangChain是什么'"""
    knowledge_base = {
        "langchain": "LangChain是一个用于构建大模型应用的开源框架，提供Agent、Chain、Tool等组件。",
        "react": "ReAct是让AI Agent通过'思考-行动-观察'循环来解决问题的模式。",
        "agent": "AI Agent是能自主使用工具、规划步骤完成任务的智能程序。"
    }
    topic_lower = topic.lower()
    for key, value in knowledge_base.items():
        if key in topic_lower:
            return value
    return f"关于'{topic}'的信息：这是一个需要进一步查询的话题。"

# ========== 创建带多工具的Agent ==========

model = ChatOpenAI(
    model="deepseek-chat",
    temperature=0,
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1"
)

agent = create_agent(
    model=model,
    tools=[calculator, get_weather, search_info],
    system_prompt="""你是一个智能助手，能使用工具解决问题。
规则：
1. 需要计算时用calculator
2. 需要天气时用get_weather  
3. 需要知识查询时用search_info
4. 可以组合使用多个工具
"""
)

# ========== 测试用例 ==========

test_questions = [
    "北京今天天气怎么样？",
    "计算 25 * 4 + 10",
    "什么是LangChain？",
    "上海天气如何？然后计算一下25+35等于多少？"  # 多步推理
]

for question in test_questions:
    print(f"\n{'='*50}")
    print(f"用户: {question}")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"助手: {result['messages'][-1].content}")

# ========== 对话式交互 ==========
print("\n" + "="*50)
print("进入对话模式（输入exit退出）")
while True:
    user_input = input("\n你: ")
    if user_input.lower() == 'exit':
        break
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print(f"助手: {result['messages'][-1].content}")