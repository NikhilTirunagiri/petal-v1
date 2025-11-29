//
//  HotKeyManager.swift
//  petal-mac
//
//  Global hotkey manager for Smart Copy/Paste
//
//  Note: This uses Carbon Event Manager APIs which are deprecated but still
//  fully functional. Apple has not provided a modern replacement for global
//  hotkeys in SwiftUI/Cocoa. All major menu bar apps (Slack, Raycast, Alfred)
//  still use Carbon for global hotkeys. The deprecation warnings can be safely
//  ignored - these APIs are not going away.
//
//  Alternatives considered:
//  - CGEventTap: Lower-level, more complex, same accessibility requirements
//  - NSEvent.addGlobalMonitorForEvents: Only works when app has focus
//  - Third-party libraries: Just wrappers around Carbon anyway
//

import Foundation
import Carbon
import AppKit

class HotKeyManager {
    static let shared = HotKeyManager()

    private var smartCopyHotKeyRef: EventHotKeyRef?
    private var smartPasteHotKeyRef: EventHotKeyRef?
    private var personalMemoryHotKeyRef: EventHotKeyRef?
    private var showSessionsHotKeyRef: EventHotKeyRef?
    private var openPopupHotKeyRef: EventHotKeyRef?
    private var eventHandler: EventHandlerRef?

    weak var sessionManager: SessionManager?
    var onShowSessions: (() -> Void)?
    var onOpenPopup: (() -> Void)?

    private init() {}

    func setup(sessionManager: SessionManager, onShowSessions: @escaping () -> Void, onOpenPopup: @escaping () -> Void) {
        self.sessionManager = sessionManager
        self.onShowSessions = onShowSessions
        self.onOpenPopup = onOpenPopup
        registerHotKeys()
    }

