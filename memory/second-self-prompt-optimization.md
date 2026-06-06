---
name: second-self-prompt-optimization
description: Second Self 回复质量优化经验
date: 2026-06-06
metadata:
  type: experience
  project: second-self
  component: agent_loop.py
---

# Second Self 回复质量优化

## 问题

用户反馈 Second Self 回复：
1. Markdown 没渲染（`**粗体**` 显示为纯文本）
2. 回复太长太啰嗦（"明天吃啥" 给了几百字 A/B/C 分析）
3. 不像人类（过度结构化，像客服）

## 修复

### 1. Markdown 渲染

**错误顺序：**
```js
simpleMarkdown(esc(resultText))
```

`esc()` 会把 `**` 转义成 `&#42;&#42;`，导致 Markdown 正则匹配失败。

**正确顺序：**
```js
function simpleMarkdown(text) {
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return safe
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}
```

先 escape HTML 防 XSS，再 parse Markdown。

### 2. 回复长度控制

根据 Self Engine 决策优先级动态约束：

| 优先级 | 长度 | 风格 |
|--------|------|------|
| HIGH | 80-150字 | 分析+建议，可以展开 |
| MEDIUM | 40-80字 | 直接给结论，不要铺垫 |
| LOW | 20-40字 | 一句话或一个玩笑 |

在 System Prompt 中明确写入：
```
## 回复策略（本次严格遵循）
**长度：20-40字，一句话或一个玩笑**
```

### 3. 语气优化

明确禁止：
- "首先/其次/最后"
- "综上所述""总之"
- A/B/C 三层分析（除非用户要求）
- 每句话都加 emoji
- 重复用户的问题

明确允许：
- "行啊""得了吧""别想了"
- 低优先级：开玩笑、怼他

### 4. 效果

"明天吃啥" → LOW → **"这有什么好纠结的，食堂走起。"**（14字）

## 相关文件

- `study-hub/second-self/agent_loop.py` — System Prompt 构建
- `study-hub/second-self/app/index.html` — 前端渲染
- `study-hub/frontend/public/second-self/index.html` — 前端渲染（生产版本）
