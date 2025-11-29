# ✾ petal

A context-aware memory management system for AI-assisted workflows. Petal helps you capture, organize, and intelligently retrieve information across your projects, making your AI conversations more productive and contextual.

## Overview

Petal is a full-stack application that acts as a second brain for your work. It captures important information as you research, automatically summarizes it using AI, and makes it instantly available when you need it. The system uses semantic search powered by vector embeddings to understand the meaning behind your queries, not just matching keywords.

The project consists of three main components:

- **macOS Menu Bar Application**: A native Swift app that provides global keyboard shortcuts for capturing and retrieving information
- **FastAPI Backend**: A Python-based REST API that handles AI processing, semantic search, and data management
- **Supabase Database**: PostgreSQL database with pgvector extension for vector similarity search

## Key Features

### Smart Copy
Press Option+C on any selected text to capture it. The system automatically summarizes the content using Claude AI while preserving important technical details, then generates a semantic embedding for intelligent retrieval later.

### Smart Paste
Press Option+V to retrieve relevant context from your current session. The system formats all your saved information in a clean, readable structure that you can paste directly into ChatGPT, Claude, or any AI assistant.

### Session Management
Organize your memories into project-specific sessions. Each session maintains its own isolated context, perfect for different projects, courses, or clients.

### Semantic Search
Find information based on meaning, not just keywords. Search for "authentication" and get results about JWT tokens, OAuth flows, password hashing, and session management, even if those exact words weren't in your query.

### Context-Aware Retrieval
Smart Paste can filter memories by topic, giving you exactly the context you need for your current task without information overload.

## Architecture

The system follows a modern client-server architecture:

```
Mac App (Swift/SwiftUI)
          |
          | HTTP REST API
          |
    FastAPI Backend (Python)
          |
    +-----+-----+-------+
    |           |       |
Supabase+Mem0 Claude OpenRouter
(Storage)      (AI)   (Embeddings)
```

### Data Flow

1. User selects text and presses Option+C
2. Mac app captures the text via clipboard
3. Backend processes text through Claude for summarization
4. OpenRouter generates a 1536-dimensional embedding vector
5. Both summary and embedding are stored in Supabase
6. When searching or pasting, the system uses vector similarity to find relevant memories

## Getting Started

### Prerequisites

- macOS 13.0 or later (Ventura+)
- Python 3.10 or later
- Xcode 15.0 or later
- A Supabase account (free tier works)
- Anthropic API key (for Claude)
- OpenRouter API key (for embeddings)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```env
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openrouter-api-key
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
MEM0_API_KEY=your-mem0-api-key
```

5. Set up the database by running the SQL migrations in your Supabase project:
   - First run `supabase_setup.sql` to create the base tables
   - Then run `supabase_migration_pgvector.sql` to add vector search capabilities

6. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Mac App Setup

1. Navigate to the mac-app directory:
```bash
cd mac-app
```

2. Open the Xcode project:
```bash
open petal-mac/petal-mac.xcodeproj
```

3. Configure code signing:
   - Select the petal-mac project in Xcode
   - Go to Signing & Capabilities
   - Select your development team

4. Build and run the project (Command+R)

5. Grant accessibility permissions when prompted:
   - macOS will ask for permission to control your computer
   - This is required for global keyboard shortcuts to work
   - Go to System Settings > Privacy & Security > Accessibility
   - Enable petal-mac

6. Configure the app:
   - Click the flower icon in your menu bar
   - Click the settings gear icon
   - Enter your API URL (default: `http://localhost:8000`)
   - Enter a unique user ID
   - Click "Test Connection" to verify
   - Click "Save Settings"

## Usage

### Creating Your First Session

1. Click the flower icon in your menu bar
2. Click the "+" button next to "All Sessions"
3. Choose an icon (emoji) for your session
4. Enter a descriptive name (e.g., "React Learning" or "Client Project")
5. Optionally add a description
6. Click "Create"

The new session will automatically become your active session.

### Capturing Information

1. Select any text in any application (browser, PDF, email, etc.)
2. Press Option+C
3. Wait for the success notification
4. The text is now summarized and saved to your active session

You can capture as much information as you need. Each piece is automatically processed and ready for retrieval.

### Retrieving Context

When you need to provide context to an AI assistant:

1. Position your cursor in the chat input
2. Press Option+V
3. The system copies formatted context to your clipboard
4. Press Command+V to paste it into the chat

The AI assistant now has full context about your project and can provide more accurate, relevant assistance.

### Searching Memories

You can search within a session using semantic search. This is available through the API:

```bash
GET /search/{session_id}?query=your-search-term&mode=vector
```

The search understands meaning, so searching for "state management" will find memories about Redux, Context API, hooks, and other related concepts even if those exact words weren't used.

### Switching Sessions

Click any session in the list to make it active. The active session is marked with a checkmark. All Smart Copy operations save to the active session, and Smart Paste retrieves from the active session.

