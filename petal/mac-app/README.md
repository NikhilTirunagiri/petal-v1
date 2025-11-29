# Petal Mac App

A beautiful menu bar app for macOS that brings context-aware memory to your AI workflows.

## Features

- **Smart Copy (⌥C)**: Capture selected text and save it to your current session with AI summarization
- **Smart Paste (⌥V)**: Inject relevant context from your session directly into any application
- **Personal Memory (⌥M)**: Save important information to your personal knowledge base
- **Session Management**: Organize your memories into project-specific sessions
- **Semantic Search**: Find relevant context using vector embeddings (powered by pgvector)

## Prerequisites

1. **macOS 13.0 or later** (Ventura+)
2. **Xcode 15.0 or later**
3. **Petal Backend running** (see `backend/README.md`)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/NikhilTirunagiri/Petal
cd Petal/mac-app
```

### 2. Open in Xcode

```bash
open petal-mac/petal-mac.xcodeproj
```

### 3. Configure Signing

1. Select the `petal-mac` project in Xcode
2. Go to **Signing & Capabilities**
3. Select your **Team** (Personal or Organization)
4. Xcode will automatically handle the signing

### 4. Enable Required Capabilities

The app requires these entitlements (already configured):

- ✅ **Network Client** - To communicate with the backend API
- ✅ **User Selected Files** - For file operations
- ✅ **Accessibility** - For global hotkeys

### 5. Grant Accessibility Permissions

When you first run the app, macOS will prompt you to grant Accessibility permissions.

**If you miss the prompt:**

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Find **petal-mac** in the list
3. Enable the toggle

This is required for global hotkeys (⌥C, ⌥V, etc.) to work system-wide.

### 6. Configure the Backend

1. Make sure your backend is running at `http://localhost:8000`
2. Open the Petal menu bar app
3. Click the **Settings** gear icon
4. Enter your API URL and User ID
5. Click **Test Connection** to verify
6. Click **Save Settings**

## Usage

### First Time Setup

1. Launch the app - you'll see a flower icon in your menu bar
2. Click the flower icon to open the menu
3. Create your first session:
   - Click the **+** button next to "All Sessions"
   - Choose an emoji icon
   - Enter a session name (e.g., "My Project")
   - Click **Create**

### Smart Copy (⌥C)

1. Select any text in any application
2. Press **⌥C** (Option + C)
3. The text is:
   - Summarized by Claude AI
   - Embedded with vector search
   - Saved to your current session
4. You'll see a notification confirming success

### Smart Paste (⌥V)

1. Position your cursor where you want to paste context
2. Press **⌥V** (Option + V)
3. The app:
   - Retrieves relevant memories from your current session
   - Formats them as context
   - Copies to your clipboard
4. Paste (Cmd+V) into your AI assistant chat

### Personal Memory (⌥M)

1. Select important text you want to remember long-term
2. Press **⌥M** (Option + M)
3. Saved to your personal knowledge base (persists across sessions)

### Session Management

**Switch Sessions:**
- Click any session in the list to make it active
- The current session shows a checkmark

**Delete Sessions:**
- Hover over a session
- Click the trash icon that appears

**Create Sessions:**
- Click the **+** button
- Perfect for organizing by project, client, or topic

### Other Hotkeys

- **⌥S** - Show sessions list (coming soon)
- **⌥O** - Open menu bar popup (coming soon)

## File Structure

```
mac-app/petal-mac/petal-mac/
├── petal_macApp.swift          # App entry point & hotkey setup
├── Models.swift                # Data models for API
├── APIService.swift            # Backend communication
├── SessionManager.swift        # State management & business logic
├── HotKeyManager.swift         # Global keyboard shortcuts
├── MenuBarView.swift           # Main menu UI
├── SettingsView.swift          # Settings & configuration
└── Assets.xcassets/            # App icons & resources
```

## Architecture

