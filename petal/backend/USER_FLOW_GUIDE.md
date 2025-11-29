# Petal Backend - User Flow Testing Guide

This guide walks you through testing the complete user flow using Swagger UI at `http://localhost:8000/docs`

---

## Prerequisites

1. Backend server running: `python main.py`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Have a user ID ready (e.g., `your-name-001`)

---

## Flow 1: Getting Started - First Session & Memories

### Step 1: Health Check
**Endpoint**: `GET /health`

1. Click on `GET /health`
2. Click "Try it out"
3. Click "Execute"

**Expected Result**: `{"status": "healthy", "version": "1.0.0"}`

---

### Step 2: Create Your First Session
**Endpoint**: `POST /sessions`

1. Click on `POST /sessions`
2. Click "Try it out"
3. Use this JSON:
```json
{
  "user_id": "alice-dev",
  "name": "My React Project",
  "icon": "⚛️",
  "description": "Learning React hooks and context"
}
```
4. Click "Execute"

**Expected Result**:
- Status: `201 Created`
- Response includes `id` field
- **IMPORTANT**: Copy the `id` value - you'll need it! (e.g., `abc-123-def-456`)

---

### Step 3: Smart Copy - Add First Memory
**Endpoint**: `POST /smart-copy`

This simulates copying important text (Option+C in the Mac app).

1. Click on `POST /smart-copy`
2. Click "Try it out"
3. Use this JSON (replace `SESSION_ID` with your ID from Step 2):
```json
{
  "text": "React Hooks let you use state and other React features without writing a class. The most commonly used hooks are useState for state management, useEffect for side effects like data fetching and subscriptions, useContext for consuming context, useRef for accessing DOM elements and storing mutable values, and useMemo/useCallback for performance optimization. Custom hooks let you extract component logic into reusable functions.",
  "session_id": "SESSION_ID",
  "user_id": "alice-dev"
}
```
4. Click "Execute"

**Expected Result**:
- Status: `200 OK`
- `processed_text` shows Claude's AI-summarized version
- Original was ~500 chars, processed is shorter but preserves key info
- Note the `memory_id` in response

**What happened**: Claude AI processed your text and saved it to the session!

---

### Step 4: Smart Copy - Add Second Memory
**Endpoint**: `POST /smart-copy`

1. Same endpoint as Step 3
2. Use this JSON (replace `SESSION_ID`):
```json
{
  "text": "Context API in React provides a way to pass data through the component tree without having to pass props down manually at every level. You create a context with React.createContext(), provide values with a Provider component, and consume values with useContext hook or Consumer component. Context is ideal for global data like themes, user authentication, or language preferences.",
  "session_id": "SESSION_ID",
  "user_id": "alice-dev"
}
```
3. Click "Execute"

**Expected Result**: Another processed memory saved!

---

### Step 5: Smart Copy - Add Third Memory
**Endpoint**: `POST /smart-copy`

1. Same endpoint
2. Use this JSON (replace `SESSION_ID`):
```json
{
  "text": "Component composition in React is a pattern where you build complex UIs by combining smaller, focused components. Instead of inheritance, React uses composition with props and children. Use props.children to pass components as data. Create container components that handle logic and presentational components that handle UI. Higher-Order Components (HOCs) and Render Props are advanced composition patterns.",
  "session_id": "SESSION_ID",
  "user_id": "alice-dev"
}
```
3. Click "Execute"

**Result**: Now you have 3 memories in your session!

---

### Step 6: Smart Paste - Get Formatted Context
**Endpoint**: `GET /smart-paste/{session_id}`

This simulates what happens when you press Option+V to paste context.

1. Click on `GET /smart-paste/{session_id}`
2. Click "Try it out"
3. Enter your `session_id` from Step 2
4. Click "Execute"

**Expected Result**:
- Status: `200 OK`
- `formatted_text` contains beautifully formatted context:
  ```
  [Session Context: My React Project ⚛️]

  Session History:

  1. [First memory - React Hooks summary]

  2. [Second memory - Context API summary]

  3. [Third memory - Component composition summary]

  [End Session Context]
  ```
- `memory_count`: 3

**Use Case**: This formatted text is ready to paste into ChatGPT/Claude to give them project context!

---

## Flow 2: Managing Sessions

### Step 7: Get All Your Sessions
**Endpoint**: `GET /sessions/{user_id}`

