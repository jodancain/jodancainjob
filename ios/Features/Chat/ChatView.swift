import SwiftUI
import UniformTypeIdentifiers

struct ChatView: View {
    @StateObject var viewModel: ChatViewModel
    @State private var showFileImporter = false

    var body: some View {
        VStack(spacing: 0) {
            topBar
            Divider()
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            MessageBubbleView(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) { _, _ in
                    if let lastId = viewModel.messages.last?.id {
                        withAnimation {
                            proxy.scrollTo(lastId, anchor: .bottom)
                        }
                    }
                }
            }
            Divider()
            inputArea
        }
        .navigationTitle("聊天")
        .toolbar(.hidden, for: .navigationBar)
        .alert(item: Binding(get: {
            viewModel.toastMessage.map { IdentifiedMessage(id: UUID(), message: $0) }
        }, set: { _ in viewModel.toastMessage = nil })) { item in
            Alert(title: Text(item.message))
        }
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(viewModel.headerTitle)
                    .font(.headline)
                HStack(spacing: 6) {
                    Circle()
                        .fill(statusColor(viewModel.connectionStatus))
                        .frame(width: 8, height: 8)
                    Text(statusText(viewModel.connectionStatus))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer()
            Button("断开") { viewModel.disconnect() }
                .buttonStyle(.bordered)
        }
        .padding()
    }

    private var inputArea: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let mode = viewModel.aiMode {
                Text(mode == .qa ? "AI 问答" : "AI 代理")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(Color.blue.opacity(0.2)))
            }
            if let attachment = viewModel.attachment {
                HStack {
                    Text("已选文件: \(attachment.fileName)")
                        .font(.caption)
                    Spacer()
                    Button("清除") { viewModel.attachment = nil }
                        .font(.caption)
                }
            }
            HStack(alignment: .bottom) {
                Menu {
                    Button("AI 问答") { viewModel.selectAIMode(.qa) }
                    Button("AI 代理") { viewModel.selectAIMode(.agent) }
                    Button("普通模式") { viewModel.selectAIMode(nil) }
                } label: {
                    Label("AI", systemImage: "sparkles")
                        .labelStyle(.iconOnly)
                }
                Button(action: { showFileImporter = true }) {
                    Image(systemName: "paperclip")
                }
                TextEditor(text: $viewModel.inputText)
                    .frame(minHeight: 40, maxHeight: 120)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.gray.opacity(0.3)))
                Button {
                    Task { await viewModel.sendCurrentMessage() }
                } label: {
                    Image(systemName: "paperplane.fill")
                        .foregroundColor(.white)
                        .padding(8)
                        .background(Circle().fill(Color.accentColor))
                }
                .disabled(viewModel.isSending)
            }
            .padding(.bottom, 4)
        }
        .padding()
        .background(.thinMaterial)
        .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.item], allowsMultipleSelection: false) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    let attributes = (try? FileManager.default.attributesOfItem(atPath: url.path)) ?? [:]
                    let size = attributes[.size] as? NSNumber
                    viewModel.attachment = PendingAttachment(fileURL: url,
                                                             fileName: url.lastPathComponent,
                                                             fileSize: size?.int64Value ?? 0)
                }
            case .failure(let error):
                viewModel.toastMessage = error.localizedDescription
            }
        }
    }

    private func statusColor(_ status: ConnectionStatus) -> Color {
        switch status {
        case .connected: return .green
        case .connecting: return .yellow
        case .disconnected: return .red
        case .error: return .red
        }
    }

    private func statusText(_ status: ConnectionStatus) -> String {
        switch status {
        case .connected: return "已连接"
        case .connecting: return "连接中"
        case .disconnected: return "未连接"
        case .error(let message): return "出错: \(message)"
        }
    }
}

private struct IdentifiedMessage: Identifiable {
    let id: UUID
    let message: String
}
