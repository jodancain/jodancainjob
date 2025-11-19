import Foundation

protocol ConnectionManagerDelegate: AnyObject {
    func connectionManager(_ manager: ConnectionManager, didChange status: ConnectionStatus)
    func connectionManager(_ manager: ConnectionManager, didReceive event: ServerEvent)
    func connectionManager(_ manager: ConnectionManager, didUpdateSessionId sessionId: String?)
}

enum ServerEvent {
    case assistantDelta(AssistantDelta)
    case assistantMessage(AssistantMessage)
    case terminalOutput(TerminalOutput)
    case toolLog(ToolLog)
    case downloadReady(DownloadReady)
}

struct AssistantDelta: Codable {
    let sessionId: String
    let messageId: String
    let clientMessageIdRef: UUID
    let delta: String
}

struct AssistantMessage: Codable {
    let sessionId: String
    let messageId: String
    let clientMessageIdRef: UUID
    let content: String
    let role: String
}

struct TerminalOutput: Codable {
    let sessionId: String
    let relatedClientMessageId: UUID
    let output: String
    let isError: Bool
}

struct ToolLog: Codable {
    let sessionId: String
    let agentRunId: String
    let message: String
    let level: String
    let timestamp: TimeInterval
}

struct DownloadReady: Codable {
    let sessionId: String
    let clientMessageIdRef: UUID
    let remotePath: String
    let fileName: String
    let fileSize: Int
    let downloadUrl: URL
}

final class ConnectionManager: NSObject {
    private let httpClient: HttpClient
    private let webSocketClient: WebSocketClient
    weak var delegate: ConnectionManagerDelegate?

    private var currentConfig: ConnectionConfig?

    override init() {
        self.httpClient = HttpClient()
        self.webSocketClient = WebSocketClient()
        super.init()
        webSocketClient.delegate = self
    }

    func testConnection(config: ConnectionConfig) async -> Result<TestConnectionResponse, Error> {
        do {
            let response = try await httpClient.testConnection(config: config)
            return .success(response)
        } catch {
            return .failure(error)
        }
    }

    func uploadFile(config: ConnectionConfig,
                    sessionId: String?,
                    remotePath: String,
                    fileURL: URL) async -> Result<FileUploadResponse, Error> {
        do {
            let response = try await httpClient.uploadFile(config: config,
                                                            sessionId: sessionId,
                                                            remotePath: remotePath,
                                                            fileURL: fileURL)
            return .success(response)
        } catch {
            return .failure(error)
        }
    }

    func connect(config: ConnectionConfig) {
        currentConfig = config
        guard let url = config.websocketURL else {
            delegate?.connectionManager(self, didChange: .error(message: "Invalid URL"))
            return
        }
        var request = URLRequest(url: url)
        if let header = config.basicAuthHeader {
            request.setValue(header, forHTTPHeaderField: "Authorization")
        }
        delegate?.connectionManager(self, didChange: .connecting)
        webSocketClient.connect(request: request)
    }

    func disconnect() {
        webSocketClient.disconnect()
        delegate?.connectionManager(self, didChange: .disconnected)
    }

    func send(envelope: CommandEnvelope) async throws {
        let data = try JSONEncoder().encode(envelope)
        try await webSocketClient.send(data: data)
    }
}

extension ConnectionManager: WebSocketClientDelegate {
    func webSocketClientDidOpen(_ client: WebSocketClient) {
        delegate?.connectionManager(self, didChange: .connected)
    }

    func webSocketClient(_ client: WebSocketClient, didReceive message: Result<URLSessionWebSocketTask.Message, Error>) {
        switch message {
        case .success(let wsMessage):
            switch wsMessage {
            case .data(let data):
                handleIncomingData(data)
            case .string(let string):
                handleIncomingData(Data(string.utf8))
            @unknown default:
                break
            }
        case .failure(let error):
            delegate?.connectionManager(self, didChange: .error(message: error.localizedDescription))
        }
    }

    func webSocketClientDidClose(_ client: WebSocketClient, error: Error?) {
        if let error {
            delegate?.connectionManager(self, didChange: .error(message: error.localizedDescription))
        } else {
            delegate?.connectionManager(self, didChange: .disconnected)
        }
    }

    private func handleIncomingData(_ data: Data) {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String,
              let payload = json["data"] else { return }

        switch type {
        case "assistant_delta":
            if let event: AssistantDelta = decode(payload) {
                delegate?.connectionManager(self, didReceive: .assistantDelta(event))
                delegate?.connectionManager(self, didUpdateSessionId: event.sessionId)
            }
        case "assistant_message_done":
            if let event: AssistantMessage = decode(payload) {
                delegate?.connectionManager(self, didReceive: .assistantMessage(event))
                delegate?.connectionManager(self, didUpdateSessionId: event.sessionId)
            }
        case "terminal_output":
            if let event: TerminalOutput = decode(payload) {
                delegate?.connectionManager(self, didReceive: .terminalOutput(event))
                delegate?.connectionManager(self, didUpdateSessionId: event.sessionId)
            }
        case "tool_log":
            if let event: ToolLog = decode(payload) {
                delegate?.connectionManager(self, didReceive: .toolLog(event))
                delegate?.connectionManager(self, didUpdateSessionId: event.sessionId)
            }
        case "download_ready":
            if let event: DownloadReady = decode(payload) {
                delegate?.connectionManager(self, didReceive: .downloadReady(event))
                delegate?.connectionManager(self, didUpdateSessionId: event.sessionId)
            }
        default:
            break
        }
    }

    private func decode<T: Decodable>(_ value: Any) -> T? {
        guard JSONSerialization.isValidJSONObject(value),
              let data = try? JSONSerialization.data(withJSONObject: value) else {
            return nil
        }
        return try? JSONDecoder().decode(T.self, from: data)
    }
}
