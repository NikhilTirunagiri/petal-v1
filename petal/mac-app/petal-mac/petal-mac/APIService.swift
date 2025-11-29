//
//  APIService.swift
//  petal-mac
//
//  Backend API client for Petal
//

import Foundation
import Combine

enum APIError: Error {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case serverError(Int, String)
    case noData

    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message)"
        case .noData:
            return "No data received from server"
        }
    }
}

@MainActor
class APIService: ObservableObject {
    @Published var baseURL: String

    init(baseURL: String = "http://localhost:8000") {
        self.baseURL = baseURL
    }

    // MARK: - Generic Request Method

    private func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Encodable? = nil,
        queryParams: [String: String]? = nil
    ) async throws -> T {
        var urlString = "\(baseURL)\(endpoint)"

        // Add query parameters
        if let queryParams = queryParams, !queryParams.isEmpty {
            let queryString = queryParams.map { "\($0.key)=\($0.value.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? $0.value)" }.joined(separator: "&")
            urlString += "?\(queryString)"
        }

        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.noData
            }

            if httpResponse.statusCode >= 400 {
                let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
                throw APIError.serverError(httpResponse.statusCode, errorMessage)
            }

            let decoder = JSONDecoder()
            let result = try decoder.decode(T.self, from: data)
            return result

        } catch let error as APIError {
            throw error
        } catch let decodingError as DecodingError {
            throw APIError.decodingError(decodingError)
        } catch {
            throw APIError.networkError(error)
        }
    }

    // MARK: - Health Check

    func healthCheck() async throws -> [String: String] {
        return try await request(endpoint: "/health")
    }

    // MARK: - Session Endpoints

    func getSessions(userId: String) async throws -> [Session] {
        return try await request(endpoint: "/sessions/\(userId)")
    }

    func createSession(sessionRequest: CreateSessionRequest) async throws -> Session {
        return try await request(endpoint: "/sessions", method: "POST", body: sessionRequest)
    }

    func getSession(sessionId: String) async throws -> SessionDetail {
        return try await request(endpoint: "/sessions/detail/\(sessionId)")
    }

    func deleteSession(sessionId: String) async throws -> [String: String] {
        return try await request(endpoint: "/sessions/\(sessionId)", method: "DELETE")
    }

    func activateSession(sessionId: String) async throws -> ActivateSessionResponse {
        return try await request(endpoint: "/sessions/\(sessionId)/activate", method: "POST")
    }

    func getSessionPreview(sessionId: String) async throws -> SessionPreview {
        return try await request(endpoint: "/sessions/\(sessionId)/preview")
    }

    // MARK: - Memory Endpoints

    func smartCopy(copyRequest: SmartCopyRequest) async throws -> SmartCopyResponse {
        return try await request(endpoint: "/smart-copy", method: "POST", body: copyRequest)
    }

    func smartPaste(sessionId: String, query: String? = nil, limit: Int = 10) async throws -> SmartPasteResponse {
        var params: [String: String] = ["limit": String(limit)]
        if let query = query {
            params["query"] = query
        }
        return try await request(endpoint: "/smart-paste/\(sessionId)", queryParams: params)
    }

    func searchSession(
        sessionId: String,
        query: String,
        mode: String = "vector",
        limit: Int = 10
    ) async throws -> SearchResponse {
        let params: [String: String] = [
            "query": query,
            "mode": mode,
            "limit": String(limit)
        ]
        return try await request(endpoint: "/search/\(sessionId)", queryParams: params)
    }
}