### Managing Sessions

To delete a session:
1. Hover over the session in the list
2. Click the trash icon that appears
3. Confirm the deletion

Note that deleting a session also deletes all memories within it. This action cannot be undone.

## API Documentation

The backend provides a RESTful API with the following main endpoints:

### Health Check
```
GET /health
```
Returns the API status and version.

### Session Management
```
POST /sessions
GET /sessions/{user_id}
GET /sessions/detail/{session_id}
PUT /sessions/{session_id}
DELETE /sessions/{session_id}
```

### Memory Operations
```
POST /smart-copy
GET /smart-paste/{session_id}
GET /sessions/{session_id}/memories
DELETE /memories/{memory_id}
GET /search/{session_id}
```

### Personal Memory
```
POST /memory/add
GET /memory/{user_id}
```

Full API documentation with request/response examples is available at `http://localhost:8000/docs` when the server is running.

## Project Structure

```
Petal/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic and external integrations
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database client
│   │   └── models.py          # Request/response models
│   ├── main.py                # Application entry point
│   ├── requirements.txt       # Python dependencies
│   ├── supabase_setup.sql     # Database schema
│   └── supabase_migration_pgvector.sql  # Vector search setup
│
├── mac-app/                   # macOS menu bar application
│   └── petal-mac/
│       └── petal-mac/
│           ├── petal_macApp.swift      # App entry point
│           ├── Models.swift            # Data models
│           ├── APIService.swift        # Backend communication
│           ├── SessionManager.swift    # State management
│           ├── HotKeyManager.swift     # Keyboard shortcuts
│           ├── MenuBarView.swift       # Main UI
│           └── SettingsView.swift      # Settings interface
│
├── browser-extension/         # Future: Chrome/Firefox extension
├── electron-app/             # Future: Cross-platform desktop app
├── shared/                   # Shared types and constants
└── README.md                 # This file
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Supabase**: Managed PostgreSQL database with real-time capabilities
- **pgvector**: PostgreSQL extension for vector similarity search
- **Anthropic Claude**: AI model for text summarization
- **OpenRouter**: Embedding generation for semantic search
- **Uvicorn**: Lightning-fast ASGI server

### Mac App
- **Swift 5**: Modern, safe programming language for Apple platforms
- **SwiftUI**: Declarative UI framework for native macOS interfaces
- **AppKit**: macOS-specific features like clipboard and notifications
- **Carbon Events API**: System-level keyboard event handling for global shortcuts

### Database
- **PostgreSQL 15+**: Robust, open-source relational database
- **pgvector extension**: Efficient vector storage and similarity search
- **IVFFlat indexing**: Approximate nearest neighbor search for fast queries

## How It Works

### Smart Copy Pipeline

1. User selects text and triggers Option+C hotkey
2. Mac app intercepts the hotkey event via Carbon Events API
3. App simulates Command+C to copy selected text to clipboard
4. App reads clipboard content and sends to backend via POST /smart-copy
5. Backend validates the request and extracts the text
6. Claude API processes the text with a carefully crafted prompt that preserves technical details while removing redundancy
7. OpenRouter generates a 1536-dimensional embedding vector from the processed text
8. Both the original text, summary, and embedding are stored in Supabase
9. Backend returns success response with metadata
10. Mac app displays a notification to confirm the operation

### Smart Paste Pipeline

1. User triggers Option+V hotkey in any application
2. Mac app calls GET /smart-paste/{session_id} endpoint
3. Backend retrieves the current session information
4. If a query parameter is provided, the system:
   - Generates an embedding for the query
   - Performs vector similarity search to find relevant memories
   - Returns memories ranked by semantic relevance
5. If no query is provided, returns the most recent memories chronologically
6. Backend formats the memories into a structured text block
7. Mac app copies the formatted text to clipboard
8. User presses Command+V to paste the context
9. AI assistant receives full context and can provide better assistance

### Semantic Search

The system uses vector embeddings to understand semantic meaning:

1. Each memory is converted to a 1536-dimensional vector that represents its meaning
2. When searching, the query is also converted to a vector
3. PostgreSQL's pgvector extension calculates cosine similarity between vectors
4. Results are ranked by similarity score (0 to 1)
5. Only results above a threshold (typically 0.3-0.5) are returned

This allows the system to find conceptually related information even when exact keywords don't match.

## Configuration

### Environment Variables

The backend requires several environment variables defined in a `.env` file:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access
- `OPENAI_API_KEY`: Your OpenRouter API key for embeddings (uses OpenAI-compatible API)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anonymous key
- `MEM0_API_KEY`: Optional, for personal memory features
- `ENVIRONMENT`: Set to "development" or "production"
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

### Mac App Settings

Stored in UserDefaults and configurable via the Settings window:

- `apiBaseURL`: Backend API URL (default: http://localhost:8000)
- `userId`: Unique identifier for the user
- Connection test results are displayed in real-time

## Performance Considerations

### Response Times
- Health check: ~10ms
- Session operations: 100-300ms
- Smart Copy: 2-5 seconds (includes AI processing)
- Smart Paste: 200-500ms
- Vector search: 100-300ms

### Database Optimization
- Indexed session_id and user_id columns for fast filtering
- IVFFlat index on embedding vectors for approximate nearest neighbor search
- Full-text search index on processed_text for keyword fallback
- Cascade deletion for referential integrity

### API Optimization
- Async/await throughout the backend for non-blocking operations
- Connection pooling for database queries
- Efficient JSON serialization with Pydantic
- Automatic request validation to fail fast on invalid input

## Cost Estimates

For typical personal use (100 smart copies and 500 searches per month):

- Claude API (text summarization): ~$2.00/month
- OpenRouter (embeddings): ~$0.05/month
- Supabase (free tier): $0.00/month
- **Total: ~$2.05/month**

The free tier of Supabase provides 500MB database storage and 2GB bandwidth, which is sufficient for most personal use cases.

## Security

### API Keys
All API keys are stored in environment variables and never exposed in the codebase or responses. The `.env` file is excluded from version control via `.gitignore`.

### User Isolation
All database queries filter by user_id to ensure users can only access their own data. Row-level security policies can be added to Supabase for additional protection.

### Data Storage
- Memories are stored in Supabase with encryption at rest
- All API communication uses HTTPS in production
- Mac app stores settings in secure UserDefaults
- No sensitive data is logged

### Input Validation
- All API requests are validated using Pydantic models
- Text length limits prevent abuse (50KB max per request)
- SQL injection is prevented through parameterized queries
- UUID validation for all ID parameters

## Troubleshooting

### Backend won't start
- Verify Python version is 3.10 or later
- Check that all environment variables are set in `.env`
- Ensure virtual environment is activated
- Review logs for specific error messages

### Mac app hotkeys don't work
- Verify accessibility permissions are granted
- Check System Settings > Privacy & Security > Accessibility
- Restart the app after granting permissions
- Look for error messages in Xcode console

### Cannot connect to backend
- Ensure backend server is running on port 8000
- Test with: `curl http://localhost:8000/health`
- Verify firewall settings aren't blocking connections
- Check the API URL in Mac app settings