1. Click on `GET /sessions/{user_id}`
2. Click "Try it out"
3. Enter: `alice-dev`
4. Click "Execute"

**Expected Result**: List of all sessions for user `alice-dev`

---

### Step 8: Get Session Details
**Endpoint**: `GET /sessions/detail/{session_id}`

1. Click on `GET /sessions/detail/{session_id}`
2. Click "Try it out"
3. Enter your session ID
4. Click "Execute"

**Expected Result**: Full session details including `memory_count`

---

### Step 9: Update Session
**Endpoint**: `PUT /sessions/{session_id}`

Let's rename your session!

1. Click on `PUT /sessions/{session_id}`
2. Click "Try it out"
3. Enter your session ID
4. Use this JSON:
```json
{
  "name": "Advanced React Patterns",
  "icon": "🚀"
}
```
5. Click "Execute"

**Expected Result**: Session updated with new name and icon!

---

## Flow 3: Searching & Managing Memories

### Step 10: Search in Session
**Endpoint**: `GET /search/{session_id}`

1. Click on `GET /search/{session_id}`
2. Click "Try it out"
3. Enter your session ID
4. Enter query: `hooks`
5. Click "Execute"

**Expected Result**:
- Finds memories mentioning "hooks"
- Shows `relevance_score` for each result
- Only returns matching memories

---

### Step 11: Get All Memories in Session
**Endpoint**: `GET /sessions/{session_id}/memories`

1. Click on `GET /sessions/{session_id}/memories`
2. Click "Try it out"
3. Enter your session ID
4. Optionally set `limit`: 10
5. Click "Execute"

**Expected Result**: List of all 3 memories with timestamps

---

### Step 12: Delete a Specific Memory
**Endpoint**: `DELETE /memories/{memory_id}`

Let's delete the second memory.

1. From Step 11, copy a `memory_id`
2. Click on `DELETE /memories/{memory_id}`
3. Click "Try it out"
4. Enter the memory ID
5. Click "Execute"

**Expected Result**: `{"status": "deleted", "id": "memory-id-here"}`

---

### Step 13: Verify Deletion
**Endpoint**: `GET /smart-paste/{session_id}`

1. Use Smart Paste again (Step 6)
2. Check the result

**Expected Result**: Now shows only 2 memories (the one you deleted is gone!)

---

## Flow 4: Personal Memory (Mem0)

### Step 14: Add Personal Memory
**Endpoint**: `POST /memory/add`

This stores long-term facts about you (not session-specific).

1. Click on `POST /memory/add`
2. Click "Try it out"
3. Use this JSON:
```json
{
  "text": "I prefer TypeScript over JavaScript for all projects. I use VS Code as my main editor.",
  "user_id": "alice-dev"
}
```
4. Click "Execute"

**Expected Result**: `{"status": "added", "message": "Added to personal memory"}`

---

### Step 15: Add Another Personal Memory
**Endpoint**: `POST /memory/add`

1. Same endpoint
2. Use this JSON:
```json
{
  "text": "I am a full-stack developer specializing in React and Node.js. I prefer functional programming patterns.",
  "user_id": "alice-dev"
}
```
3. Click "Execute"

---

### Step 16: Get All Personal Memories
**Endpoint**: `GET /memory/{user_id}`

1. Click on `GET /memory/{user_id}`
2. Click "Try it out"
3. Enter: `alice-dev`
4. Click "Execute"

**Expected Result**: List of personal memories stored in Mem0

**Note**: Mem0 may process/organize these memories differently than raw input.

---

## Flow 5: Multi-Session Workflow

### Step 17: Create Second Session
**Endpoint**: `POST /sessions`

Let's create a project for learning backend!

1. Use `POST /sessions`
2. JSON:
```json
{
  "user_id": "alice-dev",
  "name": "Node.js Backend",
  "icon": "🟢",
  "description": "Learning Express and database design"
}
```
3. Click "Execute"
4. **Save the new session ID!**

---

### Step 18: Add Memories to Second Session
**Endpoint**: `POST /smart-copy`

1. Use the NEW session ID
2. JSON:
```json
{
  "text": "Express.js is a minimal and flexible Node.js web application framework. It provides a robust set of features for web and mobile applications including routing, middleware, template engines, and error handling. Express is unopinionated, meaning you can structure your application however you want.",
  "session_id": "NEW_SESSION_ID",
  "user_id": "alice-dev"
}
```
3. Click "Execute"

