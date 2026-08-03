# Dashboard Card Refinement Preview V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a second in-conversation homepage preview that stays visually faithful to Figma node `349:96` while correcting the internal hierarchy and alignment of six supporting cards.

**Architecture:** Create one new self-contained HTML fragment in the existing thread visualization directory. Keep the 1440×980 Figma canvas as the single layout coordinate system, scale the entire stage uniformly into selectable preview ratios, and use one shared 16px card inset with module-specific internal layouts.

**Tech Stack:** HTML fragment, scoped CSS, vanilla JavaScript, Codex visualization renderer, Figma design context.

---

### Task 1: Create the faithful V2 preview shell

**Files:**
- Create: `C:/Users/Administrator/.codex/visualizations/2026/08/02/019fc2f7-a155-7860-ad05-d991071afd4b/study-hub-dashboard-card-refinement-v2.html`
- Reference: `C:/Users/Administrator/.codex/visualizations/2026/08/02/019fc2f7-a155-7860-ad05-d991071afd4b/study-hub-fit-dashboard.html`
- Reference: `study-hub/docs/superpowers/specs/2026-08-03-dashboard-card-refinement-design.md`

- [ ] **Step 1: Add a new fragment root and preview controls**

Create a unique root named `study-hub-card-refinement-v2`. Add three ratio buttons (`16:9`, `超宽屏`, `4:3`) and one `显示网格` checkbox. Keep these controls outside the depicted product surface.

- [ ] **Step 2: Rebuild the 1440×980 page shell from Figma node `349:96`**

Use a fixed 1440×980 stage with the Figma navigation, greeting, clock, 8×4 grid, footer, dark surfaces, `#d7ff63` primary accent, 22px card radius, and 14px grid gap. Fit the stage with one scale value:

```javascript
const fitStage = () => {
  const scale = Math.min(viewport.clientWidth / 1440, viewport.clientHeight / 980)
  stage.style.setProperty('--studyhub-v2-scale', String(scale))
}
```

- [ ] **Step 3: Preserve the current module placement**

Use the confirmed placements: heatmap `4×2`, calendar `2×2`, today focus `2×3`, queue `2×2`, knowledge `2×1`, creation `2×2`, memory `1×1`, commands `1×1`, and workflow `2×1`. Do not use dense auto-placement inside the preview.

- [ ] **Step 4: Read the fragment back and check its basic contract**

Run:

```powershell
Get-Content -Raw -Encoding UTF8 'C:\Users\Administrator\.codex\visualizations\2026\08\02\019fc2f7-a155-7860-ad05-d991071afd4b\study-hub-dashboard-card-refinement-v2.html'
```

Expected: a literal HTML fragment with no `<!doctype>`, `<html>`, `<head>`, or `<body>` tags; no escaped `\"` markup; and one root with the exact ID `study-hub-card-refinement-v2`.

### Task 2: Refine the six supporting cards

**Files:**
- Modify: `C:/Users/Administrator/.codex/visualizations/2026/08/02/019fc2f7-a155-7860-ad05-d991071afd4b/study-hub-dashboard-card-refinement-v2.html`

- [ ] **Step 1: Apply the shared card inset**

Give every dashboard module `box-sizing: border-box` and `padding: 16px`. Do not add compact-mode media or container queries that change this inset.

- [ ] **Step 2: Rebuild the automation queue as normal flow**

Keep the Figma sequence of three queue rows, `查看队列`, link input, and `开始解析`. Use a grid with three equal rows followed by the secondary action and bottom action group. Align each task title, status, and progress bar without absolute percentages.

- [ ] **Step 3: Normalize the knowledge list**

Keep the title and two rows. Give both rows equal height and reserve the same action lane. Show `复制` on both rows; expose `删除` only when the first row is hovered or keyboard-focused so the resting layout stays balanced.

- [ ] **Step 4: Recenter the memory and command cards**

Keep the memory cover, `Memories`, and `今日手账` as one vertically centered group. Keep the quick-command title above two equal-height dashed buttons. Both cards retain the same 16px inset as larger cards.

- [ ] **Step 5: Tighten creation and workflow rhythm**

Keep creation's title, two tabs, two knowledge rows, and three thumbnails per row. Group each row with its thumbnails and align both groups to one left baseline. Keep workflow's title, three steps, arrows, and input field; change only baseline and vertical centering.

- [ ] **Step 6: Preserve the primary modules**

Do not redesign heatmap, calendar, or today focus. Only align their outer inset to the shared 16px rule and retain their Figma-derived visual hierarchy.

### Task 3: Verify layout and interactions

**Files:**
- Verify: `C:/Users/Administrator/.codex/visualizations/2026/08/02/019fc2f7-a155-7860-ad05-d991071afd4b/study-hub-dashboard-card-refinement-v2.html`

- [ ] **Step 1: Validate structure and JavaScript identifiers**

Search for the root, viewport, stage, grid toggle, ratio controls, and every element queried by JavaScript. Expected: each selector exists exactly once and no identifier is referenced before definition.

- [ ] **Step 2: Render the fragment**

Run:

```powershell
python3 'C:\Users\Administrator\.codex\plugins\cache\openai-bundled\visualize\1.0.16\skills\visualize\scripts\render.py' 'C:\Users\Administrator\.codex\visualizations\2026\08\02\019fc2f7-a155-7860-ad05-d991071afd4b\study-hub-dashboard-card-refinement-v2.html' 'C:\Users\Administrator\AppData\Local\Temp\study-hub-dashboard-card-refinement-v2-rendered.html'
```

Expected: successful render with no fragment contract errors.

- [ ] **Step 3: Inspect the default 16:9 view**

Open the rendered preview at desktop width and verify the whole stage is visible, no card text overlaps, all six supporting cards retain their Figma identity, and the repeated 16px inset is visually consistent.

- [ ] **Step 4: Exercise ratio and grid controls**

Switch to `超宽屏` and `4:3`, then toggle the grid. Expected: the stage scales uniformly with possible side or top/bottom letterboxing, card proportions do not stretch, and the overlay remains aligned to the 8×4 layout.

- [ ] **Step 5: Compare against the Figma screenshot**

Check navigation, page framing, module placement, color, radius, and content order against Figma node `349:96`. Reject changes that make the page read as a different design system; retain only the approved internal card corrections.
