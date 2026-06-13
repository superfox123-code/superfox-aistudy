import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver  # 新增
import uuid  # 新增

load_dotenv()

# ==================== 工具1：天气查询（增强版）====================
@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的实时天气信息。
    
    参数说明：
    - city: 城市名称，如'北京'、'上海'、'深圳'、'杭州'
    
    返回值：该城市的天气状况和温度
    """
    weather_db = {
        "北京": "晴天，温度25°C，湿度45%，适合外出活动",
        "上海": "小雨，温度22°C，湿度80%，记得带伞",
        "深圳": "多云，温度28°C，湿度65%，天气舒适",
        "广州": "雷阵雨，温度30°C，湿度85%，注意防雷",
        "成都": "阴天，温度20°C，湿度70%，体感凉爽",
        "杭州": "晴天，温度23°C，湿度60%，西湖边散步很舒服",
        "南京": "多云，温度24°C，湿度55%，适合出游",
        "武汉": "晴天，温度27°C，湿度65%，热干面配豆浆",
        "西安": "阴天，温度22°C，湿度50%，兵马俑值得一看",
        "长沙": "小雨，温度26°C，湿度75%，臭豆腐走起",
        "重庆": "雾天，温度25°C，湿度80%，火锅安排上",
        "苏州": "晴天，温度22°C，湿度65%，园林甲天下",
        "天津": "多云，温度24°C，湿度50%，煎饼果子来一套",
    }
    
    # 支持模糊匹配
    for key in weather_db:
        if city in key or key in city:
            return weather_db[key]
    
    # 返回支持的城市列表
    cities = "、".join(weather_db.keys())
    return f"暂无{city}的天气数据。支持查询的城市：{cities}"

# ==================== 其他工具保持不变 ====================
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除和括号。"""
    try:
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算错误：{str(e)}"

@tool
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """单位换算。支持长度和重量单位。"""
    length_units = {'米': 1, '千米': 1000, '厘米': 0.01, '毫米': 0.001, '英尺': 0.3048}
    weight_units = {'千克': 1, '克': 0.001, '磅': 0.453592}
    
    if from_unit in length_units and to_unit in length_units:
        result = value * length_units[from_unit] / length_units[to_unit]
        return f"{value}{from_unit} = {result:.4f}{to_unit}"
    elif from_unit in weight_units and to_unit in weight_units:
        result = value * weight_units[from_unit] / weight_units[to_unit]
        return f"{value}{from_unit} = {result:.4f}{to_unit}"
    else:
        return f"错误：{from_unit} 和 {to_unit} 不是同一种单位类型"

@tool
def query_knowledge(topic: str) -> str:
    """查询编程相关的知识点。"""
    knowledge_base = {
        "装饰器": "装饰器是一个接收函数、返回新函数的函数，使用@语法糖。",
        "异步编程": "async/await实现并发执行，适合IO密集型任务。",
        "lambda": "lambda是匿名函数，格式为 lambda 参数: 返回值。",
        "生成器": "使用yield关键字逐个产生值，节省内存。",
        "列表推导式": "[x*2 for x in range(10)] 是简洁的列表创建方式。",
    }
    for key in knowledge_base:
        if key in topic or topic in key:
            return knowledge_base[key]
    return f"暂无关于「{topic}」的知识。可查询：{', '.join(knowledge_base.keys())}"

# ==================== 创建Agent（带记忆）====================
model = ChatOpenAI(
    model="deepseek-chat",
    temperature=0,
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1"
)

agent = create_agent(
    model=model,
    tools=[get_weather, calculator, convert_units, query_knowledge],
    system_prompt="""你是一个智能个人助理，可以帮助用户解决各种问题。

重要规则：
1. 当用户需要天气信息时，必须使用 get_weather 工具
2. 当用户需要数学计算时，必须使用 calculator 工具
3. 当用户需要单位换算时，必须使用 convert_units 工具
4. 当用户询问编程知识时，必须使用 query_knowledge 工具

对话规则：
- 记住用户之前提到的内容（比如城市名、话题）
- 如果用户只说了"杭州"而没有说具体需求，可以询问"你想查询杭州的天气吗？"
- 用友好、热情的语气回复
""",
    checkpointer=MemorySaver()  # 关键：添加记忆功能
)

# ==================== 交互模式（带记忆）====================
def interactive_mode():
    """进入交互对话模式（支持多轮记忆）"""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "=" * 60)
    print("🤖 智能个人助理已启动（支持多轮对话记忆）")
    print("=" * 60)
    print("试试这些对话：")
    print("  你: 杭州")
    print("  你: 天气")
    print("  你: 那上海呢？")
    print("=" * 60)
    
    while True:
        user_input = input("\n👤 你: ").strip()
        if user_input.lower() in ['exit', 'quit', '退出']:
            print("🤖 助手: 再见！")
            break
        if not user_input:
            continue
        
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config  # 传入config保持记忆
            )
            print(f"🤖 助手: {result['messages'][-1].content}")
        except Exception as e:
            print(f"❌ 出错: {e}")

if __name__ == "__main__":
    interactive_mode()