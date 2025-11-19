import Foundation
import SwiftUI

@MainActor
final class ConnectViewModel: ObservableObject {
    @Published var host: String
    @Published var port: String
    @Published var username: String
    @Published var password: String
    @Published var statusText: String = "未连接"
    @Published var testResult: TestConnectionResponse?
    @Published var errorMessage: String?

    private let appState: AppState

    init(appState: AppState) {
        self.appState = appState
        self.host = appState.serverConfig.host
        self.port = String(appState.serverConfig.port)
        self.username = appState.serverConfig.username
        self.password = appState.serverConfig.password
    }

    var connectionStatus: ConnectionStatus {
        appState.connectionStatus
    }

    func bindAppState() {
        appState.serverConfig.host = host
        appState.serverConfig.port = Int(port) ?? 443
        appState.serverConfig.username = username
        appState.serverConfig.password = password
    }

    func testConnection() async {
        bindAppState()
        let config = appState.serverConfig
        let result = await appState.connectionManager.testConnection(config: config)
        switch result {
        case .success(let response):
            testResult = response
            errorMessage = response.ok ? nil : (response.message ?? "未知错误")
            statusText = response.ok ? "连接正常" : "连接失败"
        case .failure(let error):
            errorMessage = error.localizedDescription
            statusText = "连接失败"
        }
    }

    func connect() {
        bindAppState()
        appState.connectionManager.connect(config: appState.serverConfig)
    }

    func persistIfNeeded() {
        if case .connected = appState.connectionStatus {
            appState.persistSuccessfulConnection()
        }
    }
}
