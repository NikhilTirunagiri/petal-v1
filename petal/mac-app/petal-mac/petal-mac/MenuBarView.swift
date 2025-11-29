//
//  MenuBarView.swift
//  petal-mac
//
//  Menu bar popup UI
//

import SwiftUI

struct MenuBarView: View {
    @EnvironmentObject var sessionManager: SessionManager
    @State private var showCreateSession = false
    @State private var newSessionName = ""
    @State private var newSessionIcon = "📁"
    @State private var searchQuery = ""

    let emojiOptions = ["📁", "💼", "🎨", "🚀", "💡", "📚", "🔬", "🎯", "⚡️", "🌟"]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            headerSection

            Divider()

            // Current Session
            currentSessionSection

            Divider()

            // Sessions List
            sessionsListSection

            Divider()

            // Quick Actions
            quickActionsSection

            Divider()

            // Footer
            footerSection
        }
        .frame(width: 300)
        .onAppear {
            Task {
                await sessionManager.loadSessions()
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            Text("Petal")
                .font(.title2)
                .fontWeight(.semibold)

            Spacer()

            SettingsLink {
                Image(systemName: "gearshape")
                    .font(.body)
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help("Settings")
        }
        .padding()
    }

    // MARK: - Current Session Section

    private var currentSessionSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Current Session")
                .font(.caption)
                .foregroundColor(.secondary)
                .textCase(.uppercase)

            if let session = sessionManager.currentSession {
                HStack(spacing: 8) {
                    Circle()
                        .fill(Color.accentColor)
                        .frame(width: 8, height: 8)
                    Text(session.name)
                        .fontWeight(.medium)
                    Spacer()
                }
            } else {
                Text("No session selected")
                    .foregroundColor(.secondary)
                    .font(.subheadline)
            }
        }
        .padding()
    }

    // MARK: - Sessions List Section

    private var sessionsListSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text("All Sessions")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .textCase(.uppercase)

                Spacer()

                Button(action: {
                    showCreateSession.toggle()
                }) {
                    Image(systemName: "plus")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
                .help("Create new session")
            }
            .padding(.horizontal)
            .padding(.vertical, 8)

            if showCreateSession {
                createSessionForm
            }

            ScrollView {
                LazyVStack(spacing: 6) {
                    ForEach(sessionManager.sessions) { session in
                        SessionRowView(session: session)
                            .environmentObject(sessionManager)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 8)
            }
            .frame(minHeight: 150, maxHeight: 250)
        }
    }

    // MARK: - Create Session Form

    private var createSessionForm: some View {
        VStack(spacing: 12) {
            TextField("Session name", text: $newSessionName)
                .textFieldStyle(.roundedBorder)

            HStack(spacing: 8) {
                Button("Cancel") {
                    showCreateSession = false
                    newSessionName = ""
                }
                .buttonStyle(.bordered)

                Spacer()

                Button("Create") {
                    Task {
                        await sessionManager.createSession(
                            name: newSessionName,
                            icon: "•"
                        )
                        showCreateSession = false
                        newSessionName = ""
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(newSessionName.isEmpty)
                .keyboardShortcut(.return)
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(6)
        .padding(.horizontal)
        .padding(.bottom, 4)
    }

    // MARK: - Quick Actions Section

    private var quickActionsSection: some View {
        VStack(spacing: 8) {
            Text("Keyboard Shortcuts")
                .font(.caption)
                .foregroundColor(.secondary)
                .textCase(.uppercase)
                .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 4) {
                ShortcutRow(icon: "doc.on.clipboard", title: "Smart Copy", shortcut: "⌥C")
                ShortcutRow(icon: "doc.on.doc", title: "Smart Paste", shortcut: "⌥V")
                ShortcutRow(icon: "brain.head.profile", title: "Personal Memory", shortcut: "⌥M")
            }
        }
        .padding()
    }

    // MARK: - Footer Section

    private var footerSection: some View {
        VStack(spacing: 4) {
            if let error = sessionManager.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .lineLimit(2)
            }

            HStack {
                Text("v1.0.0")
                    .font(.caption2)
                    .foregroundColor(.secondary)

                Spacer()

                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.plain)
                .font(.caption)
                .foregroundColor(.red)
            }
        }
        .padding()
    }
}

// MARK: - Session Row View

struct SessionRowView: View {
    let session: Session
    @EnvironmentObject var sessionManager: SessionManager
    @State private var isHovered = false
    @State private var showPreview = false

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(sessionManager.currentSession?.id == session.id ? Color.accentColor : Color.secondary.opacity(0.3))
                .frame(width: 6, height: 6)

            Text(session.name)
                .lineLimit(1)
                .font(.subheadline)

            Spacer()

            if sessionManager.currentSession?.id == session.id {
                Image(systemName: "checkmark")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if isHovered {
                Button(action: {
                    Task {
                        await sessionManager.deleteSession(session.id)
                    }
                }) {
                    Image(systemName: "xmark")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .frame(minHeight: 36)
        .background(sessionManager.currentSession?.id == session.id ? Color.accentColor.opacity(0.1) : Color.clear)
        .cornerRadius(4)
        .onHover { hovering in
            isHovered = hovering
            showPreview = hovering
        }
        .popover(isPresented: $showPreview, arrowEdge: .trailing) {
            SessionPreviewPopover(preview: sessionManager.sessionPreviews[session.id])
                .frame(width: 280)
        }
        .onTapGesture {
            sessionManager.switchSession(session)
        }
    }
}

// MARK: - Session Preview Popover

struct SessionPreviewPopover: View {
    let preview: SessionPreview?

    var body: some View {
        if let preview = preview {
            VStack(alignment: .leading, spacing: 12) {
                // Session name
                Text(preview.sessionName)
                    .font(.headline)
                    .fontWeight(.semibold)

                Divider()

                // Memory count
                HStack(spacing: 4) {
                    Image(systemName: "doc.text")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(preview.memoryCount) memories")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                // Description
                Text(preview.description)
                    .font(.subheadline)
                    .foregroundColor(.primary)
                    .fixedSize(horizontal: false, vertical: true)

                // Recent memories
                if !preview.recentMemories.isEmpty {
                    Divider()

                    Text("Recent Memories")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .textCase(.uppercase)

                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(Array(preview.recentMemories.enumerated()), id: \.offset) { index, memory in
                            HStack(alignment: .top, spacing: 6) {
                                Text("\(index + 1).")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                                    .frame(width: 16, alignment: .leading)

                                Text(memory)
                                    .font(.caption)
                                    .foregroundColor(.primary)
                                    .lineLimit(2)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                }
            }
            .padding()
        } else {
            VStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                Text("Loading preview...")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
        }
    }
}

// MARK: - Shortcut Row

struct ShortcutRow: View {
    let icon: String
    let title: String
    let shortcut: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(width: 20)

            Text(title)
                .font(.subheadline)

            Spacer()

            Text(shortcut)
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(4)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
    }
}

#Preview {
    MenuBarView()
        .environmentObject(SessionManager())
}
