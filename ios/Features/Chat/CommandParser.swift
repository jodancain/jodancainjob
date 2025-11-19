import Foundation

enum AIMode: String {
    case qa
    case agent
}

struct CommandParser {
    struct Result {
        var payload: CommandPayload
        var clientMessageId: UUID
        var errors: [String]
    }

    func parse(text: String,
               aiMode: AIMode?,
               attachment: PendingAttachment?,
               sessionId: String?) -> Result {
        var errors: [String] = []
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let clientMessageId = UUID()
        var payload = CommandPayload(commandType: .terminal,
                                     commandText: trimmed,
                                     remotePath: nil,
                                     prompt: nil,
                                     goal: nil,
                                     options: nil,
                                     constraints: nil,
                                     context: nil,
                                     originalFileName: nil,
                                     fileId: nil,
                                     extra: nil)

        if trimmed.lowercased().hasPrefix("/download ") {
            let path = trimmed.dropFirst("/download ".count).trimmingCharacters(in: .whitespaces)
            if path.isEmpty {
                errors.append("请输入要下载的路径")
            }
            payload.commandType = .download
            payload.remotePath = String(path)
            payload.commandText = nil
        } else if trimmed.lowercased().hasPrefix("/upload to ") {
            let path = trimmed.dropFirst("/upload to ".count).trimmingCharacters(in: .whitespaces)
            if path.isEmpty {
                errors.append("请输入上传目标路径")
            }
            guard let attachment else {
                errors.append("请先选择要上传的文件")
                return Result(payload: payload, clientMessageId: clientMessageId, errors: errors)
            }
            payload.commandType = .uploadNotify
            payload.remotePath = String(path)
            payload.commandText = nil
            payload.originalFileName = attachment.fileName
        } else if let aiMode {
            var prompt = trimmed
            if let range = prompt.range(of: "@ai") {
                prompt.removeSubrange(range)
            }
            prompt = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
            if prompt.isEmpty {
                errors.append("请填写要发送给 AI 的内容")
            }
            switch aiMode {
            case .qa:
                payload.commandType = .aiQA
                payload.prompt = prompt
                payload.options = ["language": "zh-CN"]
            case .agent:
                payload.commandType = .aiAgent
                payload.goal = prompt
                payload.constraints = ["maxSteps": CodableValue(20)]
            }
            payload.commandText = nil
        } else {
            payload.commandType = .terminal
            payload.commandText = trimmed
        }

        return Result(payload: payload, clientMessageId: clientMessageId, errors: errors)
    }
}
