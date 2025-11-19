import Foundation
import SwiftUI

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var inputText: String = ""
    @Published var aiMode: AIMode?
    @Published var attachment: PendingAttachment?
    @Published var isSending: Bool = false
    @Published var toastMessage: String?

    private let parser = CommandParser()
    private let appState: AppState
    private var eventObserver: NSObjectProtocol?

    init(appState: AppState) {
        self.appState = appState
        eventObserver = NotificationCenter.default.addObserver(forName: .connectionManagerEvent,
                                                               object: nil,
                                                               queue: .main) { [weak self] notification in
            guard let event = notification.object as? ServerEvent else { return }
            self?.handle(event: event)
        }
    }

    deinit {
        if let observer = eventObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }

    var connectionStatus: ConnectionStatus {
        appState.connectionStatus
    }

    var headerTitle: String {
        "\(appState.serverConfig.username)@\(appState.serverConfig.host):\(appState.serverConfig.port)"
    }

    func sendCurrentMessage() async {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || attachment != nil else {
            toastMessage = "请输入要发送的内容"
            return
        }

        isSending = true
        let result = parser.parse(text: inputText,
                                  aiMode: aiMode,
                                  attachment: attachment,
                                  sessionId: appState.sessionId)
        guard result.errors.isEmpty else {
            toastMessage = result.errors.joined(separator: "\n")
            isSending = false
            return
        }

        var payload = result.payload
        let messageText = inputText
        switch payload.commandType {
        case .terminal:
            appendUserMessage(text: messageText, clientMessageId: result.clientMessageId)
        case .download:
            appendUserMessage(text: "下载 \(payload.remotePath ?? "")", clientMessageId: result.clientMessageId)
        case .uploadNotify:
            appendUserMessage(text: "上传 \(payload.remotePath ?? "")", clientMessageId: result.clientMessageId)
        case .aiQA:
            appendUserMessage(text: "[AI 问答] \(payload.prompt ?? "")", clientMessageId: result.clientMessageId)
        case .aiAgent:
            appendUserMessage(text: "[AI 代理] \(payload.goal ?? "")", clientMessageId: result.clientMessageId)
        }

        inputText = ""
        aiMode = nil
        attachment = nil

        if payload.commandType == .uploadNotify,
           let remotePath = payload.remotePath,
           let attachment = attachment {
            let uploadResult = await appState.connectionManager.uploadFile(config: appState.serverConfig,
                                                                           sessionId: appState.sessionId,
                                                                           remotePath: remotePath,
                                                                           fileURL: attachment.fileURL)
            switch uploadResult {
            case .success(let response):
                payload.fileId = response.fileId
                payload.remotePath = response.remotePath
                payload.originalFileName = response.fileName
                let successMessage = ChatMessage(role: .system,
                                                 kind: .toolLog("上传成功: \(response.fileName)"),
                                                 clientMessageId: result.clientMessageId)
                messages.append(successMessage)
            case .failure(let error):
                toastMessage = error.localizedDescription
                isSending = false
                return
            }
        }

        let envelope = CommandEnvelope(data: .init(clientMessageId: result.clientMessageId,
                                                   sessionId: appState.sessionId,
                                                   payload: payload))

        do {
            try await appState.connectionManager.send(envelope: envelope)
        } catch {
            toastMessage = error.localizedDescription
        }
        isSending = false
    }

    func disconnect() {
        appState.connectionManager.disconnect()
    }

    func selectAIMode(_ mode: AIMode?) {
        aiMode = mode
    }

    func attachMockFile() {
        let tempURL = URL(fileURLWithPath: NSTemporaryDirectory()).appending(path: "mock.txt")
        try? "demo".data(using: .utf8)?.write(to: tempURL)
        let attributes = (try? FileManager.default.attributesOfItem(atPath: tempURL.path)) ?? [:]
        let size = attributes[.size] as? NSNumber
        attachment = PendingAttachment(fileURL: tempURL,
                                       fileName: tempURL.lastPathComponent,
                                       fileSize: size?.int64Value ?? 0)
    }

    private func appendUserMessage(text: String, clientMessageId: UUID) {
        let message = ChatMessage(role: .user,
                                  kind: .text(text),
                                  clientMessageId: clientMessageId)
        messages.append(message)
    }

    private func handle(event: ServerEvent) {
        switch event {
        case .assistantDelta(let delta):
            mergeAssistantDelta(delta)
        case .assistantMessage(let message):
            finalizeAssistantMessage(message)
        case .terminalOutput(let output):
            let message = ChatMessage(role: .assistant,
                                      kind: .terminal(output.output, isError: output.isError),
                                      clientMessageId: output.relatedClientMessageId)
            messages.append(message)
        case .toolLog(let log):
            let message = ChatMessage(role: .assistant,
                                      kind: .toolLog(log.message),
                                      clientMessageId: nil)
            messages.append(message)
        case .downloadReady(let download):
            let message = ChatMessage(role: .assistant,
                                      kind: .download(downloadUrl: download.downloadUrl,
                                                      fileName: download.fileName,
                                                      fileSize: download.fileSize),
                                      clientMessageId: download.clientMessageIdRef)
            messages.append(message)
        }
    }

    private func mergeAssistantDelta(_ delta: AssistantDelta) {
        if let index = messages.firstIndex(where: { $0.clientMessageId == delta.clientMessageIdRef }) {
            if case .text(let current) = messages[index].kind {
                messages[index].kind = .text(current + delta.delta)
            }
        } else {
            let placeholder = ChatMessage(role: .assistant,
                                          kind: .text(delta.delta),
                                          clientMessageId: delta.clientMessageIdRef)
            messages.append(placeholder)
        }
    }

    private func finalizeAssistantMessage(_ message: AssistantMessage) {
        if let index = messages.firstIndex(where: { $0.clientMessageId == message.clientMessageIdRef }) {
            messages[index].kind = .text(message.content)
        } else {
            let message = ChatMessage(role: .assistant,
                                      kind: .text(message.content),
                                      clientMessageId: message.clientMessageIdRef)
            messages.append(message)
        }
    }
}
