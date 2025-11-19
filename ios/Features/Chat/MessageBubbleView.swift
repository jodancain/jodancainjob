import SwiftUI

struct MessageBubbleView: View {
    let message: ChatMessage

    var body: some View {
        switch message.kind {
        case .text(let text):
            bubble(text: text,
                   isUser: message.role == .user,
                   background: message.role == .user ? Color.blue.opacity(0.2) : Color.gray.opacity(0.2),
                   foreground: .primary)
        case .terminal(let output, let isError):
            VStack(alignment: .leading) {
                Text(output)
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(isError ? .red : .green)
            }
            .padding()
            .background(Color.black.opacity(0.85))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        case .toolLog(let log):
            bubble(text: log,
                   isUser: false,
                   background: Color.green.opacity(0.15),
                   foreground: .green)
        case .download(let url, let fileName, let fileSize):
            VStack(alignment: .leading, spacing: 8) {
                Text("下载就绪: \(fileName)")
                    .font(.headline)
                Text("大小: \(ByteCountFormatter.string(fromByteCount: Int64(fileSize), countStyle: .file))")
                    .font(.caption)
                Link("下载", destination: url)
                    .font(.body)
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 12).fill(Color.orange.opacity(0.2)))
        }
    }

    @ViewBuilder
    private func bubble(text: String, isUser: Bool, background: Color, foreground: Color) -> some View {
        HStack {
            if isUser { Spacer() }
            Text(text)
                .padding()
                .foregroundColor(foreground)
                .background(background)
                .clipShape(RoundedRectangle(cornerRadius: 16))
            if !isUser { Spacer() }
        }
    }
}
