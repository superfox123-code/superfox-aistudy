# first_agent.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件中的 API Key
load_dotenv()

# 初始化 DeepSeek 客户端（兼容 OpenAI 接口）
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def call_deepseek(prompt, temperature=0.7):
    """调用 DeepSeek API 的通用函数"""
    response = client.chat.completions.create(
        model="deepseek-chat",  # 使用 deepseek-chat 模型
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        stream=False
    )
    return response.choices[0].message.content

# 测试调用
if __name__ == "__main__":
    print("正在测试 DeepSeek API...")
    
    result = call_deepseek("用一句话解释什么是 AI Agent")
    
    print(f"\nDeepSeek 的回答：\n{result}")
    print("\n✅ API 调用成功！环境配置完成。")