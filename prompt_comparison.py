# prompt_comparison.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 初始化客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def call_deepseek(messages, temperature=0.7):
    """调用DeepSeek API"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

print("=" * 60)
print("实验1：对比【有SYSTEM】vs【无SYSTEM】")
print("=" * 60)

question = "什么是Python装饰器？"

# 方式1：无SYSTEM（直接问）
print("\n【无SYSTEM】直接问：")
result1 = call_deepseek([
    {"role": "user", "content": question}
])
print(result1)

# 方式2：有SYSTEM（先设定角色）
print("\n【有SYSTEM】设定角色为'资深Python工程师'：")
result2 = call_deepseek([
    {"role": "system", "content": "你是一个资深Python工程师，擅长用通俗易懂的方式解释技术概念"},
    {"role": "user", "content": question}
])
print(result2)

print("\n" + "=" * 60)
print("实验2：思维链（CoT）的效果")
print("=" * 60)

math_question = "一个商店有120个苹果，上午卖出35个，下午进货28个，晚上卖出42个，还剩多少个？"

# 方式1：直接问
print("\n【直接问】：")
result3 = call_deepseek([
    {"role": "user", "content": math_question}
])
print(result3)

# 方式2：加思维链引导
print("\n【加思维链引导】：")
cot_prompt = f"""请一步一步思考，然后回答：
{math_question}

步骤：
1. 上午卖出后还剩：
2. 下午进货后变成：
3. 晚上卖出后还剩：
4. 最终答案："""
result4 = call_deepseek([
    {"role": "user", "content": cot_prompt}
])
print(result4)

print("\n" + "=" * 60)
print("实验3：temperature参数的影响")
print("=" * 60)

creative_question = "给我写一句有创意的咖啡广告语"

for temp in [0, 0.8, 1.5]:
    print(f"\n【temperature = {temp}】：")
    result = call_deepseek(
        [{"role": "user", "content": creative_question}],
        temperature=temp
    )
    print(result)

print("\n✅ 所有实验完成！")