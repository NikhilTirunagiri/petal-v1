# Memory Assistant MVP - Complete Build Plan

## Project Overview

A personal memory/context management system that stores user information and intelligently injects it into AI conversations (Claude, ChatGPT) and form fields.

---

## 🎯 MVP Features

### Mac Menu Bar App (Swift)
- **Option+M** → Capture selected text to queue
- **Option+O** → Open review popup
- Menu bar icon shows queue count (🧠 3)
- AI categorizes each memory (Fact/Preference/Episode/Semantic)
- Real-time deduplication check
- Save to Supabase

### Browser Extension (React/TypeScript)
- Works on Claude.ai & ChatGPT
- Sidebar shows relevant memories based on conversation
- Select + inject memories into conversation
- Quick search all memories

### Backend (Supabase)
- Auth + Row Level Security (RLS)
- Postgres with vector embeddings (pgvector)
- Memory storage with categories
- Edge functions for AI operations

### AI Layer
- Claude API for categorization + similarity matching
- Vector embeddings for semantic search

---

## Phase 2 Features (Later)
- LinkedIn auto-sync
- Form autofill
- Advanced encryption
- Calendar integration
- Email signature extraction

---

## 📋 Build Plan

### PHASE 1: Setup & Infrastructure (1-2 hours)

#### 1.1 Supabase Setup
- [ ] Create Supabase project
- [ ] Enable Vector extension (`pgvector`)
- [ ] Set up authentication (email/password)
- [ ] Configure Row Level Security (RLS)
- [ ] Get API keys (anon, service role)

#### 1.2 Development Environment
- [ ] Create GitHub repo
- [ ] Set up project structure:
  ```
  /memory-app
    /mac-app          # Swift project
    /browser-extension # React/TypeScript
    /supabase         # Schema & migrations
    /shared           # Types, constants
    README.md
    .gitignore
  ```
- [ ] Install dependencies
- [ ] Set up environment variables

---

### PHASE 2: Database Schema (1 hour)

#### 2.1 Create Tables

**memories table:**
```sql
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  content TEXT NOT NULL,
  category TEXT CHECK (category IN ('fact', 'preference', 'episode', 'semantic')),
  embedding VECTOR(1536), -- for Claude/OpenAI embeddings
  source TEXT, -- 'manual', 'email', 'bookmark', 'linkedin'
  metadata JSONB DEFAULT '{}',
  is_processed BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON memories (user_id, created_at);
CREATE INDEX ON memories (user_id, category);
```

**memory_queue table (for unprocessed captures):**
```sql
CREATE TABLE memory_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  content TEXT NOT NULL,
  captured_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON memory_queue (user_id, captured_at);
```

**linkedin_profiles table (for Phase 2):**
```sql
CREATE TABLE linkedin_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL UNIQUE,
  profile_url TEXT NOT NULL,
  last_scraped TIMESTAMP,
  raw_data JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2.2 RLS Policies
```sql
-- Users can only see their own memories
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own memories" ON memories
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users insert own memories" ON memories
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users update own memories" ON memories
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users delete own memories" ON memories
  FOR DELETE USING (auth.uid() = user_id);

-- Same for queue
ALTER TABLE memory_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own queue" ON memory_queue
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users insert own queue" ON memory_queue
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users delete own queue" ON memory_queue
  FOR DELETE USING (auth.uid() = user_id);
```

#### 2.3 Supabase Edge Functions
- [ ] Create `categorize-memory` function (calls Claude API)
- [ ] Create `check-duplicate` function (vector similarity search)
- [ ] Create `process-queue` function (batch processing)
- [ ] Create `search-memories` function (semantic search)

**Example: categorize-memory function**
```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import Anthropic from '@anthropic-ai/sdk'

