import Foundation

protocol WebSocketClientDelegate: AnyObject {
    func webSocketClient(_ client: WebSocketClient, didReceive message: Result<URLSessionWebSocketTask.Message, Error>)
    func webSocketClientDidClose(_ client: WebSocketClient, error: Error?)
    func webSocketClientDidOpen(_ client: WebSocketClient)
}

final class WebSocketClient: NSObject {
    private var task: URLSessionWebSocketTask?
    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.default
        return URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
    }()

    weak var delegate: WebSocketClientDelegate?

    func connect(request: URLRequest) {
        disconnect()
        task = session.webSocketTask(with: request)
        task?.resume()
        receiveLoop()
    }

    func disconnect() {
        task?.cancel(with: .goingAway, reason: nil)
        task = nil
    }

    func send(data: Data) async throws {
        try await task?.send(.data(data))
    }

    private func receiveLoop() {
        task?.receive { [weak self] result in
            guard let self else { return }
            self.delegate?.webSocketClient(self, didReceive: result)
            if case .failure = result { return }
            self.receiveLoop()
        }
    }
}

extension WebSocketClient: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        delegate?.webSocketClientDidOpen(self)
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        delegate?.webSocketClientDidClose(self, error: nil)
    }
}
