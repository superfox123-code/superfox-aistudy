import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import random
import datetime

# 创建服务器实例（注意：不使用 FastMCP）
server = Server("MyFirstMCP")

# ========== 列出所有工具 ==========
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """返回服务器提供的所有工具列表"""
    return [
        types.Tool(
            name="add",
            description="将两个数字相加",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数字"},
                    "b": {"type": "number", "description": "第二个数字"}
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="multiply",
            description="将两个数字相乘",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数字"},
                    "b": {"type": "number", "description": "第二个数字"}
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="roll_dice",
            description="掷一个骰子",
            inputSchema={
                "type": "object",
                "properties": {
                    "sides": {"type": "integer", "description": "骰子的面数", "default": 6}
                }
            }
        ),
        types.Tool(
            name="get_current_time",
            description="获取当前时间",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

# ========== 执行工具调用 ==========
@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理工具调用请求"""
    
    if name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return [types.TextContent(type="text", text=str(result))]
    
    elif name == "multiply":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a * b
        return [types.TextContent(type="text", text=str(result))]
    
    elif name == "roll_dice":
        sides = arguments.get("sides", 6)
        result = random.randint(1, sides)
        return [types.TextContent(type="text", text=f"🎲 掷了一个{sides}面骰子，结果是：{result}")]
    
    elif name == "get_current_time":
        now = datetime.datetime.now()
        return [types.TextContent(type="text", text=f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")]
    
    else:
        raise ValueError(f"未知工具: {name}")

# ========== 主函数 ==========
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="MyFirstMCP",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())