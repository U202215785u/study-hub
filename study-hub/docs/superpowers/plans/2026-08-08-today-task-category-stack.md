# Today Task Category Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users manage task categories and switch among three category task lists in the home dashboard's draggable stacked-card widget.

**Architecture:** SQLite owns categories and task-to-category assignment. The DDL API exposes category CRUD, ordered reads, and category-aware task writes. The DDL view manages categories and consumes a one-time creation route query; Home maps categories plus scheduled tasks into the focused widget, which owns pointer, click, keyboard, and reduced-motion card transitions.

**Tech Stack:** FastAPI, SQLite, Vue 3 Composition API, Vue Router, Vitest, Vue Test Utils, pytest.

---

### Task 1: Category schema and migration

**Files:**
- Modify: `backend/database.py`
- Create: `backend/tests/test_ddl_categories.py`

- [ ] **Step 1: Write the failing migration test**

```python
def test_init_db_seeds_categories_and_backfills_legacy_task_types(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "study_hub.db"))
    database.init_db()
    conn = database.get_db()
    categories = conn.execute("SELECT name, is_system FROM ddl_categories ORDER BY sort_order").fetchall()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(ddl_tasks)").fetchall()}
    assert [row["name"] for row in categories] == ["待办", "学习任务", "里程碑", "未分类"]
    assert "category_id" in columns
```

- [ ] **Step 2: Run the test and verify it fails because `ddl_categories` does not exist.**

Run: `pytest backend/tests/test_ddl_categories.py::test_init_db_seeds_categories_and_backfills_legacy_task_types -q`

- [ ] **Step 3: Add the minimal migration.**

```python
def _migrate_ddl_categories(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS ddl_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
        sort_order INTEGER NOT NULL DEFAULT 0, is_system INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    if "category_id" not in {row[1] for row in conn.execute("PRAGMA table_info(ddl_tasks)")}:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN category_id INTEGER")
    # Seed fixed legacy labels and backfill by legacy task_type.
```

- [ ] **Step 4: Re-run the migration test and then the backend test suite.**

Run: `pytest backend/tests/test_ddl_categories.py -q`

### Task 2: Category and category-aware task API

**Files:**
- Modify: `backend/endpoints/ddl.py`
- Modify: `backend/tests/test_ddl_categories.py`

- [ ] **Step 1: Write failing API tests.**

```python
def test_category_crud_reorders_and_deletion_reassigns_tasks(client):
    created = client.post("/ddl/categories", json={"name": "深度工作"}).json()
    task = client.post("/ddl/tasks", json={"title": "专注", "category_id": created["id"]}).json()
    assert client.put("/ddl/categories/reorder", json={"category_ids": [created["id"]]}).json()["status"] == "ok"
    assert client.delete(f"/ddl/categories/{created['id']}").json()["status"] == "ok"
    assert client.get("/ddl/tasks").json()[0]["category_id"] != created["id"]
```

- [ ] **Step 2: Run it and verify the API route is missing.**

Run: `pytest backend/tests/test_ddl_categories.py::test_category_crud_reorders_and_deletion_reassigns_tasks -q`

- [ ] **Step 3: Implement ordered category CRUD and task validation.**

```python
@router.get("/ddl/categories")
def list_categories():
    return [dict(row) for row in get_db().execute("SELECT * FROM ddl_categories ORDER BY sort_order, id")]

@router.delete("/ddl/categories/{category_id}")
def delete_category(category_id: int):
    # Reject protected category; otherwise update matching ddl_tasks to the protected category and delete in one transaction.
```

- [ ] **Step 4: Persist `category_id` from task create/update and join category metadata on task reads.**

```python
category_id = payload.get("category_id")
if category_id is not None and not conn.execute("SELECT 1 FROM ddl_categories WHERE id = ?", (category_id,)).fetchone():
    return {"error": "任务分类不存在"}
```

- [ ] **Step 5: Run the focused and full backend suites.**

Run: `pytest backend/tests/test_ddl_categories.py backend/tests/test_home_api_contract.py -q`

### Task 3: DDL category management and create intent

**Files:**
- Modify: `frontend/src/views/DDL.vue`
- Create: `frontend/src/views/DDL.test.js`

- [ ] **Step 1: Write failing DDL tests.**

```javascript
it('creates a task with the category and date provided by the home create intent', async () => {
  const wrapper = mount(DDL, { global: { plugins: [router] } })
  await router.push('/ddl?create=1&categoryId=7&planDate=2026-08-08')
  await nextTick()
  expect(wrapper.find('[data-testid="task-category"]').element.value).toBe('7')
  expect(wrapper.find('[data-testid="task-plan-date"]').element.value).toBe('2026-08-08')
})
```

