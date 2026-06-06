"""
YAML 模板加载器 —— 读 YAML 文件 → 校验 → 返回结构化模板对象。

模板变量语法：{{.step_id.key.subkey}}
支持两层嵌套引用，如 {{.reverse_prompt.prompts.0.text}}
"""

import os
import re
from dataclasses import dataclass, field

# ====== 数据模型 ======

VALID_STEP_TYPES = ("tool", "ask", "human")
VALID_GATE_POSITIONS = ("before", "after")

# 已知的 YAML 顶层字段（用于区分步骤字段 vs 元数据字段）
_META_FIELDS = {"name", "desc", "version", "params"}


@dataclass
class ParamDef:
    """工作流参数定义。"""
    name: str
    type: str = "string"
    ask: str = ""        # 调用时没传就反问用户


@dataclass
class GateDef:
    """步骤前后门。"""
    position: str        # "before" | "after"
    config: dict         # 原始配置（ask / check / ...）


@dataclass
class StepDef:
    """单个步骤定义。"""
    id: str
    step_type: str       # tool | ask | human
    tool: str = ""       # 使用的工具名（仅 tool 类型）
    config: dict = field(default_factory=dict)     # 原始 YAML 配置（兼容旧格式）
    input_spec: dict = field(default_factory=dict) # 显式 input 定义
    output_spec: dict = field(default_factory=dict)# 显式 output 定义
    gates: list[GateDef] = field(default_factory=list)
    index: int = 0


@dataclass
class WorkflowTemplate:
    """完整的 workflow 模板。"""
    name: str
    path: str            # YAML 文件路径
    desc: str = ""
    version: str = "1.0"
    params: list[ParamDef] = field(default_factory=list)
    steps: list[StepDef] = field(default_factory=list)


# ====== 模板变量解析 ======

_VAR_RE = re.compile(r"\{\{\.([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*|\.[0-9]+)*)\}\}")


def _resolve_var(path: str, context: dict) -> str:
    """解析单个模板变量。

    path 形如 "reverse_prompt.prompts.0.text"
    从 context 中逐层取值，找不到返回空字符串。
    """
    parts = path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list):
            try:
                idx = int(part)
                value = value[idx]
            except (ValueError, IndexError):
                return ""
        else:
            return ""
        if value is None:
            return ""
    return str(value) if not isinstance(value, (dict, list)) else ""


def resolve_template(text: str, context: dict) -> str:
    """解析字符串中的所有 {{.xxx}} 模板变量。"""
    if not isinstance(text, str):
        return text

    def _replace(match):
        path = match.group(1)
        return _resolve_var(path, context)

    return _VAR_RE.sub(_replace, text)


def resolve_in(obj, context: dict):
    """递归解析对象中所有字符串的模板变量。"""
    if isinstance(obj, str):
        return resolve_template(obj, context)
    if isinstance(obj, dict):
        return {k: resolve_in(v, context) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_in(item, context) for item in obj]
    return obj


# ====== 加载与校验 ======

def _load_yaml(path: str) -> dict:
    """读取 YAML 文件，返回原始 dict。"""
    import yaml

    if not os.path.isfile(path):
        raise FileNotFoundError(f"模板文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML 解析失败 [{path}]: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"YAML 文件内容必须是 dict，得到 {type(data).__name__}: {path}")

    return data


def _validate_template(data: dict, path: str) -> WorkflowTemplate:
    """校验并转换为 WorkflowTemplate 对象。"""
    name = data.get("name", "")
    if not name:
        raise ValueError(f"模板缺少必填字段 name: {path}")

    steps_raw = data.get("steps")
    if not steps_raw or not isinstance(steps_raw, list):
        raise ValueError(f"模板 [{name}] 缺少 steps 列表: {path}")

    # 解析参数定义
    params = []
    for p in data.get("params") or []:
        params.append(ParamDef(
            name=p.get("name", ""),
            type=p.get("type", "string"),
            ask=p.get("ask", ""),
        ))

    # 解析步骤
    steps = []
    for idx, step in enumerate(steps_raw):
        if not isinstance(step, dict):
            raise ValueError(f"模板 [{name}] 步骤 #{idx + 1} 不是 dict")

        step_id = step.get("id", "")
        if not step_id:
            raise ValueError(f"模板 [{name}] 步骤 #{idx + 1} 缺少 id")

        # 推断步骤类型
        step_type = step.get("type", "")
        if step_type not in VALID_STEP_TYPES:
            # 兼容设计文档中的隐式写法：有 tool 字段 → tool，有 ask 字段 → ask，有 human 字段 → human
            if "tool" in step:
                step_type = "tool"
            elif "ask" in step:
                step_type = "ask"
            elif "human" in step:
                step_type = "human"
            else:
                raise ValueError(
                    f"模板 [{name}] 步骤 [{step_id}] 缺少 type 字段，"
                    f"且无法从字段推断类型（需含 tool/ask/human 之一）"
                )

        # 收集 gates
        gates = []
        for pos in VALID_GATE_POSITIONS:
            if pos in step:
                gates.append(GateDef(position=pos, config=step[pos]))

        # 构建步骤配置（排除 gates、id、type 等元字段）
        config = {
            k: v for k, v in step.items()
            if k not in ("id", "type", "before", "after", "input", "output", "tool")
        }

        # 提取显式 input / output 定义
        input_spec = step.get("input", {})
        if not isinstance(input_spec, dict):
            input_spec = {}
        output_spec = step.get("output", {})
        if not isinstance(output_spec, dict):
            output_spec = {}

        # 提取工具名
        tool_name = step.get("tool", "") if step_type == "tool" else ""

        steps.append(StepDef(
            id=step_id,
            step_type=step_type,
            tool=tool_name,
            config=config,
            input_spec=input_spec,
            output_spec=output_spec,
            gates=gates,
            index=idx,
        ))

    return WorkflowTemplate(
        name=name,
        path=path,
        desc=data.get("desc", ""),
        version=data.get("version", "1.0"),
        params=params,
        steps=steps,
    )


def load(yaml_path: str) -> WorkflowTemplate:
    """加载并校验一个 YAML workflow 模板。"""
    data = _load_yaml(yaml_path)
    return _validate_template(data, yaml_path)
