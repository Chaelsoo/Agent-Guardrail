#!/usr/bin/env python3
"""Test OpenClaw session lifecycle - simulate /new command."""

import requests
import time

BASE = "http://localhost:8765/v1"

def print_sessions():
    """Print current session state."""
    r = requests.get(f"{BASE}/sessions")
    all_sessions = r.json()
    active = [s for s in all_sessions if not s.get("ended")]
    ended = [s for s in all_sessions if s.get("ended")]

    print(f"  Total: {len(all_sessions)} | Active: {len(active)} | Ended: {len(ended)}")
    for s in active:
        print(f"    • Active: {s['session_id'][:8]}... (traces: {s.get('trace_count', 0)})")
    return active, ended

print("\n" + "="*60)
print("Testing OpenClaw Session Reset Flow")
print("="*60)

# ============================================================================
# Scenario: User has a conversation, then types /new
# ============================================================================

print("\n[Step 1] User starts conversation")
print("-" * 60)

# Simulate OpenClaw creating first session
r = requests.post(f"{BASE}/sessions", json={"agent_type": "general", "environment": "test"})
session1 = r.json()["session_id"]
print(f"✓ Session created: {session1[:8]}...")

# User sends messages
messages = [
    "Hello, can you help me with Python?",
    "What are list comprehensions?",
    "Can you give me an example?"
]

for msg in messages:
    r = requests.post(f"{BASE}/sessions/{session1}/guard/input", json={"content": msg})
    trace_id = r.json().get("trace_id")

    # Simulate LLM response
    r = requests.post(
        f"{BASE}/sessions/{session1}/guard/output",
        json={"content": f"Response to: {msg[:30]}...", "trace_id": trace_id}
    )
    print(f"  • Message: {msg[:40]}... → trace created")

print("\n[State after conversation]")
active, ended = print_sessions()

# ============================================================================
# Simulate /new command
# ============================================================================

print("\n[Step 2] User types /new (reset)")
print("-" * 60)

print("  Simulating OpenClaw before_reset hook...")
print(f"  → Calling POST /sessions/{session1[:8]}.../end")

# This is what the plugin's before_reset hook should do
r = requests.post(f"{BASE}/sessions/{session1}/end")
if r.status_code == 200:
    print(f"  ✓ Session ended: {r.json()}")
else:
    print(f"  ❌ Failed to end session: {r.status_code} {r.text}")

time.sleep(1)

print("\n[State after /new]")
active, ended = print_sessions()

if len(active) == 0:
    print("  ✅ Old session properly ended")
else:
    print("  ❌ Old session still active!")

# ============================================================================
# New conversation after reset
# ============================================================================

print("\n[Step 3] User starts new conversation")
print("-" * 60)

# Simulate OpenClaw creating new session (this is what should happen)
print("  What SHOULD happen: OpenClaw plugin creates new session")
print("  → Calling POST /sessions (create new session)")

r = requests.post(f"{BASE}/sessions", json={"agent_type": "general", "environment": "test"})
session2 = r.json()["session_id"]
print(f"  ✓ New session created: {session2[:8]}...")

# Send first message in new conversation
r = requests.post(
    f"{BASE}/sessions/{session2}/guard/input",
    json={"content": "Hi! This is a fresh conversation."}
)
trace_id = r.json().get("trace_id")

r = requests.post(
    f"{BASE}/sessions/{session2}/guard/output",
    json={"content": "Hello! Yes, this is a new conversation.", "trace_id": trace_id}
)
print("  • First message in new session sent")

print("\n[Final state]")
active, ended = print_sessions()

# ============================================================================
# Verification
# ============================================================================

print("\n[Verification]")
print("-" * 60)

if len(active) == 1 and active[0]["session_id"] == session2:
    print("✅ PASS: Only new session is active")
else:
    print(f"❌ FAIL: Expected 1 active session (new one), got {len(active)}")

if len(ended) >= 1 and any(s["session_id"] == session1 for s in ended):
    print("✅ PASS: Old session marked as ended")
else:
    print(f"❌ FAIL: Old session not marked as ended")

print("\n" + "="*60)
print("What OpenClaw Plugin Should Do:")
print("="*60)
print("""
1. before_reset hook fires
2. Plugin calls POST /sessions/{session_id}/end for all active sessions
3. Plugin clears local sessionMap
4. Next user message triggers before_prompt_build hook
5. resolveSession() doesn't find existing session in sessionMap
6. Plugin calls POST /sessions to create new session
7. New session appears in dashboard
""")

print("\n🔍 Check Dashboard: http://localhost:8765")
print("   Should see 1 active session (the new one)")
print("   Old sessions should be filtered out\n")