    private func registerHotKeys() {
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))

        // Install event handler
        InstallEventHandler(GetApplicationEventTarget(), { (_, event, userData) -> OSStatus in
            guard let userData = userData else { return OSStatus(eventNotHandledErr) }
            let manager = Unmanaged<HotKeyManager>.fromOpaque(userData).takeUnretainedValue()

            var hotKeyID = EventHotKeyID()
            GetEventParameter(event, UInt32(kEventParamDirectObject), UInt32(typeEventHotKeyID), nil, MemoryLayout<EventHotKeyID>.size, nil, &hotKeyID)

            Task { @MainActor in
                await manager.handleHotKey(id: hotKeyID.id)
            }

            return noErr
        }, 1, &eventType, Unmanaged.passUnretained(self).toOpaque(), &eventHandler)

        // Register Option+C for Smart Copy
        // Note: 'var' required for Carbon API even though value isn't mutated
        var smartCopyID = EventHotKeyID(signature: OSType(0x73636F70), id: 1) // 'scop'
        RegisterEventHotKey(
            UInt32(kVK_ANSI_C),
            UInt32(optionKey),
            smartCopyID,
            GetApplicationEventTarget(),
            0,
            &smartCopyHotKeyRef
        )

        // Register Option+V for Smart Paste
        var smartPasteID = EventHotKeyID(signature: OSType(0x73706173), id: 2) // 'spas'
        RegisterEventHotKey(
            UInt32(kVK_ANSI_V),
            UInt32(optionKey),
            smartPasteID,
            GetApplicationEventTarget(),
            0,
            &smartPasteHotKeyRef
        )

        // Register Option+M for Personal Memory
        var personalMemoryID = EventHotKeyID(signature: OSType(0x706D656D), id: 3) // 'pmem'
        RegisterEventHotKey(
            UInt32(kVK_ANSI_M),
            UInt32(optionKey),
            personalMemoryID,
            GetApplicationEventTarget(),
            0,
            &personalMemoryHotKeyRef
        )

        // Register Option+S for Show Sessions
        var showSessionsID = EventHotKeyID(signature: OSType(0x7373656C), id: 4) // 'ssel'
        RegisterEventHotKey(
            UInt32(kVK_ANSI_S),
            UInt32(optionKey),
            showSessionsID,
            GetApplicationEventTarget(),
            0,
            &showSessionsHotKeyRef
        )

        // Register Option+O for Open Popup
        var openPopupID = EventHotKeyID(signature: OSType(0x706F7075), id: 5) // 'popu'
        RegisterEventHotKey(
            UInt32(kVK_ANSI_O),
            UInt32(optionKey),
            openPopupID,
            GetApplicationEventTarget(),
            0,
            &openPopupHotKeyRef
        )

        print("HotKeys registered:")
        print("  ⌥C - Smart Copy")
        print("  ⌥V - Smart Paste")
        print("  ⌥M - Personal Memory")
        print("  ⌥S - Show Sessions")
        print("  ⌥O - Open Popup")
    }

    @MainActor
    private func handleHotKey(id: UInt32) async {
        guard sessionManager != nil else { return }

        switch id {
        case 1: // Smart Copy (Option+C)
            await performSmartCopy()
        case 2: // Smart Paste (Option+V)
            await performSmartPaste()
        case 3: // Personal Memory (Option+M)
            await performPersonalMemory()
        case 4: // Show Sessions (Option+S)
            performShowSessions()
        case 5: // Open Popup (Option+O)
            performOpenPopup()
        default:
            break
        }
    }

    @MainActor
    private func performSmartCopy() async {
        guard let sessionManager = sessionManager else { return }

        print("⌥C pressed - Getting selected text...")

        // Get selected text
        if let selectedText = sessionManager.getSelectedText() {
            print("Captured text length: \(selectedText.count) chars")
            print("First 100 chars: \(selectedText.prefix(100))")

            if !selectedText.isEmpty {
                _ = await sessionManager.smartCopy(text: selectedText)
            } else {
                print("Selected text is empty")
                showAlert(message: "Please select some text to copy")
            }
        } else {
            print("Failed to get selected text")
            showAlert(message: "Please select some text to copy")
        }
    }

    @MainActor
    private func performSmartPaste() async {
        guard let sessionManager = sessionManager else { return }

        print("⌥V pressed - Getting context...")

        if let context = await sessionManager.smartPaste() {
            print("Context ready (\(context.count) chars)")
            print("First 100 chars: \(context.prefix(100))")

            // Context is already copied to clipboard by sessionManager.smartPaste()
            // User can now press Cmd+V to paste
            print("Smart Paste completed - clipboard ready")

            // Note: We removed auto-paste simulation because it's unreliable
            // User now needs to press Cmd+V manually after Option+V
            // This is more predictable and gives users control
        } else {
            print("Failed to get context")
            showAlert(message: "Failed to retrieve context. Check if a session is selected.")
        }
    }

    @MainActor
    private func performPersonalMemory() async {
        guard let sessionManager = sessionManager else { return }

        // Get selected text
        if let selectedText = sessionManager.getSelectedText(), !selectedText.isEmpty {
            print("Personal Memory triggered with text: \(selectedText.prefix(50))...")
            await sessionManager.savePersonalMemory(text: selectedText)
        } else {
            print("No text selected for Personal Memory")
            showAlert(message: "Please select some text to save as personal memory")
        }
    }

    @MainActor
    private func performShowSessions() {
        print("Show Sessions triggered")
        onShowSessions?()
    }

    @MainActor
    private func performOpenPopup() {
        print("Open Popup triggered")
        onOpenPopup?()
    }

    private func showAlert(message: String) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = "Petal"
            alert.informativeText = message
            alert.alertStyle = .informational
            alert.runModal()
        }
    }

    deinit {
        if let ref = smartCopyHotKeyRef {
            UnregisterEventHotKey(ref)
        }
        if let ref = smartPasteHotKeyRef {
            UnregisterEventHotKey(ref)
        }
        if let ref = personalMemoryHotKeyRef {
            UnregisterEventHotKey(ref)
        }
        if let ref = showSessionsHotKeyRef {
            UnregisterEventHotKey(ref)
        }
        if let ref = openPopupHotKeyRef {
            UnregisterEventHotKey(ref)
        }
        if let handler = eventHandler {
            RemoveEventHandler(handler)
        }
    }
}
