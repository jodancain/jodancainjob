import Foundation

struct TestConnectionResponse: Codable {
    let ok: Bool
    let message: String?
}

struct FileUploadResponse: Codable {
    let remotePath: String
    let fileId: String
    let fileName: String
    let fileSize: Int
}

struct HttpClient {
    let urlSession: URLSession

    init(configuration: URLSessionConfiguration = .default) {
        configuration.waitsForConnectivity = true
        self.urlSession = URLSession(configuration: configuration)
    }

    func testConnection(config: ConnectionConfig) async throws -> TestConnectionResponse {
        guard let url = config.baseURL?.appending(path: "/api/test-connection") else {
            throw URLError(.badURL)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        if let header = config.basicAuthHeader {
            request.setValue(header, forHTTPHeaderField: "Authorization")
        }
        let (data, response) = try await urlSession.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              200..<300 ~= httpResponse.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(TestConnectionResponse.self, from: data)
    }

    func uploadFile(config: ConnectionConfig,
                    sessionId: String?,
                    remotePath: String,
                    fileURL: URL) async throws -> FileUploadResponse {
        guard let url = config.baseURL?.appending(path: "/api/files/upload") else {
            throw URLError(.badURL)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        if let header = config.basicAuthHeader {
            request.setValue(header, forHTTPHeaderField: "Authorization")
        }

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        let body = try MultipartFormDataBuilder(boundary: boundary)
            .addTextField(name: "sessionId", value: sessionId)
            .addTextField(name: "remotePath", value: remotePath)
            .addFileField(name: "file",
                          fileURL: fileURL,
                          fileName: fileURL.lastPathComponent,
                          mimeType: "application/octet-stream")
            .build()
        request.httpBody = body

        let (data, response) = try await urlSession.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              200..<300 ~= httpResponse.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(FileUploadResponse.self, from: data)
    }
}

struct MultipartFormDataBuilder {
    private var boundary: String
    private var body = Data()

    init(boundary: String) {
        self.boundary = boundary
    }

    func addTextField(name: String, value: String?) -> MultipartFormDataBuilder {
        var builder = self
        guard let value else { return builder }
        var field = "--\(boundary)\r\n"
        field += "Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n"
        field += "\(value)\r\n"
        builder.body.append(field.data(using: .utf8) ?? Data())
        return builder
    }

    func addFileField(name: String,
                      fileURL: URL,
                      fileName: String,
                      mimeType: String) throws -> MultipartFormDataBuilder {
        var builder = self
        let fileData = try Data(contentsOf: fileURL)
        var field = "--\(boundary)\r\n"
        field += "Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(fileName)\"\r\n"
        field += "Content-Type: \(mimeType)\r\n\r\n"
        builder.body.append(field.data(using: .utf8) ?? Data())
        builder.body.append(fileData)
        builder.body.append("\r\n".data(using: .utf8) ?? Data())
        return builder
    }

    func build() -> Data {
        var finalData = body
        finalData.append("--\(boundary)--\r\n".data(using: .utf8) ?? Data())
        return finalData
    }
}
