# STUDYHUB-15 热力图与 Codex Taskboard

## 目标与职责

热力图是任务工具的观察层：用每日记录密度帮助用户识别投入节奏、空档和近期变化。它不承担任务创建、状态流转、评论或协作管理。执行层复用现有 Codex Taskboard，并固定到 `study-hub` 项目。

首页工作热力提供“热力图 / 任务版”切换：热力图显示 196 天紧凑概览；任务版仅显示项目识别和进入详情入口。`/heatmap` 是完整工作区，通过 `?view=heatmap|taskboard` 保持刷新后的视图选择。

## 统一数据口径

- 指标固定为 `records`，统计记录数量，而非用户行为审计。
- `ddl_tasks` 按 `updated_at || created_at` 归日。
- `documents` 按 `created_at` 归日。
- `task_queue` 按 `created_at` 归日，只统计 `pending`、`extracting`、`summarizing`、`importing`、`done`；排除 `error`。
- 队列只保留查询终点往前 7 天内按创建时间最新的 200 条，不能使用自动化状态接口的 50 条内存队列。
- 前端以浏览器本地日期显式传 `end_date`，后端按该日期生成区间，避免服务器与浏览器跨时区差一天。

## 后端契约

- `GET /heatmap/catalog`：返回可用样式、reserved 样式和字段级 settings schema。
- `GET /heatmap/preferences`：返回当前样式与设置。
- `PUT /heatmap/preferences`：根据 catalog schema 统一校验和规范化设置。
- `GET /heatmap/data`：返回真实日期 cells、来源拆分、统计摘要和网格元数据。

第一期只有 `grid` 可用。`calendar`、`circular`、`flow` 只返回 `reserved`，不提供 renderer 或假预览。`range_days` 的网格固定为 7 行，90/196/365 天分别使用 13/28/53 列；cells 只包含真实日期，前端根据空槽元数据补齐布局。

`heatmap_preferences` 必须在 `database.py:init_db()` 中位于 DEC-023 的 `if not db_exists` 之外，以 `CREATE TABLE IF NOT EXISTS` 在已有数据库上也幂等创建。

## 设置模型

catalog 是前后端唯一设置契约，字段包含控件类型、选项或范围、步进、默认值与依赖条件。第一期方格支持：显示范围、来源、配色、刻度、形状、间距、圆角、透明度、图例、日期标记和周起始日。

`cell_shape=square` 时后端强制 `cell_radius=0`，前端禁用圆角控件。用户不能取消最后一个数据来源。首页使用已保存的可视偏好，但范围固定为 196 天。

## Taskboard 集成

Taskboard URL 固定为 `http://127.0.0.1:47823/?project=study-hub`，不允许用户输入或更换。由于该服务 API 不支持跨域读取，前端不能用 `fetch` 探测，也不能读取 iframe 内容；详情页仅通过 iframe `load` / `error` 和 8 秒超时判断服务是否可达，并提供重试和新窗口入口。首页紧凑卡不嵌入 iframe。

## 验收与边界

- 首页不再跳转 `/ddl`，而是进入 `/heatmap`。
- 默认打开方格样式；reserved 样式可见但禁用。
- 设置保存后刷新可恢复，恢复默认是未保存草稿，须由用户确认保存。
- 不改 Taskboard 服务的 CORS、API 或业务逻辑。
- 不复制 Taskboard 的议题 CRUD、状态流转、评论和协作功能。
