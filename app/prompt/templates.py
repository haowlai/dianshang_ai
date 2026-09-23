"""
提示词模板加载与变量渲染工具
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

def load_prompt_template(agent_name: str) -> str:
    prompt_file = PROMPTS_DIR / f"{agent_name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return ""
