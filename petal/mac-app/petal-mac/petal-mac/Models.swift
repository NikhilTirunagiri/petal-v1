//
//  Models.swift
//  petal-mac
//
//  Data models for Petal app
//

import Foundation

// MARK: - Session Models

struct Session: Codable, Identifiable, Hashable {
    let id: String
    let userId: String
    let name: String
    let icon: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case name
        case icon
        case createdAt = "created_at"
    }
}

struct CreateSessionRequest: Codable {
    let userId: String
    let name: String
    let icon: String
    let description: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case name
        case icon
        case description
    }
}

struct SessionDetail: Codable {
    let id: String
    let userId: String
    let name: String
    let icon: String
    let description: String?
    let memoryCount: Int
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case name
        case icon
        case description
        case memoryCount = "memory_count"
        case createdAt = "created_at"
    }
}

struct ActivateSessionResponse: Codable {
    let status: String
    let sessionId: String
    let cachedMemories: Int

    enum CodingKeys: String, CodingKey {
        case status
        case sessionId = "session_id"
        case cachedMemories = "cached_memories"
    }
}

struct SessionPreview: Codable {
    let sessionName: String
    let memoryCount: Int
    let description: String
    let recentMemories: [String]

    enum CodingKeys: String, CodingKey {
        case sessionName = "session_name"
        case memoryCount = "memory_count"
        case description
        case recentMemories = "recent_memories"
    }
}

// MARK: - Memory Models

struct Memory: Codable, Identifiable {
    let id: String
    let processedText: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case processedText = "processed_text"
        case createdAt = "created_at"
    }
}

struct SmartCopyRequest: Codable {
    let text: String
    let sessionId: String
    let userId: String
    let source: String?

    enum CodingKeys: String, CodingKey {
        case text
        case sessionId = "session_id"
        case userId = "user_id"
        case source
    }
}

struct SmartCopyResponse: Codable {
    let status: String
    let memoryId: String
    let originalLength: Int
    let processedLength: Int
    let processedText: String

    enum CodingKeys: String, CodingKey {
        case status
        case memoryId = "memory_id"
        case originalLength = "original_length"
        case processedLength = "processed_length"
        case processedText = "processed_text"
    }
}

struct SmartPasteResponse: Codable {
    let formattedText: String
    let memoryCount: Int
    let sessionName: String

    enum CodingKeys: String, CodingKey {
        case formattedText = "formatted_text"
        case memoryCount = "memory_count"
        case sessionName = "session_name"
    }
}

struct SearchResult: Codable, Identifiable {
    let id: String
    let processedText: String
    let relevanceScore: Double
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case processedText = "processed_text"
        case relevanceScore = "relevance_score"
        case createdAt = "created_at"
    }
}

struct SearchResponse: Codable {
    let results: [SearchResult]
    let total: Int
}

// MARK: - App Settings

struct AppSettings: Codable {
    var apiBaseURL: String
    var userId: String
    var currentSessionId: String?
    var smartCopyHotkey: String
    var smartPasteHotkey: String
    var personalMemoryHotkey: String
    var showSessionsHotkey: String
    var openPopupHotkey: String

    static let `default` = AppSettings(
        apiBaseURL: "http://127.0.0.1:8000",
        userId: "default-user",
        currentSessionId: nil,
        smartCopyHotkey: "⌥C",
        smartPasteHotkey: "⌥V",
        personalMemoryHotkey: "⌥M",
        showSessionsHotkey: "⌥S",
        openPopupHotkey: "⌥O"
    )
}
