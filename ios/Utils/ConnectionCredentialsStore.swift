import Foundation

struct ConnectionCredentialsStore {
    private let defaults = UserDefaults.standard
    private let key = "remote_dev_credentials"

    func save(credentials: ConnectionConfig) {
        let stored = StoredCredentials(host: credentials.host,
                                       port: credentials.port,
                                       username: credentials.username)
        guard let data = try? JSONEncoder().encode(stored) else { return }
        defaults.set(data, forKey: key)
    }

    func load() -> StoredCredentials? {
        guard let data = defaults.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(StoredCredentials.self, from: data)
    }
}