- [ ] **Step 2: Run it and verify it fails because the queried controls do not exist.**

Run: `npm run test:unit -- src/views/DDL.test.js`

- [ ] **Step 3: Implement category fetch, management controls, and a category select in the task modal.**

```vue
<select v-model="form.category_id" data-testid="task-category">
  <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
</select>
```

- [ ] **Step 4: Consume the route query exactly once and remove it after opening the existing modal.**

```javascript
watch(() => route.query.create, () => {
  if (route.query.create === '1') {
    openAddModal('todo', { category_id: Number(route.query.categoryId), plan_type: 'daily', plan_date: route.query.planDate })
    router.replace({ query: {} })
  }
}, { immediate: true })
```

- [ ] **Step 5: Run focused view tests.**

Run: `npm run test:unit -- src/views/DDL.test.js`

### Task 4: Category-aware home data and stacked-card widget

**Files:**
- Modify: `frontend/src/composables/home/useHomeDashboardData.js`
- Modify: `frontend/src/composables/home/useHomeDashboardData.test.js`
- Modify: `frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Modify: `frontend/src/design-system/widgets/DashboardCompositeWidgets.test.js`
- Modify: `frontend/src/views/Home.vue`
- Modify: `frontend/src/views/Home.test.js`

- [ ] **Step 1: Write failing mapping and widget tests.**

```javascript
it('rotates the front category after a horizontal pointer drag', async () => {
  const wrapper = mount(TodayFocusWidget, { props: { categories: [{ id: 1, name: '工作' }, { id: 2, name: '学习' }, { id: 3, name: '生活' }] } })
  await wrapper.get('[data-testid="today-card-stack"]').trigger('pointerdown', { clientX: 200, pointerId: 1 })
  await wrapper.get('[data-testid="today-card-stack"]').trigger('pointerup', { clientX: 100, pointerId: 1 })
  expect(wrapper.get('[data-testid="today-card-title"]').text()).toBe('学习')
})
```

- [ ] **Step 2: Run the focused test and verify it fails because the stack contract is absent.**

Run: `npm run test:unit -- src/design-system/widgets/DashboardCompositeWidgets.test.js`

- [ ] **Step 3: Add category task grouping and category props in Home.**

```javascript
mapTodayTaskCategories(tasks, categories, selectedDate) {
  return categories.map((category) => ({ ...category, tasks: tasks.filter((task) => recordDate(task) === selectedDate && task.category_id === category.id) }))
}
```

- [ ] **Step 4: Replace static layers with three interactive cards.**

```vue
<div data-testid="today-card-stack" tabindex="0" @pointerdown="startDrag" @pointermove="moveDrag" @pointerup="finishDrag" @keydown.left.prevent="rotate(-1)" @keydown.right.prevent="rotate(1)">
  <section v-for="(category, index) in stackedCategories" :key="category.id" :data-front="index === 0" @click="index && rotate(index)">
    <button v-if="index === 0" @click.stop="$emit('create', category.id)">建立任务</button>
  </section>
</div>
```

- [ ] **Step 5: Wire the create event to `/ddl?create=1&categoryId=...&planDate=...`, then run all affected tests.**

Run: `npm run test:unit -- src/composables/home/useHomeDashboardData.test.js src/design-system/widgets/DashboardCompositeWidgets.test.js src/views/Home.test.js`

### Task 5: Accessibility, regression, and visual verification

**Files:**
- Modify: `frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Modify: `frontend/src/design-system/widgets/DashboardCompositeWidgets.test.js`

- [ ] **Step 1: Write failing tests for keyboard rotation and reduced-motion state changes.**

```javascript
it('rotates the focused stack with ArrowRight', async () => {
  const wrapper = mount(TodayFocusWidget, { props: { categories } })
  await wrapper.get('[data-testid="today-card-stack"]').trigger('keydown', { key: 'ArrowRight' })
  expect(wrapper.get('[data-testid="today-card-title"]').text()).toBe('学习')
})
```

- [ ] **Step 2: Run and verify the tests fail, then implement semantic labels, focus styles, and a reduced-motion CSS branch.**

Run: `npm run test:unit -- src/design-system/widgets/DashboardCompositeWidgets.test.js`

- [ ] **Step 3: Run the full frontend suite and production build.**

Run: `npm run test:unit && npm run build`

- [ ] **Step 4: Start the local app and verify in a browser.**

Check that cards do not overlap controls at desktop and mobile widths; click a rear card, drag across and below the threshold, use arrow keys, create a task from each category, rename/reorder/delete a category, and confirm deleted-category tasks appear under `未分类`.
