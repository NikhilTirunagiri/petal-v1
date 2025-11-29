# Petal Backend - pgvector Setup Guide

This guide walks you through setting up vector search (semantic search) using Supabase pgvector and OpenRouter.

---

## What You're Getting

**Before pgvector:**
- Search: "authentication" → Finds only memories with exact word "authentication"
- Smart Paste: Returns last 10 memories (might not be relevant)

**After pgvector:**
- Search: "authentication" → Finds memories about login, JWT, OAuth, security, etc.
- Smart Paste: Can filter by topic - "Show me everything about auth"
- Cross-session search: Find concepts across ALL your sessions
- Duplicate detection: Avoid saving the same content twice

---

## Prerequisites

1. ✅ Supabase project created (already done)
2. ✅ Backend running locally (already done)
3. 🔲 OpenRouter API key ([Get one here](https://openrouter.ai/keys))

---

## Step 1: Get OpenRouter API Key

1. Go to https://openrouter.ai/keys
2. Sign up / Log in
3. Click "Create Key"
4. Copy your key (starts with `sk-or-...`)
5. Add to `backend/.env`:
   ```env
   OPENAI_API_KEY="sk-or-your-key-here"
   ```

**Cost**: ~$0.05 per 1,000 embeddings (very cheap!)

---

## Step 2: Run SQL Migration in Supabase

1. Open your Supabase project dashboard
2. Go to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the entire contents of `supabase_migration_pgvector.sql`
5. Paste into the editor
6. Click **Run** (or press Cmd/Ctrl + Enter)

**Expected output**:
```
pgvector extension    | Installed ✓
embedding column      | Added ✓
vector index          | Created ✓
```

**What this does**:
- ✅ Enables pgvector extension
- ✅ Adds `embedding` column (vector(1536)) to `session_memories` table
- ✅ Creates vector similarity search functions
- ✅ Creates indexes for fast searches

---

## Step 3: Install New Dependencies

```bash
cd backend
pip install openai>=1.0.0
```

(Already in requirements.txt, but run this to be sure)

---

## Step 4: Restart the Server

```bash
# Kill the current server (Ctrl+C)
python main.py
```

The server should start without errors.

---

## Step 5: Migrate Existing Memories (Optional)

If you already have memories in the database, run the migration script:

```bash
python migrate_embeddings.py
```

**What it does**:
- Finds all memories without embeddings
- Generates embeddings using OpenRouter
- Updates the database
- Shows progress

**Output example**:
```
Found 25 memories without embeddings
Processing batch 1/1
Progress: 10/25 completed
Progress: 20/25 completed
==================================================
Migration complete!
✓ Successful: 25
✗ Failed: 0
Total processed: 25/25
==================================================
```

---

## Step 6: Test Vector Search

### Test 1: Smart Copy (Auto-generates embeddings)

```bash
curl -X POST http://localhost:8000/smart-copy \
  -H "Content-Type: application/json" \
  -d '{
    "text": "React hooks let you use state in function components. useState manages state, useEffect handles side effects.",
    "session_id": "YOUR_SESSION_ID",
    "user_id": "test-user"
  }'
```

**Expected**: Returns successfully with `memory_id`

**Behind the scenes**:
1. Claude summarizes the text
2. OpenRouter generates embedding (1536-dimension vector)
3. Both saved to database

---

### Test 2: Semantic Search

```bash
# Search for "state management"
# Should find the React hooks memory above, even though it doesn't contain those exact words!
curl "http://localhost:8000/search/YOUR_SESSION_ID?query=state%20management&mode=vector"
```

**Expected**: Returns the React hooks memory with high relevance score

**Try this**:
- Add memory about "Redux for global state"
- Add memory about "Context API for theme switching"
- Search for "state" → Should find all three!

---

### Test 3: Smart Paste with Context

```bash
# Default: Last 10 memories
curl "http://localhost:8000/smart-paste/YOUR_SESSION_ID"

# With topic filter: Only memories about hooks
curl "http://localhost:8000/smart-paste/YOUR_SESSION_ID?query=hooks&limit=5"
```

**Expected**:
- Without query: Recent memories
- With query: Most relevant memories about "hooks"

---

## How It Works

### Architecture

```
User copies text
    ↓
POST /smart-copy
    ↓
├─> Claude: "React hooks let..." → "Hooks: useState for state..."
├─> OpenRouter: Text → [0.123, 0.456, ..., 0.789] (1536 numbers)
    ↓
Saved to Supabase:
├─> processed_text: "Hooks: useState for state..."
└─> embedding: vector(1536)
```

### When User Searches

```
GET /search/session-id?query="state management"
    ↓
OpenRouter: "state management" → [0.111, 0.222, ..., 0.333]
    ↓
Supabase pgvector: Find similar vectors
    ↓
Returns: Memories about state, hooks, redux, context
```

---

## API Changes

### Smart Paste (Enhanced)

**Before**:
```
GET /smart-paste/{session_id}
→ Returns last 1000 memories
```

**After**:
```
GET /smart-paste/{session_id}?query=authentication&limit=10
→ Returns 10 most relevant memories about authentication
```

---

### Search (Enhanced)

**Before**:
```
GET /search/{session_id}?query=JWT
→ Text search only
```

**After**:
```
GET /search/{session_id}?query=JWT&mode=vector&limit=10
→ Semantic search (default)

GET /search/{session_id}?query=JWT&mode=text
→ Old text search (fallback)
```

---

## New Features Unlocked

### 1. Context-Aware Smart Paste

```python
# Mac app can detect current file
if editing "LoginPage.tsx":
    smart_paste(session_id, query="authentication login")

if editing "PaymentPage.tsx":
    smart_paste(session_id, query="payment stripe checkout")
```

### 2. Cross-Session Search (Future)

```bash
POST /search/cross-session
{
  "user_id": "user-123",
  "query": "react hooks"
}
→ Finds hooks info across ALL sessions
```

### 3. Duplicate Detection (Future)

```python
# Before saving, check if similar content exists
if similarity > 0.95:
    "You already saved this!"
```

---

## Cost Analysis

### OpenRouter Pricing

| Operation | Tokens | Cost | Example |
|-----------|--------|------|---------|
| 1 embedding | ~100 | $0.00002 | One memory |
| 50 embeddings | ~5K | $0.001 | Typical session |
| 1,000 embeddings | ~100K | $0.02 | Heavy user/month |

**Realistic cost**: $0.05-0.10 per user per month

---

## Troubleshooting

### Error: "pgvector extension not found"
**Solution**: Run the SQL migration in Supabase SQL Editor

### Error: "OpenAI API key not found"
**Solution**: Add OpenRouter key to `.env` as `OPENAI_API_KEY`

### Error: "Failed to generate embedding"
**Solution**:
1. Check OpenRouter API key is valid
2. Check OpenRouter quota/billing
3. Text might be too long (max ~8K words)

### Search returns no results
**Solution**:
1. Memories might not have embeddings yet
2. Run `python migrate_embeddings.py`
3. Or save new memories (auto-generates embeddings)

### Slow performance
**Solution**:
1. Check Supabase index exists: `idx_memories_embedding`
2. Reduce `limit` parameter
3. Increase `match_threshold` (0.5 instead of 0.3)

---

## Comparison: Text vs Vector Search

### Example Session:
```
Memory 1: "JWT tokens for authentication"
Memory 2: "OAuth2 login flow"
Memory 3: "Password hashing with bcrypt"
Memory 4: "CSS flexbox layout"
Memory 5: "React component styling"
```

### Search: "user security"

**Text Search**:
- No results (exact match only)

**Vector Search**:
- ✅ Memory 1: 0.89 similarity (JWT tokens)
- ✅ Memory 2: 0.85 similarity (OAuth2)
- ✅ Memory 3: 0.92 similarity (Password hashing)
- ❌ Memory 4: 0.12 similarity (CSS)
- ❌ Memory 5: 0.15 similarity (React)

**Result**: Finds relevant security content, ignores CSS/styling

---

## Monitoring

### Check Embedding Coverage

```sql
-- Run in Supabase SQL Editor
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
    COUNT(*) as total
FROM session_memories;
```

### Find Memories Without Embeddings

```sql
SELECT id, processed_text, created_at
FROM session_memories
WHERE embedding IS NULL
ORDER BY created_at DESC
LIMIT 10;
```

---

## Next Steps

1. ✅ **Test basic search** - Try semantic search in Swagger UI
2. ✅ **Test smart paste** - Use query parameter
3. 🔲 **Build Mac app integration** - Use these endpoints
4. 🔲 **Deploy to Railway** - Everything will work in production

---

## Performance Tips

1. **Batch embeddings**: If migrating >1000 memories, use batch API
2. **Cache query embeddings**: Same query → reuse embedding
3. **Adjust threshold**: Higher threshold (0.7) = stricter matches
4. **Limit results**: 10-20 results is usually enough

---

## FAQ

**Q: Can I use direct OpenAI instead of OpenRouter?**
A: Yes! Change `base_url` in `app/services/embeddings.py` to use OpenAI directly. Cost is similar.

**Q: What if OpenRouter is down?**
A: System falls back to text search automatically. Memories still save without embeddings.

**Q: Can I change the embedding model?**
A: Yes! Update `self.model` in `embeddings.py`. Make sure to update `self.dimensions` too.

**Q: Do I need to regenerate embeddings if I change models?**
A: Yes, different models create different-sized vectors.

---

**Setup complete! 🎉**

You now have semantic search powered by pgvector and OpenRouter.

Test it out in Swagger UI: `http://localhost:8000/docs`
