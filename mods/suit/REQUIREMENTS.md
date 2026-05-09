# 私人减肥教练 — 开发需求文档

## 1. 项目概述

一款轻量化、用户体验优先的私人减肥教练工具。单人使用，规则驱动，帮助执行健身计划和饮食计划。

**核心定位**：私人减肥教练，不是社交工具、不是通用健康 App。

## 2. 技术方案

| 项目 | 选择 |
|------|------|
| 前端框架 | React + TypeScript |
| 构建工具 | Vite |
| UI 样式 | TailwindCSS |
| 后端/BaaS | Supabase（PostgreSQL + 自动 REST API） |
| 部署 | Vercel（前端）/ Supabase 托管 |
| 客户端类型 | PWA（可安装到桌面和手机主屏幕） |
| 移动端导航 | 顶部 Tab + 左右滑动切换（4 个 Tab） |
| 响应式 | 一套代码，适配桌面和移动端 |

## 3. 功能模块

### 3.1 Tab 结构（4 个顶层 Tab）

```
今日  │  健身  │  饮食  │  看板
```

### 3.2 「今日」首页

每天打开看到的第一屏，核心信息聚合：

- **顶部区域**：日期、减肥天数、体重（今日/变化/目标）
- **核心指标**：今日已摄入热量 / 目标热量、运动完成状态、饮水量
- **教练提示**：一句"教练口吻"的每日反馈（基于近期数据生成的文字提示）
- **今日行动清单**：
  - 今日训练计划（可展开，显示动作列表）
  - 今日饮食计划（可展开，显示餐次）
  - 体重记录入口
- **快捷操作**：「开始今天训练」「记录饮食」

**设计重点**：权重仪表盘风格，体重是视觉中心，指标用数字突出，行动入口清晰。

### 3.3 「健身」模块

#### 3.3.1 健身计划管理
- 创建/编辑训练计划模板（名称、目标肌群、周期）
- 每个计划包含多个训练日
- 每个训练日包含多个动作（动作名、组数、次数、重量、休息时间）
- 预设动作库（推胸、划船、深蹲、硬拉等常见动作）

#### 3.3.2 训练执行
- 按当天计划开始训练
- 逐动作记录完成情况（实际组数/次数/重量）
- 训练计时器
- 完成/跳过/替换动作

#### 3.3.3 训练历史
- 按日期查看历史训练记录
- 各动作的历史重量变化趋势

### 3.4 「饮食」模块

#### 3.4.1 饮食计划管理
- 创建/编辑饮食计划模板
- 每天分餐次（早餐/午餐/晚餐/加餐）
- 每餐关联食物，自动计算热量和营养素汇总

#### 3.4.2 饮食记录
- 按餐次记录实际吃的食物
- 从食物库搜索/选择食物
- 记录份量和热量

#### 3.4.3 食物库
- 内置常见食物数据（名称、热量 kcal、蛋白质 g、碳水 g、脂肪 g）
- **支持外部数据导入**（CSV/JSON 格式，接口设计为批量导入做好准备）
- 搜索和筛选食物
- 自定义添加食物

### 3.5 「看板」模块

- **体重趋势图**：折线图展示体重变化，标注目标线
- **热量趋势图**：每日摄入热量 vs 目标热量柱状图
- **运动打卡日历**：类似 GitHub 贡献图的日历热力图
- **周/月/全部**时间范围切换

### 3.6 「设置」模块

- 个人身体数据（性别、出生日期、身高、体重、体脂率、目标体重）
- 目标设定（每周减重速度、每日热量目标、每日蛋白质目标）
- 数据导出

## 4. 数据模型

