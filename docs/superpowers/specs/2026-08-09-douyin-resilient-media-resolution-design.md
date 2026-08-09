# 抖音韧性媒体解析设计

**状态：** 已确认，待实施

**日期：** 2026-08-09

**关联：** STUDYHUB-22

## 1. 背景与证据

当前 Study-Hub 在 `DouyinProcessor.parse_share_url()` 中从页面
`video.play_addr.url_list[0]` 取地址，并将 `playwm` 字符串替换为 `play`。
这并不保证得到可下载的媒体地址。

用户提供的 `https://v.douyin.com/kKwqfnHP1gY/` 已复现以下结果：

- 短链、作品 ID 和页面 Router 数据均有效，作品 ID 为 `7671127699377749370`。
- 替换后的 `aweme.snssdk.com/.../play/` 请求返回 HTTP 200，但
  `Content-Length` 为 0 且没有响应体。
- 同一页面的 `play_addr.uri` 直接 CDN 地址返回 HTTP 200、2,044,412 字节，
  且首块是可读的 MP4 数据。

现有后端把所有小于 1 KB 的结果都提示为“链接已过期”，因此把播放代理的
空响应误报成媒体过期。

参考项目 TokBrain 的可借鉴部分是：短链仅用于定位作品 ID；通过 F2
PostDetail 获取结构化的媒体候选；下载时逐个验证候选。TokBrain 不对
`playwm` 做字符串替换。它的 F2 详情在没有 Cookie 的环境中也可能返回
HTTP 200 空响应，因此 F2 不能成为无 Cookie 用户的唯一来源。

## 2. 目标

1. 对视频、图文笔记和无可用媒体保持明确分类。
2. 不再把播放代理空响应误报为链接过期。
3. 让解析器产出多个有来源标记的媒体候选，而不是单一未经验证的 URL。
4. 优先利用可选 Cookie 下的 F2 结构化详情，同时保证无 Cookie 时仍可使用
   页面直链回退。
5. 在下载阶段验证实际响应，按候选顺序回退，并以稳定错误码反馈失败原因。
6. 维持现有图文图片下载、视觉理解、ASR 和深度摘要行为。

## 3. 非目标

- 不迁移 TokBrain 的数据库、队列、RAG、前端或完整权限系统。
- 不自动读取浏览器 Cookie，不登录抖音，不规避验证码或风控。
- 不改变用户主动提交少量公开链接的产品入口。
- 第一阶段不把 F2 的下载权限字段设为阻断条件，以免无 Cookie 用户失去现有
  主动解析能力；字段只作为诊断信息保留。严格权限模式另行设计。

## 4. 总体架构

```
分享文本
  -> 输入标准化和短链重定向
  -> 作品 ID
  -> F2 详情适配器（Cookie 可选） -----------+
  -> 页面详情适配器（始终可用的回退） ------+-> 媒体候选集合
                                               -> 受控流式下载器
                                               -> ASR / 关键帧 / 摘要
```

两个详情适配器都只负责发现候选，不负责下载或 ASR。下载器是唯一可以选择、
验证和写入视频临时文件的组件。

## 5. 媒体候选契约

`DouyinProcessor.parse_share_url()` 对视频返回现有字段，并新增
`media_candidates`。`video_url` 和兼容字段 `url` 指向优先候选，供旧调用方
过渡；后端新逻辑必须优先读取 `media_candidates`。

```json
{
  "content_type": "video",
  "video_id": "7671127699377749370",
  "canonical_url": "https://www.iesdouyin.com/share/video/7671127699377749370",
  "media_candidates": [
    {
      "url": "https://v3-web.douyinvod.com/...",
      "source": "f2.video_play_addr",
      "priority": 10,
      "kind": "video"
    },
    {
      "url": "https://sf6-cdn-tos.douyinstatic.com/...",
      "source": "page.play_addr.uri",
      "priority": 20,
      "kind": "video"
    }
  ],
  "resolver_diagnostics": {
    "f2": "available | cookie_required | unavailable | skipped",
    "page": "available | unavailable"
  }
}
```

