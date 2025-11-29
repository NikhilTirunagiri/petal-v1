# Petal Backend - Complete Documentation for Cursor

## Project Overview

Petal is a context management system with a Python FastAPI backend that manages:
1. **Sessions** - Project-specific contexts stored in Supabase
2. **Personal Memories** - User preferences/info stored in Mem0
3. **Smart Processing** - Claude API for text summarization

---

## System Architecture

```
┌─────────────────┐
│   Mac App       │
│   (Client)      │
└────────┬────────┘
         │ HTTP REST API
         │
┌────────▼────────┐
│ FastAPI Backend │
│   (Python)      │
└────────┬────────┘
         │
    ┌────┼────┐
    │    │    │
┌───▼┐ ┌─▼─┐ ┌▼────┐
│Supa│ │Mem│ │Claude│
│base│ │0  │ │ API  │
└────┘ └───┘ └──────┘
```

---

## Core Functionality

### 1. Sessions (Supabase)
- Users can create multiple sessions (projects)
- Each session stores processed memories
- Sessions are isolated by user_id

### 2. Smart Copy (Option+C)
- User copies text → Backend processes with Claude → Saves to active session
- Processing = Summarize while retaining important details
- Original + processed text both stored

### 3. Smart Paste (Option+V)
- Retrieves ALL memories from active session
- Formats in structured way
- Returns formatted text for injection

### 4. Personal Memory (Option+M)
- Stores to Mem0 (global user context)
- Long-term preferences, facts about user
- Separate from session-specific data

---

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: Supabase (PostgreSQL)
- **Memory Store**: Mem0 API
- **AI Processing**: Claude API (Anthropic)
- **Server**: Uvicorn (ASGI)

---

## Database Schema (Supabase)

### Table: `sessions`
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '📁',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
```

### Table: `session_memories`
```sql
CREATE TABLE session_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    processed_text TEXT NOT NULL,
    source TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_memories_session ON session_memories(session_id);
CREATE INDEX idx_memories_user ON session_memories(user_id);
```

---

## API Endpoints Specification

### Base URL: `http://localhost:8000`

---

### 1. Health Check

**GET** `/health`

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

---

### 2. Create Session

**POST** `/sessions`

**Request Body:**
```json
{
    "user_id": "user-123",
    "name": "Website Project",
    "icon": "🌐",
    "description": "Next.js portfolio website"
}
```

**Response:**
```json
{
    "id": "uuid-here",
    "user_id": "user-123",
    "name": "Website Project",
    "icon": "🌐",
    "description": "Next.js portfolio website",
    "created_at": "2025-01-01T00:00:00Z"
}
```

---

### 3. Get All Sessions for User

**GET** `/sessions/{user_id}`

**Response:**
```json
[
    {
        "id": "uuid-1",
        "name": "Website Project",
        "icon": "🌐",
        "created_at": "2025-01-01T00:00:00Z"
    },
    {
        "id": "uuid-2",
        "name": "CS 484 Homework",
        "icon": "📚",
        "created_at": "2025-01-02T00:00:00Z"
    }
]
```

---

### 4. Get Single Session

**GET** `/sessions/detail/{session_id}`

**Response:**
```json
{
    "id": "uuid-here",
    "name": "Website Project",
    "icon": "🌐",
    "description": "Next.js portfolio website",
    "memory_count": 5,
    "created_at": "2025-01-01T00:00:00Z"
}
```

---

### 5. Update Session

**PUT** `/sessions/{session_id}`

**Request Body:**
```json
{
    "name": "Portfolio Website (Updated)",
    "icon": "✨",
    "description": "Updated description"
}
```