```sql
-- 用户身体数据（按时间线记录）
user_profile (
  id, user_id, date, weight, height, body_fat_pct,
  created_at
)

-- 健身计划模板
workout_plan (
  id, user_id, name, description, target_muscles,
  cycle_days, is_active, created_at
)

-- 训练日（计划中的一天）
workout_day (
  id, plan_id, day_number, day_name,
  sort_order
)

-- 训练动作
workout_exercise (
  id, day_id, exercise_name, sets, reps,
  weight_kg, rest_seconds, notes, sort_order
)

-- 训练执行记录
workout_log (
  id, user_id, plan_id, day_id, date,
  completed, duration_minutes, notes, created_at
)

-- 每个动作的执行明细
workout_log_detail (
  id, log_id, exercise_name, planned_sets, planned_reps,
  actual_sets, actual_reps, actual_weight_kg, completed, notes
)

-- 饮食计划模板
diet_plan (
  id, user_id, name, description, daily_calorie_target,
  is_active, created_at
)

-- 餐次（计划中的一顿）
diet_meal (
  id, plan_id, meal_type, meal_name,
  sort_order
)

-- 餐次中的食物项
diet_meal_item (
  id, meal_id, food_id, quantity, unit
)

-- 食物库（核心表，支持外部数据导入）
food_item (
  id, name, calories_per_100g, protein_per_100g,
  carbs_per_100g, fat_per_100g, category, source, created_at
)

-- 饮食执行记录
diet_log (
  id, user_id, date, meal_type, food_id,
  quantity, unit, calories, protein, carbs, fat, created_at
)

-- 每日体重记录
weight_log (
  id, user_id, date, weight, note, created_at
)
```

**关键设计说明**：
- `food_item` 独立成表，设计为开放式数据接口，支持后期批量导入外部数据
- 计划表（plan）和执行记录表（log）分离，方便对比计划和实际
- 所有时间序列数据（体重、饮食、训练）按日期记录，支持趋势分析

## 5. 核心计算逻辑（规则驱动）

### 5.1 基础代谢率（BMR）
使用 Mifflin-St Jeor 公式：
- 男性：BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 - 161 + 166
- 女性：BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 - 161

### 5.2 每日总消耗（TDEE）
TDEE = BMR × 活动系数
- 久坐（1.2）/ 轻度活动（1.375）/ 中度活动（1.55）/ 高度活动（1.725）

### 5.3 减脂热量目标
- 每日热量摄入 = TDEE - 500 kcal（约每周减 0.5kg）
- 蛋白质：1.6-2.2g / kg 体重
- 脂肪：总热量的 20-30%
- 碳水：剩余热量

### 5.4 教练提示生成规则
- 体重连续下降 → 鼓励型提示
- 体重连续 3 天不降 → 提醒关注饮食执行
- 训练日未完成 → 温和督促
- 达到阶段性目标 → 庆祝型提示

## 6. Supabase 配置要点

### 6.1 数据库
- 所有上述表结构在 Supabase PostgreSQL 中创建
- 启用 Row Level Security（RLS），策略设置为单用户模式

### 6.2 API
- Supabase 自动生成 RESTful API，前端通过 `@supabase/supabase-js` 调用
- 食物数据导入接口：通过 Supabase 管理后台直接导入 CSV，或在前端做上传页面调 Supabase API 批量插入

### 6.3 认证
- Supabase Auth，使用邮箱 + 密码模式
- 仅需一个用户账号

## 7. 非功能需求

- **PWA**：Service Worker + manifest.json，可离线访问已加载数据，可安装到主屏幕
- **响应式**：移动优先设计，桌面端自适应加宽
- **轻量化**：首屏加载 < 3s，无冗余依赖
- **数据安全**：用户数据仅自己可见（RLS 策略）
- **数据接口规范**：所有 API 调用集中在 service 层，food_item 表设计为可批量导入结构

## 8. 开发顺序建议

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | 项目初始化、Supabase 建表、认证登录 | P0 |
| Phase 2 | 设置页（身体数据录入）、今日首页（体重记录+指标） | P0 |
| Phase 3 | 健身计划 CRUD + 训练执行 + 训练历史 | P0 |
| Phase 4 | 饮食计划 CRUD + 饮食记录 + 食物库 | P0 |
| Phase 5 | 看板（体重趋势图、热量图、运动日历） | P1 |
| Phase 6 | PWA 配置、离线支持、安装优化 | P1 |
| Phase 7 | 食物数据批量导入功能 | P2 |
| Phase 8 | UI 打磨、移动端手势优化、加载状态 | P2 |
