#!/usr/bin/env python3
"""Full integration test - simulate OpenClaw plugin behavior."""

import requests
import time

BASE = "http://localhost:8765/v1"

def test_full_conversation_cycle():
    """Simulate complete OpenClaw conversation with reset."""

    print("\n" + "="*70)
    print("FULL INTEGRATION TEST - Simulating OpenClaw Plugin")
    print("="*70)

    # ========================================================================
    # Part 1: First Conversation
    # ========================================================================
    print("\n[PART 1] First Conversation")
    print("-" * 70)

    # Simulate: User starts conversation, OpenClaw plugin creates session
    print("\n1. User opens OpenClaw web UI and sends first message")
    r = requests.post(f"{BASE}/sessions", json={"agent_type": "general", "environment": "dev"})
    session1 = r.json()["session_id"]
    print(f"   ✓ Plugin creates Aegis session: {session1[:12]}...")

    # Simulate: User message → input gate
    print("\n2. User: 'Hello, how are you?'")
    r = requests.post(
        f"{BASE}/sessions/{session1}/guard/input",
        json={"content": "Hello, how are you?", "metadata": {"source": "openclaw-web-ui"}}
    )
    input_result = r.json()
    trace_id = input_result.get("trace_id")
    print(f"   ✓ Input gate: allowed={input_result['allowed']}, trace_id={trace_id[:8]}...")

    # Simulate: LLM response → output gate
    print("\n3. Agent responds: 'I'm doing great! How can I help you?'")
    r = requests.post(
        f"{BASE}/sessions/{session1}/guard/output",
        json={
            "content": "I'm doing great! How can I help you?",
            "trace_id": trace_id,
            "metadata": {"source": "openclaw-web-ui"}
        }
    )
    output_result = r.json()
    print(f"   ✓ Output gate: allowed={output_result['allowed']}")

    # Simulate: Another message
    print("\n4. User: 'Can you help me with Python?'")
    r = requests.post(
        f"{BASE}/sessions/{session1}/guard/input",
        json={"content": "Can you help me with Python?"}
    )
    trace_id = r.json().get("trace_id")

    r = requests.post(
        f"{BASE}/sessions/{session1}/guard/output",
        json={"content": "Of course! What would you like to know about Python?", "trace_id": trace_id}
    )
    print(f"   ✓ Another turn completed")

    # Check session state
    print("\n5. Checking Aegis dashboard state...")
    r = requests.get(f"{BASE}/sessions")
    all_sessions = r.json()
    active = [s for s in all_sessions if not s.get("ended")]

    print(f"   • Total sessions: {len(all_sessions)}")
    print(f"   • Active sessions: {len(active)}")

    # Find our session
    our_session = next((s for s in active if s["session_id"] == session1), None)
    if our_session:
        print(f"   ✓ Our session found: {our_session['trace_count']} traces")
    else:
        print(f"   ✗ ERROR: Session {session1[:12]}... not found in active list!")
        return False

    # ========================================================================
    # Part 2: User Types /new (Reset)
    # ========================================================================
    print("\n[PART 2] User Types /new")
    print("-" * 70)

    print("\n6. User types: /new")
    print("   → This should trigger OpenClaw's before_reset hook")
    print("   → Plugin should call: POST /sessions/{session_id}/end")

    # Simulate what the plugin's before_reset hook does
    r = requests.post(f"{BASE}/sessions/{session1}/end", json={})
    if r.status_code == 200:
        print(f"   ✓ Session ended successfully")
    else:
        print(f"   ✗ Failed to end session: {r.status_code}")
        return False

    # Verify session is marked as ended
    print("\n7. Verifying session was ended...")
    r = requests.get(f"{BASE}/sessions/{session1}")
    session_data = r.json()
    if session_data.get("ended"):
        print(f"   ✓ Session marked as ended=True")
    else:
        print(f"   ✗ ERROR: Session NOT marked as ended!")
        return False

    # Check dashboard state after reset
    print("\n8. Checking dashboard after reset...")
    r = requests.get(f"{BASE}/sessions")
    all_sessions = r.json()
    active = [s for s in all_sessions if not s.get("ended")]
    ended = [s for s in all_sessions if s.get("ended")]

    print(f"   • Active sessions: {len(active)}")
    print(f"   • Ended sessions: {len(ended)}")

    if session1 not in [s["session_id"] for s in active]:
        print(f"   ✓ Old session filtered out of active list")
    else:
        print(f"   ✗ ERROR: Old session still showing as active!")
        return False

    # ========================================================================
    # Part 3: New Conversation After Reset
    # ========================================================================
    print("\n[PART 3] New Conversation After Reset")
    print("-" * 70)

    print("\n9. User sends first message in new conversation")
    print("   User: 'Hi! This is a fresh start.'")
    print("   → Plugin should create NEW session (old one was ended)")

    # Simulate: Plugin creates new session
    r = requests.post(f"{BASE}/sessions", json={"agent_type": "general", "environment": "dev"})
    session2 = r.json()["session_id"]
    print(f"   ✓ Plugin creates NEW session: {session2[:12]}...")

    if session2 == session1:
        print(f"   ✗ ERROR: Same session ID! Should be different!")
        return False
    else:
        print(f"   ✓ Different session ID (correct)")

    # Send message in new session
    print("\n10. Sending message in new session...")
    r = requests.post(
        f"{BASE}/sessions/{session2}/guard/input",
        json={"content": "Hi! This is a fresh start."}
    )
    trace_id = r.json().get("trace_id")

    r = requests.post(
        f"{BASE}/sessions/{session2}/guard/output",
        json={"content": "Hello! Yes, this is a brand new conversation.", "trace_id": trace_id}
    )
    print(f"   ✓ Message sent and received")

    # Final verification
    print("\n11. Final verification...")
    r = requests.get(f"{BASE}/sessions")
    all_sessions = r.json()
    active = [s for s in all_sessions if not s.get("ended")]
    ended = [s for s in all_sessions if s.get("ended")]

    print(f"   • Active sessions: {len(active)}")
    print(f"   • Ended sessions: {len(ended)}")

    # Check that session2 is active
    if session2 in [s["session_id"] for s in active]:
        print(f"   ✓ New session {session2[:12]}... is active")
    else:
        print(f"   ✗ ERROR: New session not in active list!")
        return False

    # Check that session1 is ended
    if session1 in [s["session_id"] for s in ended]:
        print(f"   ✓ Old session {session1[:12]}... is ended")
    else:
        print(f"   ✗ ERROR: Old session not in ended list!")
        return False

    # ========================================================================
    # Success!
    # ========================================================================
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nWhat this proves:")
    print("  • Sessions are created correctly")
    print("  • Messages flow through input/output gates")
    print("  • Sessions can be ended (simulating /new)")
    print("  • New sessions are created after reset")
    print("  • Dashboard correctly filters ended sessions")
    print("\n🌐 Check dashboard: http://localhost:8765")
    print(f"   Should show {len(active)} active session(s)")
    print(f"   Session {session2[:12]}... should be visible")
    print(f"   Session {session1[:12]}... should be hidden (ended)")
    print()

    return True

if __name__ == "__main__":
    success = test_full_conversation_cycle()
    exit(0 if success else 1)
