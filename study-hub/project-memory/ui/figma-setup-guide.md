# Study Hub — Figma 设计系统搭建清单

> 由 HTML 原型自动解析生成，供设计师在 Figma 中快速建立 Variables 和 Components

---

## 一、颜色变量（Figma Local Variables → Colors）

| Figma 变量名 | CSS Token | 当前值 | 建议用途 |
|---|---|---|---|
| `color/--app-bg` | `--app-bg` | `#090a08` | - |
| `color/--app-shell` | `--app-shell` | `#121311` | - |
| `color/--surface-1` | `--surface-1` | `#1b1d1a` | - |
| `color/--surface-2` | `--surface-2` | `#242722` | - |
| `color/--surface-3` | `--surface-3` | `#30342d` | - |
| `color/--text-strong` | `--text-strong` | `#f5f6ee` | - |
| `color/--text` | `--text` | `#d9dbd0` | - |
| `color/--text-muted` | `--text-muted` | `#8f948a` | - |
| `color/--line` | `--line` | `rgba(245, 246, 238, 0.10)` | - |
| `color/--line-strong` | `--line-strong` | `rgba(211, 255, 93, 0.38)` | - |
| `color/--accent` | `--accent` | `#d7ff63` | - |
| `color/--accent-2` | `--accent-2` | `#8b73ff` | - |
| `color/--accent-3` | `--accent-3` | `#ff8655` | - |
| `color/--success` | `--success` | `#59f86d` | - |
| `color/--warn` | `--warn` | `#f4e35c` | - |
| `color/--danger` | `--danger` | `#ff6b6b` | - |
| `color/--shadow-card` | `--shadow-card` | `0 18px 50px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.04)` | - |


---

## 二、尺寸/间距变量（Figma Local Variables → Numbers）

| Figma 变量名 | CSS Token | 当前值 |
|---|---|---|
| `spacing/--radius-card` | `--radius-card` | `28px` |
| `spacing/--radius-control` | `--radius-control` | `999px` |


---

## 三、圆角变量（Figma Local Variables → Numbers）

| Figma 变量名 | CSS Token | 当前值 |
|---|---|---|


---

## 四、阴影效果（Figma Effect Styles）

| Figma Style 名 | CSS Token | 当前值 |
|---|---|---|


---

## 五、字体尺寸汇总（Figma Text Styles）

HTML 中使用的所有 font-size：

| 尺寸 | 建议 Text Style 名 |
|---|---|
| `10px` | - |
| `11px` | - |
| `12px` | - |
| `13px` | - |
| `13px !important` | - |
| `14px` | - |
| `15px` | - |
| `15px !important` | - |
| `16px` | - |
| `18px` | - |
| `20px` | - |
| `24px` | - |
| `28px` | - |
| `28px !important` | - |
| `32px` | - |
| `9px` | - |


---

## 六、内边距汇总（用于组件规范）

HTML 中使用的所有 padding：

| Padding 值 | 出现场景 |
|---|---|
| `0` | - |
| `0 12px` | - |
| `0 18px` | - |
| `0 18px !important` | - |
| `0 24px` | - |
| `0 2px` | - |
| `10px` | - |
| `10px 0` | - |
| `10px 12px` | - |
| `10px 14px` | - |
| `10px 20px` | - |
| `10px 24px` | - |
| `10px 4px 4px` | - |
| `12px` | - |
| `12px !important` | - |
| `12px 0` | - |
| `12px 16px` | - |
| `12px 20px` | - |
| `14px` | - |
| `14px 16px` | - |
| `14px 20px` | - |
| `16px` | - |
| `18px` | - |
| `18px !important` | - |
| `1px 4px` | - |
| `20px` | - |
| `20px 22px 22px` | - |
| `20px 22px 22px !important` | - |
| `20px 24px` | - |
| `24px` | - |
| `2px 8px` | - |
| `2px 8px !important` | - |
| `32px` | - |
| `3px 10px` | - |
| `4px` | - |
| `4px 10px` | - |
| `4px 6px` | - |
| `6px 0` | - |
| `6px 12px` | - |
| `6px 14px` | - |
| `6px 16px` | - |
| `8px` | - |
| `8px 0` | - |
| `8px 10px` | - |
| `8px 14px` | - |
| `8px 14px !important` | - |
| `8px 16px` | - |
| `9px 0` | - |
| `9px 14px` | - |
| `9px 14px !important` | - |


---

## 七、圆角值汇总

HTML 中使用的所有 border-radius：

