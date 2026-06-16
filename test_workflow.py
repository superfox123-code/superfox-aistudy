import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_single_server():
    """测试单个MCP服务器"""
    
    print("🧪 测试数据服务器...")
    
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_servers/data_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 列出工具
            tools = await session.list_tools()
            print("  可用工具：")
            for tool in tools.tools:
                print(f"    - {tool.name}")
            
            # 测试get_total_sales
            result = await session.call_tool(
                "get_total_sales",
                arguments={"start_date": "2026-06-01", "end_date": "2026-06-07"}
            )
            print(f"\n  get_total_sales 测试结果：")
            print(f"  {result.content[0].text[:200]}...")

async def main():
    await test_single_server()

if __name__ == "__main__":
    asyncio.run(main())