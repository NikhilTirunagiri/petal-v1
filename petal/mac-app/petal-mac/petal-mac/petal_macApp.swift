//
//  petal_macApp.swift
//  petal-mac
//
//  Created by Nikhil Tirunagiri on 11/20/25.
//

import SwiftUI
import AppKit
import UserNotifications

class AppDelegate: NSObject, NSApplicationDelegate {
    var sessionManager: SessionManager?
    var statusItem: NSStatusItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Request notification permissions
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if granted {
                print("Notification permissions granted")
            } else if let error = error {
                print("Notification permission error: \(error)")
            }
        }

        // Note: HotKey setup moved to petal_macApp.initializeHotKeys()
        // This ensures SessionManager is fully initialized before registering hotkeys
    }
}

@main
struct petal_macApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var sessionManager = SessionManager()

    init() {
        // Request accessibility permissions on launch
        requestAccessibilityPermissions()
    }

    var body: some Scene {
        // Menu bar app (no window)
        MenuBarExtra("✾") {
            MenuBarView()
                .environmentObject(sessionManager)
                .task {
                    // Initialize hotkeys when view appears
                    await initializeHotKeys()
                }
        }
        .menuBarExtraStyle(.window)

        // Settings window (opened via menu)
        Settings {
            SettingsView()
                .environmentObject(sessionManager)
        }
    }

    private func requestAccessibilityPermissions() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        let accessEnabled = AXIsProcessTrustedWithOptions(options)

        if !accessEnabled {
            print("Accessibility permissions required for hotkeys to work")
            print("Please enable accessibility access in System Preferences > Privacy & Security > Accessibility")
        } else {
            print("Accessibility permissions granted")
        }
    }

    @MainActor
    private func initializeHotKeys() async {
        // Give SwiftUI time to initialize SessionManager
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds

        appDelegate.sessionManager = sessionManager
        HotKeyManager.shared.setup(
            sessionManager: sessionManager,
            onShowSessions: {
                print("Show sessions triggered")
            },
            onOpenPopup: {
                print("Open popup triggered")
            }
        )
        print("HotKey manager initialized")
    }
}