**Response:**
```json
{
    "id": "uuid-here",
    "name": "Portfolio Website (Updated)",
    "icon": "✨",
    "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### 6. Delete Session

**DELETE** `/sessions/{session_id}`

**Response:**
```json
{
    "status": "deleted",
    "session_id": "uuid-here"
}
```

---

### 7. Smart Copy (Main Feature!)

**POST** `/smart-copy`

**Request Body:**
```json
{
    "text": "To implement Next.js routing, you need to understand the App Router which was introduced in Next.js 13. The App Router uses a file-system based routing where folders define routes. Each folder can contain a page.tsx file...",
    "session_id": "uuid-here",
    "user_id": "user-123"
}
```

**What it does:**
1. Takes long text
2. Sends to Claude API for processing/summarization
3. Saves both original and processed to session_memories table
4. Returns processed version

**Response:**
```json
{
    "status": "saved",
    "memory_id": "uuid-here",
    "original_length": 500,
    "processed_length": 150,
    "processed_text": "Next.js 13+ App Router: File-system routing, folders = routes. Key files: page.tsx (UI), layout.tsx (wrapper). Supports nested routes, dynamic routes with [param]."
}
```

---

### 8. Smart Paste (Main Feature!)

**GET** `/smart-paste/{session_id}`

**What it does:**
1. Gets ALL memories from the session
2. Formats them in structured way
3. Returns ready-to-paste text

**Response:**
```json
{
    "formatted_text": "[Session Context: Website Project 🌐]\n\nSession History:\n\n1. Next.js 13+ App Router: File-system routing...\n\n2. Tailwind CSS setup: Install via npm, configure tailwind.config.js...\n\n[End Session Context]\n",
    "memory_count": 2,
    "session_name": "Website Project"
}
```

---

### 9. Get Session Memories

**GET** `/sessions/{session_id}/memories`

**Query Parameters:**
- `limit` (optional): Number of memories to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
    "memories": [
        {
            "id": "uuid-1",
            "processed_text": "Next.js routing summary...",
            "created_at": "2025-01-01T10:00:00Z"
        },
        {
            "id": "uuid-2",
            "processed_text": "Tailwind setup summary...",
            "created_at": "2025-01-01T11:00:00Z"
        }
    ],
    "total": 2
}
```

---

### 10. Delete Memory

**DELETE** `/memories/{memory_id}`

**Response:**
```json
{
    "status": "deleted",
    "memory_id": "uuid-here"
}
```

---

### 11. Add to Personal Memory (Mem0)

**POST** `/memory/add`

**Request Body:**
```json
{
    "text": "I prefer TypeScript over JavaScript",
    "user_id": "user-123"
}
```

**What it does:**
- Sends to Mem0 API for storage
- Mem0 handles categorization
- This is for long-term personal facts

**Response:**
```json
{
    "status": "added",
    "message": "Added to personal memory"
}
```

---

### 12. Get Personal Memories

**GET** `/memory/{user_id}`

**Response:**
```json
{
    "memories": [
        {
            "id": "mem0-id-1",
            "text": "User prefers TypeScript",
            "category": "preference"
        },
        {
            "id": "mem0-id-2",
            "text": "User is a CS student at GMU",
            "category": "fact"
        }
    ]
}
```

---

### 13. Search in Session

**GET** `/search/{session_id}`

**Query Parameters:**
- `query` (required): Search term

**Response:**
```json
{
    "results": [
        {
            "id": "uuid-1",
            "processed_text": "Next.js routing with App Router...",
            "relevance_score": 0.95
        }
    ],
    "total": 1
}
```

---

## Environment Variables

Create `.env` file:

```env
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Mem0
MEM0_API_KEY=your-mem0-api-key

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Project Structure

```
 I backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore file
├── README.md              # Setup instructions
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models (request/response)
│   ├── database.py        # Supabase client
│   ├── services/
│   │   ├── __init__.py
│   │   ├── claude.py      # Claude API service
│   │   ├── mem0.py        # Mem0 API service
│   │   └── sessions.py    # Session management logic
│   └── routes/
│       ├── __init__.py
│       ├── sessions.py    # Session endpoints
│       ├── memories.py    # Memory endpoints
│       └── health.py      # Health check
└── tests/
    ├── __init__.py
    └── test_api.py        # API tests
```

---

## Key Implementation Details

### Processing with Claude

**Prompt Template:**
```
Summarize this text concisely while retaining ALL important information, 
technical details, code snippets, decisions, and actionable items. 

Rules:
- Keep it under 300 words
- Preserve technical terms exactly
- Keep code examples if present
- Maintain decision points
- Remove redundancy and fluff

Text:
{original_text}

Concise Summary:
```

**Token Limits:**
- Max input: 10,000 tokens (~7,500 words)
- Max output: 500 tokens (~375 words)
- Model: claude-sonnet-4-20250514

---

### Smart Paste Formatting

**Template:**
```
[Session Context: {session_name} {session_icon}]

Session History:

1. {first_memory_processed_text}

2. {second_memory_processed_text}

3. {third_memory_processed_text}

...

