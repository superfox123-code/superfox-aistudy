import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from openai import OpenAI
import os
import signal

load_dotenv()

class MCPClient:
    """MCP客户端封装"""
    
    def __init__(self, server_name, command, args):
        self.server_name = server_name
        self.command = command
        self.args = args
        self.session = None
        self._client_context = None
        self._read_stream = None
        self._write_stream = None
        
    async def connect(self):
        """连接到MCP服务器"""
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args
            )
            
            # 创建客户端上下文
            self._client_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._client_context.__aenter__()
            
            # 创建会话
            self.session = await ClientSession(self._read_stream, self._write_stream).__aenter__()
            await self.session.initialize()
            return True
        except Exception as e:
            print(f"⚠️ 连接 {self.server_name} 失败: {e}")
            return False
        
    async def call_tool(self, tool_name, arguments):
        """调用工具"""
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text
        except Exception as e:
            return f"❌ 调用失败: {str(e)}"
        
    async def list_tools(self):
        """列出所有工具"""
        try:
            result = await self.session.list_tools()
            return result.tools
        except:
            return []
    
    async def close(self):
        """优雅关闭连接"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
        except:
            pass
        
        try:
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
        except:
            pass

class SupervisorAgent:
    """主管智能体"""
    
    def __init__(self):
        self.clients = {}
        self.llm = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
    async def register_server(self, name, command, args):
        """注册MCP服务器"""
        client = MCPClient(name, command, args)
        success = await client.connect()
        if success:
            self.clients[name] = client
            print(f"✅ 已注册服务器: {name}")
        else:
            print(f"❌ 注册服务器失败: {name}")
        
    async def get_all_tools(self):
        """获取所有服务器的工具列表"""
        all_tools = []
        for name, client in self.clients.items():
            tools = await client.list_tools()
            for tool in tools:
                all_tools.append({
                    "server": name,
                    "name": tool.name,
                    "description": tool.description or "无描述"
                })
        return all_tools
    
    async def execute_task(self, user_request):
        """执行用户任务"""
        
        # 1. 获取所有可用工具
        tools = await self.get_all_tools()
        tools_desc = "\n".join([
            f"- [{t['server']}] {t['name']}: {t['description']}"
            for t in tools
        ])
        
        # 2. 让LLM制定计划
        plan_prompt = f"""
你是一个主管智能体，负责协调多个AI服务器完成任务。

可用服务器和工具：
{tools_desc}

用户请求：{user_request}

请按以下步骤处理：
1. 分析用户请求，拆解成子任务
2. 为每个子任务指定使用哪个工具（格式：server_name.tool_name）
3. 注意工具的参数名称必须和工具定义完全一致

重要提示：
- generate_report 工具的参数是：title（标题）、content（内容）、data_summary（数据摘要，可选）
- 请确保参数名称正确

