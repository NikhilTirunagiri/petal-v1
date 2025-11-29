# Petal Backend

FastAPI backend for the Petal context management system.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file and add your API keys:

```env
# You need to add these:
ANTHROPIC_API_KEY="your-actual-anthropic-key"
```

The Supabase and Mem0 keys are already configured.

### 3. Run the Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "name": "My First Project",
    "icon": "🚀",
    "description": "Testing the backend"
  }'
```

### Smart Copy (requires Anthropic API key)
```bash
curl -X POST http://localhost:8000/smart-copy \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text to process here...",
    "session_id": "SESSION_ID_FROM_ABOVE",
    "user_id": "test-user-123"
  }'
```

### Smart Paste
```bash
curl http://localhost:8000/smart-paste/SESSION_ID
```

## Architecture

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── app/
│   ├── config.py          # Configuration
│   ├── models.py          # Pydantic models
│   ├── database.py        # Supabase client
│   ├── services/          # Business logic
│   │   ├── claude.py      # Claude API
│   │   ├── mem0_service.py # Mem0 API
│   │   └── sessions.py    # Session management
│   └── routes/            # API endpoints
│       ├── health.py      # Health check
│       ├── sessions.py    # Session CRUD
│       └── memories.py    # Smart copy/paste
└── tests/                 # Tests
```

## Features Implemented

- ✅ Sessions CRUD
- ✅ Smart Copy (Claude processing)
- ✅ Smart Paste (formatted context)
- ✅ Personal Memory (Mem0)
- ✅ Search in sessions
- ✅ Full-text search support

## Next Steps

1. Get Anthropic API key and add to `.env`
2. Test all endpoints with curl
3. Build Mac app to connect to this backend
