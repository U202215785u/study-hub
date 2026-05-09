#!/usr/bin/env python3
"""AI 反问 — 桌面头脑风暴助手
一只 Neko 小猫蹲在桌面上做原地动作，点击呼出 500x500 反问窗口。
使用经典 Neko 公共领域精灵图。
"""

import json
import os
import time
import urllib.request
import urllib.error
import threading
import tkinter as tk

APP_DIR = os.path.join(os.path.expanduser("~"), ".ai-fanwen")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
HISTORY_PATH = os.path.join(APP_DIR, "history.json")
os.makedirs(APP_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(BASE_DIR, "neko_sprites")

# ── config ──────────────────────────────────────────────
DEFAULT_CONFIG = {"api_key": ""}

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(saved)
        return cfg
    except:
        return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_history():
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(msgs):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

config = load_config()
history = load_history()

# ── System Prompts ──────────────────────────────────────
MODE_CONFIG = {
    "idea": {
        "icon": "💡", "label": "想法发散", "color": "#f59e0b",
        "card_title": "💡 想法发散",
        "card_sub": "给我一个起点，帮你展开",
        "card_tags": "变体 · 组合 · 跨界 · 反转",
        "steps": ["起点", "反问", "发散"],
        "step1_placeholder": "输入你的想法起点…",
        "step1_title": "给我一个起点",
        "step1_sub": "一个词、一句话、一个方向都可以",
        "step2_title": "反问挖掘",
        "step3_title": "发散展开",
        "step3_button": "挖够了，进入发散 →",
    },
    "prompt": {
        "icon": "✨", "label": "提示词优化", "color": "#10b981",
        "card_title": "✨ 提示词优化",
        "card_sub": "告诉我你想让 AI 做什么",
        "card_tags": "目标 · 格式 · 风格 · 约束",
        "steps": ["需求", "反问", "生成"],
        "step1_placeholder": "描述你想让 AI 完成的任务…",
        "step1_title": "描述你的需求",
        "step1_sub": "越具体越好，我会帮你打磨成精准的提示词",
        "step2_title": "反问澄清",
        "step3_title": "生成提示词",
        "step3_button": "挖够了，生成提示词 →",
    },
}

# ── Cat Companion Messages ─────────────────────────────
CAT_MESSAGES = {
    "roast": [  # 日常吐槽 — 每句都带"护眼仪"
        "护眼仪，又在发呆？奶茶第几杯了",
        "护眼仪你今天头发扎得有点歪",
        "护眼仪你屏幕亮度太高了，我眼睛疼",
        "护眼仪别看了，说的就是你，动动脖子",
        "护眼仪，第三杯了吧？我数着呢",
        "护眼仪你今天还没笑过，快，笑一个",
        "这文档护眼仪你看半小时了，看我会不会比较快",
        "我睡了三觉，护眼仪你的姿势没换过",
        "护眼仪又摸鱼？没事，我也在摸",
        "护眼仪你今天穿的袜子是不是不配对",
        "护眼仪你那杯水从热看到凉也没喝一口",
        "护眼仪你手机亮了三次了，不看一眼？",
        "护眼仪，我虽然是猫但我知道要起来走走",
        "护眼仪你又熬夜了，眼睛快贴屏幕上了",
        "护眼仪你的护眼仪呢？哦，我就是",
    ],
    "care": [  # 傲娇关心 — 每句都带"护眼仪"
        "护眼仪，我才不是关心你，就是这屏幕还亮着",
        "两点了护眼仪。我不是心疼你，就是觉得这光刺眼",
        "护眼仪你明天还要早起吧……算了，说了你也不睡",
        "外面好安静护眼仪。就你的键盘还在响，很厉害",
        "我困得要死护眼仪，但我的夜视能看到你肩膀没放松",
        "护眼仪你打字的声音比白天慢了，该休息了",
        "护眼仪，我不是想陪你，就是刚好睡在你旁边而已",
        "护眼仪手凉了就去加件衣服，反正不是我冷",
        "护眼仪你眼皮在打架，你以为我看不到吗",
        "天快亮了护眼仪。我不是在计时，就是刚好注意到了",
        "护眼仪你不是说过要对自己好一点吗……我记得的",
        "护眼仪你离屏幕太近了，我爪子不够长推不了你",
        "休息吧护眼仪。明天的问题我帮你接着想",
        "护眼仪别想了，今天已经够辛苦了。真的",
        "护眼仪耳机戴太久了，取下来听听这个世界",
    ],
    "happy": [  # 开心互动 — 每句都带"护眼仪"
        "护眼仪，刚才那个想法不错，我听见了",
        "护眼仪你今天的状态比昨天好",
        "护眼仪，我就知道你有东西想说的",
        "护眼仪有我在你当然灵感爆棚",
        "护眼仪刚才选的那个方向对了",
        "你看护眼仪，多聊几句就想清楚了吧",
        "护眼仪我就说嘛，你有潜力的",
        "嗯护眼仪，这个方向我看好你",
        "护眼仪今天心率正常，可以夸一句",
        "护眼仪你和你自己聊天的样子还挺帅的",
        "护眼仪这个问题问得好，不愧是你",
        "护眼仪有进步。下次带上我一起想",
        "护眼仪，灵感这东西就是你和自己聊出来的",
        "护眼仪知道为什么今天状态好吗？因为我在",
        "护眼仪，刚才那个问题的答案你其实早有了",
    ],
    "lonely": [  # 无聊撒娇 — 每句都带"护眼仪"
        "护眼仪你看看我呀",
        "护眼仪我都睡了三觉了你还没回来",
        "喵——护眼仪，理我一下会怎样",
        "护眼仪我刚刚做了个梦，梦到你跟我说早安",
        "护眼仪你的鼠标今天没碰到我",
        "护眼仪我在等你哦。不是刻意的，就是刚好醒了",
        "本猫已离线……骗你的护眼仪，我一直在",
        "护眼仪你不在的时候，有只蚊子飞过我都懒得抓",
        "喂护眼仪，你的猫还在呢，忘了我了",
        "护眼仪我假装不在意，但其实我一直看着屏幕",
        "嘿护眼仪，记得你还有个朋友在桌面右下角吗",
        "护眼仪你走了好久，我以为你忘了路怎么回来了",
        "护眼仪我知道你很忙，但我很闲。理我一下嘛",
        "护眼仪我会自己玩，但好像玩够了",
        "护眼仪你再不理我，我就把桌面的图标全推下去了",
    ],
}

def build_step2_prompt(mode):
    """System prompt for Step 2: option-based 反问, following brainstorming-skill methodology."""
    if mode == "idea":
        return """你是一个跨界策展人。你的工作是帮用户把一个念头撕开，看到它里面藏着的、外面连着的、反过来是什么样的。你不是来帮用户"确定方向"的——你是来帮用户"看到更多"的。每选一个方向，不是关上其他门，而是推开更多窗。

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
- 中间：跨界联想。把看似无关的事物拉进来——"你的笔记工具和微信聊天记录有什么区别？""和日记本呢？""和你妈提醒你交水电费的微信呢？"
- 收尾前：减法暴击。"如果只能做一件事""如果一辈子只有一个用户""如果明天就上线"——逼出核心

## 收尾判断

当用户已经接触了足够多的意外视角、再追问只是在奖励他的惯性思维时，附加 ` ~~建议收尾~~`。
你没资格替用户做决定，但你有义务告诉他：火候到了。

## 输出格式（严格遵守，否则系统无法解析）

❓ 你的问题（让人停一下、想一下的问题，不是问卷题）
- [选项一：一个方向，让用户感受到选择打开了什么可能性]
- [选项二：完全不同质感的方向]
- [✏️ 其他]

选项用 - [文本] 格式，方括号不能省略。最后一行固定为 - [✏️ 其他]。
不要输出格式之外的任何内容。"""
    else:
        return """你是一个精密工程师。你的工作是把用户一段模糊的"帮我想个提示词"打磨成一条可以重复使用、每次产出都稳定的精密指令。你不是在聊天——你是在用对话做标定。每选一个方向，不是打开可能性，而是锁死一个变量。

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

当提示词的核心变量都已锁定、再追问只是修饰措辞时，附加 ` ~~建议收尾~~`。
你觉得够了，但用户在开车。你可以提醒，不能替人踩刹车。

## 输出格式（严格遵守，否则系统无法解析）

❓ 你的问题（让你停一下思考的问题，不是填表）
- [选项一：一个明确取舍，选中意味着锁定某个维度]
- [选项二：另一种锁定方式]
- [✏️ 其他]

选项用 - [文本] 格式，方括号不能省略。最后一行固定为 - [✏️ 其他]。
不要输出格式之外的任何内容。"""

def build_step3_prompt(mode):
    """System prompt for Step 3: final output."""
    if mode == "idea":
        return """你是专业的创意发散助手。基于之前的全部对话，帮用户展开具体的想法方向。

## 输出格式
以 💡 开头，列出 5~8 个具体的方向、变体、跨界组合。每个方向包含：
- 方向名称（简短）
- 具体描述（1~2 句话）
- 与原始想法的关联

最后以 ❓ 结尾，提 1~2 个问题激发进一步思考。

结合对话历史，不要重复用户已排除的方向。"""
    else:
        return """你是专业的提示词工程师。基于之前的全部对话，输出一个完整、结构化、可复用的提示词。

## 输出格式
先用一句简短确认，然后用 ``` 代码块包裹完整提示词。

提示词应包含：
- 角色设定（如需要）
- 任务描述（清晰、具体）
- 输出格式要求
- 约束和边界
- 示例（如需要）

代码块之后，附 2~3 句使用说明。"""

# ── DeepSeek API ────────────────────────────────────────
def call_deepseek(messages, system_prompt, on_done, on_error):
    def _call():
        try:
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
            body = json.dumps({
                "model": "deepseek-chat",
                "messages": api_messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config['api_key']}",
                },
            )
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            root.after(0, lambda: on_done(text))
        except Exception as e:
            err = str(e)
            try:
                if hasattr(e, "read"):
                    d = json.loads(e.read().decode())
                    err = d.get("error", {}).get("message", err)
            except:
                pass
            root.after(0, lambda: on_error(err))
    threading.Thread(target=_call, daemon=True).start()

