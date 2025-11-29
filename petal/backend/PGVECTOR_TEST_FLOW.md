# pgvector Testing Userflow

Complete step-by-step guide to test semantic search with pgvector.

**What we're testing**: Vector embeddings, semantic search, and context-aware smart paste

---

## Setup

1. ✅ OpenRouter API key added to `.env`
2. ✅ SQL migration run in Supabase
3. ✅ Server restarted
4. Open Swagger UI: `http://localhost:8000/docs`

---

## Test Flow 1: Basic Vector Search

### Step 1: Create a Test Session

**Endpoint**: `POST /sessions`

```json
{
  "user_id": "vector-test-user",
  "name": "React Learning",
  "icon": "⚛️",
  "description": "Testing vector search with React content"
}
```

**Expected**: Status 201, copy the `id` value (you'll need it!)

Let's say you got: `session-abc-123`

---

### Step 2: Add Memory About React Hooks

**Endpoint**: `POST /smart-copy`

```json
{
  "text": "React Hooks are functions that let you use state and lifecycle features in function components. The most common hooks are useState for managing component state, useEffect for handling side effects like data fetching and subscriptions, useContext for consuming context without nesting, useRef for accessing DOM elements, and useMemo and useCallback for performance optimization by memoizing values and functions.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**What happens**:
1. Claude summarizes the text
2. **OpenRouter generates embedding** ← This is new!
3. Both saved to database

**Expected**:
- Status 200
- Returns `memory_id`, `processed_text`
- Processing takes 2-5 seconds (Claude + embedding generation)

**Check the logs** in your terminal - you should see:
```
[INFO] Generated embedding for XXX chars, YYY tokens
```

---

### Step 3: Add Memory About Component Lifecycle

**Endpoint**: `POST /smart-copy`

```json
{
  "text": "Component lifecycle in React refers to the different phases a component goes through from creation to destruction. In class components, this includes mounting (componentDidMount), updating (componentDidUpdate), and unmounting (componentWillUnmount). In function components, the useEffect hook handles all lifecycle events. You can control when effects run using dependency arrays, and return cleanup functions to handle unmounting.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Expected**: Another memory saved with embedding

---

### Step 4: Add Memory About State Management

**Endpoint**: `POST /smart-copy`

```json
{
  "text": "State management in React can be handled at different levels. Local state using useState is perfect for component-specific data. For sharing state between components, you can lift state up to common parent or use Context API. For complex applications, external libraries like Redux, Zustand, or Jotai provide global state management with features like time-travel debugging, middleware, and developer tools.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Expected**: Third memory saved

---

### Step 5: Test Semantic Search (THE MAGIC!)

Now let's search for something that isn't explicitly mentioned!

**Endpoint**: `GET /search/{session_id}`

**Parameters**:
- `session_id`: `session-abc-123`
- `query`: `managing data in components`
- `mode`: `vector` (default)
- `limit`: `10`

**Expected Results**: Should find all 3 memories!
- Memory about **useState** (managing component state)
- Memory about **state management libraries**
- Memory about **useEffect** (managing side effects/data)

**Why this works**:
- Your query: "managing data in components"
- Didn't use words: "state", "hooks", or "useState"
- But vector search understands the **meaning**!

---

### Step 6: Compare with Text Search

Try the same search with text mode:

**Endpoint**: `GET /search/{session_id}`

**Parameters**:
- `session_id`: `session-abc-123`
- `query`: `managing data in components`
- `mode`: `text`
- `limit`: `10`

**Expected**: Probably 0 or 1 results (text doesn't match exactly)

**Comparison**:
| Search Mode | Query | Results |
|-------------|-------|---------|
| Vector | "managing data" | 3 results ✅ |
| Text | "managing data" | 0-1 results ❌ |

---

## Test Flow 2: Context-Aware Smart Paste

### Step 7: Add Different Topic Memory

Let's add something NOT about React:

**Endpoint**: `POST /smart-copy`

```json
{
  "text": "TypeScript is a strongly typed superset of JavaScript. It adds static type checking which helps catch errors during development. Key features include interfaces for defining object shapes, generics for reusable components, enums for named constants, and type inference. TypeScript compiles to plain JavaScript.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Now you have**: 3 React memories + 1 TypeScript memory

---

### Step 8: Smart Paste - Default (Recent)

**Endpoint**: `GET /smart-paste/{session_id}`

**Parameters**:
- `session_id`: `session-abc-123`
- `limit`: `10` (default)

**Expected**: Returns last 10 memories in chronological order

```
[Session Context: React Learning ⚛️]

Recent History:

1. [React Hooks summary]
2. [Component lifecycle summary]
3. [State management summary]
4. [TypeScript summary]

[End Session Context]
```

---

### Step 9: Smart Paste - Semantic Filter (THE NEW FEATURE!)

Now let's filter to ONLY React hooks content:

**Endpoint**: `GET /smart-paste/{session_id}`

**Parameters**:
- `session_id`: `session-abc-123`
- `query`: `hooks and state management`
- `limit`: `3`

**Expected**: Returns ONLY the 3 React memories (skips TypeScript!)

```
[Session Context: React Learning ⚛️ - Filtered by: "hooks and state management"]

Relevant Context:

1. [React Hooks summary]
2. [State management summary]
3. [Component lifecycle summary]

[End Session Context]
```

**TypeScript memory is NOT included** because it's not semantically related to hooks!

---

### Step 10: Try Different Filter

**Endpoint**: `GET /smart-paste/{session_id}`

**Parameters**:
- `session_id`: `session-abc-123`
- `query`: `types and type safety`
- `limit`: `5`

**Expected**: Returns TypeScript memory (and maybe others with low relevance)

---

## Test Flow 3: Real-World Scenario

Let's simulate a real use case:

### Step 11: Add More Diverse Content

Add these memories to the same session:

**Memory 5 - CSS**:
```json
{
  "text": "CSS Flexbox is a layout model that allows responsive design. Use display: flex on parent, then flex-direction for row/column, justify-content for main axis alignment, and align-items for cross axis. Flex items can have flex-grow, flex-shrink, and flex-basis properties.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Memory 6 - API**:
```json
{
  "text": "REST API best practices include using proper HTTP methods (GET for reading, POST for creating, PUT for updating, DELETE for removing), returning appropriate status codes, implementing pagination for large datasets, using versioning in URLs, and securing endpoints with authentication tokens like JWT.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Now you have**:
- 3× React
- 1× TypeScript
- 1× CSS
- 1× API

---

### Step 12: Search for Specific Concepts

Try these searches:

**Search 1: "fetching data from server"**
```
Expected: Finds useEffect (side effects/data fetching) + API (REST)
```

**Search 2: "visual layout and styling"**
```
Expected: Finds CSS Flexbox
```

**Search 3: "component rendering and updates"**
```
Expected: Finds lifecycle + hooks
```

**Search 4: "type checking"**
```
Expected: Finds TypeScript
```

---

### Step 13: Smart Paste for Specific Task

Scenario: You're working on a login page

**Query**: `authentication and API requests`

**Expected Context**:
```
[Session Context: React Learning ⚛️ - Filtered by: "authentication and API requests"]

Relevant Context:

1. [REST API with JWT tokens]
2. [useEffect for data fetching]

[End Session Context]
```

Notice: Skips CSS, TypeScript basics, and state management!

---

## Test Flow 4: Verify Embeddings

### Step 14: Check Database

Run this in **Supabase SQL Editor**:

```sql
SELECT
    id,
    LEFT(processed_text, 50) as text_preview,
    CASE
        WHEN embedding IS NOT NULL THEN 'Has embedding ✓'
        ELSE 'Missing embedding ✗'
    END as embedding_status
FROM session_memories
ORDER BY created_at DESC
LIMIT 10;
```

**Expected**: All recent memories should show "Has embedding ✓"

---

### Step 15: Check Embedding Dimensions

```sql
SELECT
    id,
    array_length(embedding, 1) as dimensions
FROM session_memories
WHERE embedding IS NOT NULL
LIMIT 5;
```

**Expected**: All should show `1536` (OpenAI embedding size)

---

## Test Flow 5: Edge Cases

### Step 16: Very Short Text

**Endpoint**: `POST /smart-copy`

```json
{
  "text": "npm install react",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

**Expected**:
- Still works (no error)
- Embedding generated even for short text
- Claude might keep it as-is or add minimal summary

---

### Step 17: Search with No Results

**Endpoint**: `GET /search/{session_id}`

**Parameters**:
- `query`: `quantum physics and relativity`
- `mode`: `vector`

**Expected**:
- Returns empty array (no relevant memories)
- No errors

---

### Step 18: Smart Paste with No Matching Context

**Endpoint**: `GET /smart-paste/{session_id}`

**Parameters**:
- `query`: `machine learning and neural networks`
- `limit`: `5`

**Expected**:
- Still returns results (fallback to recent memories)
- Or returns empty if threshold too high

---

## Success Checklist

After running all tests, verify:

- [ ] Smart Copy generates embeddings (check logs)
- [ ] Embeddings visible in Supabase (run SQL query)
- [ ] All embeddings are 1536 dimensions
- [ ] Vector search finds semantically related content
- [ ] Vector search better than text search
- [ ] Smart Paste with query filters correctly
- [ ] Smart Paste without query shows recent memories
- [ ] Search handles "no results" gracefully
- [ ] Short text doesn't cause errors
- [ ] Server logs show "Generated embedding for..."

---

## Debugging

### If embeddings aren't generated:

1. **Check logs** for OpenRouter errors:
   ```
   [ERROR] OpenAI embedding error: ...
   ```

2. **Verify API key** in `.env`:
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

3. **Check OpenRouter dashboard**:
   - Go to https://openrouter.ai/activity
   - See if requests are coming through

4. **Test embedding service directly**:
   ```python
   # In Python shell
   from app.services.embeddings import embedding_service
   import asyncio

   result = asyncio.run(embedding_service.create_embedding("test"))
   print(len(result))  # Should be 1536
   ```

---

### If search returns no results:

1. **Check memories have embeddings**:
   ```sql
   SELECT COUNT(*) FROM session_memories WHERE embedding IS NOT NULL;
   ```

2. **Lower the threshold**:
   ```
   Try match_threshold=0.1 (very permissive)
   ```

3. **Check vector index exists**:
   ```sql
   SELECT indexname FROM pg_indexes
   WHERE indexname = 'idx_memories_embedding';
   ```

---

## Performance Check

Expected times:
- Smart Copy: 2-5 seconds (Claude + embedding)
- Smart Paste (no query): 200-500ms
- Smart Paste (with query): 300-700ms (embedding + search)
- Search: 100-300ms

If slower:
- Check Supabase region (latency)
- Check OpenRouter status
- Check if index is being used

---

## Advanced Tests

### Test Multilingual (Bonus)

Try adding a memory in another language:

```json
{
  "text": "Les hooks de React permettent d'utiliser l'état dans les composants fonctionnels. useState gère l'état local.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

Search in English: `state management`

**Expected**: Should find the French memory too! (Embeddings work cross-language)

---

### Test with Code (Bonus)

Add a memory with code:

```json
{
  "text": "Here's a custom hook for fetching data:\n\n```javascript\nfunction useFetch(url) {\n  const [data, setData] = useState(null);\n  useEffect(() => {\n    fetch(url).then(r => r.json()).then(setData);\n  }, [url]);\n  return data;\n}\n```\nThis hook encapsulates data fetching logic and handles state updates automatically.",
  "session_id": "session-abc-123",
  "user_id": "vector-test-user"
}
```

Search: `custom hooks for API calls`

**Expected**: Finds this memory!

---

## What Good Results Look Like

### Vector Search Results:

```json
{
  "results": [
    {
      "id": "xxx",
      "processed_text": "React Hooks...",
      "relevance_score": 0.87  // ← High = very relevant
    },
    {
      "id": "yyy",
      "processed_text": "State management...",
      "relevance_score": 0.82  // ← Still relevant
    },
    {
      "id": "zzz",
      "processed_text": "CSS Flexbox...",
      "relevance_score": 0.12  // ← Low = not relevant
    }
  ],
  "total": 3
}
```

### Smart Paste Results:

```
[Session Context: React Learning ⚛️ - Filtered by: "hooks"]

Relevant Context:

1. **React Hooks Summary:**
   - useState: manages state
   - useEffect: handles side effects
   ...

2. **Custom Hooks Pattern:**
   - useFetch hook example
   - Encapsulates logic
   ...

[End Session Context]
```

---

## Next Steps

After successful testing:

1. ✅ Vector search works → Use in Mac app
2. ✅ Smart paste filtering works → Add query UI
3. ✅ All embeddings generated → You're ready!

---

**Happy Testing! 🚀**

If anything doesn't work as expected, check:
1. Server logs for errors
2. Supabase SQL editor (embedding column populated?)
3. OpenRouter dashboard (requests going through?)
