# 护眼仪小助手 — 项目文档

> 版本 1.0 | 2026-05-08 | 1190 行 Python + 304 行测试 + 295 行 GUI 测试

---

## 目录

1. [架构总览](#1-架构总览)
2. [模块详解](#2-模块详解)
3. [数据流](#3-数据流)
4. [状态机](#4-状态机)
5. [反问算法](#5-反问算法)
6. [System Prompt 设计](#6-system-prompt-设计)
7. [解析器](#7-解析器)
8. [桌面宠物](#8-桌面宠物)
9. [配置与持久化](#9-配置与持久化)
10. [测试体系](#10-测试体系)
11. [已知限制与未来方向](#11-已知限制与未来方向)

---

## 1. 架构总览

```
┌──────────────────────────────────────────────┐
│                  NekoWidget                   │
│         桌面宠物（Toplevel, 96×96）            │
│    原地动画循环（坐→洗→打盹→睡）  │
│        点击 → 惊讶 → 呼出 MainWindow          │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│                 MainWindow                     │
│          主对话窗口（Toplevel, 500×500）         │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │            Progress Bar                   │ │
│  │  ← 返回 | ◎ 步骤1 → ○ 步骤2 → ○ 步骤3  │ │
│  └──────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │              Main Area                    │ │
│  │   welcome / step1 / step2 / step3         │ │
│  │        （动态视图容器，同一时间只有一个）    │ │
│  └──────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │               Footer                      │ │
│  │    按钮区（随步骤变化）                     │ │
│  └──────────────────────────────────────────┘ │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│              DeepSeek API                      │
│     POST /chat/completions                     │
│     model: deepseek-chat, timeout: 30s         │
│     每次请求携带 system prompt + 完整历史        │
└──────────────────────────────────────────────┘
```

**单文件设计** — `ai-fanwen.py` 包含所有逻辑、UI、API 调用。零外部依赖。

---

## 2. 模块详解

### 2.1 全局配置层（行 15-51）

```
APP_DIR    → ~/.ai-fanwen/
CONFIG_PATH → ~/.ai-fanwen/config.json
HISTORY_PATH → ~/.ai-fanwen/history.json
SPRITE_DIR → ./neko_sprites/
```

- `DEFAULT_CONFIG = {"api_key": ""}` — 只保留 API Key，历史遗留的 mode/depth 已清理
- `load_config()` — 读取 + DEFAULT_CONFIG 兜底合并
- `save_config(cfg)` — JSON 写入，UTF-8
- `load_history()` / `save_history(msgs)` — 对话历史持久化

### 2.2 Mode 配置层（行 55-82）

```python
MODE_CONFIG = {
    "idea": {
        "icon": "💡", "label": "想法发散", "color": "#f59e0b",
        "steps": ["起点", "反问", "发散"],
        "step1_placeholder": "输入你的想法起点…",
        "step3_button": "挖够了，进入发散 →",
        ...
    },
    "prompt": {
        "icon": "✨", "label": "提示词优化", "color": "#10b981",
        "steps": ["需求", "反问", "生成"],
        "step3_button": "挖够了，生成提示词 →",
        ...
    },
}
```

每个模式的 UI 文案、颜色、步骤名称全部从这个配置驱动。添加新模式只需加一个字典条目。

### 2.3 System Prompt 层（行 84-207）

两个函数：

- `build_step2_prompt(mode)` — 反问阶段的 system prompt。idea 模式用"跨界策展人"人格，prompt 模式用"精密工程师"人格
- `build_step3_prompt(mode)` — 最终产出阶段的 system prompt。idea 产出方向列表，prompt 产出结构化提示词

**Step 2 提示词关键差异：**

| | Idea（1037 chars） | Prompt（1114 chars） |
|---|---|---|
| 人格 | 跨界策展人 | 精密工程师 |
| 方向 | 撕开→跨界→减法暴击 | 锁定→场景化→反例校准 |
| 选项前缀 | ◎（空心圆） | ▸（箭头） |
| 模式标签 | "每选一次，视野更大" | "每选一次，轮廓更清" |

### 2.4 DeepSeek API 层（行 209-237）

```python
def call_deepseek(messages, system_prompt, on_done, on_error):
```

- **输入转换**：内部 messages（含 `questions`/`options` 字段）→ API 格式（全部展开为 content 文本）
- **异步执行**：`threading.Thread` 后台调用，`root.after(0, ...)` 回到主线程回调
- **超时**：30 秒（`urllib.request.urlopen(req, timeout=30)`）
- **错误处理**：尝试从 DeepSeek 错误响应中提取具体错误信息

### 2.5 解析器（行 239-321）

```python
def parse_反问_response(text):
    return question, options, dig_recommended
```

解析 AI 的选项式回复，支持多种格式（见[第 7 节](#7-解析器)）。

### 2.6 NekoWidget（行 324-457）

桌面宠物组件，详见[第 8 节](#8-桌面宠物)。

### 2.7 MainWindow（行 459-1140）

主窗口组件，包含：
- 视图管理（`_show_view`）
- 四种视图构建（welcome / step1 / step2 / step3）
- 步骤导航（`_go_back` / `_jump_to_step` / `_back_to_step2`）
- API 调用管理
- 选项点击处理与状态流转
- 进度条更新
- 设置对话框 / 导出功能

---

## 3. 数据流

### 3.1 完整对话生命周期

```
用户输入起点
  │
  ▼
Step 1 → messages = [{"role": "user", "content": "..."}]
  │
  ▼
Step 1 点击"下一步"
  │ call_deepseek(messages, step2_prompt, done, error)
  ▼
Step 2 ← messages 追加 {"role": "assistant", "questions": [...], "options": [...]}
  │
  │ 用户点击选项
  │   → messages 追加 {"role": "user", "content": "选中的选项"}
  │   → call_deepseek(完整 messages, step2_prompt, done, error)
  │   → messages 追加新的 assistant 消息
  │   → 循环…
  │
  │ 用户点击"挖够了"
  ▼
Step 3 → call_deepseek(完整 messages, step3_prompt, done, error)
  │
  ▼
最终产出展示
```

### 3.2 Messages 内部结构

```python
# User message
{"role": "user", "content": "我想做一个笔记工具"}

# Assistant message (Step 2 反问)
{
    "role": "assistant",
    "questions": ["偏向哪种类型？"],
    "options": ["轻量便签", "知识管理", "结构化", "✏️ 其他"],
    "round": 1,
    "_raw": "❓ 偏向哪种类型？\n- [轻量便签]\n- [知识管理]\n..."
}

# User message (点击选项)
{"role": "user", "content": "轻量便签"}
```

### 3.3 API 请求格式

```json
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "<system prompt>"},
    {"role": "user", "content": "我想做一个笔记工具"},
    {"role": "assistant", "content": "❓ 偏向哪种类型？\n- [轻量便签]\n- [知识管理]\n- [✏️ 其他]"},
    {"role": "user", "content": "轻量便签"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

注意：内部 messages 中的 `questions`/`options` 在发送前被展开为纯文本 `❓ q\n- [opt]\n...`

---

## 4. 状态机

### 4.1 核心状态变量

```python
self.mode       = None          # "idea" | "prompt" | None
self.step       = 1             # 1 | 2 | 3
self.messages   = []            # 对话历史
self.loading    = False         # API 调用进行中
self.other_input_visible = False  # "其他"输入框可见
self._dig_recommended  = False  # AI 建议收尾
self.current_view = "welcome"   # "welcome" | "step1" | "step2" | "step3"
```

### 4.2 视图转换图

```
        welcome ──────────────┐
          │                   │
    _enter_mode()       ← 返回（step=1）
          │                   │
          ▼                   │
        step1 ────────────────┘
          │
    _step1_next()
          │
          ▼
        step2 ←── _back_to_step2()
          │
    _dig_enough()
          │
          ▼
        step3
          │
    _restart_mode() → step1
    _go_home()      → welcome
```

### 4.3 加载状态处理

```
loading=True 期间：
  ✅ "挖够了"按钮始终可用（强制 reset loading → go step3）
  ✅ 错误回调提供 ["重试", "换个方向", "✏️ 其他"] 兜底选项
  ✅ "重试"点击后自动移除失败的 assistant 消息再重试
  ❌ 选项按钮不可点击（防重复提交）
  ❌ "其他"输入不可用
```

---

## 5. 反问算法

### 5.1 当前实现：纯 LLM 驱动

没有状态机、没有预设决策树。每轮 API 调用携带完整对话历史 + system prompt，DeepSeek 自主决定问什么。

### 5.2 两大改进（本次迭代）

**A. 举例陷阱防护：**
- 问题：用户说"比如记账"，AI 把例子当成了新目标
- 修复：System prompt 明确要求把"比如"翻译回偏好维度，禁止把例子当需求

**B. 混合终止模式：**
- AI 判断时机成熟时，在回复中附加 `~~建议收尾~~`
- 解析器检测信号，UI 按钮变金色 + `✓` 前缀
- 用户决定是继续还是收尾

### 5.3 未来方向：战略/执行分离

当前 LLM 同时承担"决定问什么维度"和"措辞怎么写"两项职责。
考虑未来将"维度选择"抽到本地 Python 状态机，LLM 只负责措辞。
详见设计文档中的讨论。

---

## 6. System Prompt 设计

### 6.1 设计原则

1. **AI 有立场** — 它不是中立提问机，它带着经验预判回答中隐含的坑
2. **选项有取舍** — 每个选项代表一个明确方向 + 一句话说明利弊
3. **推荐有理由** — 用 ✓ 标注推荐项，不只是标记，而是带判断
4. **问题像导师** — 不是"你想要 X 还是 Y"，是"我见过选 X 的人后来都遇到了 Z"

### 6.2 收尾信号规范

```
格式：在问题末尾附加 ` ~~建议收尾~~`
示例：❓ 你已经有了三条明确的产品边界，方向很清晰了 ~~建议收尾~~
解析：检测 "建议收尾" → dig_recommended = True → UI 高亮按钮
剥离：问题文本中的 ~~建议收尾~~ 不显示给用户
```

### 6.3 输出格式约定

```
❓ 问题文本
- [选项一文本]
- [选项二文本]
- [✏️ 其他]

约束：
- 选项必须用 - [文本] 格式，方括号不能省略
- 最后一行固定为 - [✏️ 其他]
- 不要输出格式之外的任何内容
```

---

## 7. 解析器

### 7.1 设计目标

AI 不会严格遵循格式要求。解析器需要防御性地处理各种变体。

### 7.2 支持的格式

| 格式 | 示例 | 解析方式 |
|------|------|---------|
| 标准括号 | `- [轻量便签]` | `line[start:end]` |
| 无括号 | `- 轻量便签` | `clean_opt(line)` 剥离前缀 |
| 编号列表 | `1. 轻量便签` | 检测数字前缀 |
| 圆点 | `• 轻量便签` | 检测 `• ` 前缀 |
| ❓ 带括号问题 | `❓ [问题]` | `clean_opt()` 剥离括号 |
| ❓ 无括号问题 | `❓ 问题` | 直接截取 |
| 无 ❓ | `问题\n- [A]` | 取第一个非选项行 |
| 收尾信号 | `~~建议收尾~~` | 全文搜索，剥离 |

### 7.3 clean_opt 函数

```python
def clean_opt(s):
    s = s.strip()
    while s and s[0] in '[*•#_~`-':    # 剥离前缀标记
        s = s[1:].strip()
    while s and s[-1] in ']*•#_~`-':   # 剥离后缀标记
        s = s[:-1].strip()
    if s.endswith('：') or s.endswith(':'):
        s = s[:-1].strip()
    return s
```

### 7.4 兜底策略

```
无 question → "继续深入"
options < 2 → ["继续深入", "换个方向"]
无 "其他"    → options.append("✏️ 其他")
```

---

## 8. 桌面宠物

### 8.1 精灵映射

经典 Neko 32 帧公共领域图（32×32px → 96×96px, 3x 缩放）：

| 索引 | 动作 |
|------|------|
| 24 | 坐 |
| 25-26 | 洗脸（2 帧交替） |
| 27 | 打盹前 |
| 28-29 | 睡觉（2 帧交替） |
| 31 | 惊讶 |

### 8.2 动画状态机

```
idle 循环：
  timer 0-30   → sit（坐）
  timer 30-80  → wash（洗脸，两帧交替）
  timer 80-120 → presleep（打盹前）
  timer 120-300 → sleep（睡觉，两帧交替）
  timer 300+   → reset to 0

点击：
  state → surprised（惊讶）
  0.5s 后 → 恢复 idle

拖动：
  Button-1 + 移动 → 更新位置
  释放 → 如果不是拖动 → 触发点击
```

### 8.3 透明实现

```python
self.win.configure(bg="#ff00ff")
self.win.wm_attributes("-transparentcolor", "#ff00ff")
```

洋红色 `#ff00ff` 作为透明遮罩色，猫的白色身体不受影响。

---

## 9. 配置与持久化

### 9.1 文件布局

```
~/.ai-fanwen/
  ├── config.json    # API Key
  └── history.json   # 最后一次对话历史
```

### 9.2 自动保存时机

- 窗口关闭（`WM_DELETE_WINDOW` → `_hide` → `save_history`）
- 进程退出（`root.protocol("WM_DELETE_WINDOW", on_closing)`）

### 9.3 导出格式

Markdown 格式，包含模式名称、对话轮次、问题列表和选项列表。

---

## 10. 测试体系

### 10.1 测试架构

| 文件 | 测试数 | 范围 |
|------|--------|------|
| `test_app.py` | 8 组 | 配置、MODE_CONFIG、System Prompts、解析器、API 签名、消息格式化、状态转换、历史持久化 |
| `test_gui.py` | 9 组 | 欢迎页、Step 1-3 视图、选项点击、其他输入、导航、重启/首页、设置对话框 |

### 10.2 运行

```bash
python test_app.py   # 无 GUI，纯逻辑验证
python test_gui.py   # 需要显示器，Tk 交互验证
```

### 10.3 模块导入方式

因为文件名包含连字符（`ai-fanwen.py`），使用 `importlib.util.spec_from_file_location` 导入，且入口代码有 `if __name__ == "__main__":` 守卫。

---

## 11. 已知限制与未来方向

### 11.1 当前限制

- **单 API 提供商** — 仅支持 DeepSeek Chat
- **无流式输出** — API 响应一次性返回，无打字动画
- **单线程 UI** — 复杂渲染时可能有 UI 卡顿
- **无国际化** — 仅简体中文
- **tkinter 风格限制** — 无法使用现代 CSS 动画/圆角/阴影

### 11.2 未来方向

- **战略层抽离** — 维度状态机本地化，LLM 只负责措辞
- **多模型支持** — Claude / GPT / 本地模型
- **流式输出** — Step 3 结果逐字显示
- **对话可编辑** — 允许用户修改历史回答后重新生成
- **模板库** — 常见场景的预设起点

---

## 附录 A：文件清单

```
brainstorm/
├── ai-fanwen.py              # 主程序（1190 行）
├── start.bat                 # Windows 启动脚本
├── test_app.py               # 逻辑测试（304 行）
├── test_gui.py               # GUI 测试（295 行）
├── README.md                 # 用户文档
├── .gitignore
├── neko_sprites/             # 32 个 GIF 精灵图
│   ├── 1.gif ... 32.gif
└── docs/
    ├── PROJECT.md            # 本文档
    └── superpowers/
        └── specs/
            └── 2026-05-07-ai-fanwen-redesign-design.md
```