```
┌─────────────────────────┐
│   Menu Bar Icon         │
│   (Flower 🌸)          │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│   MenuBarView           │
│   - Session List        │
│   - Quick Actions       │
│   - Create Session      │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│   SessionManager        │
│   - State Management    │
│   - API Calls           │
│   - Clipboard Ops       │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│   APIService            │
│   - HTTP Client         │
│   - JSON Encoding       │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│   Backend (FastAPI)     │
│   localhost:8000        │
└─────────────────────────┘
```

## Troubleshooting

### Hotkeys Don't Work

**Problem**: Pressing ⌥C or ⌥V does nothing

**Solution**:
1. Check accessibility permissions in System Settings
2. Look for console logs when pressing hotkeys
3. Restart the app after granting permissions

### "Connection Failed" Error

**Problem**: Can't connect to backend

**Solution**:
1. Make sure backend is running: `cd backend && python main.py`
2. Check the URL in Settings (default: `http://localhost:8000`)
3. Test with: `curl http://localhost:8000/health`

### No Sessions Appear

**Problem**: Sessions list is empty

**Solution**:
1. Check backend logs for errors
2. Verify Supabase connection in backend
3. Create a test session via Swagger UI first

### Smart Copy Takes Too Long

**Problem**: Long delay after pressing ⌥C

**Reasons**:
- Claude API summarization takes 2-5 seconds
- OpenRouter embedding generation adds 1-2 seconds
- This is normal for the first copy

**Tips**:
- Only copy relevant text (not entire files)
- Backend caches embeddings for faster repeat searches

### Clipboard Issues

**Problem**: Smart Paste doesn't paste anything

**Solution**:
1. Check if context was copied (check clipboard)
2. Look for error notifications
3. Ensure current session has memories
4. Verify backend is reachable

## Development

### Building from Source

```bash
# Open in Xcode
open petal-mac/petal-mac.xcodeproj

# Or build from command line
xcodebuild -project petal-mac/petal-mac.xcodeproj -scheme petal-mac -configuration Debug
```

### Debugging

1. Run in Xcode with debugger attached
2. Check console logs (View → Debug Area → Show Debug Area)
3. Look for log messages:
   - `✅ HotKey manager initialized`
   - `Smart Copy triggered with text: ...`
   - `Smart Paste triggered`

### Adding New Features

**To add a new hotkey:**
1. Register it in `HotKeyManager.swift`
2. Add handler method
3. Update `AppSettings` in `Models.swift`
4. Add UI in `SettingsView.swift`

**To add a new API endpoint:**
1. Add method in `APIService.swift`
2. Call it from `SessionManager.swift`
3. Update UI to trigger it

## API Integration

The app communicates with the backend via REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/sessions/{userId}` | GET | Get all sessions |
| `/sessions` | POST | Create session |
| `/sessions/{sessionId}` | DELETE | Delete session |
| `/smart-copy` | POST | Save memory with AI |
| `/smart-paste/{sessionId}` | GET | Get context |
| `/search/{sessionId}` | GET | Semantic search |

See `backend/BACKEND_DOCUMENTATION.md` for full API spec.

## Roadmap

- [ ] In-app search with semantic filtering
- [ ] Cross-session memory search (⌥S)
- [ ] Keyboard shortcut customization
- [ ] Memory preview on hover
- [ ] Export/import sessions
- [ ] Dark mode support
- [ ] Menubar icon customization
- [ ] Smart Paste with query prompt
- [ ] Memory tagging and organization

## Known Issues

1. **First launch delay**: App takes 3-5 seconds to load sessions (fetching from backend)
2. **Hotkey conflicts**: If another app uses ⌥C/⌥V, there may be conflicts
3. **Menu bar icon**: Currently uses SF Symbol (may want custom icon)

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a PR

## License

MIT License - see LICENSE file

## Support

- **Issues**: [GitHub Issues](https://github.com/NikhilTirunagiri/Petal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NikhilTirunagiri/Petal/discussions)

---

**Made with 💜 by Nikhil Tirunagiri**
