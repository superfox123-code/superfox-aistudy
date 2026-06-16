# test_mcp_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    # 创建服务器参数
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_demo_server.py"]
    )
    
    # 建立连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()
            
            # 列出所有工具
            tools = await session.list_tools()
            print("可用工具：")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # 调用计算器工具
            print("\n调用add(5, 3)...")
            result = await session.call_tool("add", arguments={"a": 5, "b": 3})
            print(f"结果: {result.content[0].text}")
            
            # 调用骰子工具
            print("\n调用roll_dice(20)...")
            result = await session.call_tool("roll_dice", arguments={"sides": 20})
            print(f"结果: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())