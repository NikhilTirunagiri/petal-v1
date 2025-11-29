//
//  SessionManager.swift
//  petal-mac
//
//  Central state manager for Petal
//

import Foundation
import SwiftUI
import AppKit
import Combine
import UserNotifications

@MainActor
class SessionManager: ObservableObject {
    @Published var sessions: [Session] = []
    @Published var currentSession: Session?
    @Published var settings: AppSettings
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var lastCopiedText: String?
    @Published var lastPastedContext: String?
    @Published var sessionPreviews: [String: SessionPreview] = [:]  // Session ID -> Preview

    let apiService: APIService

    private let settingsKey = "PetalAppSettings"
    private var isOperationInProgress = false  // Lock for preventing session switching during operations
    private var lastCopyHash: String?  // Track last copied text to prevent duplicates
    private var lastCopyTime: Date?    // Track when last copy happened

    init() {
        // Load settings from UserDefaults
        let loadedSettings: AppSettings
        if let data = UserDefaults.standard.data(forKey: settingsKey),
           let savedSettings = try? JSONDecoder().decode(AppSettings.self, from: data) {
            loadedSettings = savedSettings
        } else {
            loadedSettings = AppSettings.default
        }

        self.settings = loadedSettings
        self.apiService = APIService(baseURL: loadedSettings.apiBaseURL)

        // Load sessions
        Task {
            await loadSessions()
        }
    }

    // MARK: - Settings Management

    func saveSettings() {
        if let encoded = try? JSONEncoder().encode(settings) {
            UserDefaults.standard.set(encoded, forKey: settingsKey)
        }
        apiService.baseURL = settings.apiBaseURL
    }

    func updateSettings(baseURL: String? = nil, userId: String? = nil) {
        if let baseURL = baseURL {
            settings.apiBaseURL = baseURL
        }
        if let userId = userId {
            settings.userId = userId
        }
        saveSettings()
    }

    // MARK: - Session Management

    func loadSessions() async {
        isLoading = true
        errorMessage = nil

        do {
            sessions = try await apiService.getSessions(userId: settings.userId)

            // Set current session if we have a saved ID
            if let savedSessionId = settings.currentSessionId {
                currentSession = sessions.first { $0.id == savedSessionId }
            }

            // If no current session, use the first one
            if currentSession == nil, let first = sessions.first {
                currentSession = first
                settings.currentSessionId = first.id
                saveSettings()
            }

            // Load previews for all sessions in parallel
            await loadSessionPreviews()

        } catch {
            errorMessage = "Failed to load sessions: \(error.localizedDescription)"
            print("Error loading sessions: \(error)")
        }

        isLoading = false
    }

    func loadSessionPreviews() async {
        // Fetch all previews in parallel
        await withTaskGroup(of: (String, SessionPreview?).self) { group in
            for session in sessions {
                group.addTask {
                    do {
                        let preview = try await self.apiService.getSessionPreview(sessionId: session.id)
                        return (session.id, preview)
                    } catch {
                        print("Failed to load preview for session \(session.id): \(error)")
                        return (session.id, nil)
                    }
                }
            }

            for await (sessionId, preview) in group {
                if let preview = preview {
                    sessionPreviews[sessionId] = preview
                }
            }
        }
    }

    func createSession(name: String, icon: String = "📁", description: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let sessionRequest = CreateSessionRequest(
                userId: settings.userId,
                name: name,
                icon: icon,
                description: description
            )

            let newSession = try await apiService.createSession(sessionRequest: sessionRequest)
            sessions.insert(newSession, at: 0)
            currentSession = newSession
            settings.currentSessionId = newSession.id
            saveSettings()

        } catch {
            errorMessage = "Failed to create session: \(error.localizedDescription)"
            print("Error creating session: \(error)")
        }

