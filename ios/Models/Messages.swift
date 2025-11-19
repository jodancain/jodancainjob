import Foundation
import SwiftUI

enum ChatRole: String, Codable {
    case user
    case assistant
    case system
}

enum MessageKind {
    case text(String)
    case terminal(String, isError: Bool)
    case toolLog(String)
    case download(downloadUrl: URL, fileName: String, fileSize: Int)
}

struct ChatMessage: Identifiable {
    var id: UUID
    var role: ChatRole
    var kind: MessageKind
    var timestamp: Date
    var clientMessageId: UUID?

    init(id: UUID = UUID(),
         role: ChatRole,
         kind: MessageKind,
         timestamp: Date = .init(),
         clientMessageId: UUID? = nil) {
        self.id = id
        self.role = role
        self.kind = kind
        self.timestamp = timestamp
        self.clientMessageId = clientMessageId
    }
}

enum CommandType: String, Codable {
    case terminal
    case download
    case uploadNotify = "upload_notify"
    case aiQA = "ai_qa"
    case aiAgent = "ai_agent"
}

struct CommandEnvelope: Codable {
    var type: String = "client_command"
    var data: CommandData

    struct CommandData: Codable {
        var clientMessageId: UUID
        var sessionId: String?
        var payload: CommandPayload
    }
}

struct CommandPayload: Codable {
    var commandType: CommandType
    var commandText: String?
    var remotePath: String?
    var prompt: String?
    var goal: String?
    var options: [String: String]?
    var constraints: [String: CodableValue]?
    var context: [String: CodableValue]?
    var originalFileName: String?
    var fileId: String?
    var extra: [String: String]?
}

struct CodableValue: Codable {
    let value: AnyCodable

    init(_ value: Any) {
        self.value = AnyCodable(value)
    }

    init(from decoder: Decoder) throws {
        value = try AnyCodable(from: decoder)
    }

    func encode(to encoder: Encoder) throws {
        try value.encode(to: encoder)
    }
}

struct AnyCodable: Codable {
    private let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array
        } else {
            throw DecodingError.dataCorruptedError(in: container,
                                                  debugDescription: "Unsupported type")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let bool as Bool:
            try container.encode(bool)
        case let string as String:
            try container.encode(string)
        case let dict as [String: AnyCodable]:
            try container.encode(dict)
        case let array as [AnyCodable]:
            try container.encode(array)
        default:
            throw EncodingError.invalidValue(value,
                                             EncodingError.Context(codingPath: encoder.codingPath,
                                                                   debugDescription: "Unsupported type"))
        }
    }
}
