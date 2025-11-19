import Foundation

struct PendingAttachment: Identifiable, Equatable {
    let id = UUID()
    var fileURL: URL
    var fileName: String
    var fileSize: Int64
}