        isLoading = false
    }

    func switchSession(_ session: Session) {
        // Prevent session switching during operations
        if isOperationInProgress {
            print("Cannot switch session - operation in progress")
            errorMessage = "Please wait for current operation to complete"
            return
        }

        currentSession = session
        settings.currentSessionId = session.id
        saveSettings()

        // Warm cache for new session (non-blocking)
        Task {
            do {
                let response = try await apiService.activateSession(sessionId: session.id)
                print("Cache warmed for session: \(session.name) (\(response.cachedMemories) memories)")
            } catch {
                print("Failed to warm cache: \(error)")
            }
        }
    }

    func deleteSession(_ sessionId: String) async {
        isLoading = true
        errorMessage = nil

        do {
            _ = try await apiService.deleteSession(sessionId: sessionId)
            sessions.removeAll { $0.id == sessionId }

            // If we deleted the current session, switch to another
            if currentSession?.id == sessionId {
                currentSession = sessions.first
                settings.currentSessionId = currentSession?.id
                saveSettings()
            }

        } catch {
            errorMessage = "Failed to delete session: \(error.localizedDescription)"
            print("Error deleting session: \(error)")
        }

        isLoading = false
    }

    // MARK: - Smart Copy

    func smartCopy(text: String) async -> Bool {
        guard let sessionId = currentSession?.id else {
            errorMessage = "No session selected"
            return false
        }

        // Prevent duplicate requests if already in progress
        if isOperationInProgress {
            print("Smart Copy already in progress, ignoring duplicate request")
            return false
        }

        // Deduplicate identical text within 2 seconds
        let textHash = String(text.hashValue)
        let now = Date()
        if let lastHash = lastCopyHash,
           let lastTime = lastCopyTime,
           lastHash == textHash,
           now.timeIntervalSince(lastTime) < 2.0 {
            print("Duplicate text copied within 2 seconds, ignoring")
            showNotification(
                title: "Already Copied",
                message: "This text was just copied"
            )
            return false
        }

        // Update deduplication tracking
        lastCopyHash = textHash
        lastCopyTime = now

        // Lock to prevent session switching during operation
        isOperationInProgress = true
        isLoading = true
        errorMessage = nil

        do {
            let copyRequest = SmartCopyRequest(
                text: text,
                sessionId: sessionId,
                userId: settings.userId,
                source: "mac-app"
            )

            let response = try await apiService.smartCopy(copyRequest: copyRequest)
            lastCopiedText = response.processedText

            // Show success notification
            showNotification(
                title: "Smart Copy Success",
                message: "Saved to \(currentSession?.name ?? "session")"
            )

            isLoading = false
            isOperationInProgress = false  // Release lock
            return true

        } catch {
            errorMessage = "Smart Copy failed: \(error.localizedDescription)"
            showNotification(
                title: "Smart Copy Failed",
                message: error.localizedDescription
            )
            print("Error in Smart Copy: \(error)")
            isLoading = false
            isOperationInProgress = false  // Release lock
            return false
        }
    }

    // MARK: - Smart Paste

    func smartPaste(query: String? = nil, limit: Int = 10) async -> String? {
        guard let sessionId = currentSession?.id else {
            errorMessage = "No session selected"
            return nil
        }

        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiService.smartPaste(
                sessionId: sessionId,
                query: query,
                limit: limit
            )

            lastPastedContext = response.formattedText

            // Copy to clipboard
            copyToClipboard(response.formattedText)

            // Show success notification
            let filterText = query != nil ? " (filtered)" : ""
            showNotification(
                title: "Smart Paste",
                message: "Pasting \(response.memoryCount) memories from \(response.sessionName)"
            )

            isLoading = false
            return response.formattedText

        } catch {
            errorMessage = "Smart Paste failed: \(error.localizedDescription)"
            showNotification(
                title: "Smart Paste Failed",
                message: error.localizedDescription
            )
            print("Error in Smart Paste: \(error)")
            isLoading = false
            return nil
        }
    }

    // MARK: - Personal Memory

    func savePersonalMemory(text: String) async {
        isLoading = true
        errorMessage = nil

        do {
            // For now, we'll use smart copy to the current session
            // TODO: Add dedicated personal memory endpoint when Mem0 integration is complete
            let copyRequest = SmartCopyRequest(
                text: text,
                sessionId: currentSession?.id ?? "",
                userId: settings.userId,
                source: "personal-memory"
            )

            _ = try await apiService.smartCopy(copyRequest: copyRequest)

            showNotification(
                title: "Personal Memory Saved",
                message: "Saved to your personal knowledge base"
            )

            isLoading = false

        } catch {
            errorMessage = "Failed to save personal memory: \(error.localizedDescription)"
            showNotification(
                title: "Personal Memory Failed",
                message: error.localizedDescription
            )
            print("Error saving personal memory: \(error)")
            isLoading = false
        }
    }

    // MARK: - Helper Methods

    private func copyToClipboard(_ text: String) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
    }

    func getSelectedText() -> String? {
        let pasteboard = NSPasteboard.general

        // Save current clipboard content
        let oldContent = pasteboard.string(forType: .string)
        let oldChangeCount = pasteboard.changeCount

        print("Old clipboard content: \(oldContent?.prefix(50) ?? "nil")")
        print("Old change count: \(oldChangeCount)")

        // Small delay to ensure we're in the right context
        usleep(100000) // 100ms (increased from 50ms)

        // Simulate Cmd+C to copy selected text
        let source = CGEventSource(stateID: .hidSystemState)

        // Press Cmd+C with proper event creation
        if let cmdCDown = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: true) {
            cmdCDown.flags = .maskCommand
            cmdCDown.post(tap: .cghidEventTap)
            print("Posted Cmd+C down event")

            // Small delay between down and up
            usleep(10000) // 10ms

            if let cmdCUp = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: false) {
                cmdCUp.flags = .maskCommand
                cmdCUp.post(tap: .cghidEventTap)
                print("Posted Cmd+C up event")
            }
        }

        // Wait for clipboard to update (try multiple times)
        var attempts = 0
        while attempts < 25 { // 25 attempts * 50ms = 1.25 seconds max
            usleep(50000) // 50ms

            let currentChangeCount = pasteboard.changeCount
            if currentChangeCount != oldChangeCount {
                // Clipboard changed!
                print("Clipboard changed! Old count: \(oldChangeCount), New count: \(currentChangeCount)")
                if let newContent = pasteboard.string(forType: .string) {
                    if newContent != oldContent {
                        print("Got new content (\(newContent.count) chars): \(newContent.prefix(100))")
                        return newContent
                    } else {
                        print("Clipboard changed but content is the same")
                    }
                }
            }

            attempts += 1
        }

        // If nothing new, return what we got
        print("Clipboard didn't change after \(attempts) attempts")
        return pasteboard.string(forType: .string)
    }

    private func showNotification(title: String, message: String) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = message
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Error showing notification: \(error)")
            }
        }
    }
}
