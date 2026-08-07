# Rendering Research · Round 02 索引

> 文档角色：导航层。本文只记录输入、产物、工作包状态和指向；当前决策以 [`../综合报告.md`](../综合报告.md) 为准。

## 产物

| 文件 | 角色 | 工作包 | 当前状态 |
|---|---|---|---|
| `01-motion-v-integration.md` | Motion 集成证据与契约参考 | W1-A | POC，需批准依赖后实施 |
| `02-tresjs-lazy-fallback.md` | WebGL 懒加载、降级、生命周期参考 | W1-B | POC，Phase 3 默认后置 |
| `03-css-background-impl.md` | Phase 1A CSS 背景与实心降级参考 | W1-C | POC，可独立实施但仍需按综合报告放行 |
| `README.md` | 本轮导航和状态索引 | W2-B | 导航层 |

## 输入与输出

- 输入：Round 01 七份文档和项目现状；详细来源保留在各 POC 的验证级别表中。
- 输出：三份不互相覆盖文件的 POC，供 Wave 2 汇总，不直接改变业务代码。
- 后续：W2-A 更新综合报告，W2-B 只维护两个 README，Wave 3 独立审查所有目标文档。

## 统一口径

1. Phase 1A 是零依赖 CSS 视觉底座。
2. Phase 1B 只有在批准 motion-v 构建增量后才进入。
3. Phase 2 是交互反馈和转场，必须在 Phase 1B 验收后按需增加。
4. Phase 3 WebGL 默认不实施；需要时必须具备能力探测、加载失败、context lost、reduced-motion 四条降级路径。
5. “静态兼容”“构建实测”“Electron 实机通过”是三种不同状态，不能互换。

## 交接

每个工作包的任务、已知、定位、范围、验收和回传格式在综合报告附录维护。此处不复制任务卡，避免索引文件重新产生决策分歧。