| 圆角值 | 出现场景 |
|---|---|
| `10px` | - |
| `12px` | - |
| `15px` | - |
| `15px !important` | - |
| `16px` | - |
| `18px` | - |
| `18px !important` | - |
| `20px` | - |
| `26px` | - |
| `26px !important` | - |
| `28px` | - |
| `28px !important` | - |
| `2px` | - |
| `34px` | - |
| `3px` | - |
| `4px` | - |
| `50%` | - |
| `50% !important` | - |
| `6px` | - |
| `8px` | - |
| `8px !important` | - |
| `999px` | - |
| `999px !important` | - |
| `var(--radius-card)` | - |
| `var(--radius-card) !important` | - |
| `var(--radius-control)` | - |
| `var(--radius-control) !important` | - |


---

## 八、核心组件规格（直接用于 Figma Components）

### Navigation (`.top-nav-bar`)

| 属性 | 值 |
|---|---|
| `height` | `72px` |
| `padding` | `0 18px` |
| `margin` | `18px 22px 0` |
| `border-radius` | `26px` |
| `background` | `rgba(18, 19, 17, 0.88)` |
| `border` | `1px solid var(--line)` |
| `box-shadow` | `var(--shadow-card)` |

### Logo (`.nav-logo-icon`)

| 属性 | 值 |
|---|---|
| `width` | `38px` |
| `height` | `38px` |
| `border-radius` | `15px` |
| `background` | `var(--accent)` |
| `color` | `#14170f` |
| `font-weight` | `800` |
| `box-shadow` | `0 0 0 7px rgba(215,255,99,0.10)` |

### Nav Link (`.nav-link`)

| 属性 | 值 |
|---|---|
| `padding` | `9px 14px` |
| `border-radius` | `var(--radius-control)` |
| `color` | `var(--text-muted)` |
| `border` | `1px solid transparent` |

### Search Input (`.nav-search`)

| 属性 | 值 |
|---|---|
| `width` | `268px` |
| `height` | `42px` |
| `border-radius` | `var(--radius-control)` |
| `background` | `rgba(255,255,255,0.07)` |
| `color` | `var(--text-muted)` |
| `border` | `1px solid var(--line)` |

### Action Button (`.nav-action-btn`)

| 属性 | 值 |
|---|---|
| `width` | `36px` |
| `height` | `36px` |
| `border-radius` | `8px` |
| `background` | `#2a2a2a` |
| `color` | `#aaa` |
| `font-size` | `14px` |
| `border` | `none` |

### Avatar (`.nav-avatar`)

| 属性 | 值 |
|---|---|
| `width` | `42px` |
| `height` | `42px` |
| `border-radius` | `50%` |
| `background` | `var(--surface-2)` |
| `color` | `var(--text)` |
| `border` | `1px solid var(--line)` |

### Grid Card (`.grid-card`)

| 属性 | 值 |
|---|---|
| `padding` | `18px` |

### Sidebar (`.sidebar`)

| 属性 | 值 |
|---|---|
| `padding` | `16px` |
| `border-radius` | `12px` |
| `background` | `#fff` |
| `border` | `2px solid #ddd` |

### Main Panel (`.main-panel`)

| 属性 | 值 |
|---|---|
| `padding` | `24px` |
| `border-radius` | `12px` |
| `background` | `#fff` |
| `border` | `2px solid #ddd` |

### Dock Panel (`.dock-panel`)

| 属性 | 值 |
|---|---|
| `padding` | `16px` |
| `border-radius` | `12px` |
| `background` | `#fff` |
| `border` | `2px solid #ddd` |

### Skill Card (`.skill-card`)

| 属性 | 值 |
|---|---|
| `padding` | `20px` |
| `border-radius` | `12px` |
| `background` | `#fff` |
| `border` | `2px solid #ddd` |

### Dropdown (`.dropdown-menu`)

| 属性 | 值 |
|---|---|
| `border-radius` | `var(--radius-card)` |
| `background` | `radial-gradient(circle at 0% 0%, rgba(255,255,255,0.055), transparent 34%),
                linear-gradient(145deg, var(--surface-2), var(--surface-1))` |
| `color` | `var(--text)` |
| `border` | `1px solid var(--line)` |
| `box-shadow` | `var(--shadow-card)` |



---

## 九、页面清单

页面 ID 需手动检查 HTML 中的 `.page` 元素


---

*生成时间：自动解析*
*源文件：study-hub-dashboard-style-refresh.html*
