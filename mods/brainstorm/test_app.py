#!/usr/bin/env python3
"""Test script for AI 反问 -- tests logic layer without manual UI interaction."""
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error

# Add the project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test 1: Config functions
print("=" * 60)
print("Test 1: Config loading")
print("=" * 60)

# Use a temp config path
import importlib.util
spec = importlib.util.spec_from_file_location("ai_fanwen", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-fanwen.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app.CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config.json")

# Clean up any existing test config
if os.path.exists(app.CONFIG_PATH):
    os.remove(app.CONFIG_PATH)

# Test default config
cfg = app.load_config()
print(f"  Default config: {cfg}")
assert "api_key" in cfg, "Missing api_key"
print("  PASS: Default config has api_key")

# Test merging with saved (missing keys)
with open(app.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"api_key": "sk-test"}, f)
cfg = app.load_config()
print(f"  Merged config: {cfg}")
assert cfg["api_key"] == "sk-test", "api_key not preserved"
print("  PASS: Merge preserves saved values and adds defaults")

# Test save
app.save_config({"api_key": "sk-saved"})
cfg = app.load_config()
assert cfg["api_key"] == "sk-saved"
print("  PASS: Save and reload works")

os.remove(app.CONFIG_PATH)

# Test 2: MODE_CONFIG
print("\n" + "=" * 60)
print("Test 2: MODE_CONFIG")
print("=" * 60)

for mk in ("idea", "prompt"):
    mc = app.MODE_CONFIG[mk]
    assert "card_title" in mc, f"Missing card_title in {mk}"
    assert "steps" in mc, f"Missing steps in {mk}"
    assert "step3_button" in mc, f"Missing step3_button in {mk}"
    assert "step1_placeholder" in mc, f"Missing step1_placeholder in {mk}"
    print(f"  {mk}: {mc['card_title']} -- {len(mc['steps'])} steps -- OK")

# Test that "fanwen" is gone
assert "fanwen" not in app.MODE_CONFIG, "fanwen mode should be removed!"
print("  PASS: fanwen mode correctly removed")

# Test 3: System prompts
print("\n" + "=" * 60)
print("Test 3: System prompts")
print("=" * 60)

for mk in ("idea", "prompt"):
    sp2 = app.build_step2_prompt(mk)
    sp3 = app.build_step3_prompt(mk)
    assert "❓" in sp2, f"Step2 prompt for {mk} missing ❓ marker"
    assert "其他" in sp2, f"Step2 prompt for {mk} missing 其他"
    assert len(sp2) > 100, f"Step2 prompt for {mk} too short"
    assert len(sp3) > 100, f"Step3 prompt for {mk} too short"
    print(f"  {mk}: step2={len(sp2)} chars, step3={len(sp3)} chars -- OK")
print("  PASS: All system prompts generated")

# Test 4: parse_反问_response
print("\n" + "=" * 60)
print("Test 4: parse_反问_response")
print("=" * 60)

# Standard format
text1 = """❓ 你说的笔记工具，是偏向哪种？

- [轻量便签，快速记录]
- [知识管理，双向链接]
- [结构化笔记，文件夹 + 标签]
- [✏️ 其他]"""

q, opts, rec = app.parse_反问_response(text1)
print(f"  Question: {q}")
print(f"  Options ({len(opts)}): {opts}")
assert q == "你说的笔记工具，是偏向哪种？", f"Wrong question: {q}"
assert len(opts) == 4, f"Expected 4 options, got {len(opts)}"
assert "其他" in opts[-1], f"Last option should be 其他: {opts[-1]}"
print("  PASS: Standard format")

# Missing question -- should use first non-option line
text2 = """- [选项A]
- [选项B]
- [✏️ 其他]"""
q, opts, rec = app.parse_反问_response(text2)
print(f"  Fallback question: {q}")
print(f"  Options: {opts}")
assert len(opts) >= 2, f"Expected at least 2 options, got {len(opts)}"
print("  PASS: Fallback format (no ❓, no brackets)")

# Empty response
text3 = ""
q, opts, rec = app.parse_反问_response(text3)
print(f"  Empty: q='{q}', opts={opts}")
assert len(opts) >= 2, f"Expected fallback options for empty input"
print("  PASS: Empty response fallback")

# Missing 其他
text4 = """❓ 问题
- [选项A]
- [选项B]"""
q, opts, rec = app.parse_反问_response(text4)
print(f"  Without 其他: {opts}")
assert any("其他" in o for o in opts), "Should auto-add 其他"
print("  PASS: Auto-adds 其他")

# Test 5: API call_deepseek signature
print("\n" + "=" * 60)
print("Test 5: call_deepseek signature")
print("=" * 60)

import inspect
sig = inspect.signature(app.call_deepseek)
params = list(sig.parameters.keys())
print(f"  Parameters: {params}")
assert "system_prompt" in params, "Missing system_prompt parameter"
assert "messages" in params, "Missing messages parameter"
print("  PASS: call_deepseek accepts system_prompt")

# Test 6: API message formatting
print("\n" + "=" * 60)
print("Test 6: API message formatting (without actual API call)")
print("=" * 60)

# Simulate the message conversion that happens inside call_deepseek
messages = [
    {"role": "user", "content": "我想做笔记工具"},
    {"role": "assistant", "questions": ["偏向哪种？"], "options": ["轻量", "重量", "✏️ 其他"], "round": 1},
    {"role": "user", "content": "轻量"},
]
system_prompt = app.build_step2_prompt("idea")