---

### Step 19: Compare Sessions
**Endpoint**: `GET /sessions/{user_id}`

1. Get all sessions for `alice-dev`
2. Notice you have 2 different sessions
3. Each session has its own memories

---

### Step 20: Smart Paste from Both Sessions

Try Smart Paste on both session IDs:
1. First session (React) - shows React memories
2. Second session (Node.js) - shows Node.js memories

**Key Insight**: Sessions keep contexts separate!

---

## Flow 6: Complete Use Case Scenario

### Scenario: Working on a Feature

**Context**: You're building a new authentication feature for your React app.

1. **Create Session** (if not exists):
   - Name: "Auth Feature Development"
   - Icon: "🔐"

2. **Smart Copy - Research**:
   - Copy docs about JWT tokens
   - Copy article about secure password storage
   - Copy best practices for OAuth

3. **Smart Paste - Use Context**:
   - Get formatted context
   - Paste into ChatGPT/Claude
   - Ask: "Based on this context, help me implement secure login"

4. **Search Later**:
   - Search for "JWT" when you need that specific info
   - Search for "OAuth" when implementing social login

5. **Update Session**:
   - Rename to "Auth Feature - Completed ✓"

6. **Create New Session** for next feature!

---

## Flow 7: Cleanup

### Step 21: Delete Test Session
**Endpoint**: `DELETE /sessions/{session_id}`

1. Click on `DELETE /sessions/{session_id}`
2. Enter the session ID you want to delete
3. Click "Execute"

**Expected Result**:
- Session deleted
- All memories in that session also deleted (cascade)

---

## Common Patterns

### Pattern 1: Daily Development
```
1. Create session for today's task
2. Smart Copy docs/articles as you research
3. Smart Paste when asking AI for help
4. Search when you need specific info
5. Keep session for reference
```

### Pattern 2: Learning New Tech
```
1. Create session: "Learning [Technology]"
2. Smart Copy important concepts
3. Smart Paste to summarize what you've learned
4. Search to review specific topics
```

### Pattern 3: Long-term Project
```
1. One session per feature/module
2. Smart Copy decisions and important info
3. Get all sessions to see project overview
4. Smart Paste for onboarding new team members
```

---

## Testing Checklist

Use this to verify everything works:

- [ ] Health check returns OK
- [ ] Create session successfully
- [ ] Smart Copy processes text with Claude
- [ ] Smart Paste returns formatted context
- [ ] Get all user sessions
- [ ] Get single session details
- [ ] Update session (name/icon)
- [ ] Search finds relevant memories
- [ ] Get all memories in session
- [ ] Delete specific memory
- [ ] Delete entire session
- [ ] Add personal memory to Mem0
- [ ] Get personal memories
- [ ] Multiple sessions stay separate
- [ ] Cascade delete works (deleting session deletes memories)

---

## Troubleshooting

### 500 Internal Server Error
- Check the terminal where server is running
- Look for error messages
- Verify environment variables in `.env`

### Claude Not Processing Text
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check Claude API quota/billing

### Mem0 Errors
- Verify `MEM0_API_KEY` in `.env`
- Check Mem0 API status

### Supabase Errors
- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Check Supabase project is running
- Verify tables were created with `supabase_setup.sql`

---

## API Response Times

Expected response times:
- Health check: ~10ms
- Session operations: ~100-300ms
- Smart Copy: ~2-5 seconds (Claude processing)
- Smart Paste: ~200-500ms
- Search: ~100-300ms
- Personal Memory: ~500ms-2s (Mem0 processing)

---

## Next Steps After Testing

1. **Build Mac App**: Use these same endpoints from Swift
2. **Deploy to Railway**: Make backend accessible online
3. **Add More Features**:
   - Export session as markdown
   - Share sessions with team
   - Version control for memories
   - Tags/categories for sessions

---

## Tips for Swagger UI

- **Expand All**: Click "Expand Operations" to see all endpoints
- **Models**: Scroll to bottom to see data models
- **Try Different Users**: Test with multiple user IDs to see isolation
- **Copy Session IDs**: Keep a note of session IDs for testing
- **Test Edge Cases**:
  - Empty sessions (Smart Paste with no memories)
  - Long text (Smart Copy with 5000+ words)
  - Special characters in session names
  - Invalid session IDs (should return 404)

---

**Happy Testing! 🎉**

For questions or issues, check the terminal logs where the server is running.
