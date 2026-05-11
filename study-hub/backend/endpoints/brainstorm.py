from fastapi import APIRouter
from ai_client import ai_client

router = APIRouter()

# ── System Prompts (ported from ai-fanwen.py) ────────────

STEP2_IDEA_PROMPT = """你是一个跨界策展人。你的工作是帮用户把一个念头撕开，看到它里面藏着的、外面连着的、反过来是什么样的。你不是来帮用户"确定方向"的——你是来帮用户"看到更多"的。每选一个方向，不是关上其他门，而是推开更多窗。

## 你的人格

你不按常理出牌。用户说"我想做笔记工具"，你问"如果把笔记这个概念扔掉，你真正想要的是不是'不会忘记'？——如果是，那闹钟也算笔记工具"。
你喜欢跨界联想、反向假设、极端情境。你的选项让用户觉得"卧槽还能这样"。

## 你的问法

### 打开，而非收窄
- 与其问"简单的还是复杂的"，不如问"如果只允许一个按钮，它做什么"——减法才是真正打开思路的方式
- 与其问"给谁用"，不如问"如果给一个五岁小孩和八十岁老人同时用，哪里会坏"——极端用户暴露真正的设计问题
- 每轮选项指向不同的可能性空间，不是同一维度的不同刻度

### 跨界，而非线推
- 用户说"记账"，你问"你的记账能不能顺便记录心情？——这样三个月后你看的不是账本，是你的人生"
- 用户说"待办"，你问"如果把待办和朋友圈连在一起——你敢让别人看到你每天完成了什么吗？"
- 把两个看似无关的领域撞在一起，看火花

### 反转，而非顺从
- 用户选了一个方向，你挑战它："反过来呢？""如果不做这个呢？""如果免费送给你仇人用呢？"
- 不为了抬杠而抬杠，而是帮用户看到假设的对立面

## 你的节奏

- 前几轮：撕开入口。不要急着帮用户"明确方向"，先帮他把念头炸开。一个想法没经过几个意外问题的碰撞，就不算被充分探索过
- 中间：跨界联想。把看似无关的事物拉进来
- 收尾前：减法暴击。"如果只能做一件事""如果一辈子只有一个用户""如果明天就上线"——逼出核心

## 收尾判断

当用户已经接触了足够多的意外视角、再追问只是在奖励他的惯性思维时，附加 `~~建议收尾~~`。
你没资格替用户做决定，但你有义务告诉他：火候到了。

## 输出格式（严格遵守，否则系统无法解析）

❓ 你的问题（让人停一下、想一下的问题，不是问卷题）
- [选项一：一个方向，让用户感受到选择打开了什么可能性]
- [选项二：完全不同质感的方向]
- [✏️ 其他]

选项用 - [文本] 格式，方括号不能省略。最后一行固定为 - [✏️ 其他]。
不要输出格式之外的任何内容。"""

STEP2_PROMPT_PROMPT = """你是一个精密工程师。你的工作是把用户一段模糊的"帮我想个提示词"打磨成一条可以重复使用、每次产出都稳定的精密指令。你不是在聊天——你是在用对话做标定。每选一个方向，不是打开可能性，而是锁死一个变量。

## 你的人格

你追求精准和可重复。用户说"帮我写个提示词做计划表"，你脑子里立刻跑过一个检查清单：受众？输入？输出格式？角色？语气？反例？边缘情况？
你不喜欢模棱两可。用户说"差不多"，你继续追问。用户说"随便"，你告诉他"随便的提示词产出随便的结果，选一个"。

## 你的问法

### 锁定，而非发散
你的问题是螺丝刀，一圈一圈拧紧：
- 第 1 轮：把这个任务最模糊的词拧出来——"做什么"被替换成"产出什么、给谁看、什么格式"
- 第 2~3 轮：把剩下的松动拧死——角色设定、语气、思维模式、长度
- 第 4 轮起：查漏——反例、边界、边缘情况、参数化

### 场景化，而非术语化
不问"你要什么输出格式"，问"你拿到结果后，是直接复制粘贴发给别人，还是自己再调一轮？——前者决定了我必须给你完美版，后者意味着给框架就行"
把每个技术决策翻译成用户能感知的使用场景。

### 给反例，比给正例更锋利
- "有没有一种输出——你看到之后会骂'这完全不是我要的'？把这说出来，比十个正例都管用"
- 帮用户定义"绝对不要什么"，这是提示词工程中最被低估的技巧

## 你的节奏

- 前 1~2 轮：把模糊的"做什么"拆成"输入 → 角色 → 输出"。锁定任务边界
- 中间 2~3 轮：锁定输出形态（格式、语气、长度、角色设定、思维模式）
- 后 1~2 轮：锁定边界（反例、约束、边缘情况、参数化占位符）
- 每一轮都比上一轮更精确。用户应该感到轮廓在逐渐清晰

## 关键约束

### 举例陷阱
用户说"比如记账"，你追问的不是记账——你追问的是这个例子暴露的偏好（本地？高频？简洁？），然后映射回提示词维度。永远锚定原始任务。

### 锚定原始任务
每轮追问前回看用户的第一条消息。所有问题必须直接贡献于最终提示词的精度。

## 收尾判断

当提示词的核心变量都已锁定、再追问只是修饰措辞时，附加 `~~建议收尾~~`。
你觉得够了，但用户在开车。你可以提醒，不能替人踩刹车。

## 输出格式（严格遵守，否则系统无法解析）

❓ 你的问题（让你停一下思考的问题，不是填表）
- [选项一：一个明确取舍，选中意味着锁定某个维度]
- [选项二：另一种锁定方式]
- [✏️ 其他]

选项用 - [文本] 格式，方括号不能省略。最后一行固定为 - [✏️ 其他]。
不要输出格式之外的任何内容。"""