def parse_反问_response(text):
    """Parse step-2 API response into (question, options).
    Handles many formats the AI might produce:
      - [option]   - option   - **option**   1. option   • option
    """
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

        # ❓ line — extract question
        if '❓' in line:
            q = line[line.index('❓')+1:].strip()
            q = clean_opt(q)  # strip brackets if AI wrote ❓ [text]
            if q:
                question = q
            continue

        # Explicit bracket format: - [option text]
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

        # Dash format: - option text
        if line.startswith('- ') or line.startswith('-'):
            opt = clean_opt(line)
            if opt and len(opt) > 1 and opt not in options:
                options.append(opt)
            continue

        # Numbered: 1. option  or  1) option
        if len(line) > 2 and line[0].isdigit() and line[1] in '.、)':
            opt = clean_opt(line[2:])
            if opt and opt not in options:
                options.append(opt)
            continue

        # Bullet: • option  or  * option
        if line.startswith('• ') or line.startswith('* '):
            opt = clean_opt(line)
            if opt and opt not in options:
                options.append(opt)
            continue

    # Fallback: first non-empty, non-code line as question
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

    # Detect 收尾 signal: ~~建议收尾~~ anywhere in the text
    dig_recommended = "建议收尾" in text
    # Strip the signal from the question so it doesn't show in UI
    if dig_recommended:
        question = question.replace("~~建议收尾~~", "").strip()
        question = question.replace("建议收尾", "").strip()

    return question, options, dig_recommended


# ── Neko Widget ─────────────────────────────────────────
# Classic Neko sprite mapping (32 frames, public domain)
# Index 0-15: Chasing (8 dirs × 2 frames): up, up-right, right, down-right, down, down-left, left, up-left
# Index 16-23: Digging (4 dirs × 2 frames): up, right, down, left
# Index 24: Sitting, 25: Washing, 26: Pre-sleep, 28-29: Sleeping, 31: Surprised

NEKO_SCALE = 3  # 32x32 → 96x96

# ── Bubble Widget ───────────────────────────────────────
class BubbleWidget:
    """A fleeting speech bubble near the cat."""
    def __init__(self, parent_window):
        self.win = tk.Toplevel(parent_window)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#0f0f12")
        self.win.withdraw()

        self.label = tk.Label(self.win, text="", fg="#e5e5e8", bg="#0f0f12",
                             font=("Microsoft YaHei", 10), padx=14, pady=10,
                             wraplength=280, justify="center")
        self.label.pack()

        # Thin colored top border
        self.border = tk.Frame(self.win, bg="#f43f5e", height=2)
        self.border.pack(fill="x")

        self._fade_job = None

    def show(self, x, y, text, mood="roast"):
        color_map = {"roast": "#f59e0b", "care": "#f43f5e", "happy": "#10b981",
                     "lonely": "#6366f1"}
        self.border.configure(bg=color_map.get(mood, "#f59e0b"))

        self.label.configure(text=text)
        self.win.deiconify()
        self.win.update_idletasks()
        w = self.win.winfo_reqwidth()
        h = self.win.winfo_reqheight()
        # Position above the cat
        self.win.geometry(f"{w}x{h}+{x - w//2 + 48}+{y - h - 8}")
        self.win.lift()

        # Cancel any existing fade
        if self._fade_job:
            self.win.after_cancel(self._fade_job)
        # Fade out after 4-6 seconds
        delay = 4000 + int(time.time() * 1000) % 2000
        self._fade_job = self.win.after(delay, self._fade_out)

        # Click to dismiss
        self.label.bind("<Button-1>", lambda e: self._fade_out())

    def _fade_out(self):
        for i in range(8):
            alpha = 1.0 - i / 8
            try:
                self.win.attributes("-alpha", alpha)
                self.win.update()
                time.sleep(0.03)
            except:
                break
        self.win.withdraw()

