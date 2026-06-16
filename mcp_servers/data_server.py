from mcp.server.fastmcp import FastMCP
import random
import json
from datetime import datetime, timedelta

mcp = FastMCP("DataServer")

# 模拟数据库
SALES_DATA = {
    "2026-06-01": {"product_a": 12000, "product_b": 8500, "product_c": 6300},
    "2026-06-02": {"product_a": 9800, "product_b": 9200, "product_c": 7100},
    "2026-06-03": {"product_a": 15000, "product_b": 7800, "product_c": 5500},
    "2026-06-04": {"product_a": 11200, "product_b": 10300, "product_c": 8900},
    "2026-06-05": {"product_a": 13500, "product_b": 6700, "product_c": 9400},
    "2026-06-06": {"product_a": 8900, "product_b": 11200, "product_c": 7600},
    "2026-06-07": {"product_a": 16800, "product_b": 9500, "product_c": 8200},
}

@mcp.tool()
def get_sales_data(start_date: str, end_date: str) -> str:
    """
    获取指定日期范围内的销售数据。
    
    参数:
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
    
    返回:
        JSON格式的销售数据
    """
    result = {}
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in SALES_DATA:
            result[date_str] = SALES_DATA[date_str]
        current += timedelta(days=1)
    
    if not result:
        return json.dumps({"error": "指定日期范围内没有数据"})
    
    return json.dumps(result, indent=2)

@mcp.tool()
def get_product_list() -> str:
    """获取所有产品列表"""
    products = ["product_a", "product_b", "product_c"]
    return json.dumps({"products": products})

@mcp.tool()
def get_total_sales(start_date: str, end_date: str) -> str:
    """
    获取指定日期范围内的总销售额。
    
    参数:
        start_date: 开始日期
        end_date: 结束日期
    """
    data = json.loads(get_sales_data(start_date, end_date))
    if "error" in data:
        return json.dumps(data)
    
    totals = {}
    for date, products in data.items():
        for product, amount in products.items():
            totals[product] = totals.get(product, 0) + amount
    
    return json.dumps({"total_sales": totals, "period": f"{start_date} ~ {end_date}"})

if __name__ == "__main__":
    mcp.run(transport="stdio")