//
//  SettingsView.swift
//  petal-mac
//
//  Settings and configuration
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var sessionManager: SessionManager
    @State private var apiBaseURL: String = ""
    @State private var userId: String = ""
    @State private var showingSaveSuccess = false

    var body: some View {
        TabView {
            generalSettingsTab
                .tabItem {
                    Label("General", systemImage: "gearshape")
                }

            hotkeysTab
                .tabItem {
                    Label("Hotkeys", systemImage: "keyboard")
                }

            aboutTab
                .tabItem {
                    Label("About", systemImage: "info.circle")
                }
        }
        .frame(width: 500, height: 400)
        .onAppear {
            apiBaseURL = sessionManager.settings.apiBaseURL
            userId = sessionManager.settings.userId
        }
    }

    // MARK: - General Settings Tab

    private var generalSettingsTab: some View {
        Form {
            Section {
                TextField("API Base URL", text: $apiBaseURL)
                    .textFieldStyle(.roundedBorder)

                Text("Example: http://localhost:8000")
                    .font(.caption)
                    .foregroundColor(.secondary)

                TextField("User ID", text: $userId)
                    .textFieldStyle(.roundedBorder)

                Text("Unique identifier for your memories")
                    .font(.caption)
                    .foregroundColor(.secondary)

            } header: {
                Text("API Configuration")
                    .font(.headline)
            }

            Section {
                if let currentSession = sessionManager.currentSession {
                    HStack {
                        Text("Current Session:")
                        Text(currentSession.icon)
                        Text(currentSession.name)
                            .fontWeight(.medium)
                    }
                } else {
                    Text("No session selected")
                        .foregroundColor(.secondary)
                }

                Text("Sessions: \(sessionManager.sessions.count)")
                    .foregroundColor(.secondary)

            } header: {
                Text("Session Info")
                    .font(.headline)
            }

            HStack {
                Spacer()

                Button("Test Connection") {
                    Task {
                        await testAPIConnection()
                    }
                }
                .buttonStyle(.bordered)

                Button("Save Settings") {
                    saveSettings()
                }
                .buttonStyle(.borderedProminent)
            }

            if showingSaveSuccess {
                Text("Settings saved successfully!")
                    .foregroundColor(.green)
                    .font(.caption)
            }
        }
        .padding()
    }

    // MARK: - Hotkeys Tab

    private var hotkeysTab: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Global Hotkeys")
                .font(.title2)
                .fontWeight(.bold)

            Text("These hotkeys work system-wide, even when Petal is not focused.")
                .font(.caption)
                .foregroundColor(.secondary)

            Divider()

            VStack(alignment: .leading, spacing: 12) {
                HotkeyRow(
                    icon: "doc.on.clipboard",
                    title: "Smart Copy",
                    description: "Save selected text to current session",
                    hotkey: "⌥C",
                    color: .blue
                )

                HotkeyRow(
                    icon: "doc.on.doc",
                    title: "Smart Paste",
                    description: "Paste context from current session",
                    hotkey: "⌥V",
                    color: .green
                )

                HotkeyRow(
                    icon: "brain.head.profile",
                    title: "Personal Memory",
                    description: "Save to personal knowledge base",
                    hotkey: "⌥M",
                    color: .purple
                )

                HotkeyRow(
                    icon: "list.bullet",
                    title: "Show Sessions",
                    description: "View and switch sessions",
                    hotkey: "⌥S",
                    color: .orange
                )

                HotkeyRow(
                    icon: "rectangle.stack",
                    title: "Open Menu",
                    description: "Show Petal menu bar popup",
                    hotkey: "⌥O",
                    color: .pink
                )
            }

            Spacer()

            Text("Accessibility permissions required")
                .font(.caption)
                .foregroundColor(.orange)

            Button("Open System Preferences") {
                openAccessibilityPreferences()
            }
            .buttonStyle(.bordered)
        }
        .padding()
    }

    // MARK: - About Tab

    private var aboutTab: some View {
        VStack(spacing: 20) {
            Text("✾")
                .font(.system(size: 80))

            Text("Petal")
                .font(.title)
                .fontWeight(.bold)

            Text("Version 1.0.0")
                .font(.caption)
                .foregroundColor(.secondary)

            Divider()
                .padding(.horizontal, 40)

            Text("Context Memory Layer for AI Assistants")
                .font(.headline)
                .multilineTextAlignment(.center)

            Text("Petal helps AI remember your project context by capturing and organizing code snippets, documentation, and notes into searchable sessions.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)

            Spacer()

            VStack(spacing: 8) {
                Link("Documentation", destination: URL(string: "https://github.com/NikhilTirunagiri/Petal")!)
                Link("Report an Issue", destination: URL(string: "https://github.com/NikhilTirunagiri/Petal/issues")!)
            }
            .font(.caption)

            Text("Made with 💜 by Nikhil")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding()
    }

    // MARK: - Helper Methods

    private func saveSettings() {
        sessionManager.updateSettings(
            baseURL: apiBaseURL,
            userId: userId
        )
        showingSaveSuccess = true

        // Hide success message after 2 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            showingSaveSuccess = false
        }
    }

    private func testAPIConnection() async {
        do {
            let result = try await sessionManager.apiService.healthCheck()
            print("API Connection successful: \(result)")

            DispatchQueue.main.async {
                let alert = NSAlert()
                alert.messageText = "Connection Successful"
                alert.informativeText = "Successfully connected to Petal backend!"
                alert.alertStyle = .informational
                alert.runModal()
            }
        } catch {
            print("API Connection failed: \(error)")

            DispatchQueue.main.async {
                let alert = NSAlert()
                alert.messageText = "Connection Failed"
                alert.informativeText = error.localizedDescription
                alert.alertStyle = .warning
                alert.runModal()
            }
        }
    }

    private func openAccessibilityPreferences() {
        let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
        NSWorkspace.shared.open(url)
    }
}

// MARK: - Hotkey Row

struct HotkeyRow: View {
    let icon: String
    let title: String
    let description: String
    let hotkey: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
                .frame(width: 30)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .fontWeight(.medium)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Text(hotkey)
                .font(.system(.body, design: .monospaced))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.2))
                .cornerRadius(4)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    SettingsView()
        .environmentObject(SessionManager())
}
