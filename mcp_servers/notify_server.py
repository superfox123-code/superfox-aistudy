from mcp.server.fastmcp import FastMCP
import json
from datetime import datetime

mcp = FastMCP("NotifyServer")

# 模拟邮件发送记录
EMAIL_LOG = []

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """
    发送邮件。
    
    参数:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {
        "timestamp": timestamp,
        "to": to,
        "subject": subject,
        "body": body[:100] + "..." if len(body) > 100 else body,
        "status": "sent"
    }
    EMAIL_LOG.append(log_entry)
    
    return json.dumps({
        "status": "success",
        "message": f"邮件已发送至 {to}",
        "subject": subject,
        "timestamp": timestamp
    }, indent=2, ensure_ascii=False)

@mcp.tool()
def get_email_log(limit: int = 5) -> str:
    """获取最近的邮件发送记录"""
    recent = EMAIL_LOG[-limit:] if EMAIL_LOG else []
    return json.dumps(recent, indent=2, ensure_ascii=False)

@mcp.tool()
def generate_report(title: str, content: str, data_summary: str = "") -> str:
    """
    生成格式化的报告。
    
    参数:
        title: 报告标题
        content: 报告正文内容（可以是JSON字符串或文本）
        data_summary: 数据摘要（JSON格式，可选）
    """
    # 尝试解析content为JSON
    try:
        data = json.loads(content)
        # 如果content是JSON，自动提取摘要
        if isinstance(data, dict):
            if "total_sales" in data:
                summary = data.get("total_sales", {})
                summary_text = "\n".join([f"{k}: {v}" for k, v in summary.items()])
            else:
                summary_text = json.dumps(data, indent=2)
        else:
            summary_text = content
    except:
        summary_text = content
    
    # 如果提供了data_summary，优先使用
    if data_summary:
        try:
            summary_dict = json.loads(data_summary)
            summary_text = "\n".join([f"{k}: {v}" for k, v in summary_dict.items()])
        except:
            pass
    
    report = f"""
╔══════════════════════════════════════════════════════════╗
║                    业务分析报告                          ║
╠══════════════════════════════════════════════════════════╣
║  标题：{title}
╠══════════════════════════════════════════════════════════╣
║  数据摘要：
║    {summary_text[:200]}
╠══════════════════════════════════════════════════════════╣
║  详细内容：
║  {content[:500]}
╠══════════════════════════════════════════════════════════╣
║  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
╚══════════════════════════════════════════════════════════╝
"""
    return report

if __name__ == "__main__":
    mcp.run(transport="stdio")