serve(async (req) => {
  const { content } = await req.json()
  
  const anthropic = new Anthropic({
    apiKey: Deno.env.get('ANTHROPIC_API_KEY'),
  })
  
  const message = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 100,
    messages: [{
      role: 'user',
      content: `Categorize this memory into exactly one of these categories: fact, preference, episode, semantic.

Memory: "${content}"

Respond with ONLY the category name, nothing else.`
    }]
  })
  
  const category = message.content[0].text.trim().toLowerCase()
  
  return new Response(JSON.stringify({ category }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

---

### PHASE 3: Mac Menu Bar App (6-8 hours)

#### 3.1 Project Setup (30 min)
- [ ] Create new Swift project (macOS App)
- [ ] Set minimum deployment target: macOS 13.0+
- [ ] Add dependencies via Swift Package Manager:
  - Supabase Swift SDK (or custom REST client)
  - HotKey library for global shortcuts
  - Sparkle for auto-updates (optional)

#### 3.2 Core Features (3-4 hours)

**3.2.1 Menu Bar Icon**
- [ ] Create NSStatusBar item
- [ ] Design icon (simple brain emoji 🧠 or custom SF Symbol)
- [ ] Add badge count for queue items
- [ ] Click → show menu with:
  - "Review Queue (3)" → Opens review window
  - "Search Memories" → Opens search window
  - "Settings" → Opens preferences
  - "Sign Out"
  - "Quit"

**3.2.2 Global Hotkeys**
- [ ] Register Option+M (capture text)
- [ ] Register Option+O (open review window)
- [ ] Handle accessibility permissions:
  ```swift
  // Check and request accessibility permissions
  let trusted = AXIsProcessTrusted()
  if !trusted {
    // Show alert directing to System Preferences
  }
  ```
- [ ] Show permission prompt on first launch with instructions

**3.2.3 Capture Flow (Option+M)**
```swift
// Pseudo-code implementation
class CaptureManager {
  func captureSelectedText() {
    // 1. Read from pasteboard (clipboard)
    let pasteboard = NSPasteboard.general
    guard let text = pasteboard.string(forType: .string),
          !text.isEmpty else {
      showToast("No text selected")
      return
    }
    
    // 2. Add to local queue
    QueueManager.shared.add(text)
    
    // 3. Update menu bar badge
    StatusBarManager.shared.updateBadgeCount()
    
    // 4. Show success toast
    showToast("Captured ✓")
    
    // 5. Optional: Immediately save to Supabase queue
    Task {
      await SupabaseClient.shared.addToQueue(text)
    }
  }
}
```

**3.2.4 Review Popup Window (Option+O)**
- [ ] Create NSWindow with floating panel style
- [ ] Design UI layout:
  ```
  ┌───────────────────────────────────┐
  │ Review Memories (3)          [×]  │
  ├───────────────────────────────────┤
  │                                   │
  │ ☑ Memory 1:                      │
  │   "John's email: john@ex..."      │
  │   Category: Fact ▼    [Edit] [×] │
  │   ───────────────────────────────│
  │                                   │
  │ ☑ Memory 2:                      │
  │   "Prefers concise responses"     │
  │   Category: Preference ▼ [Edit][×]│
  │   ───────────────────────────────│
  │                                   │
  │ ☐ Memory 3:                      │
  │   "Meeting with Sarah on..."      │
  │   Category: Episode ▼  [Edit] [×] │
  │                                   │
  ├───────────────────────────────────┤
  │ [×] Select All                    │
  │        [Process Selected] [Save All]│
  └───────────────────────────────────┘
  ```

- [ ] Load queue items from Supabase
- [ ] For each item, call AI categorization API
- [ ] Show loading state while categorizing
- [ ] Allow manual category override via dropdown
- [ ] Edit button → opens text editor
- [ ] Delete button (×) → removes from queue
- [ ] "Process Selected" → saves checked items
- [ ] "Save All" → saves all items at once

#### 3.3 AI Integration (2 hours)

**3.3.1 Claude API Client**
```swift
class ClaudeAPIClient {
  private let apiKey: String
  private let baseURL = "https://api.anthropic.com/v1/messages"
  
  func categorizeMemory(_ text: String) async throws -> MemoryCategory {
    let prompt = """
    Categorize this memory into exactly one category:
    - fact: concrete information (names, dates, places, identifiers)
    - preference: likes, dislikes, communication style
    - episode: past events, experiences, conversations
    - semantic: concepts, relationships, domain knowledge
    
    Memory: "\(text)"
    
    Respond with ONLY the category name.
    """
    
    let response = try await makeRequest(prompt: prompt)
    
    guard let category = MemoryCategory(rawValue: response) else {
      throw APIError.invalidCategory
    }
    
    return category
  }
  
  func generateEmbedding(_ text: String) async throws -> [Float] {
    // Call embedding API
    // Return 1536-dimensional vector
  }
}

enum MemoryCategory: String, Codable, CaseIterable {
  case fact
  case preference
  case episode
  case semantic
}
```

**3.3.2 Deduplication Check**
```swift
class DeduplicationManager {
  func checkForDuplicates(_ newMemory: String) async throws -> [Memory] {
    // 1. Generate embedding for new memory
    let embedding = try await ClaudeAPIClient.shared.generateEmbedding(newMemory)
    
    // 2. Query Supabase for similar embeddings
    let similarMemories = try await SupabaseClient.shared
      .searchSimilarMemories(embedding: embedding, threshold: 0.85)
    
    // 3. Return matches
    return similarMemories
  }
  
  func showDuplicateAlert(existing: Memory, new: String) {
    let alert = NSAlert()
    alert.messageText = "Similar memory exists"
    alert.informativeText = """
    Existing: "\(existing.content)"
    New: "\(new)"
    """
    alert.addButton(withTitle: "Merge")
    alert.addButton(withTitle: "Keep Both")
    alert.addButton(withTitle: "Cancel")
    
    let response = alert.runModal()
    // Handle user choice
  }
}
```

#### 3.4 Supabase Integration (1 hour)

**3.4.1 Auth Flow**
- [ ] Create login/signup window
- [ ] Email + password authentication
- [ ] Store session token securely in Keychain
- [ ] Handle token refresh

**3.4.2 Data Operations**
```swift
class SupabaseClient {
  func saveMemory(_ memory: Memory) async throws {
    // POST to Supabase REST API
    // Include user_id from auth token
  }
  
  func fetchMemories(category: MemoryCategory? = nil) async throws -> [Memory] {
    // GET from Supabase with optional category filter
  }
  
  func searchSimilarMemories(embedding: [Float], threshold: Double) async throws -> [Memory] {
    // Call Supabase RPC function for vector search
  }
  
  func addToQueue(_ content: String) async throws {
    // Insert into memory_queue table
  }
}
```

**3.4.3 Offline Mode**
- [ ] Queue saves locally when offline
- [ ] Sync when connection restored
- [ ] Show sync status in menu bar

#### 3.5 Polish & UX (1 hour)

**3.5.1 Error Handling**
- [ ] Network errors → show retry option
- [ ] API rate limits → queue for later
- [ ] Invalid auth → prompt re-login
- [ ] Empty captures → helpful message

**3.5.2 Loading States**
- [ ] Spinner while categorizing
- [ ] Progress bar for batch processing
- [ ] Skeleton loaders in review window

**3.5.3 Keyboard Shortcuts (in review window)**
- [ ] `Cmd+S` → Save all
- [ ] `Cmd+A` → Select all
- [ ] `Escape` → Close window
- [ ] `Delete` → Remove selected item
- [ ] `↑↓` → Navigate items

**3.5.4 Preferences Window**
- [ ] Customize global hotkeys
- [ ] API key settings
- [ ] Auto-process toggle (skip review, save immediately)
- [ ] Appearance (light/dark mode)

**3.5.5 Notifications**
- [ ] macOS notification for successful saves
- [ ] Toast messages for quick actions
- [ ] Badge count updates

---

### PHASE 4: Browser Extension (6-8 hours)

#### 4.1 Project Setup (1 hour)

**4.1.1 Initialize Project**
```bash
npm create vite@latest browser-extension -- --template react-ts
cd browser-extension
npm install
npm install @supabase/supabase-js
npm install lucide-react # for icons
```

**4.1.2 Manifest Configuration**
```json
{
  "manifest_version": 3,
  "name": "Memory Assistant",
  "version": "1.0.0",
  "description": "Inject personal context into AI conversations",
  "permissions": [
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "https://claude.ai/*",
    "https://chat.openai.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://claude.ai/*",
        "https://chat.openai.com/*"
      ],
      "js": ["content.js"],
      "css": ["content.css"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "web_accessible_resources": [
    {
      "resources": ["sidebar.html"],
      "matches": ["https://claude.ai/*", "https://chat.openai.com/*"]
    }
  ]
}
```

#### 4.2 Content Script (3-4 hours)

**4.2.1 Inject Sidebar**
```typescript
// content.ts
function injectSidebar() {
  // Detect if on Claude.ai or ChatGPT
  const isClaude = window.location.hostname.includes('claude.ai')
  const isChatGPT = window.location.hostname.includes('openai.com')
  
  if (!isClaude && !isChatGPT) return
  
  // Create sidebar container
  const sidebar = document.createElement('div')
  sidebar.id = 'memory-assistant-sidebar'
  sidebar.innerHTML = `
    <iframe src="${chrome.runtime.getURL('sidebar.html')}" 
            style="width: 300px; height: 100vh; border-left: 1px solid #ccc;">
    </iframe>
  `
  
  document.body.appendChild(sidebar)
}

injectSidebar()
```

**4.2.2 Detect Conversation Context**
```typescript
class ConversationMonitor {
  private observer: MutationObserver
  
  startMonitoring() {
    // Watch for new messages in the chat
    this.observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
          this.onNewMessage()
        }
      }
    })
    
    const chatContainer = document.querySelector('[data-testid="chat-messages"]')
    if (chatContainer) {
      this.observer.observe(chatContainer, { childList: true, subtree: true })
    }
  }
  
  async onNewMessage() {
    const context = this.extractRecentContext()
    const relevantMemories = await this.fetchRelevantMemories(context)
    this.updateSidebar(relevantMemories)
  }
  
  extractRecentContext(): string {
    // Get last 3-5 messages
    const messages = document.querySelectorAll('.message')
    const lastMessages = Array.from(messages).slice(-5)
    return lastMessages.map(m => m.textContent).join('\n')
  }
  
  async fetchRelevantMemories(context: string): Promise<Memory[]> {
    // Send to background script to query Supabase
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { type: 'SEARCH_MEMORIES', context },
        (response) => resolve(response.memories)
      )
    })
  }
}
```

**4.2.3 Memory Sidebar UI (sidebar.html + React)**
```tsx
// Sidebar.tsx
import { useState, useEffect } from 'react'
import { Search, Check } from 'lucide-react'

interface Memory {
  id: string
  content: string
  category: string
  relevanceScore: number
}

export default function Sidebar() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  
  useEffect(() => {
    // Listen for updates from content script
    window.addEventListener('message', (event) => {
      if (event.data.type === 'UPDATE_MEMORIES') {
        setMemories(event.data.memories)
      }
    })
  }, [])
  
  const toggleMemory = (id: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelected(newSelected)
  }
  
  const injectSelected = async () => {
    const selectedMemories = memories.filter(m => selected.has(m.id))
    
    // Send message to content script to inject
    window.parent.postMessage({
      type: 'INJECT_MEMORIES',
      memories: selectedMemories
    }, '*')
  }
  
  return (
    <div className="sidebar">
      <div className="header">
        <h3>🧠 Memories</h3>
        <input 
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      
      <div className="memories-list">
        <div className="section">
          <h4>Relevant ({memories.length})</h4>
          {memories.map(memory => (
            <div 
              key={memory.id} 
              className={`memory-item ${selected.has(memory.id) ? 'selected' : ''}`}
              onClick={() => toggleMemory(memory.id)}
            >
              <div className="checkbox">
                {selected.has(memory.id) && <Check size={16} />}
              </div>
              <div className="content">
                <p>{memory.content}</p>
                <span className="category">{memory.category}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="actions">
        <button 
          onClick={injectSelected}
          disabled={selected.size === 0}
        >
          Inject Selected ({selected.size})
        </button>
        <button onClick={() => window.parent.postMessage({ type: 'VIEW_ALL' }, '*')}>
          View All
        </button>
      </div>
    </div>
  )
}
```

**4.2.4 Injection Logic**
```typescript
// content.ts
function injectMemories(memories: Memory[]) {
  // Find the input textarea
  const textarea = document.querySelector('textarea[data-id="root"]') as HTMLTextAreaElement
  
  if (!textarea) {
    console.error('Could not find input textarea')
    return
  }
  
  // Format memories as context
  const context = formatMemoriesAsContext(memories)
  
  // Get current value
  const currentValue = textarea.value
  
  // Prepend context
  const newValue = currentValue 
    ? `${context}\n\n${currentValue}`
    : context
  
  // Update textarea
  textarea.value = newValue
  
  // Trigger input event so the app detects the change
  textarea.dispatchEvent(new Event('input', { bubbles: true }))
  
  // Focus textarea
  textarea.focus()
}

function formatMemoriesAsContext(memories: Memory[]): string {
  const formatted = memories.map(m => `- ${m.content}`).join('\n')
  return `[Context from my memory:\n${formatted}]\n`
}
```

#### 4.3 Popup Window (1 hour)

**4.3.1 Popup UI (popup.html + React)**
```tsx
// Popup.tsx
export default function Popup() {
  const [stats, setStats] = useState({
    total: 0,
    byCategory: {
      fact: 0,
      preference: 0,
      episode: 0,
      semantic: 0
    }
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState<Memory[]>([])
  
  const handleSearch = async () => {
    const response = await chrome.runtime.sendMessage({
      type: 'SEARCH_MEMORIES',
      query: searchQuery
    })
    setResults(response.memories)
  }
  
  return (
    <div className="popup">
      <h2>Memory Assistant</h2>
      
      <div className="stats">
        <div>Total Memories: {stats.total}</div>
        <div>Facts: {stats.byCategory.fact}</div>
        <div>Preferences: {stats.byCategory.preference}</div>
        <div>Episodes: {stats.byCategory.episode}</div>
        <div>Semantic: {stats.byCategory.semantic}</div>
      </div>
      
      <div className="search">
        <input 
          type="text"
          placeholder="Search memories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      
      {results.length > 0 && (
        <div className="results">
          {results.map(memory => (
            <div key={memory.id} className="result-item">
              <p>{memory.content}</p>
              <span>{memory.category}</span>
            </div>
          ))}
        </div>
      )}
      
      <div className="links">
        <a href="#" onClick={() => chrome.tabs.create({ url: 'settings.html' })}>
          Settings
        </a>
      </div>
    </div>
  )
}
```

#### 4.4 Background Service Worker (1 hour)

**4.4.1 Handle API Calls**
```typescript
// background.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'SEARCH_MEMORIES':
      handleSearchMemories(message, sendResponse)
      return true // Keep channel open for async response
    
    case 'GET_STATS':
      handleGetStats(sendResponse)
      return true
  }
})

async function handleSearchMemories(message: any, sendResponse: Function) {
  try {
    let query = supabase
      .from('memories')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (message.query) {
      // Text search
      query = query.ilike('content', `%${message.query}%`)
    } else if (message.context) {
      // Semantic search - generate embedding and search
      const embedding = await generateEmbedding(message.context)
      
      // Call RPC function for vector search
      const { data, error } = await supabase.rpc('search_memories_by_embedding', {
        query_embedding: embedding,
        match_threshold: 0.7,
        match_count: 5
      })
      
      if (error) throw error
      sendResponse({ memories: data })
      return
    }
    
    const { data, error } = await query
    
    if (error) throw error
    sendResponse({ memories: data })
  } catch (error) {
    console.error('Error searching memories:', error)
    sendResponse({ memories: [], error: error.message })
  }
}

async function generateEmbedding(text: string): Promise<number[]> {
  // Call Claude API or OpenAI to generate embedding
  const response = await fetch('https://api.anthropic.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY!
    },
    body: JSON.stringify({
      model: 'claude-3-sonnet',
      input: text
    })
  })
  
  const data = await response.json()
  return data.embedding
}
```

**4.4.2 Sync & Cache Management**
```typescript
// Sync memories to IndexedDB for offline access
class CacheManager {
  private db: IDBDatabase
  
  async init() {
    this.db = await openDB('memory-assistant', 1, {
      upgrade(db) {
        db.createObjectStore('memories', { keyPath: 'id' })
        db.createObjectStore('embeddings', { keyPath: 'id' })
      }
    })
  }
  
  async syncMemories() {
    // Fetch all memories from Supabase
    const { data } = await supabase
      .from('memories')
      .select('*')
    
    // Store in IndexedDB
    const tx = this.db.transaction('memories', 'readwrite')
    for (const memory of data) {
      tx.objectStore('memories').put(memory)
    }
    await tx.done
  }
  
  async getCachedMemories(): Promise<Memory[]> {
    const tx = this.db.transaction('memories', 'readonly')
    return await tx.objectStore('memories').getAll()
  }
}

// Sync every 5 minutes
setInterval(() => {
  CacheManager.syncMemories()
}, 5 * 60 * 1000)
```

#### 4.5 Polish & Styling (1 hour)

**4.5.1 Responsive Design**
- [ ] Sidebar adapts to page layout
- [ ] Works on different screen sizes
- [ ] Collapsible sidebar option

**4.5.2 Dark Mode Support**
- [ ] Detect Claude.ai/ChatGPT theme
- [ ] Match extension theme accordingly
- [ ] CSS variables for easy theming

**4.5.3 Loading States**
```tsx
{loading ? (
  <div className="loading">
    <Spinner />
    <p>Loading memories...</p>
  </div>
) : (
  <MemoriesList memories={memories} />
)}
```

**4.5.4 Error States**
- [ ] No memories found
- [ ] Network error
- [ ] Auth expired
- [ ] API rate limit

---

### PHASE 5: Integration & Testing (3-4 hours)

#### 5.1 End-to-End Testing

**Test Flow 1: Complete User Journey**
- [ ] Open any application (Chrome, Notes, etc.)
- [ ] Select text: "My email is john@example.com"
- [ ] Press Option+M
- [ ] Verify toast appears: "Captured ✓"
- [ ] Verify menu bar shows count: 🧠 1
- [ ] Press Option+O
- [ ] Verify review window opens
- [ ] Verify AI categorizes as "fact"
- [ ] Click "Save All"
- [ ] Verify memory saved to Supabase
- [ ] Open Claude.ai
- [ ] Start new conversation
- [ ] Verify extension sidebar appears
- [ ] Verify memory shows in "Relevant" section
- [ ] Check memory checkbox
- [ ] Click "Inject Selected"
- [ ] Verify context appears in input field
- [ ] Send message and verify Claude uses context

**Test Flow 2: Deduplication**
- [ ] Capture: "John's email is john@gmail.com"
- [ ] Save successfully
- [ ] Later, capture: "Email: john@gmail.com"
- [ ] Press Option+O
- [ ] Verify deduplication alert appears
- [ ] Test "Merge" option → updates existing memory
- [ ] Test "Keep Both" → saves as separate memory
- [ ] Test "Cancel" → discards new capture

**Test Flow 3: Multiple Memories**
- [ ] Capture 5 different memories
- [ ] Press Option+O
- [ ] Verify all 5 appear in review window
- [ ] Change category on 2 memories
- [ ] Edit text on 1 memory
- [ ] Delete 1 memory
- [ ] Save remaining 3
- [ ] Verify correct data in Supabase

**Test Flow 4: Browser Extension - ChatGPT**
- [ ] Add memories via Mac app
- [ ] Open ChatGPT (chat.openai.com)
- [ ] Verify extension works on ChatGPT too
- [ ] Test memory injection
- [ ] Verify formatting matches ChatGPT's interface

#### 5.2 Edge Cases & Error Handling

**Mac App:**
- [ ] No text selected when pressing Option+M
  - Expected: Toast shows "No text selected"
- [ ] Network offline when saving
  - Expected: Queues locally, shows "Will sync when online"
- [ ] Supabase quota exceeded
  - Expected: Error message with upgrade prompt
- [ ] Invalid auth token
  - Expected: Redirects to login
- [ ] Empty queue when pressing Option+O
  - Expected: Window shows "No memories to review"
- [ ] AI categorization fails
  - Expected: Defaults to "fact", allows manual override
- [ ] Very long text (10,000+ chars)
  - Expected: Truncates or shows warning

**Browser Extension:**
- [ ] Extension on non-Claude/ChatGPT page
  - Expected: Sidebar doesn't inject
- [ ] No memories in database
  - Expected: Shows "No memories yet. Use Mac app to add."
- [ ] Slow API response
  - Expected: Shows loading spinner, doesn't freeze UI
- [ ] User not logged in
  - Expected: Shows login prompt in sidebar
- [ ] Injection fails (textarea not found)
  - Expected: Error toast, doesn't crash extension

#### 5.3 Performance Testing

**Mac App:**
- [ ] Memory usage: < 50MB idle, < 100MB active
- [ ] Capture latency: < 100ms from hotkey to toast
- [ ] Review window open time: < 500ms
- [ ] AI categorization: < 2s per memory
- [ ] Dedup check: < 500ms
- [ ] Can handle 1000+ memories without lag

**Browser Extension:**
- [ ] Doesn't slow down page load (< 100ms overhead)
- [ ] Sidebar renders in < 300ms
- [ ] Memory search: < 500ms
- [ ] Injection: < 200ms
- [ ] Works smoothly with 100+ memories loaded

#### 5.4 Security Testing

- [ ] API keys not exposed in client code
- [ ] Auth tokens stored securely (Keychain on Mac, secure storage in extension)
- [ ] RLS policies prevent cross-user data access
- [ ] No XSS vulnerabilities in memory content display
- [ ] HTTPS enforced for all API calls
- [ ] Input sanitization for search queries

---

### PHASE 6: Deployment (2-3 hours)

#### 6.1 Mac App Distribution

**6.1.1 Code Signing (Requires Apple Developer Account - $99/year)**
```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" YourApp.app

# Verify signature
codesign --verify --deep --strict --verbose=2 YourApp.app
```

**6.1.2 Notarization**
```bash
# Create DMG
hdiutil create -volname "Memory Assistant" -srcfolder YourApp.app -ov -format UDZO MemoryAssistant.dmg

# Notarize
xcrun notarytool submit MemoryAssistant.dmg --apple-id "your@email.com" --password "app-specific-password" --team-id "TEAM_ID"

# Staple notarization
xcrun stapler staple MemoryAssistant.dmg
```

**6.1.3 DMG Installer**
- [ ] Create attractive DMG with:
  - App icon
  - Applications folder shortcut
  - Background image with drag instructions
  - License agreement

**6.1.4 Distribution**
- [ ] Upload to GitHub Releases
- [ ] Create landing page with download link
- [ ] Write installation guide
- [ ] Set up auto-update server (if using Sparkle)

#### 6.2 Browser Extension Submission

**6.2.1 Build Production Bundle**
```bash
cd browser-extension
npm run build
zip -r memory-assistant-extension.zip dist/
```

**6.2.2 Chrome Web Store Submission**
- [ ] Create developer account ($5 one-time fee)
- [ ] Prepare store listing:
  - Name: "Memory Assistant"
  - Description (132 chars max): "Inject personal context into Claude & ChatGPT conversations"
  - Category: Productivity
  - Language: English
- [ ] Upload screenshots (1280x800px):
  - Sidebar with memories
  - Memory injection in action
  - Mac app capture flow
- [ ] Upload promotional images:
  - Small tile: 440x280px
  - Large tile: 920x680px
  - Marquee: 1400x560px
- [ ] Privacy policy URL
- [ ] Upload extension ZIP
- [ ] Submit for review (typically 1-3 days)

**6.2.3 Firefox Add-ons (Optional)**
- [ ] Create Mozilla account
- [ ] Submit to addons.mozilla.org
- [ ] Similar listing process
- [ ] Usually faster review (hours to 1 day)

#### 6.3 Documentation & Marketing

**6.3.1 README.md**
```markdown
# Memory Assistant

Personal memory management for AI conversations.

## Features
- 🎯 Capture text with Option+M
- 🧠 AI-powered categorization
- 🔄 Real-time deduplication
- 💬 Inject context into Claude & ChatGPT
- 🔐 Private & secure

## Installation

### Mac App
1. Download [MemoryAssistant.dmg](link)
2. Open and drag to Applications
3. Grant accessibility permissions when prompted

### Browser Extension
Install from [Chrome Web Store](link)

## Quick Start
[Video tutorial or GIF]

## Support
Email: support@memoryassistant.com
```

**6.3.2 User Guide**
- [ ] Getting started tutorial
- [ ] Screenshots of each feature
- [ ] FAQ section
- [ ] Troubleshooting common issues
- [ ] Keyboard shortcuts reference

**6.3.3 Privacy Policy**
```markdown
# Privacy Policy

## Data Collection
- We store your memories encrypted in Supabase
- Memories are only used for your personal AI interactions
- No data is shared with third parties
- You can delete all data anytime

## AI Processing
- Memories are sent to Claude API for categorization
- No data is retained by Anthropic beyond processing

## Contact
privacy@memoryassistant.com
```

**6.3.4 Landing Page**
- [ ] Hero section with demo video
- [ ] Feature highlights
- [ ] Download buttons (Mac + Chrome)
- [ ] Pricing (Free for MVP)
- [ ] Testimonials (after launch)

**6.3.5 Demo Assets**
- [ ] 60-second demo video showing:
  1. Capture text from email
  2. Review and categorize
  3. Open Claude.ai
  4. Inject memory into conversation
- [ ] GIFs for each feature
- [ ] Screenshot gallery

---

## 📊 Timeline Estimate

| Phase | Time | Dependencies |
|-------|------|--------------|
| 1. Setup & Infrastructure | 1-2h | None |
| 2. Database Schema | 1h | Phase 1 |
| 3. Mac App | 6-8h | Phase 2 |
| 4. Browser Extension | 6-8h | Phase 2 |
| 5. Integration & Testing | 3-4h | Phases 3 & 4 |
| 6. Deployment | 2-3h | Phase 5 |
| **TOTAL** | **19-26 hours** | |

**Realistic Timeline:**
- **Full-time (8h/day):** 3-4 days
- **Part-time (4h/day):** 5-7 days
- **Weekend project:** 2-3 weekends

---

## 🛠️ Tech Stack Summary

### Mac App
- **Language:** Swift 5.9+
- **UI:** SwiftUI
- **Database:** Supabase Swift SDK
- **Hotkeys:** Carbon (built-in) or third-party library
- **Distribution:** DMG, notarized

### Browser Extension
- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **API:** Chrome Extensions API (Manifest V3)
- **Styling:** CSS Modules or Tailwind
- **State:** React Context or Zustand

### Backend
- **Platform:** Supabase
- **Database:** PostgreSQL 15+
- **Extensions:** pgvector for embeddings
- **Auth:** Supabase Auth (email/password)
- **Functions:** Deno Edge Functions
- **Storage:** Supabase Storage (for future file uploads)

### AI Services
- **Categorization:** Claude API (claude-sonnet-4-20250514)
- **Embeddings:** Claude or OpenAI embeddings
- **Vector Search:** pgvector cosine similarity

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Create Supabase project
2. ✅ Set up database schema
3. ✅ Test vector search queries

### Tomorrow
4. ⬜ Initialize Mac app project
5. ⬜ Implement global hotkeys
6. ⬜ Build capture flow

### Day 3
7. ⬜ Complete Mac app UI
8. ⬜ Integrate Claude API
9. ⬜ Test deduplication

### Day 4
10. ⬜ Build browser extension structure
11. ⬜ Implement content script injection
12. ⬜ Create sidebar UI

### Day 5
13. ⬜ Integration testing
14. ⬜ Bug fixes
15. ⬜ Prepare for deployment

### Week 2
16. ⬜ Code signing & notarization
17. ⬜ Submit to Chrome Web Store
18. ⬜ Create documentation
19. ⬜ Launch! 🎉

---

## 📝 Notes

- Keep the MVP simple - resist feature creep
- Prioritize UX over fancy features
- Test on real users early (dogfood it yourself!)
- Iterate based on feedback
- Phase 2 features can wait until after launch

## Questions or Issues?

Document blockers and decisions here as you build.
