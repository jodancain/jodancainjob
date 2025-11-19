import Combine
import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var serverConfig: ConnectionConfig
    @Published var connectionStatus: ConnectionStatus
    @Published var sessionId: String?

    let connectionManager: ConnectionManager
    private let credentialsStore: ConnectionCredentialsStore

    init(connectionManager: ConnectionManager = ConnectionManager(),
         credentialsStore: ConnectionCredentialsStore = .init()) {
        self.connectionManager = connectionManager
        self.credentialsStore = credentialsStore

        let stored = credentialsStore.load()
        self.serverConfig = ConnectionConfig(host: stored?.host ?? "",
                                             port: stored?.port ?? 443,
                                             username: stored?.username ?? "",
                                             password: "")
        self.connectionStatus = .disconnected
        self.sessionId = nil

        connectionManager.delegate = self
    }

    func persistSuccessfulConnection() {
        credentialsStore.save(credentials: serverConfig)
    }
}

extension AppState: ConnectionManagerDelegate {
    func connectionManager(_ manager: ConnectionManager, didChange status: ConnectionStatus) {
        self.connectionStatus = status
    }

    func connectionManager(_ manager: ConnectionManager, didReceive event: ServerEvent) {
        NotificationCenter.default.post(name: .connectionManagerEvent,
                                        object: event)
    }

    func connectionManager(_ manager: ConnectionManager, didUpdateSessionId sessionId: String?) {
        self.sessionId = sessionId
    }
}

extension Notification.Name {
    static let connectionManagerEvent = Notification.Name("connectionManagerEvent")
}
