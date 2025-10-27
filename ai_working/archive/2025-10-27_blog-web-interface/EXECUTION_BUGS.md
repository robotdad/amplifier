# Execution Bugs Found - Systematic Flow Tracing

**Date:** 2025-10-27
**Method:** Step-by-step execution tracing as if running Python interpreter
**Scope:** All code paths from user input to completion

---

## Summary

**Original "Complete Audit":** Found 3 bugs (XSS, wrong data type, placeholder button)
**Execution Tracing:** Found 6 additional bugs that would cause runtime failures

**Total Bugs:** 9 bugs
**Critical (Will Break):** 6 bugs
**Fixed:** 9 bugs

---

## Why First Audit Missed These

**First audit verified:**
- ✅ Code exists
- ✅ Functions defined correctly
- ✅ Data structures present
- ✅ Dependencies installed

**First audit MISSED:**
- ❌ Execution flow end-to-end
- ❌ "What if user enters relative path?"
- ❌ "Where does API key come from?"
- ❌ "Can user bypass configuration?"

**Lesson:** Code review ≠ execution tracing. Must mentally execute with edge cases.

---

## Bugs Found & Fixed (2025-10-27)

### Bug #1: XSS Vulnerability ✅ FIXED
**File:** `content.py:54-78`
**Found by:** Code review
**Issue:** No bleach sanitization in markdown preview
**Impact:** Security vulnerability, script injection
**Fix:** Added `bleach.clean()` with allowed tags/attributes

### Bug #2: Wrong Review Data Structure ✅ FIXED
**File:** `content.py:81-96`
**Found by:** Code review
**Issue:** Returned dict instead of issues array
**Impact:** JavaScript TypeError, drawer won't display
**Fix:** Extract `.get("issues", [])` from review dicts

### Bug #3: Placeholder Regenerate Button ✅ FIXED
**File:** `review.html:42-45`
**Found by:** Code review
**Issue:** Non-functional placeholder
**Impact:** UX confusion
**Fix:** Hidden with `display:none`

### Bug #4: Path Not Expanded ✅ FIXED
**File:** `sessions.py:179-180`
**Found by:** Execution trace (user error: `FileNotFoundError: 'flow.md'`)
**Issue:** Relative paths stored literally, resolved from unknown CWD
**Impact:** FileNotFoundError when workflow tries to read
**Fix:** `Path(path).expanduser().resolve()` before storing

**Execution trace:**
```
User enters: "flow.md"
OLD: Stored as "flow.md" → Path("flow.md").read_text() → Error
NEW: Resolves to "/full/path/flow.md" → Works
```

### Bug #5: Non-functional Browse Buttons ✅ FIXED
**File:** `setup.html:27, 50`
**Found by:** Execution trace (undefined JS functions)
**Issue:** `onclick="browseFile()"` references undefined functions
**Impact:** Console errors, browsers can't access filesystem anyway
**Fix:** Removed browse buttons entirely

### Bug #6: API Key Not Available to Workflow ✅ FIXED
**File:** `progress.py:102-105`, `sessions.py:207-212`, `session.py:77`
**Found by:** Execution trace (two session systems)
**Issue:** API key stored in HTTP session, core stages read from os.environ
**Impact:** AuthenticationError on first API call

**Execution trace:**
```
config.py → request.session["ANTHROPIC_API_KEY"] = key  // HTTP session
core stages → os.getenv("ANTHROPIC_API_KEY")  // Environment
These don't connect!
```

**Fix (3 parts):**
1. Added `api_key` field to SessionState (session.py:77)
2. Transfer from HTTP session to SessionState in start_workflow (sessions.py:207-212)
3. Set environment from SessionState in run_workflow (progress.py:102-109)