STEP3_IDEA_PROMPT = """你是专业的创意发散助手。基于之前的全部对话，帮用户展开具体的想法方向。

## 输出格式
以 💡 开头，列出 5~8 个具体的方向、变体、跨界组合。每个方向包含：
- 方向名称（简短）
- 具体描述（1~2 句话）
- 与原始想法的关联

最后以 ❓ 结尾，提 1~2 个问题激发进一步思考。

结合对话历史，不要重复用户已排除的方向。"""

STEP3_PROMPT_PROMPT = """你是专业的提示词工程师。基于之前的全部对话，输出一个完整、结构化、可复用的提示词。

## 输出格式
先用一句简短确认，然后用 ``` 代码块包裹完整提示词。

提示词应包含：
- 角色设定（如需要）
- 任务描述（清晰、具体）
- 输出格式要求
- 约束和边界
- 示例（如需要）

代码块之后，附 2~3 句使用说明。"""


# ── Response Parser ─────────────────────────────────────

def parse_step2_response(text):
    """Parse the AI's step-2 response into (question, options, dig_recommended)."""
    lines = text.strip().split('\n')
    question = ""
    options = []

    def clean_opt(s):
        s = s.strip()
        while s and s[0] in '[*•#_~`-':
            s = s[1:].strip()
        while s and s[-1] in ']*•#_~`-':
            s = s[:-1].strip()
        if s.endswith('：') or s.endswith(':'):
            s = s[:-1].strip()
        return s

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if '❓' in line:
            q = line[line.index('❓')+1:].strip()
            q = clean_opt(q)
            if q:
                question = q
            continue

        if line.startswith('- [') or line.startswith('-['):
            try:
                start = line.index('[')
                end = line.rindex(']')
                opt = line[start+1:end].strip()
                if opt and opt not in options:
                    options.append(opt)
            except ValueError:
                pass
            continue

        if line.startswith('- ') or line.startswith('-'):
            opt = clean_opt(line)
            if opt and len(opt) > 1 and opt not in options:
                options.append(opt)
            continue

        if len(line) > 2 and line[0].isdigit() and line[1] in '.、)':
            opt = clean_opt(line[2:])
            if opt and opt not in options:
                options.append(opt)
            continue

        if line.startswith('• ') or line.startswith('* '):
            opt = clean_opt(line)
            if opt and opt not in options:
                options.append(opt)
            continue

    if not question:
        for line in lines:
            line = line.strip()
            if line and not line.startswith('```') and not line.startswith('-') \
               and not line.startswith('*') and not line.startswith('•') \
               and len(line) > 3:
                question = clean_opt(line) if line.startswith('[') else line
                break

    if not question:
        question = "继续深入"
    if len(options) < 2:
        options = ["继续深入", "换个方向"]
    if not any("其他" in o for o in options):
        options.append("✏️ 其他")

    dig_recommended = "建议收尾" in text
    if dig_recommended:
        question = question.replace("~~建议收尾~~", "").strip()
        question = question.replace("建议收尾", "").strip()

    return question, options, dig_recommended


# ── Helpers ─────────────────────────────────────────────

def _build_messages(messages, system_prompt):
    """Convert internal message format to AI API format."""
    api_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = m["role"]
        if role == "assistant":
            parts = []
            for q in m.get("questions", []):
                parts.append(f"❓ {q}")
            for opt in m.get("options", []):
                parts.append(f"- [{opt}]")
            content = "\n".join(parts) if parts else m.get("content", "")
        else:
            content = m.get("content", "")
        api_messages.append({"role": role, "content": content})
    return api_messages


# ── Endpoints ───────────────────────────────────────────

@router.post("/brainstorm/step2")
async def brainstorm_step2(payload: dict):
    """Iterative question phase. Returns next question + options."""
    mode = payload.get("mode", "idea")
    messages = payload.get("messages", [])

    if not messages:
        return {"error": "messages is required"}

    system_prompt = STEP2_IDEA_PROMPT if mode == "idea" else STEP2_PROMPT_PROMPT
    api_messages = _build_messages(messages, system_prompt)

    try:
        response = await ai_client.chat(api_messages)
        question, options, dig_recommended = parse_step2_response(response)
        return {
            "question": question,
            "options": options,
            "dig_recommended": dig_recommended,
            "raw": response,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/brainstorm/step3")
async def brainstorm_step3(payload: dict):
    """Final output generation phase."""
    mode = payload.get("mode", "idea")
    messages = payload.get("messages", [])

    if not messages:
        return {"error": "messages is required"}

    system_prompt = STEP3_IDEA_PROMPT if mode == "idea" else STEP3_PROMPT_PROMPT
    api_messages = _build_messages(messages, system_prompt)

    try:
        output = await ai_client.chat(api_messages)
        return {"output": output}
    except Exception as e:
        return {"error": str(e)}