输出格式（JSON）：
{{
    "plan": [
        {{"step": 1, "server": "server_name", "tool": "tool_name", "params": {{"参数名": "值"}}}}
    ],
    "summary": "任务计划摘要"
}}
"""
        
        try:
            response = self.llm.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": plan_prompt}],
                temperature=0.1
            )
            
            plan_text = response.choices[0].message.content
            # 提取JSON
            start = plan_text.find("{")
            end = plan_text.rfind("}") + 1
            plan_json = json.loads(plan_text[start:end])
            plan = plan_json["plan"]
            print(f"\n📋 计划已生成：{plan_json.get('summary', '')}")
            
        except Exception as e:
            print(f"⚠️ 计划解析失败: {e}，使用默认流程")
            plan = [
                {"step": 1, "server": "data_server", "tool": "get_total_sales", 
                 "params": {"start_date": "2026-06-01", "end_date": "2026-06-07"}},
                {"step": 2, "server": "calc_server", "tool": "calculate_average",
                 "params": {"data_json": "[87200, 63200, 53000]"}},
                {"step": 3, "server": "notify_server", "tool": "generate_report",
                 "params": {"title": "销售报告", "content": "销售数据汇总", "data_summary": "{}"}},
                {"step": 4, "server": "notify_server", "tool": "send_email",
                 "params": {"to": "ceo@company.com", "subject": "销售报告", "body": "报告已生成"}}
            ]
        
        # 3. 执行计划
        results = []
        for step in plan:
            step_num = step["step"]
            server_name = step["server"]
            tool_name = step["tool"]
            params = step.get("params", {})
            
            print(f"\n🔄 执行步骤 {step_num}: {server_name}.{tool_name}")
            print(f"   参数: {params}")
            
            client = self.clients.get(server_name)
            if not client:
                result = f"❌ 错误：找不到服务器 '{server_name}'"
                print(f"   ❌ 执行失败")
            else:
                result = await client.call_tool(tool_name, params)
                print(f"   ✅ 执行成功")
                
            results.append({
                "step": step_num,
                "tool": f"{server_name}.{tool_name}",
                "result": result
            })
        
        # 4. 生成最终回复
        return await self.generate_final_response(user_request, results)
    
    async def generate_final_response(self, user_request, results):
        """生成最终回复"""
        
        results_text = "\n".join([
            f"步骤{r['step']} ({r['tool']}):\n{r['result'][:300]}\n"
            for r in results
        ])
        
        summary_prompt = f"""
用户请求：{user_request}

执行结果：
{results_text}

请根据以上执行结果，生成一个清晰、完整的回复给用户。
回复要结构化，包含关键数据和结论。
"""
        
        try:
            response = self.llm.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.5
            )
            summary = response.choices[0].message.content
        except:
            summary = "任务执行完成，请查看详细结果。"
        
        return {
            "summary": summary,
            "details": results
        }
    
    async def close_all(self):
        """关闭所有连接"""
        for name, client in self.clients.items():
            await client.close()
        self.clients.clear()

async def main():
    """主函数"""
    
    print("🚀 启动多智能体系统...\n")
    
    supervisor = SupervisorAgent()
    
    try:
        # 注册三个MCP服务器
        await supervisor.register_server(
            "data_server",
            "python",
            ["mcp_servers/data_server.py"]
        )
        
        await supervisor.register_server(
            "calc_server", 
            "python",
            ["mcp_servers/calc_server.py"]
        )
        
        await supervisor.register_server(
            "notify_server",
            "python",
            ["mcp_servers/notify_server.py"]
        )
        
        print("\n" + "=" * 60)
        print("📋 系统就绪！")
        
        # 显示可用工具
        tools = await supervisor.get_all_tools()
        print("\n可用工具：")
        for t in tools:
            desc = t['description'][:50] + "..." if len(t['description']) > 50 else t['description']
            print(f"  [{t['server']}] {t['name']}: {desc}")
        
        print("\n" + "=" * 60)
        
        # 执行测试任务
        test_request = """
请帮我完成以下工作流：
1. 获取2026年6月1日到6月7日的总销售额数据
2. 计算这些销售额的平均值
3. 生成一份业务报告
4. 发送报告到 ceo@company.com
"""
        
        print(f"\n📝 执行任务：{test_request.strip()}")
        print("\n" + "=" * 60)
        
        result = await supervisor.execute_task(test_request)
        
        print("\n" + "=" * 60)
        print("📊 最终结果：")
        print("=" * 60)
        print(result["summary"])
        
        print("\n📋 执行详情：")
        for detail in result["details"]:
            result_preview = detail["result"][:150] + "..." if len(detail["result"]) > 150 else detail["result"]
            print(f"\n步骤 {detail['step']} ({detail['tool']}):")
            print(f"  {result_preview}")
            
    finally:
        # 确保所有连接被关闭
        print("\n🔄 正在关闭所有连接...")
        await supervisor.close_all()
        print("✅ 已关闭")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")