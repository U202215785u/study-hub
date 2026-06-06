---
name: threejs-cdn-version-trap
description: Three.js CDN 版本兼容性问题——0.150+ 无 UMD 构建，必须用 0.140 或更早
metadata:
  type: reference
---

# Three.js CDN 版本兼容性

Three.js 0.152 开始废弃 `build/three.min.js`（UMD），0.160 完全移除。

使用 CDN 加载 Three.js 时，必须用 **0.140 或更早** 的版本：
- `https://cdn.jsdelivr.net/npm/three@0.140.0/build/three.min.js`
- `https://cdn.jsdelivr.net/npm/three@0.140.0/examples/js/loaders/GLTFLoader.js`

0.150 的 `build/three.min.js` 存在但 `examples/js/loaders/` 已移除。

**Why:** 0.152+ 改为纯 ES module，`build/three.min.js` 不再设置 `window.THREE`。

**How to apply:** 任何需要浏览器全局 `<script>` 加载 Three.js 的场景，锁定 `@0.140.0`。
