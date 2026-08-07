# Round 02 POC · Phase 1A 纯 CSS 背景与实心降级

> 文档角色：证据层 / POC。当前决策以 `../综合报告.md` 为准。
> 独占工作包：W1-C CSS。本文只覆盖 Phase 1A；不实现 motion、粒子、WebGL 或依赖安装。

## 1. 当前范围

Phase 1A 只包含零依赖 `.bg-aurora`、`.bg-noise`、`WorkbenchFrame` 的 `background` slot、首页卡片的渐进增强玻璃样式，以及 reduced-motion / reduced-transparency / 编辑态静止路径。CSS 背景默认静止或超慢漂移；任何粒子或 WebGL 入口属于后续阶段，不应在本文的可粘贴代码中伪装成已实现。

## 2. CSS 背景实现参考

```css
@layer utilities {
  .bg-aurora {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    background: #10140f;
  }

  .bg-aurora__orb {
    position: absolute;
    width: 42%;
    aspect-ratio: 1;
    border-radius: 50%;
    filter: blur(72px);
    opacity: .18;
    animation: bg-aurora-drift 68s ease-in-out infinite alternate;
  }

  .bg-aurora__orb--lime { background: #d7ff63; left: -10%; top: -18%; }
  .bg-aurora__orb--violet { background: #8e7cff; right: -14%; top: 8%; animation-delay: -18s; }
  .bg-aurora__orb--blue { background: #4e9dff; left: 30%; bottom: -28%; animation-delay: -34s; }

  .bg-aurora__ring {
    position: absolute;
    inset: 12% 18%;
    border: 1px solid rgb(215 255 99 / 14%);
    border-radius: 50%;
    opacity: .7;
  }

  .bg-noise {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 .04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    mix-blend-mode: screen;
  }
}

@keyframes bg-aurora-drift {
  from { transform: translate3d(-2%, -1%, 0) scale(1); }
  to { transform: translate3d(2%, 1%, 0) scale(1.06); }
}

@media (prefers-reduced-motion: reduce) {
  .bg-aurora__orb { animation: none; }
}

@media (prefers-reduced-transparency: reduce) {
  .dashboard-module-card {
    background: #1b1d1a;
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}
```

SVG filter 在资源内部控制噪点 alpha。不要再叠加会改变实测对比度的 CSS opacity 层。颜色和 alpha 只是视觉起点，仍必须完成目标机器性能与对比度检查。

## 3. 舞台 slot 与层级

背景必须位于会缩放的舞台内部，不能放在舞台外的 fixed 负层：

```vue
<div class="workbench-frame" data-dashboard-stage>
  <slot name="background" />
  <slot name="navigation" />
  <main class="workbench-frame__main">
    <slot name="greeting" />
    <slot />
  </main>
  <slot name="footer" />
</div>
```

```css
.bento-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.workbench-frame__main { position: relative; z-index: 10; }

.bento-background--static .bg-aurora__orb,
.bento-background--static .bg-aurora__ring,
.bento-background--static .bg-noise {
  animation-play-state: paused;
  will-change: auto;
}
```

slot 没有默认内容，因此现有消费者不传背景时不会增加 DOM。导航、编辑器、抽屉和模态框仍位于背景之上。编辑态必须传入 static 标记，使根节点带上 `bento-background--static`，并通过上面的规则暂停动画；背景始终不能捕获指针输入。

对应的组件结构为：

```vue
<div
  class="bento-background"
  :class="{ 'bento-background--static': static }"
  aria-hidden="true"
>
  <div class="bg-aurora" />
  <div class="bg-noise" />
</div>
```

## 4. 卡片样式与降级顺序

`DashboardModuleCard` 是首页卡片的唯一基础组件，采用渐进增强：

```css
.dashboard-module-card {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  background: #1b1d1a;
  color: #f5f6ee;
  box-shadow: 0 18px 34px -8px rgb(0 0 0 / 22%);
}

@supports (backdrop-filter: blur(1px)) {
  .dashboard-module-card {
    background: rgb(255 255 255 / 6%);
    -webkit-backdrop-filter: blur(24px) saturate(140%);
    backdrop-filter: blur(24px) saturate(140%);
  }
}

@media (prefers-reduced-transparency: reduce) {
  .dashboard-module-card {
    background: #1b1d1a;
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}
```

实测降级顺序为静态背景、`blur(12px)`、实心卡片。不能声称 `blur(24px)` 在所有 Electron 机器上都安全。Storybook 卡片 story 必须将卡片放在真实背景之上；白色 story 画布不能验证玻璃效果。

## 5. 性能与无障碍门禁

- 性能数字必须来自目标机器测量，不是 CSS 保证值。分别记录 Electron 普通静置和编辑拖拽各 5 秒的结果，包括长帧数量。
- 项目门禁目标为 18 个合成层，硬上限为 22。超过上限时，将光斑合并为一个背景层，或把卡片 blur 降至 12px。
- reduced-motion 和 reduced-transparency 是独立终态，必须分别测试。
- 背景元素是装饰内容：使用 `aria-hidden="true"`、`pointer-events: none`，且不包含文本或可聚焦后代。
- Electron 28 / Chromium 120 目前只能标记为静态兼容，直到应用启动并完成目标机器测试。

## 6. 验收证据

1. Storybook 验证 CSS 背景包含三个光斑、噪点 data URI，且没有可聚焦后代。
2. 组件测试验证省略 `background` slot 时不会生成默认背景 DOM，main 层仍位于 slot 之上。
3. reduced-motion 和 reduced-transparency 测试断言终态样式，不断言动画帧。
4. 对未被 Git 跟踪的文件使用 `git diff --no-index --check` 对比空文件，并结合尾随空白扫描和仓库 Markdown 检查；不能把普通 `git diff --check` 的空输出当作完整证据。
5. Phase 1A 示例不导入 motion-v、tsParticles、regl、three 或 TresJS。
