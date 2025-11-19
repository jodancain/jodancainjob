import Foundation

struct ConnectionConfig: Codable, Equatable {
    var host: String
    var port: Int
    var username: String
    var password: String

    var baseURL: URL? {
        var components = URLComponents()
        components.scheme = "https"
        components.host = host
        components.port = port
        return components.url
    }

    var websocketURL: URL? {
        var components = URLComponents()
        components.scheme = "wss"
        components.host = host
        components.port = port
        components.path = "/ws"
        return components.url
    }

    var basicAuthHeader: String? {
        let token = "\(username):\(password)"
        guard let data = token.data(using: .utf8) else { return nil }
        return "Basic \(data.base64EncodedString())"
    }
}

enum ConnectionStatus: Equatable {
    case disconnected
    case connecting
    case connected
    case error(message: String)

    var isConnected: Bool {
        if case .connected = self { return true }
        return false
    }
}

struct StoredCredentials: Codable {
    var host: String
    var port: Int
    var username: String
}
