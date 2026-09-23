"""
AgenticCommerce — CLI 智能体工作流执行入口
用于脱离 Web 界面直接在命令行触发与调试 7-Agent 生成流程
"""

import sys
import asyncio

async def main():
    print("=" * 60)
    print("AgenticCommerce — 7-Agent 智能体工作流 CLI 调试器")
    print("=" * 60)
    print("支持通过指定 SKU ID 或模拟参数执行 LangGraph 状态图工作流...")
    # 待业务模块完善后接入编排流
    print("提示: 后续可使用 python run_workflow.py --sku-id <SKU_UUID> 运行")

if __name__ == "__main__":
    asyncio.run(main())
