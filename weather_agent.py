# weather_agent.py
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============ 定义工具（Tool） ============

def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息
    
    参数:
        city: 城市名称，如"北京"、"上海"
    
    返回:
        天气信息字符串
    """
    # 注意：这里用模拟数据，因为真实天气API需要注册
    # 第3周我们会换成真实API
    weather_db = {
        "北京": "晴天，温度25°C，湿度40%，风力2级",
        "上海": "多云，温度22°C，湿度65%，风力3级",
        "深圳": "阵雨，温度28°C，湿度80%，风力1级",
        "广州": "阴天，温度26°C，湿度70%，风力2级",
        "成都": "小雨，温度20°C，湿度75%，风力1级",
    }
    
    city = city.strip()
    for key in weather_db:
        if key in city or city in key:
            return weather_db[key]
    
    return f"未找到{city}的天气数据，请尝试：北京、上海、深圳、广州、成都"

# ============ 工具描述（给大模型看的说明书） ============

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息，包括温度、湿度、风力等",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# ============ Agent 核心逻辑 ============

def run_agent(user_input: str):
    """
    运行 Agent，支持工具调用
    """
    # 消息历史
    messages = [
        {"role": "user", "content": user_input}
    ]
    
    # 第一次调用：让大模型决定是否需要工具
    print(f"\n🤔 用户问题: {user_input}")
    print("🔄 Agent 思考中...")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,  # 告诉大模型可用的工具
        tool_choice="auto"  # 让大模型自己决定是否用工具
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    # 检查大模型是否要调用工具
    tool_calls = response_message.tool_calls
    
    if tool_calls:
        print(f"🔧 Agent 决定调用工具: {tool_calls[0].function.name}")
        
        # 执行工具
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name == "get_weather":
                city = arguments.get("city")
                print(f"🌍 查询城市: {city}")
                tool_result = get_weather(city)
                print(f"📊 工具返回: {tool_result}")
                
                # 把工具结果加入消息历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
        
        # 第二次调用：让大模型根据工具结果生成最终回答
        print("💬 Agent 根据结果生成回答...")
        final_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        
        final_answer = final_response.choices[0].message.content
        print(f"\n✅ 最终回答:\n{final_answer}")
        return final_answer
    else:
        # 不需要工具，直接返回
        answer = response_message.content
        print(f"\n✅ 直接回答:\n{answer}")
        return answer

# ============ 主程序 ============

if __name__ == "__main__":
    print("=" * 50)
    print("🌤️  天气查询 Agent")
    print("=" * 50)
    print("支持的指令示例：")
    print("  - 北京今天天气怎么样？")
    print("  - 上海热吗？")
    print("  - 深圳适合出门吗？")
    print("  - 输入 'exit' 退出")
    print("-" * 50)
    
    while True:
        user_input = input("\n👤 你: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 再见！")
            break
        
        run_agent(user_input)