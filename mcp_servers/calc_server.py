from mcp.server.fastmcp import FastMCP
import json
import statistics

mcp = FastMCP("CalcServer")

@mcp.tool()
def calculate_average(data_json: str) -> str:
    """
    计算一组数据的平均值。
    
    参数:
        data_json: JSON格式的数字列表，如 "[1, 2, 3, 4, 5]"
                  或包含数字的对象，如 '{"a": 1, "b": 2}'
    """
    try:
        data = json.loads(data_json)
        if not data:
            return "错误：数据为空"
        
        # ✅ 修复：处理两种情况
        # 情况1：列表 [1, 2, 3]
        if isinstance(data, list):
            nums = [float(x) for x in data if isinstance(x, (int, float))]
        # 情况2：对象 {"a": 1, "b": 2} → 提取所有值
        elif isinstance(data, dict):
            nums = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    nums.append(float(value))
                # 如果value是字符串，尝试转换
                elif isinstance(value, str):
                    try:
                        nums.append(float(value))
                    except ValueError:
                        pass
            # 如果对象有 total_sales 字段，从里面提取
            if "total_sales" in data and isinstance(data["total_sales"], dict):
                for key, value in data["total_sales"].items():
                    if isinstance(value, (int, float)):
                        nums.append(float(value))
                    elif isinstance(value, str):
                        try:
                            nums.append(float(value))
                        except ValueError:
                            pass
        else:
            return f"错误：不支持的数据类型 {type(data)}"
        
        if not nums:
            return "错误：没有找到有效的数字"
        
        avg = sum(nums) / len(nums)
        return f"平均值：{avg:.2f}，基于 {len(nums)} 个数据点"
    except json.JSONDecodeError:
        return f"错误：无效的JSON格式 - {data_json[:100]}"
    except Exception as e:
        return f"错误：{str(e)}"

@mcp.tool()
def calculate_summary(data_json: str) -> str:
    """
    计算一组数据的统计摘要：总和、平均值、最大值、最小值、中位数。
    
    参数:
        data_json: JSON格式的数字列表
    """
    try:
        data = json.loads(data_json)
        if not data:
            return "错误：数据为空"
        
        summary = {
            "总和": sum(data),
            "平均值": round(sum(data) / len(data), 2),
            "最大值": max(data),
            "最小值": min(data),
            "中位数": statistics.median(data),
            "数据量": len(data)
        }
        return json.dumps(summary, indent=2)
    except json.JSONDecodeError:
        return "错误：无效的JSON格式"

@mcp.tool()
def calculate_growth(current: float, previous: float) -> str:
    """
    计算增长率。
    
    参数:
        current: 当前值
        previous: 前一期值
    """
    if previous == 0:
        return "错误：分母不能为0"
    growth = ((current - previous) / previous) * 100
    direction = "增长" if growth > 0 else "下降"
    return f"{direction}率：{growth:.2f}%"

@mcp.tool()
def add(a: float, b: float) -> str:
    """两数相加"""
    return f"{a} + {b} = {a + b}"

@mcp.tool()
def multiply(a: float, b: float) -> str:
    """两数相乘"""
    return f"{a} × {b} = {a * b}"

if __name__ == "__main__":
    mcp.run(transport="stdio")