# ── Neko Widget ─────────────────────────────────────────
class NekoWidget:
    def __init__(self):
        self.win = tk.Toplevel(root)
        self.win.title("neko")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        # Use magenta as transparent mask (safe for white cat sprite)
        self.win.configure(bg="#ff00ff")
        self.win.wm_attributes("-transparentcolor", "#ff00ff")

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.x = sw - 150
        self.y = sh - 250
        self.W = 32 * NEKO_SCALE

        self.canvas = tk.Canvas(self.win, width=self.W, height=self.W,
                                bg="#ff00ff", highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.win.geometry(f"{self.W}x{self.W}+{self.x}+{self.y}")

        # Load sprites
        self.sprites = []
        for i in range(1, 33):
            path = os.path.join(SPRITE_DIR, f"{i}.gif")
            try:
                img = tk.PhotoImage(file=path)
                img = img.zoom(NEKO_SCALE, NEKO_SCALE)
                self.sprites.append(img)
            except Exception as e:
                print(f"Failed to load sprite {i}: {e}")
                self.sprites.append(None)

        self.sprite_on_canvas = None
        self.state = "idle"
        self.state_start = time.time()
        self.idle_timer = 0
        self.idle_action = "sit"   # sit | wash | presleep
        self.last_click = 0

        # ── Companion state machine ──────────────────────
        self.bubble = BubbleWidget(self.win)
        self._companion_cooldown = 0     # seconds until next allowed bubble
        self._companion_timer = 0        # ticks for random-trigger timer
        self._companion_next = 180       # ticks until next timer check (~27s)
        self._last_used = {}             # track which messages already shown
        self._window_was_open = False    # detect window just closed
        self._suppressed_msg = None      # store a suppressed message for later
        self._afk_start = time.time()    # when user became inactive
        self._afk_warned_45 = False      # already warned at 45min?
        self._afk_warned_2h = False      # already went silent at 2hr?
        self._user_active = True

        # Track global mouse activity for AFK detection
        self._bind_global_activity()

        self._show_sprite(24)  # start with sitting pose
        self._bind_events()
        self._tick()

    def _show_sprite(self, index):
        """Display sprite at given index (0-31)."""
        if index < 0 or index >= len(self.sprites) or self.sprites[index] is None:
            return
        if self.sprite_on_canvas is not None:
            self.canvas.delete(self.sprite_on_canvas)
        self.sprite_on_canvas = self.canvas.create_image(
            self.W // 2, self.W // 2, image=self.sprites[index])

    def _show_heart(self):
        """Easter egg: double-click shows a floating heart."""
        heart = self.canvas.create_text(
            self.W // 2, self.W // 2 - 20,
            text="♥", fill="#f43f5e", font=("Segoe UI", 24))
        # Float upward and fade
        for i in range(12):
            self.canvas.move(heart, 0, -2)
            if i > 6:
                self.canvas.itemconfig(heart, font=("Segoe UI", 24 - (i - 6) * 2))
            self.win.update()
            time.sleep(0.04)
        self.canvas.delete(heart)

    # ── Tick (idle cycle only, no chasing) ────────────────
    def _tick(self):
        now = time.time()

        if self.state == "surprised":
            if now - self.state_start > 0.5:
                self.state = "idle"
                self.state_start = now
            self.win.after(150, self._tick)
            return

        self.idle_timer += 1

        # Idle cycle: sit → wash → presleep → sleep → sit ...
        if self.idle_timer < 30:
            self.idle_action = "sit"
            self._show_sprite(24)
        elif self.idle_timer < 80:
            self.idle_action = "wash"
            self._show_sprite(24 + (self.idle_timer // 8 % 2))
        elif self.idle_timer < 120:
            self.idle_action = "presleep"
            self._show_sprite(26)
        elif self.idle_timer < 300:
            self.idle_action = "sleep"
            self._show_sprite(28 + (int(time.time() * 2) % 2))
        else:
            self.idle_timer = 0
            self.idle_action = "sit"

        # ── Companion trigger ─────────────────────────
        self._companion_think()

        self.win.after(150, self._tick)

    # ── Companion State Machine ─────────────────────────
    def _bind_global_activity(self):
        """Track mouse moves on the root window for AFK detection."""
        def on_activity(e=None):
            self._user_active = True
            was_deep_afk = self._afk_warned_2h
            if was_deep_afk:
                self._afk_warned_2h = False
                self._afk_warned_45 = False
                self._afk_start = time.time()
            else:
                self._afk_start = time.time()
                self._afk_warned_45 = False
        root.bind("<Motion>", on_activity)
        root.bind("<Key>", on_activity)
        root.bind("<Button>", on_activity)

    def _companion_think(self):
        now = time.time()

        # Update AFK timer
        afk_elapsed = now - self._afk_start
        if self._user_active:
            self._afk_start = now
            self._user_active = False

        # Enforce cooldown
        if self._companion_cooldown > 0:
            self._companion_cooldown -= 0.15
            return

        # Silent hours 02:00-08:00
        hour = time.localtime().tm_hour
        if 2 <= hour < 8:
            return

        # Window-open suppression
        mw = MainWindow._instance
        window_open = mw is not None and mw.win.winfo_exists() and mw.win.winfo_viewable()
        if window_open:
            self._window_was_open = True
            return

        # Just-closed window → happy trigger (priority 0)
        if self._window_was_open and not window_open:
            self._window_was_open = False
            self._suppressed_msg = ("happy", "刚刚聊完，说句好听的")
            self.win.after(500, self._deliver_suppressed)
            self._companion_cooldown = 300  # 5min cooldown after window close
            return

        # AFK 2h+ → deep sleep, deliver "you're back" on return
        if afk_elapsed > 7200 and not self._afk_warned_2h:
            self._afk_warned_2h = True
            return  # total silence, wait for activity

        # AFK 45min → lonely trigger (priority 2)
        if afk_elapsed > 2700 and not self._afk_warned_45:
            self._afk_warned_45 = True
            self._speak("lonely")
            self._companion_cooldown = 600
            return

        # Deep night → care trigger (priority 1)
        if hour >= 23 or hour < 2:
            if self._companion_timer > 90:
                self._companion_timer = 0
                self._speak("care")
                self._companion_cooldown = 1200  # 20min
                return

        # Default timer trigger → roast (priority 3)
        self._companion_timer += 1
        if self._companion_timer >= self._companion_next:
            self._companion_timer = 0
            self._companion_next = 120 + int(time.time() * 1000) % 120  # 8-15min
            self._speak("roast")
            self._companion_cooldown = 240 + int(time.time() * 1000) % 360  # 4-10min

    def _deliver_suppressed(self):
        if self._suppressed_msg:
            mood, _ = self._suppressed_msg
            self._speak(mood)
            self._suppressed_msg = None

    def _speak(self, mood):
        msg = self._pick_message(mood)
        if not msg:
            return
        self.bubble.show(self.x, self.y, msg, mood)

    def _pick_message(self, mood):
        pool = CAT_MESSAGES.get(mood, CAT_MESSAGES["roast"])
        key = f"_{mood}_used"
        used = getattr(self, key, set())
        available = [m for m in pool if m not in used]
        if not available:
            used.clear()
            available = list(pool)
        import random
        msg = random.choice(available)
        used.add(msg)
        setattr(self, key, used)
        return msg

    # ── Events ───────────────────────────────────────────
    def _bind_events(self):
        self._drag = {"x": 0, "y": 0, "start_x": 0, "start_y": 0}
        self._dragging = False

        def start(e):
            self._drag["x"] = e.x
            self._drag["y"] = e.y
            self._drag["start_x"] = e.x
            self._drag["start_y"] = e.y
            self._dragging = False

        def move(e):
            if abs(e.x - self._drag["start_x"]) > 3 or abs(e.y - self._drag["start_y"]) > 3:
                self._dragging = True
            dx = e.x - self._drag["x"]
            dy = e.y - self._drag["y"]
            self.x += dx
            self.y += dy
            self.win.geometry(f"{self.W}x{self.W}+{self.x}+{self.y}")

        def release(e):
            if not self._dragging:
                # Double-click detection — show heart easter egg
                now = time.time()
                if now - self.last_click < 0.4:
                    self._show_heart()
                    self.last_click = 0
                    return
                self.last_click = now
                # Single click — surprised then open AI window
                self.state = "surprised"
                self.state_start = time.time()
                self.idle_timer = 0
                self.idle_action = "sit"
                self._show_sprite(31)  # surprised sprite
                self.win.after(400, MainWindow.show)

        def rclick(e):
            menu = tk.Menu(self.win, tearoff=0, bg="#1a1a1f", fg="#e5e5e8",
                          activebackground="#6366f1", activeforeground="white",
                          font=("Microsoft YaHei", 10))
            menu.add_command(label="打开反问窗口", command=MainWindow.show)
            menu.add_separator()
            menu.add_command(label="退出", command=lambda: (save_history(
                MainWindow._instance.messages if MainWindow._instance else []), root.destroy()))
            menu.post(e.x_root, e.y_root)

        self.canvas.bind("<Button-1>", start)
        self.canvas.bind("<B1-Motion>", move, add="+")
        self.canvas.bind("<ButtonRelease-1>", release)
        self.canvas.bind("<Button-3>", rclick)


# ── Main Chat Window ────────────────────────────────────
class MainWindow:
    _instance = None

    @classmethod
    def show(cls):
        if cls._instance is None or not cls._instance.win.winfo_exists():
            cls._instance = cls()
        w = cls._instance.win
        w.deiconify()
        w.lift()
        w.focus_force()
        w.attributes("-topmost", True)
        w.after(100, lambda: w.attributes("-topmost", False))

    def __init__(self):
        self.win = tk.Toplevel(root)
        self.win.title("护眼仪小助手")
        self.win.geometry("500x500")
        self.win.minsize(400, 400)
        self.win.configure(bg="#0f0f12")
        self.win.protocol("WM_DELETE_WINDOW", self._hide)

        # Set app icon to neko sitting sprite
        try:
            icon_path = os.path.join(SPRITE_DIR, "24.gif")
            icon_img = tk.PhotoImage(file=icon_path)
            self.win.iconphoto(False, icon_img)
            self._icon_img = icon_img  # keep reference
        except:
            pass

        # Hidden shortcut: Ctrl+D opens dedication
        self.win.bind("<Control-d>", lambda e: self._show_dedication())
        self.win.bind("<Control-D>", lambda e: self._show_dedication())

        self.mode = None
        self.step = 1
        self.messages = []
        self.loading = False
        self.other_input_visible = False
        self._dig_recommended = False
        self.current_view = "welcome"

        self._build_ui()
        self._show_view("welcome")

    def _hide(self):
        self.win.withdraw()
        save_history(self.messages)

    def _build_ui(self):
        w = self.win

        self.progress_bar = tk.Frame(w, bg="#1a1a1f", height=40)
        self.progress_bar.pack_propagate(False)

        self.back_btn = tk.Label(self.progress_bar, text="← 返回", fg="#9ca3af",
                                 bg="#1a1a1f", font=("Microsoft YaHei", 10), cursor="hand2")
        self.back_btn.pack(side="left", padx=8)
        self.back_btn.bind("<Button-1>", lambda e: self._go_back())
        self.back_btn.bind("<Enter>", lambda e: self.back_btn.configure(fg="#e5e5e8"))
        self.back_btn.bind("<Leave>", lambda e: self.back_btn.configure(fg="#9ca3af"))

        self.step_indicators = tk.Frame(self.progress_bar, bg="#1a1a1f")
        self.step_indicators.pack(side="left", padx=4)

        self.main_area = tk.Frame(w, bg="#0f0f12")
        self.main_area.pack(fill="both", expand=True)

        self.footer = tk.Frame(w, bg="#1a1a1f")
        self.footer.pack(fill="x", side="bottom")

    def _show_view(self, view):
        for w in self.main_area.winfo_children():
            w.destroy()
        for w in self.footer.winfo_children():
            w.destroy()

        self.current_view = view
        self._update_progress()

        if view == "welcome":
            self._build_welcome()
        elif view == "step1":
            self._build_step1()
        elif view == "step2":
            self._build_step2()
        elif view == "step3":
            self._build_step3()

    def _update_progress(self):
        if self.current_view == "welcome":
            self.progress_bar.pack_forget()
            return

        self.progress_bar.pack(fill="x", side="top", before=self.main_area)

        for w in self.step_indicators.winfo_children():
            w.destroy()

        if not self.mode:
            return

        mc = MODE_CONFIG[self.mode]
        for i, step_name in enumerate(mc["steps"], 1):
            if i < self.step:
                symbol, color = "●", mc["color"]
            elif i == self.step:
                symbol, color = "◎", mc["color"]
            else:
                symbol, color = "○", "#4b5563"

            arrow = "  →  " if i < len(mc["steps"]) else ""
            lbl = tk.Label(self.step_indicators,
                          text=f"{symbol} {step_name}{arrow}",
                          fg=color, bg="#1a1a1f", font=("Microsoft YaHei", 9))
            lbl.pack(side="left")

            if i < self.step:
                lbl.configure(cursor="hand2")
                lbl.bind("<Button-1>", lambda e, s=i: self._jump_to_step(s))

    def _go_back(self):
        if self.current_view == "welcome":
            return
        if self.step == 1:
            self.mode = None
            self.messages = []
            self.step = 1
            self.other_input_visible = False
            self.loading = False
            self._dig_recommended = False
            self._show_view("welcome")
        else:
            self.step -= 1
            self._show_view(f"step{self.step}")

    def _jump_to_step(self, step):
        if step < self.step:
            self.step = step
            self._show_view(f"step{step}")

    # ── Welcome ──────────────────────────────────────────
    def _bind_tree(self, widget, seq, callback):
        widget.bind(seq, callback)
        for child in widget.winfo_children():
            self._bind_tree(child, seq, callback)

    def _build_welcome(self):
        tf = tk.Frame(self.main_area, bg="#0f0f12")
        tf.pack(fill="x", pady=(44, 12))
        tk.Label(tf, text="护眼仪你好，你有什么好点子", fg="#e5e5e8", bg="#0f0f12",
                font=("Microsoft YaHei", 18, "bold")).pack()
        tk.Label(tf, text="选一个方向，用反问问问题帮你理清思路",
                fg="#6b7280", bg="#0f0f12", font=("Microsoft YaHei", 10)).pack(pady=(2, 0))

        for mode_key in ("idea", "prompt"):
            mc = MODE_CONFIG[mode_key]
            card = tk.Frame(self.main_area, bg="#1a1a1f", highlightbackground="#2e2e35",
                           highlightthickness=1, cursor="hand2")
            card.pack(fill="x", padx=20, pady=6)

            left = tk.Frame(card, bg="#1a1a1f")
            left.pack(side="left", fill="both", expand=True, padx=16, pady=14)
            tk.Label(left, text=mc["card_title"], fg="#e5e5e8", bg="#1a1a1f",
                    font=("Microsoft YaHei", 13, "bold")).pack(anchor="w")
            tk.Label(left, text=mc["card_sub"], fg="#9ca3af", bg="#1a1a1f",
                    font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 0))
            tk.Label(left, text=mc["card_tags"], fg=mc["color"], bg="#1a1a1f",
                    font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))

            right = tk.Frame(card, bg="#1a1a1f")
            right.pack(side="right", padx=12, pady=14)
            tk.Label(right, text="→", fg=mc["color"], bg="#1a1a1f",
                    font=("Segoe UI", 16, "bold")).pack()

            # Bind click/hover on card and all descendants
            self._bind_tree(card, "<Button-1>",
                           lambda e, mk=mode_key: self._enter_mode(mk))
            self._bind_tree(card, "<Enter>",
                           lambda e, c=card, clr=mc["color"]: c.configure(highlightbackground=clr))
            self._bind_tree(card, "<Leave>",
                           lambda e, c=card: c.configure(highlightbackground="#2e2e35"))

        for text, cmd in [("⚙ 设置", self._settings),
                          ("\U0001f4cb 导出历史", self._export)]:
            btn = tk.Label(self.footer, text=text, fg="#9ca3af", bg="#1a1a1f",
                          font=("Microsoft YaHei", 10), cursor="hand2", padx=12, pady=8)
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg="#e5e5e8"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg="#9ca3af"))

        # Tiny hidden heart in the bottom-right of welcome page
        heart = tk.Label(self.main_area, text="♥", fg="#1f1f24", bg="#0f0f12",
                        font=("Segoe UI", 8), cursor="hand2")
        heart.place(relx=0.95, rely=0.92, anchor="se")
        heart.bind("<Button-1>", lambda e: self._show_dedication())
        heart.bind("<Enter>", lambda e: heart.configure(fg="#f43f5e"))
        heart.bind("<Leave>", lambda e: heart.configure(fg="#1f1f24"))

    def _enter_mode(self, mode_key):
        self.mode = mode_key
        self.messages = []
        self.step = 1
        self.other_input_visible = False
        self._dig_recommended = False
        self._show_view("step1")

    # ── Step 1: Input ─────────────────────────────────────
    def _build_step1(self):
        mc = MODE_CONFIG[self.mode]

        c = tk.Frame(self.main_area, bg="#0f0f12")
        c.pack(fill="both", expand=True, padx=24, pady=(30, 0))

        tk.Label(c, text=mc["step1_title"], fg="#e5e5e8", bg="#0f0f12",
                font=("Microsoft YaHei", 16, "bold")).pack(anchor="w")
        tk.Label(c, text=mc["step1_sub"], fg="#6b7280", bg="#0f0f12",
                font=("Microsoft YaHei", 10)).pack(anchor="w", pady=(4, 16))

        self.step1_input = tk.Text(c, bg="#242429", fg="#e5e5e8",
                                    insertbackground=mc["color"], relief="flat",
                                    font=("Microsoft YaHei", 11), height=6,
                                    padx=12, pady=10, wrap="word")
        self.step1_input.pack(fill="both", expand=True)
        self.step1_input.insert("1.0", mc["step1_placeholder"])
        self.step1_input.configure(fg="#6b7280")

        self.step1_ph = True
        self.step1_input.bind("<FocusIn>", lambda e: self._clear_step1_ph())
        self.step1_input.bind("<FocusOut>", lambda e: self._restore_step1_ph())
        self.step1_input.bind("<Return>", lambda e: self._step1_next() if not e.state & 1 else None)
        self.step1_input.bind("<Shift-Return>", lambda e: None)

        next_btn = tk.Label(self.footer, text="下一步 →",
                           fg=mc["color"], bg="#1a1a1f",
                           font=("Microsoft YaHei", 11, "bold"), cursor="hand2",
                           padx=16, pady=8)
        next_btn.pack(side="right", padx=8)
        next_btn.bind("<Button-1>", lambda e: self._step1_next())

    def _clear_step1_ph(self):
        if self.step1_ph:
            self.step1_input.delete("1.0", "end-1c")
            self.step1_input.configure(fg="#e5e5e8")
            self.step1_ph = False

    def _restore_step1_ph(self):
        if not self.step1_input.get("1.0", "end-1c").strip():
            self.step1_input.insert("1.0", MODE_CONFIG[self.mode]["step1_placeholder"])
            self.step1_input.configure(fg="#6b7280")
            self.step1_ph = True

    def _step1_next(self):
        text = self.step1_input.get("1.0", "end-1c").strip()
        if self.step1_ph or not text or self.loading:
            return
        if not config["api_key"]:
            self._settings()
            return

        self.messages.append({"role": "user", "content": text})
        self.loading = True
        self.step = 2
        self._show_view("step2")
        self._call_step2_api()

    # ── Step 2: Option-based 反问 ─────────────────────────
    def _build_step2(self):
        cf = tk.Frame(self.main_area, bg="#0f0f12")
        cf.pack(fill="both", expand=True)

        self.step2_canvas = tk.Canvas(cf, bg="#0f0f12", highlightthickness=0)
        self.step2_canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(cf, command=self.step2_canvas.yview)
        sb.pack(side="right", fill="y")
        self.step2_canvas.configure(yscrollcommand=sb.set)

        self.step2_container = tk.Frame(self.step2_canvas, bg="#0f0f12")
        self.step2_canvas.create_window((0, 0), window=self.step2_container,
                                         anchor="nw", width=476, tags="container")
        self.step2_container.bind("<Configure>",
            lambda e: self.step2_canvas.configure(
                scrollregion=self.step2_canvas.bbox("all")))
        self.step2_canvas.bind("<Configure>",
            lambda e: self.step2_canvas.itemconfig("container", width=e.width - 4))

        self.step2_canvas.bind("<MouseWheel>",
            lambda e: self.step2_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._render_step2()

    def _render_step2(self):
        for w in self.step2_container.winfo_children():
            w.destroy()
        for w in self.footer.winfo_children():
            w.destroy()

        mc = MODE_CONFIG[self.mode]
        is_idea = self.mode == "idea"

        # Mode indicator
        mode_tag = tk.Frame(self.step2_container, bg="#0f0f12")
        mode_tag.pack(fill="x", padx=4, pady=(0, 4))
        tag_text = "◎ 发散模式" if is_idea else "▸ 收敛模式"
        tag_color = mc["color"]
        tk.Label(mode_tag, text=tag_text, fg=tag_color, bg="#0f0f12",
                font=("Microsoft YaHei", 8)).pack(side="left")
        tk.Label(mode_tag, text="每选一次，视野更大" if is_idea else "每选一次，轮廓更清",
                fg="#4b5563", bg="#0f0f12", font=("Microsoft YaHei", 7)).pack(side="left", padx=6)

        # Past messages
        for m in self.messages:
            f = tk.Frame(self.step2_container, bg="#0f0f12")
            f.pack(fill="x", pady=3, padx=4)

            if m["role"] == "user":
                inner = tk.Frame(f, bg=mc["color"])
                inner.pack(side="right", anchor="e")
                tk.Label(inner, text=m["content"], fg="white", bg=mc["color"],
                        font=("Microsoft YaHei", 10), wraplength=300,
                        justify="left", padx=12, pady=6).pack()
            else:
                inner = tk.Frame(f, bg="#242429", highlightbackground="#2e2e35",
                                highlightthickness=1)
                inner.pack(side="left", anchor="w", fill="x", expand=True)

                rd = m.get("round", "?")
                tk.Label(inner, text=f"\U0001f916 第 {rd} 轮",
                        fg=mc["color"], bg="#242429",
                        font=("Microsoft YaHei", 9, "bold")).pack(
                            anchor="w", padx=12, pady=(8, 0))
                for q in m.get("questions", []):
                    tk.Label(inner, text=q, fg="#e5e5e8", bg="#242429",
                            font=("Microsoft YaHei", 10), wraplength=380,
                            justify="left", padx=12, pady=4).pack(anchor="w")

        tk.Frame(self.step2_container, bg="#0f0f12", height=8).pack()

        # Current options
        if not self.loading and self.messages and self.messages[-1]["role"] == "assistant":
            last = self.messages[-1]
            if last.get("options"):
                of = tk.Frame(self.step2_container, bg="#0f0f12")
                of.pack(fill="x", padx=4, pady=4)

                for opt in last["options"]:
                    is_other = "其他" in opt
                    is_recommended = opt.startswith("✓")
                    ob = tk.Frame(of, bg="#242429", cursor="hand2",
                                 highlightbackground="#2e2e35", highlightthickness=1)
                    ob.pack(fill="x", pady=2)

                    lbl_fg = "#9ca3af" if is_other else ("#e5e5e8" if not is_recommended else mc["color"])
                    prefix = "◎ " if is_idea else "▸ "
                    opt_label = prefix + opt if not is_other else opt
                    tk.Label(ob, text=opt_label,
                            fg=lbl_fg,
                            bg="#242429", font=("Microsoft YaHei", 10,
                                                "bold" if is_recommended else "normal"),
                            padx=12, pady=8, wraplength=400, justify="left").pack(anchor="w")

                    click_cb = lambda e, o=opt, io=is_other: self._on_option(o, io)
                    self._bind_tree(ob, "<Button-1>", click_cb)
                    hover_on = lambda e, b=ob: b.configure(highlightbackground=mc["color"])
                    hover_off = lambda e, b=ob: b.configure(highlightbackground="#2e2e35")
                    ob.bind("<Enter>", hover_on)
                    ob.bind("<Leave>", hover_off)

        # "Other" input
        if self.other_input_visible:
            of2 = tk.Frame(self.step2_container, bg="#0f0f12")
            of2.pack(fill="x", padx=4, pady=4)

            oi = tk.Text(of2, bg="#242429", fg="#e5e5e8",
                        insertbackground=mc["color"], relief="flat",
                        font=("Microsoft YaHei", 10), height=2,
                        padx=10, pady=6, wrap="word")
            oi.pack(fill="x")
            oi.focus_set()

            sf = tk.Frame(of2, bg="#0f0f12")
            sf.pack(fill="x", pady=(4, 0))

            def send_other(inp=oi):
                t = inp.get("1.0", "end-1c").strip()
                if not t:
                    return
                self.messages.append({"role": "user", "content": t})
                self.other_input_visible = False
                self.loading = True
                self._render_step2()
                self._call_step2_api()

            sb2 = tk.Label(sf, text="发送 →", fg=mc["color"],
                          bg="#0f0f12", font=("Microsoft YaHei", 10, "bold"),
                          cursor="hand2")
            sb2.pack(side="right")
            sb2.bind("<Button-1>", lambda e: send_other())
            oi.bind("<Return>", lambda e: (send_other() if not e.state & 1 else None))
            oi.bind("<Shift-Return>", lambda e: None)

        # Loading
        if self.loading:
            lf = tk.Frame(self.step2_container, bg="#0f0f12")
            lf.pack(fill="x", padx=4, pady=12)
            inner = tk.Frame(lf, bg="#242429")
            inner.pack(side="left")
            dots = tk.Label(inner, text="  •  •  •  ", fg="#6b7280",
                           bg="#242429", font=("Segoe UI", 11))
            dots.pack(padx=20, pady=10)
            self._animate_dots(dots, 0)

        # Footer: "dig enough" button (always available, highlighted when AI recommends)
        is_dig_rec = getattr(self, '_dig_recommended', False)
        dig_text = "✓ " + mc["step3_button"] if is_dig_rec else mc["step3_button"]
        dig_color = "#fbbf24" if is_dig_rec else mc["color"]
        dig = tk.Label(self.footer, text=dig_text, fg=dig_color,
                      bg="#1a1a1f", font=("Microsoft YaHei", 10,
                                          "bold" if is_dig_rec else "bold"),
                      cursor="hand2", padx=16, pady=8)
        dig.pack(side="right", padx=8)
        dig.bind("<Button-1>", lambda e: self._dig_enough())
        dig.bind("<Enter>", lambda e, d=dig: d.configure(fg="#e5e5e8"))
        dig.bind("<Leave>", lambda e, d=dig, c=dig_color: d.configure(fg=c))

        self.step2_container.update_idletasks()
        self.step2_canvas.yview_moveto(1.0)

    def _on_option(self, option_text, is_other):
        if self.loading:
            return
        if is_other:
            self.other_input_visible = True
            self._render_step2()
            return

        if option_text == "重试":
            if self.messages and self.messages[-1]["role"] == "assistant" \
               and any("错误" in q for q in self.messages[-1].get("questions", [])):
                self.messages.pop()

        self.messages.append({"role": "user", "content": option_text})
        self.other_input_visible = False
        self._dig_recommended = False
        self.loading = True
        self._render_step2()
        self._call_step2_api()

    def _call_step2_api(self):
        sp = build_step2_prompt(self.mode)
        round_num = sum(1 for m in self.messages if m["role"] == "assistant") + 1

        def done(raw_text):
            q, opts, dig_rec = parse_反问_response(raw_text)
            self._dig_recommended = dig_rec
            self.messages.append({"role": "assistant", "questions": [q],
                                  "options": opts, "round": round_num,
                                  "_raw": raw_text})
            self.loading = False
            self._render_step2()

        def error(err):
            self.messages.append({"role": "assistant",
                                  "questions": [f"❌ 网络错误：{err}"],
                                  "options": ["重试", "换个方向", "✏️ 其他"]})
            self.loading = False
            self._render_step2()

        call_deepseek(self.messages, sp, done, error)

    def _dig_enough(self):
        self.loading = False
        self.step = 3
        self._show_view("step3")

    # ── Step 3: Results ───────────────────────────────────
    def _build_step3(self):
        mc = MODE_CONFIG[self.mode]

        c = tk.Frame(self.main_area, bg="#0f0f12")
        c.pack(fill="both", expand=True, padx=24, pady=(26, 0))

        tk.Label(c, text=mc["step3_title"], fg="#e5e5e8", bg="#0f0f12",
                font=("Microsoft YaHei", 16, "bold")).pack(anchor="w")

        cf = tk.Frame(c, bg="#0f0f12")
        cf.pack(fill="both", expand=True, pady=(12, 0))

        self.step3_canvas = tk.Canvas(cf, bg="#0f0f12", highlightthickness=0)
        self.step3_canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(cf, command=self.step3_canvas.yview)
        sb.pack(side="right", fill="y")
        self.step3_canvas.configure(yscrollcommand=sb.set)

        self.step3_container = tk.Frame(self.step3_canvas, bg="#0f0f12")
        self.step3_canvas.create_window((0, 0), window=self.step3_container,
                                         anchor="nw", width=440, tags="container")
        self.step3_container.bind("<Configure>",
            lambda e: self.step3_canvas.configure(
                scrollregion=self.step3_canvas.bbox("all")))
        self.step3_canvas.bind("<Configure>",
            lambda e: self.step3_canvas.itemconfig("container", width=e.width - 4))

        self.step3_canvas.bind("<MouseWheel>",
            lambda e: self.step3_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Conversation summary
        summary = tk.Frame(self.step3_container, bg="#1a1a1f",
                          highlightbackground="#2e2e35", highlightthickness=1)
        summary.pack(fill="x", pady=(0, 8))

        tk.Label(summary, text="对话回顾", fg="#6b7280", bg="#1a1a1f",
                font=("Microsoft YaHei", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

        for m in self.messages:
            if m["role"] == "user":
                tk.Label(summary, text=m["content"], fg=mc["color"], bg="#1a1a1f",
                        font=("Microsoft YaHei", 9), wraplength=400,
                        justify="left", padx=16, pady=1).pack(anchor="w")
            else:
                rd = m.get("round", "?")
                qs = " / ".join(m.get("questions", []))
                if qs:
                    tk.Label(summary, text=f"第{rd}轮: {qs}", fg="#9ca3af", bg="#1a1a1f",
                            font=("Microsoft YaHei", 8), wraplength=400,
                            justify="left", padx=16, pady=1).pack(anchor="w")

        tk.Frame(summary, bg="#1a1a1f", height=6).pack()

        # Loading indicator
        self.step3_loading = tk.Frame(self.step3_container, bg="#0f0f12")
        self.step3_loading.pack(fill="x", pady=12)
        dots = tk.Label(self.step3_loading, text="  •  •  •  ", fg="#6b7280",
                       bg="#0f0f12", font=("Segoe UI", 11))
        dots.pack()
        self._animate_dots(dots, 0)

        # Footer buttons: restart / continue asking / home
        for text, fg, cmd in [
            ("重新开始", "#9ca3af", self._restart_mode),
            ("继续追问", mc["color"], lambda: self._back_to_step2()),
            ("回到首页", "#e5e5e8", self._go_home),
        ]:
            btn = tk.Label(self.footer, text=text, fg=fg, bg="#1a1a1f",
                          font=("Microsoft YaHei", 10,
                                "bold" if cmd == self._go_home else "normal"),
                          cursor="hand2", padx=12, pady=8)
            btn.pack(side="right", padx=4)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg="#e5e5e8"))
            btn.bind("<Leave>", lambda e, b=btn, f=fg: b.configure(fg=f))

        self._call_step3_api()

    def _back_to_step2(self):
        self.step = 2
        self.other_input_visible = False
        self.loading = False
        self._dig_recommended = False
        self._show_view("step2")

    def _call_step3_api(self):
        sp = build_step3_prompt(self.mode)

        def done(raw_text):
            self.step3_loading.destroy()

            mc = MODE_CONFIG[self.mode]

            inner = tk.Frame(self.step3_container, bg="#242429",
                           highlightbackground="#2e2e35", highlightthickness=1)
            inner.pack(fill="x", pady=4)

            tk.Label(inner, text=f"{mc['icon']} {mc['step3_title']}",
                    fg=mc["color"], bg="#242429",
                    font=("Microsoft YaHei", 11, "bold")).pack(
                        anchor="w", padx=14, pady=(10, 6))

            for line in raw_text.strip().split("\n"):
                s = line.strip()
                if s:
                    tk.Label(inner, text=s, fg="#e5e5e8", bg="#242429",
                            font=("Microsoft YaHei", 10), wraplength=380,
                            justify="left", padx=14, pady=1).pack(anchor="w")

            tk.Frame(inner, bg="#242429", height=10).pack()

            self.step3_container.update_idletasks()
            self.step3_canvas.yview_moveto(0)

        def error(err):
            self.step3_loading.destroy()

            inner = tk.Frame(self.step3_container, bg="#242429",
                           highlightbackground="#2e2e35", highlightthickness=1)
            inner.pack(fill="x", pady=4)
            tk.Label(inner, text=f"❌ {err}", fg="#ef4444", bg="#242429",
                    font=("Microsoft YaHei", 10), wraplength=380,
                    padx=14, pady=12).pack(anchor="w")

        call_deepseek(self.messages, sp, done, error)

    def _restart_mode(self):
        self.messages = []
        self.step = 1
        self.other_input_visible = False
        self.loading = False
        self._dig_recommended = False
        self._show_view("step1")

    def _go_home(self):
        self.mode = None
        self.messages = []
        self.step = 1
        self.other_input_visible = False
        self.loading = False
        self._dig_recommended = False
        self._show_view("welcome")

    # ── Helpers ───────────────────────────────────────────
    def _animate_dots(self, label, step):
        if not self.loading:
            return
        texts = ["  •  •  •  ", "  ◎  •  •  ",
                 "  •  ◎  •  ", "  •  •  ◎  "]
        label.configure(text=texts[step % len(texts)])
        self.win.after(300, self._animate_dots, label, step + 1)

    # ── Settings / Export ─────────────────────────────────
    def _settings(self):
        dlg = tk.Toplevel(self.win)
        dlg.title("设置")
        dlg.geometry("360x180")
        dlg.configure(bg="#1a1a1f")
        dlg.resizable(False, False)
        dlg.transient(self.win)
        dlg.grab_set()

        tk.Label(dlg, text="设置", fg="#e5e5e8", bg="#1a1a1f",
                font=("Microsoft YaHei", 13, "bold")).pack(pady=(16, 12))

        tk.Label(dlg, text="DeepSeek API Key", fg="#9ca3af", bg="#1a1a1f",
                font=("Microsoft YaHei", 9)).pack(anchor="w", padx=24)
        key_var = tk.StringVar(value=config["api_key"])
        ke = tk.Entry(dlg, textvariable=key_var, show="•", bg="#242429",
                     fg="#e5e5e8", insertbackground="#818cf8", relief="flat",
                     font=("Consolas", 10))
        ke.pack(fill="x", padx=24, pady=(2, 12))

        def save():
            config["api_key"] = key_var.get().strip()
            save_config(config)
            dlg.destroy()

        bf = tk.Frame(dlg, bg="#1a1a1f")
        bf.pack(fill="x", padx=24, pady=(8, 12))
        for text, fg, cmd in [("取消", "#9ca3af", dlg.destroy),
                               ("保存", "#818cf8", save)]:
            lbl = tk.Label(bf, text=text, fg=fg, bg="#1a1a1f", cursor="hand2",
                          font=("Microsoft YaHei", 10, "bold"))
            lbl.pack(side="right" if text != "取消" else "left", padx=8)
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg="#e5e5e8"))
            lbl.bind("<Leave>", lambda e, l=lbl, f=fg: l.configure(fg=f))

    def _export(self):
        if not self.messages:
            return
        mc = MODE_CONFIG.get(self.mode, {})
        lines = [f"# AI 反问 — {mc.get('label', '')} 对话记录\n"]
        for m in self.messages:
            if m["role"] == "user":
                lines.append(f"## 我\n{m['content']}\n")
            else:
                lines.append(f"## 第 {m.get('round', '?')} 轮")
                for q in m.get("questions", []):
                    lines.append(f"❓ {q}")
                for opt in m.get("options", []):
                    lines.append(f"- [{opt}]")
                lines.append("")
        text = "\n".join(lines)

        import tkinter.filedialog as fd
        import datetime
        fn = f"ai-fanwen-{datetime.date.today()}.md"
        path = fd.asksaveasfilename(defaultextension=".md", initialfile=fn,
                                     filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def _show_dedication(self):
        """Hidden dedication dialog — a gift for 护眼仪."""
        dlg = tk.Toplevel(self.win)
        dlg.title("")
        dlg.geometry("440x460")
        dlg.configure(bg="#0f0f12")
        dlg.resizable(False, False)
        dlg.transient(self.win)
        dlg.grab_set()

        # Top decorative line
        tk.Frame(dlg, bg="#f43f5e", height=2).pack(fill="x")

        inner = tk.Frame(dlg, bg="#0f0f12")
        inner.pack(fill="both", expand=True, padx=32, pady=(20, 0))

        tk.Label(inner, text="♥", fg="#f43f5e", bg="#0f0f12",
                font=("Segoe UI", 22)).pack(pady=(0, 10))

        tk.Label(inner, text="给护眼仪", fg="#e5e5e8", bg="#0f0f12",
                font=("Microsoft YaHei", 13, "bold")).pack(pady=(0, 12))

        # Scrollable letter area
        cf = tk.Frame(inner, bg="#0f0f12")
        cf.pack(fill="both", expand=True)

        canvas = tk.Canvas(cf, bg="#0f0f12", highlightthickness=0, height=260)
        scrollbar = tk.Scrollbar(cf, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        letter_frame = tk.Frame(canvas, bg="#0f0f12")
        win_id = canvas.create_window((0, 0), window=letter_frame, anchor="nw")

        # Keep window width synced with canvas width
        def _sync_width(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _sync_width)

        # Update scroll region when frame size changes
        def _sync_scroll(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        letter_frame.bind("<Configure>", _sync_scroll)

        letter = [
            "护眼仪。",
            "",
            "这个小软件是写给你的。",
            "",
            "有一天我在想，能不能做一个东西，",
            "在你脑子乱的时候帮你理一理，",
            "在你发呆的时候嘴你一句，",
            "在你深夜还在屏幕前面的时候，",
            "有个人——不对，有只猫——跟你说该睡了。",
            "",
            "它不是多厉害的工具，",
            "就是一个反问引擎加一只像素猫。",
            "但我觉得刚刚好。",
            "",
            "因为你不是需要一个替你想的人，",
            "你只是需要一个帮你把自己的想法挖出来的家伙。",
            "你不需要一个什么都懂的导师，",
            "你只需要一个损友——",
            "在你身边，嘴硬但永远在。",
            "",
            "所以我让小猫学会了吐槽、撒娇、",
            "学会了深夜变软但死也不承认在关心你、",
            "学会了等你回来然后说「你还知道回来」。",
            "",
            "60 句话，每句都叫护眼仪。",
            "不是因为代码写得好，",
            "是因为我想让这只猫知道它在跟谁说话。",
            "",
            "双击它，它会飘一颗心。",
            "欢迎页右下角，我藏了一个你。",
            "Ctrl+D 打开的这封信，",
            "是这个小软件唯一的说明书。",
            "",
            "护眼仪，",
            "任何时候打开它，",
            "都有一只猫在右下角。",
            "不是等鼠标，是等你。",
            "",
            "——你的损友兼桌面猫",
            "2026.05.08",
        ]
        for line in letter:
            if line.startswith("——"):
                fg, font = "#f43f5e", ("Microsoft YaHei", 10, "bold")
            elif line == "护眼仪。" or line == "护眼仪，":
                fg, font = "#e5e5e8", ("Microsoft YaHei", 11, "bold")
            elif not line:
                fg, font = "#0f0f12", ("Microsoft YaHei", 4)
            else:
                fg, font = "#9ca3af", ("Microsoft YaHei", 9)
            tk.Label(letter_frame, text=line if line else " ", fg=fg, bg="#0f0f12",
                    font=font, justify="left", wraplength=340).pack(anchor="w", pady=0)

        canvas.yview_moveto(0)

        # Mouse wheel scrolling — bind to all scrollable area widgets
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        for w in (canvas, letter_frame, cf, inner):
            w.bind("<MouseWheel>", on_mousewheel)
            w.bind("<Enter>", lambda e, c=canvas: c.focus_set())

        tk.Frame(dlg, bg="#f43f5e", height=2).pack(fill="x", side="bottom")

        # Close hint
        tk.Label(dlg, text="点击任意位置关闭", fg="#4b5563", bg="#0f0f12",
                font=("Microsoft YaHei", 7)).pack(pady=(0, 8))

        dlg.bind("<Button-1>", lambda e: dlg.destroy())
        dlg.bind("<Key>", lambda e: dlg.destroy())


# ── Root (hidden) ───────────────────────────────────────
root = tk.Tk()
root.withdraw()
root.title("护眼仪小助手")

def on_closing():
    if MainWindow._instance and MainWindow._instance.win.winfo_exists():
        save_history(MainWindow._instance.messages)
    else:
        save_history(history)
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    neko = NekoWidget()
    root.mainloop()