### Smart Copy takes too long
- Claude API processing takes 2-5 seconds normally
- Check your internet connection
- Verify Anthropic API key is valid and has quota remaining
- Consider copying smaller chunks of text

### Search returns no results
- Verify the session has memories saved
- Check that embeddings were generated (look for non-null embedding column)
- Try lowering the similarity threshold
- Use text search mode as a fallback

### Database errors
- Verify Supabase project is active
- Check that both SQL migration files were run
- Ensure pgvector extension is enabled
- Review Supabase logs for detailed errors

## Development

### Running Tests

Backend tests (when implemented):
```bash
cd backend
pytest
```

### Code Style

The project follows standard conventions:
- Python: PEP 8 style guide
- Swift: Swift API Design Guidelines
- Async/await patterns throughout
- Type hints in Python code
- Comprehensive error handling

### Contributing

While this is primarily a personal project, contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Ensure code follows existing style
5. Test thoroughly
6. Submit a pull request with a detailed description

## Known Limitations

### Current Version
- macOS only (no Windows or Linux support)
- Requires internet connection for AI processing
- Global hotkeys may conflict with other applications
- English-language focused (UI not localized)
- Limited to 8K tokens per memory for embedding generation

### Future Improvements
- Custom hotkey configuration
- Offline mode with local caching
- Dark mode support for Mac app
- Memory preview on hover
- Bulk operations for memories
- Export/import session data
- Team collaboration features
- Browser extension for web capture
- Mobile app for iOS

## Roadmap

### Version 1.1 (Short-term)
- Implement duplicate detection alerts
- Add cross-session search endpoint
- Memory preview tooltips
- Customizable hotkeys
- Improved error messages

### Version 2.0 (Medium-term)
- Browser extension for Chrome and Firefox
- Web application for cross-platform access
- Memory tagging and categorization
- Advanced filtering options
- Collaborative sessions

### Version 3.0 (Long-term)
- Mobile app for iOS
- LinkedIn profile integration
- Automatic form filling
- Calendar event extraction
- Email integration
- Team workspaces

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

Built with:
- FastAPI by Sebastián Ramírez
- Supabase by Supabase Inc.
- pgvector by Andrew Kane
- Claude API by Anthropic
- OpenRouter for embedding services

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/NikhilTirunagiri/Petal/issues
- Documentation: See the README files in backend/ and mac-app/ directories

## Authors

Developed by Nikhil Tirunagiri, Yasah Sai Chandra Borusu

## Project Status

Active development. The core features are fully implemented and functional. The system is ready for personal use, with ongoing enhancements planned for future releases.
