# Douyin Image Note Vision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse and summarize Douyin image notes with grounded visual analysis and a configured fallback model.

**Architecture:** The MCP parser classifies source media. The automation worker downloads image-note media within strict limits, invokes the multimodal AI client, and passes visual facts into the existing summary prompt. The settings endpoint owns the encrypted fallback credentials.

**Tech Stack:** Python, requests, httpx, FastAPI, pytest, Windows DPAPI, OpenAI-compatible Chat Completions.

---

### Task 1: Normalize source media

**Files:**
- Modify: `douyin-mcp-server/douyin_mcp_server/server.py`
- Test: `douyin-mcp-server/tests/test_image_notes.py`

- [x] Add failing tests for image notes, direct note pages, video posts, and posts without media.
- [x] Preserve resolved note URLs and return a typed normalized media record.
- [x] Verify: `python -m pytest tests/test_image_notes.py -q` reports 4 passed.

### Task 2: Add multimodal fallback routing

**Files:**
- Modify: `study-hub/backend/ai_client.py`
- Test: `study-hub/backend/tests/test_vision_client.py`

- [x] Add failing tests for image messages, primary-to-fallback routing, and safe all-failure behavior.
- [x] Implement transient data URL messages and retry only recoverable upstream failures.
- [x] Verify: `python -m pytest backend/tests/test_vision_client.py -q` reports 3 passed.

### Task 3: Route image notes through visual analysis

**Files:**
- Modify: `study-hub/backend/endpoints/automation.py`
- Test: `study-hub/backend/tests/test_douyin_image_notes.py`

- [x] Add failing tests for skipping ASR, partial download handling, and no-download failure.
- [x] Add bounded image retrieval, pass validated source URLs to the vision model, and inject visual facts into the existing deep-summary raw data.
- [x] Verify: `python -m pytest backend/tests/test_douyin_image_notes.py -q` reports 3 passed.

### Task 4: Expose and configure the fallback service

**Files:**
- Modify: `study-hub/backend/endpoints/settings.py`
- Test: `study-hub/backend/tests/test_vision_settings.py`

- [x] Add a failing settings catalogue test.
- [x] Add DPAPI-backed base URL, model, and secret fields.
- [x] Store the user-supplied credential locally without writing it to a tracked file.
- [ ] Run focused regression and endpoint smoke checks.