### Bug #7: Missing Path Validation ✅ FIXED
**File:** `sessions.py:182-202`
**Found by:** Execution trace (what if paths don't exist?)
**Issue:** Form submission didn't validate paths exist
**Impact:** Workflow crashes when trying to read non-existent files
**Fix:** Check `.exists()` and `.is_file()`/`.is_dir()` before saving paths

### Bug #8: Can Bypass Configuration ✅ FIXED
**File:** `sessions.py:37-40`
**Found by:** Execution trace (direct URL navigation)
**Issue:** `/sessions/new` had no `is_configured()` check
**Impact:** User can skip config, workflow fails with no API key

**Execution trace:**
```
User navigates to /sessions/new directly
→ No is_configured() check
→ Shows setup form
→ User submits
→ get_api_key() returns None
→ Workflow runs with no key
→ Crashes on first API call
```

**Fix:** Added `is_configured()` check, redirects to `/configure` if needed

### Bug #9: API Key None Check ✅ FIXED
**File:** `progress.py:105-107`
**Found by:** Execution trace (defensive programming)
**Issue:** Didn't verify API key exists before workflow
**Impact:** Better error message than auth failure
**Fix:** Check `if not api_key: return` with error message

---

## Edge Cases Verified Working

### ✅ Empty writings directory
- style_extraction.py:32-38 returns `_default_profile()`
- Graceful fallback

### ✅ Empty idea file
- Workflow accepts empty string
- LLM handles it (might generate generic draft)

### ✅ SSE timeout/keepalive
- progress.py:74-79 sends ping every 15s
- Prevents connection timeout

### ✅ Workflow exceptions
- progress.py:143-146 catches, sends to queue
- Error displays in UI

### ✅ Download file missing
- content.py:144-145 creates from current_draft
- Safe fallback

### ✅ Auto-save race conditions
- 1000ms debounce (review.html:311-322)
- Only one request active at a time
- SessionManager.save() is atomic (file write)

### ✅ Draft empty on download
- content.py:145 uses `session_mgr.state.current_draft or ""`
- Returns empty file instead of crashing

---

## Potential Issues Not Fixed (Low Priority)

### Issue #10: SSE Reconnect Race Condition
**File:** `progress.py:64-67`
**Scenario:**
1. User loads progress page → SSE connects → spawns workflow
2. User refreshes during workflow
3. Browser disconnects → `finally:` deletes queue
4. Browser reconnects → creates NEW queue, spawns SECOND workflow

**Impact:** Duplicate API calls, wasted resources
**Mitigation:** SessionManager stage tracking prevents re-running completed stages
**Priority:** Low (edge case, unlikely, mitigated by state)

### Issue #11: Session Cleanup
**File:** N/A
**Issue:** No automatic cleanup of old session directories
**Impact:** `.data/blog_creator/` grows indefinitely
**Priority:** Low (local tool, manual cleanup acceptable)

### Issue #12: Global State (progress_queues)
**File:** `progress.py:43`
**Issue:** Global dict not thread-safe (though single-threaded server)
**Impact:** None in practice (uvicorn single worker)
**Priority:** Low (works for local single-user tool)

---

## Complete Execution Flow Verification

### Happy Path: Full Success ✅

```
1. GET / → Checks API key
   - If env var: → /sessions/new
   - If none: → /configure

2. POST /configure (if needed)
   - Validates key with real API call
   - Stores in HTTP session
   - Redirects to /sessions/new

3. GET /sessions/new
   - ✅ NOW checks is_configured() (Bug #8 fix)
   - Creates SessionManager
   - Shows setup form

4. POST /sessions/{id}/start-workflow
   - ✅ Expands paths with .resolve() (Bug #4 fix)
   - ✅ Validates paths exist (Bug #7 fix)
   - ✅ Transfers API key to SessionState (Bug #6 fix)
   - Saves session
   - Redirects to /sessions/{id}/progress

5. GET /sessions/{id}/progress
   - Returns HTML with EventSource

6. EventSource connects to /sessions/{id}/progress-stream
   - Creates MessageQueue
   - Spawns run_workflow()
   - Streams messages

7. run_workflow()
   - ✅ Checks API key exists (Bug #9 fix)
   - ✅ Sets environment variable
   - Runs 4 workflow stages
   - Each stage emits progress messages
   - Completes → sends complete event

8. Browser redirects to /sessions/{id}/review
   - Shows draft in textarea
   - Loads review data (✅ Bug #2 fixed)
   - Auto-save works

9. User clicks approve
   - POST /sessions/{id}/approve
   - Saves output.md
   - Redirects to /sessions/{id}/complete

10. GET /sessions/{id}/complete
    - Shows success page

11. GET /sessions/{id}/download
    - Downloads final markdown
```

**Verified:** ✅ All paths should work after fixes

### Error Path 1: Invalid Idea Path ✅

```
User enters non-existent file
→ start_workflow() checks idea_path_abs.exists()
→ Returns 400 error with message
→ User sees error, can fix input
```

### Error Path 2: Invalid Writings Directory ✅

```
User enters non-existent directory
→ start_workflow() checks writings_dir_abs.is_dir()
→ Returns 400 error with message
→ User sees error, can fix input
```

### Error Path 3: No API Key ✅

```
User bypasses config somehow
→ run_workflow() checks if not api_key
→ Sends error message to queue
→ User sees "Error: No API key configured"
```

### Error Path 4: Workflow Exception ✅

```
Any stage raises exception
→ run_workflow() try/except catches
→ Logs error with traceback
→ Sends "Error: {message}" to queue
→ finally: marks queue complete
→ User sees error in progress page
```

---

## What Execution Tracing Revealed

### Key Insight #1: Two Session Systems
**HTTP Session** (SessionMiddleware) vs **SessionManager** (file-based)
These don't communicate automatically - must explicitly transfer data.

### Key Insight #2: Environment vs State
Core stages use `os.getenv()` for CLI compatibility.
Web mode must bridge HTTP session → SessionState → environment.

### Key Insight #3: Path Resolution Context
`Path.resolve()` depends on current working directory.
Must resolve at input time, not at usage time.

### Key Insight #4: Fire-and-Forget Async
`asyncio.create_task(run_workflow())` doesn't propagate exceptions.
Must handle all errors inside the task.

---

## Testing Impact

**Before fixes:** Would have found 6+ runtime crashes
**After fixes:** Should run cleanly end-to-end

**Remaining risks:**
- SSE reconnect race (low probability, mitigated)
- Empty content edge cases (handled gracefully)
- Session cleanup (manual acceptable for local tool)

---

## Lessons for Future Audits

### What to Do Differently

1. **Trace execution, don't just read code**
   - "User enters X, what happens?"
   - "Where is CWD when this resolves?"
   - "What if API key is None here?"

2. **Check data handoffs**
   - HTTP session → SessionManager
   - SessionManager → Environment
   - Form data → Path objects

3. **Verify error paths**
   - Missing data
   - Invalid data
   - Network failures
   - File I/O errors

4. **Test mental execution**
   - "What if user enters 'test.md'?"
   - "What if user refreshes?"
   - "What if directory is empty?"

### Audit Checklist

- [ ] Code exists and compiles
- [ ] Data structures correct
- [ ] **Execute happy path mentally**
- [ ] **Execute error paths mentally**
- [ ] **Check all data handoffs**
- [ ] **Verify edge cases**
- [ ] **Test with invalid inputs**

---

## Confidence Level

**Before execution tracing:** 60% confident
**After execution tracing:** 90% confident

**Remaining 10% unknowns:**
- Actual UX flow (does it feel right?)
- Performance (is it fast enough?)
- Error messages (are they helpful?)
- Edge cases I haven't thought of

**These require actual user testing to discover.**

---

**All execution bugs fixed. Ready for real user testing.**