[End Session Context]
```

---

## Error Handling

All endpoints should return consistent error format:

```json
{
    "error": "Error message here",
    "detail": "Detailed error information",
    "status_code": 400
}
```

**Common Error Codes:**
- `400` - Bad request (invalid input)
- `404` - Resource not found
- `500` - Internal server error
- `503` - External service unavailable (Claude/Mem0/Supabase)

---

## Rate Limiting

Implement basic rate limiting:
- 100 requests per minute per user_id
- 10 smart-copy requests per minute per user_id (expensive)

---

## Logging

Log format:
```
[2025-01-01 10:00:00] [INFO] [endpoint=/smart-copy] [user=user-123] Processing text of length 500
[2025-01-01 10:00:01] [INFO] [endpoint=/smart-copy] [user=user-123] Claude processing completed: 150 tokens
[2025-01-01 10:00:01] [INFO] [endpoint=/smart-copy] [user=user-123] Saved to session: uuid-here
```

---

## Testing Requirements

### Unit Tests
- Test each service independently
- Mock external APIs (Claude, Mem0, Supabase)

### Integration Tests
- Test full flow: create session → smart copy → smart paste
- Test error scenarios

### CLI Testing (Initial)
Use `curl` or `httpie` to test each endpoint manually.

---

## Performance Requirements

- API response time < 2 seconds (except smart-copy which may take 3-5s)
- Handle 100 concurrent requests
- Claude processing queue if needed

---

## Security Considerations

1. **API Key Management**
   - Never expose in responses
   - Load from environment only
   - Rotate regularly

2. **User Isolation**
   - Always filter by user_id
   - Validate user_id on every request

3. **Input Validation**
   - Sanitize all inputs
   - Limit text size (max 50KB per request)
   - Validate UUIDs

4. **CORS**
   - Allow only specific origins in production
   - Development: allow localhost

---

## Dependencies (requirements.txt)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# External APIs
anthropic==0.8.1
mem0ai==0.0.10
supabase==2.3.0

# Utilities
httpx==0.25.2
python-multipart==0.0.6
```

---

## Cursor AI Prompts to Use

### 1. Generate Initial Structure
```
Create a FastAPI project with the following structure:
- main.py with FastAPI app
- app/config.py for environment configuration
- app/models.py for Pydantic models
- app/database.py for Supabase client initialization
- app/services/ directory with claude.py, mem0.py, sessions.py
- app/routes/ directory with sessions.py, memories.py, health.py

Use Python 3.10+ type hints and async/await.
```

### 2. Implement Smart Copy
```
Implement the /smart-copy endpoint that:
1. Accepts text, session_id, user_id
2. Calls Claude API to summarize text (keep under 300 words, preserve technical details)
3. Saves original + processed to Supabase session_memories table
4. Returns processed text and metadata

Use the Anthropic SDK with claude-sonnet-4-20250514 model.
```

### 3. Implement Smart Paste
```
Implement the /smart-paste/{session_id} endpoint that:
1. Fetches ALL memories from session_memories table for the session
2. Formats them in this template:
[Session Context: {name} {icon}]

Session History:

1. {memory1}
2. {memory2}
...

[End Session Context]

3. Returns formatted_text and memory_count
```

---

## Next Steps After Building

1. **Local Testing**
   - Test with curl/httpie
   - Verify all endpoints work
   - Check error handling

2. **Swift Integration**
   - Create simple APIClient in Swift
   - Test smart-copy and smart-paste flows
   - Build full Mac app

3. **Railway Deployment**
   - Push to GitHub
   - Connect Railway
   - Set environment variables
   - Deploy

4. **Update Mac App**
   - Change base URL to Railway URL
   - Test in production

---

## Success Criteria

✅ All endpoints return correct responses
✅ Claude processing works and summarizes well
✅ Sessions can be created, listed, deleted
✅ Smart copy saves to correct session
✅ Smart paste formats correctly
✅ Mem0 integration works
✅ Error handling is robust
✅ Can test everything via curl

---

## Questions for Cursor to Handle

1. **Supabase Connection**
   - Proper async client initialization
   - Connection pooling
   - Error handling for timeouts

2. **Claude API**
   - Retry logic for failed requests
   - Token counting/limits
   - Cost optimization

3. **Mem0 Integration**
   - Proper API usage
   - Error handling
   - User ID mapping

4. **Data Validation**
   - UUID validation
   - Text length limits
   - SQL injection prevention

---

This documentation should give Cursor everything it needs to build the backend!