规则：

- `url` 必须是 HTTPS，且主机通过抖音媒体域名白名单。
- 用完整 URL 去重，保留第一个发现来源和最低优先级值。
- `play_addr.uri` 是页面适配器的首选视频候选。
- `play_addr.url_list` 中的原始地址可以作为低优先级候选。
- 不得对 URL 做 `playwm -> play` 或其他字符串替换。
- 图文笔记继续输出 `image_urls`，不生成视频候选，也不进入 ASR。

## 6. F2 详情适配器

新增独立的 F2 适配器，职责是 `video_id -> F2 PostDetail -> 媒体候选`：

1. F2 运行时固定为经验证版本并隔离安装，启动时报告是否可用。
2. 配置项 `douyin.f2_cookie` 是可选敏感字段，使用现有 Windows DPAPI 安全
   设置存储，接口仅返回“已配置/未配置”。
3. 仅在用户主动提交的解析任务中调用 F2；每个任务最多一次详情请求。
4. 请求使用固定浏览器 UA、`Referer: https://www.douyin.com/`、20 秒超时和
   一次内部尝试；不提取或刷新 Cookie。
5. F2 成功时，从结构化 `video_play_addr` 读取全部媒体候选，并记录可选的
   `allow_download`、音频和字幕信息。
6. `cookie_required`、空响应、结构变化、超时、403、429 或 5xx 不能阻断页面
   适配器；只写入诊断信息。
7. 403、429、验证码/风险页需开启短时冷却，停止同批次后续 F2 请求；冷却期间
   直接使用页面适配器。

## 7. 页面详情适配器

页面适配器保留现有短链和 Router 数据解析能力，但输出候选而不是单 URL：

1. 将短链规范化到作品页并提取作品 ID。
2. 从 `window._ROUTER_DATA` 读取视频或笔记详情。
3. 视频按以下优先级收集候选：`play_addr.uri`、`play_addr.url_list`、可用码率
   分支中的 `play_addr.uri` 与 `url_list`。
4. 图文按既有逻辑收集图片候选，最多保留 9 张。
5. 页面结构缺失返回 `DY-2004` 或 `DY-2005`；不得伪造媒体 URL。

## 8. 受控媒体下载器

后端以候选列表替代 `requests.get(video_url).content`，使用流式读取，避免先把
无效响应完整载入内存。

### 8.1 请求安全

- 只接受 HTTPS，拒绝用户名密码、非 443 端口、私网 IP 和非白名单域名。
- 白名单覆盖 `douyin.com`、`douyinvod.com`、`douyinpic.com`、`byteimg.com`、
  `bytecdn.cn`、`bytedance.com`、`snssdk.com`、`zjcdn.com` 的合法子域。
- 最多跟随 5 次重定向；每次重定向都重新校验 URL 与 DNS。
- 错误消息不得回显带签名的完整 CDN 查询参数。

### 8.2 有效媒体判定

对每个候选依次执行：

1. HTTP 301/302/303/307/308：校验后继续下一跳。
2. HTTP 403：标记 `access_forbidden`；HTTP 429：标记 `rate_limited`，两者均
   触发冷却。
3. HTTP 404/410：标记该候选 `media_expired`，继续下一个候选。
4. HTTP 5xx、连接错误、超时：延迟 15 至 30 秒后只重试一次。
5. 响应 MIME 必须是 `video/*`、`audio/*` 或 `application/octet-stream`；HTML、
   JSON、空 MIME 或其它类型判定为 `unsupported_content_type`。
6. 流式读取首块，至少取得 4 KB；零字节或小于 1 KB 判定为 `empty_media_response`。
7. 对视频候选在前 4 KB 中校验 ISO BMFF/MP4 `ftyp` 标记；不匹配判定为
   `invalid_media_signature`。
8. 检查声明大小和累计大小，不得超过现有下载上限；通过后再写入临时文件。

候选失败时删除临时文件并继续下一个。只有所有候选耗尽才使 ASR 进入失败状态。