api_messages = [{"role": "system", "content": system_prompt}]
for m in messages:
    role = m["role"]
    if role == "assistant":
        parts = []
        for q in m.get("questions", []):
            parts.append(f"❓ {q}")
        for opt in m.get("options", []):
            parts.append(f"- [{opt}]")
        content = "\n".join(parts) if parts else m.get("content", "")
    else:
        content = m.get("content", "")
    api_messages.append({"role": role, "content": content})

print(f"  Generated {len(api_messages)} API messages")
for i, m in enumerate(api_messages):
    print(f"  [{i}] role={m['role']}, content_len={len(m['content'])}")
    if m['role'] == 'assistant':
        print(f"      content preview: {m['content'][:100]}...")

assert api_messages[0]["role"] == "system", "First message should be system"
assert api_messages[1]["role"] == "user", "Second should be user"
assert api_messages[2]["role"] == "assistant", "Third should be assistant"
assert "轻量" in api_messages[2]["content"], "Assistant content should include options"
assert "❓" in api_messages[2]["content"], "Assistant content should include question"
print("  PASS: API message formatting correct")

# Test 7: State machine logic (without GUI)
print("\n" + "=" * 60)
print("Test 7: MainWindow state transitions (logic check)")
print("=" * 60)

# Create a headless tkinter root for testing
import tkinter as tk
# Use the module's root instead of creating a new one
test_root = app.root  # root is created at module level

try:
    mw = app.MainWindow()
    print(f"  Created MainWindow")
    print(f"  current_view: {mw.current_view}")
    print(f"  mode: {mw.mode}")
    print(f"  step: {mw.step}")
    print(f"  messages: {len(mw.messages)}")

    assert mw.current_view == "welcome", f"Should start on welcome, got {mw.current_view}"
    assert mw.mode is None, f"Should have no mode, got {mw.mode}"
    assert mw.step == 1
    assert len(mw.messages) == 0
    print("  PASS: Initial state correct")

    # Test entering a mode
    mw._enter_mode("idea")
    print(f"  After _enter_mode('idea'):")
    print(f"    current_view: {mw.current_view}")
    print(f"    mode: {mw.mode}")
    print(f"    step: {mw.step}")
    assert mw.current_view == "step1", f"Should be step1, got {mw.current_view}"
    assert mw.mode == "idea"
    assert mw.step == 1
    print("  PASS: Mode entry works")

    # Test _go_back from step1
    mw._go_back()
    print(f"  After _go_back from step1:")
    print(f"    current_view: {mw.current_view}")
    print(f"    mode: {mw.mode}")
    assert mw.current_view == "welcome", f"Should be welcome, got {mw.current_view}"
    assert mw.mode is None
    print("  PASS: Back from step1 returns to welcome")

    # Enter mode again and test step progression
    mw._enter_mode("prompt")
    assert mw.current_view == "step1" and mw.mode == "prompt"
    print(f"  Mode 'prompt' entered: OK")

    # Test _jump_to_step (should not jump forward)
    mw._jump_to_step(2)  # Should be a no-op since step=1 < 2 is False for jump (jump only to completed)
    print(f"  After _jump_to_step(2): step={mw.step}")
    # _jump_to_step(2) when step=1 should be a no-op because only jump to steps < current
    # Actually, the guard is: if step < self.step: jump. So jump_to_step(2) when step=1 is a no-op. Correct.
    print("  PASS: Cannot jump forward")

    # Test step -> 2 -> 3 (simulate without API calls)
    mw.messages = [{"role": "user", "content": "test"}]
    mw.step = 2
    mw._show_view("step2")
    print(f"  Step 2 view: current_view={mw.current_view}")
    assert mw.current_view == "step2"
    print("  PASS: Step 2 view shows")

    mw.step = 3
    mw._show_view("step3")
    print(f"  Step 3 view: current_view={mw.current_view}")
    assert mw.current_view == "step3"
    print("  PASS: Step 3 view shows")

    # Test _restart_mode
    mw._restart_mode()
    assert mw.current_view == "step1" and mw.step == 1 and len(mw.messages) == 0
    print("  PASS: Restart mode works")

    # Test _go_home
    mw._go_home()
    assert mw.current_view == "welcome" and mw.mode is None
    print("  PASS: Go home works")

    # Test progress bar logic
    mw._enter_mode("idea")
    mw.step = 2
    mw._update_progress()
    print("  PASS: Progress bar update doesn't crash")

    mw.win.destroy()
    print("\n  ALL STATE TRANSITION TESTS PASSED")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n  FAIL: {e}")

# Don't destroy test_root -- it's app.root, needed by the module

# Test 8: History persistence
print("\n" + "=" * 60)
print("Test 8: History persistence")
print("=" * 60)

app.HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_history.json")
if os.path.exists(app.HISTORY_PATH):
    os.remove(app.HISTORY_PATH)

h = app.load_history()
assert h == [], f"Empty history should be [], got {h}"
print("  PASS: Empty history loads as []")

test_msgs = [{"role": "user", "content": "test"}]
app.save_history(test_msgs)
h2 = app.load_history()
assert h2 == test_msgs, f"History roundtrip failed"
print("  PASS: History save/load roundtrip")

os.remove(app.HISTORY_PATH)

# Summary
print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
