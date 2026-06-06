"""
工具注册表 —— 每个工具有明确的输入/输出定义。

工具声明了「我需要什么输入」「我会产出什么」，引擎据此校验和对接。
"""

from typing import Callable


class ToolDef:
    """工具定义 —— 声明输入输出契约。"""

    def __init__(self, name: str, desc: str,
                 inputs: dict,    # {字段名: {type, label, required, placeholder}}
                 outputs: dict,   # {字段名: {type, label}}
                 executor):
        self.name = name
        self.desc = desc
        self.inputs = inputs
        self.outputs = outputs
        self.executor = executor   # Callable[[dict, dict, str], dict]

    def to_dict(self):
        return {
            "name": self.name,
            "desc": self.desc,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }


_registry: dict[str, ToolDef] = {}


def register(name: str, desc: str, inputs: dict, outputs: dict, executor) -> None:
    """注册一个工具。"""
    _registry[name] = ToolDef(name, desc, inputs, outputs, executor)


def get(name: str) -> ToolDef | None:
    """获取工具定义。"""
    return _registry.get(name)


def list_tools() -> list[dict]:
    """列出所有已注册工具的信息（给前端）。"""
    return [t.to_dict() for t in _registry.values()]


def execute(name: str, input_data: dict, context: dict, workspace: str) -> dict:
    """执行工具调用。

    参数：
        name       —— 工具名
        input_data —— 步骤的 input 字段（模板变量已解析）
        context    —— workflow 上下文
        workspace  —— 本次运行的输出目录（文件产出存这里）

    返回：dict，含 type 和具体产出字段
    """
    tool = _registry.get(name)
    if tool is None:
        available = ", ".join(sorted(_registry.keys())) or "(无)"
        raise ValueError(f"未注册的工具: {name}，可用工具: {available}")

    try:
        result = tool.executor(input_data, context, workspace)
    except Exception as exc:
        raise RuntimeError(f"工具 [{name}] 执行失败: {exc}") from exc

    if not isinstance(result, dict):
        result = {"value": str(result)}

    return result
