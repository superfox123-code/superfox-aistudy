from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from dotenv import load_dotenv
import operator

load_dotenv()

# ========== 定义状态 ==========
class AgentState(TypedDict):
    """智能体共享状态"""
    messages: Annotated[list, operator.add]  # 消息历史
    next_agent: str  # 下一个要调用的智能体
    user_input: str  # 用户原始输入
    intermediate_results: dict  # 中间结果缓存

# ========== 定义工具 ==========
@tool
def query_database(sql: str) -> str:
    """执行数据库查询（模拟）"""
    # 模拟数据库查询
    if "销售额" in sql.lower():
        return "Top 5销售额：产品A: 100万，产品B: 80万，产品C: 60万"
    return f"查询结果：对SQL '{sql}' 返回模拟数据"

@tool
def generate_chart(data: str, chart_type: str = "bar") -> str:
    """生成图表（模拟）"""
    return f"已生成{chart_type}图表，基于数据：{data[:50]}..."

@tool
def send_email(recipient: str, subject: str, content: str) -> str:
    """发送邮件（模拟）"""
    return f"邮件已发送至{recipient}，主题：{subject}"

# ========== 创建专门的智能体 ==========
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 数据分析智能体
data_analyst_prompt = """你是数据分析专家。你的职责是：
1. 理解用户的数据查询需求
2. 将需求转化为SQL或数据处理逻辑
3. 使用query_database工具获取数据
4. 返回分析结果

请一步步处理用户需求。"""

# 可视化智能体
visualizer_prompt = """你是数据可视化专家。你的职责是：
1. 接收数据分析结果
2. 决定最佳的图表类型
3. 使用generate_chart工具创建图表
4. 返回图表描述

请基于提供的数据生成合适的可视化。"""

# 报告智能体
reporter_prompt = """你是报告撰写专家。你的职责是：
1. 综合所有分析结果
2. 生成结构化的业务报告
3. 使用send_email工具发送报告（如需要）
4. 返回报告摘要

请专业地完成报告撰写。"""

# ========== 构建多智能体图 ==========
def create_supervisor_graph():
    """创建主管模式的多智能体系统"""
    
    # 初始化图
    workflow = StateGraph(AgentState)
    
    # 定义节点（每个节点是一个智能体或工具）
    def data_analyst_node(state: AgentState):
        """数据分析智能体"""
        messages = [
            {"role": "system", "content": data_analyst_prompt},
            {"role": "user", "content": state["user_input"]}
        ]
        response = llm.invoke(messages)
        return {
            "messages": [response.content],
            "intermediate_results": {"data": response.content}
        }
    
    def visualizer_node(state: AgentState):
        """可视化智能体"""
        data = state["intermediate_results"].get("data", "")
        messages = [
            {"role": "system", "content": visualizer_prompt},
            {"role": "user", "content": f"请基于以下数据生成可视化：{data}"}
        ]
        response = llm.invoke(messages)
        return {
            "messages": [response.content],
            "intermediate_results": {"visualization": response.content}
        }
    
    def reporter_node(state: AgentState):
        """报告智能体"""
        data = state["intermediate_results"].get("data", "")
        viz = state["intermediate_results"].get("visualization", "")
        messages = [
            {"role": "system", "content": reporter_prompt},
            {"role": "user", "content": f"数据分析结果：{data}\n可视化结果：{viz}"}
        ]
        response = llm.invoke(messages)
        return {"messages": [response.content]}
    
    # 主管节点：决定下一步调用哪个智能体
    def supervisor_node(state: AgentState):
        """主管智能体：协调调度"""
        prompt = f"""你是主管，负责协调任务执行。
当前任务：{state['user_input']}
已完成步骤：{len(state.get('messages', []))}步

请决定下一步应该调用哪个智能体：
- data_analyst: 数据分析（第一步）
- visualizer: 数据可视化（第二步）
- reporter: 报告撰写（第三步）
- FINISH: 任务完成

只输出智能体名称或FINISH。"""
        
        response = llm.invoke(prompt)
        decision = response.content.strip().lower()
        
        if "finish" in decision:
            return {"next_agent": "FINISH"}
        elif "visualizer" in decision:
            return {"next_agent": "visualizer"}
        elif "reporter" in decision:
            return {"next_agent": "reporter"}
        else:
            return {"next_agent": "data_analyst"}
    
    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("data_analyst", data_analyst_node)
    workflow.add_node("visualizer", visualizer_node)
    workflow.add_node("reporter", reporter_node)
    
    # 添加边
    workflow.add_edge("data_analyst", "supervisor")
    workflow.add_edge("visualizer", "supervisor")
    workflow.add_edge("reporter", END)
    
    # 条件边：主管决定下一步
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_agent"],
        {
            "data_analyst": "data_analyst",
            "visualizer": "visualizer",
            "reporter": "reporter",
            "FINISH": END
        }
    )
    
    # 设置入口
    workflow.set_entry_point("supervisor")
    
    return workflow.compile()

# ========== 运行示例 ==========
if __name__ == "__main__":
    app = create_supervisor_graph()
    
    # 测试输入
    user_query = "请分析上个月Top 5产品的销售额，生成图表，并发送报告到ceo@company.com"
    
    print(f"用户问题：{user_query}\n")
    print("=" * 50)
    print("多智能体系统开始执行...\n")
    
    result = app.invoke({
        "user_input": user_query,
        "messages": [],
        "intermediate_results": {}
    })
    
    print("\n" + "=" * 50)
    print("执行完成！最终结果：")
    for msg in result.get("messages", []):
        print(f"\n{msg[:200]}...")