# Content Parser Markdown Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render content-parser documents through the existing MarkdownReader surface instead of showing their source Markdown.

**Architecture:** Keep the document modal and its ASR failure notice in `ContentParser.vue`. Replace only the raw-content node with the existing `MarkdownRenderer`, which owns marked GFM parsing and reading controls.

**Tech Stack:** Vue 3, Vitest, @vue/test-utils, marked.

---

### Task 1: Content Parser Markdown Reader

**Files:**
- Create: `study-hub/frontend/src/views/ContentParser.markdown.test.js`
- Modify: `study-hub/frontend/src/views/ContentParser.vue`

- [x] **Step 1: Write the failing view test**

```js
expect(wrapper.get('.markdown-content').html()).toContain('<h1>Markdown heading</h1>')
expect(wrapper.get('.markdown-content').html()).toContain('<table>')
expect(wrapper.find('pre').exists()).toBe(false)
```

- [x] **Step 2: Run the focused test and confirm it fails because `.markdown-content` is absent**

Run: `npm run test:unit -- src/views/ContentParser.markdown.test.js`

- [x] **Step 3: Reuse the shared reader**

```vue
<MarkdownRenderer :content="document.content" />
```

```js
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
```

- [x] **Step 4: Run the focused test and confirm it passes**

Run: `npm run test:unit -- src/views/ContentParser.markdown.test.js`

- [x] **Step 5: Run the parser view tests and the frontend production build**

Run: `npm run test:unit -- src/views/ContentParser.test.js src/views/ContentParser.markdown.test.js`

Run: `npm run build`
