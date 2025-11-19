import SwiftUI

struct ConnectView: View {
    @StateObject var viewModel: ConnectViewModel
    @FocusState private var focusedField: Field?

    enum Field: Hashable { case host, port, username, password }

    var body: some View {
        Form {
            Section(header: Text("服务器")) {
                TextField("Host", text: $viewModel.host)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .focused($focusedField, equals: .host)
                TextField("Port", text: $viewModel.port)
                    .keyboardType(.numberPad)
                    .focused($focusedField, equals: .port)
            }

            Section(header: Text("账号")) {
                TextField("Username", text: $viewModel.username)
                    .textInputAutocapitalization(.never)
                    .focused($focusedField, equals: .username)
                SecureField("Password", text: $viewModel.password)
                    .focused($focusedField, equals: .password)
            }

            Section(header: Text("状态")) {
                HStack {
                    Circle()
                        .fill(color(for: viewModel.connectionStatus))
                        .frame(width: 10, height: 10)
                    Text(viewModel.statusText)
                        .font(.subheadline)
                    Spacer()
                    if let error = viewModel.errorMessage {
                        Text(error)
                            .font(.footnote)
                            .foregroundColor(.red)
                    }
                }
            }

            Section {
                Button("测试连接") {
                    Task { await viewModel.testConnection() }
                }
                Button("连接") {
                    viewModel.connect()
                }
                .disabled(viewModel.host.isEmpty || viewModel.username.isEmpty || viewModel.password.isEmpty)
            }
        }
        .navigationTitle("连接服务器")
        .onAppear {
            viewModel.statusText = statusDescription(for: viewModel.connectionStatus)
        }
        .onChange(of: viewModel.connectionStatus) { _, newValue in
            viewModel.statusText = statusDescription(for: newValue)
            if case .connected = newValue {
                viewModel.persistIfNeeded()
            }
        }
    }

    private func color(for status: ConnectionStatus) -> Color {
        switch status {
        case .connected: return .green
        case .connecting: return .yellow
        case .error: return .red
        case .disconnected: return .gray
        }
    }

    private func statusDescription(for status: ConnectionStatus) -> String {
        switch status {
        case .connected: return "已连接"
        case .connecting: return "连接中"
        case .disconnected: return "未连接"
        case .error(let message): return "出错: \(message)"
        }
    }
}
