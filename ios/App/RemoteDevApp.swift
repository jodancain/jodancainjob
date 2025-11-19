import SwiftUI

@main
struct RemoteDevApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            if appState.connectionStatus.isConnected {
                ChatView(viewModel: ChatViewModel(appState: appState))
            } else {
                ConnectView(viewModel: ConnectViewModel(appState: appState))
            }
        }
    }
}