## 9. 错误模型与用户文案

| 错误码 | 条件 | 用户提示 |
|---|---|---|
| `PARSER-ASR-2002` | 全部候选 404/410 | 视频媒体地址已失效，请重新提交链接后重试。 |
| `PARSER-ASR-2004` | 200 空响应或首块过小 | 抖音播放地址返回空数据，已尝试其它地址但未成功。 |
| `PARSER-ASR-2005` | HTML、JSON、空 MIME 或错误文件头 | 抖音返回的不是可处理的视频数据。 |
| `PARSER-ASR-2006` | 403、429、验证码/风控 | 抖音暂时限制访问，请稍后重试。 |
| `PARSER-ASR-2007` | F2 失败但页面回退成功 | 不向用户报错；写入诊断日志。 |
| `DY-2005` | 页面和 F2 都没有可处理媒体 | 未发现可处理的视频或图文媒体。 |

`PARSER-ASR-2002` 不得再用于 200 空响应。任务详情保存来源、HTTP 状态、内容类型、
字节数和候选编号，但 UI 仅展示安全的摘要。

## 10. 兼容与迁移

- 解析器先同时返回 `media_candidates` 与旧 `url`/`video_url`，后端切换到候选
  下载器后再逐步减少旧字段依赖。
- 对正在排队或已保存的旧任务，若没有候选列表，则将其原 `video_url` 包装为一个
  `legacy.video_url` 候选，保证可重新执行。
- 配置了旧抖音 Cookie 的用户不自动迁移或复制；F2 Cookie 必须由用户在设置中
  显式保存。
- F2 不可安装、未配置或冷却时，不阻断服务启动和页面解析回退。

## 11. 可观测性

每个解析任务记录：

- `resolver_sources`：F2 和页面的状态。
- `candidate_count`、`selected_candidate_source`、`selected_candidate_index`。
- 每个候选的安全化结果：状态码、内容类型、字节数、失败类别。
- F2 冷却开始与结束时间，以及触发原因。

日志不得记录 Cookie、完整签名 URL、请求头授权字段或响应正文。

## 12. 测试与验收

### 单元测试

- 页面 `play_addr.uri` 优先于 `url_list`，且不会进行 `playwm` 替换。
- F2 成功、Cookie 缺失、空响应、超时、结构变化、403、429 和冷却状态。
- 多个候选的去重、优先级与后备顺序。
- `200 + 0`、首块不足、HTML、空 MIME、非 MP4 文件头、404、410、5xx 重试、
  重定向越界和超大响应。
- 图文笔记继续不进入 ASR，视觉摘要测试保持通过。
- 旧 `video_url` 任务可被包装为兼容候选。

### 集成测试

- 使用 mock 传输复现用户短链对应的“代理 200/0，页面直链 200/有效 MP4”场景，
  断言最终选择直链并完成后续音频提取入口。
- F2 返回候选但第一地址失效、第二地址有效时，断言成功且记录选中来源。
- F2 要求 Cookie 时，断言页面回退仍可解析；页面也失败时才返回聚合错误。

### 发布验收

1. 当前用户短链不再产生“链接已过期，0 字节”的误报。
2. 可用直连候选被下载并进入既有 ASR 流程。
3. F2 未配置 Cookie 时服务仍正常运行。
4. 失败 UI 能区分过期、空响应、非媒体响应与访问受限。
5. 既有图文笔记、视频解析和自动化队列测试全部通过。

## 13. 分阶段交付

**阶段一：候选化与下载校验**

- 删除字符串替换，页面适配器输出候选列表。
- 后端按候选下载并实现准确错误分类。
- 修复本次 0 字节误报。

**阶段二：F2 优先解析**

- 引入隔离 F2 适配器、DPAPI Cookie 设置和冷却机制。
- 合并 F2 与页面候选，提供来源诊断。

**阶段三：可选严格权限模式**

- 基于 F2 的下载权限字段提供“仅字幕/音频/元数据”降级。
- 默认策略与交互文案需要单独评审，避免改变当前用户工作流。
