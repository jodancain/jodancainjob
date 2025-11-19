# RemoteDev iOS Skeleton

This directory contains a SwiftUI-only project skeleton that targets iOS 17+ and wires together:

- A connect screen that performs HTTP test requests and bootstraps the WebSocket connection
- A chat experience with command parsing, attachment handling, and AI modes
- Shared networking utilities (URLSession + URLSessionWebSocketTask)
- Models for messages, commands, and server events
- Persistence for the most recent host/port/username via `UserDefaults`

The code is structured into the following modules:

```
ios/
├── App/                # AppState and entry point
├── Features/
│   ├── Connect/        # ConnectView and view model
│   └── Chat/           # Chat screen, messages, parser
├── Models/             # Connection + message models
├── Networking/         # HTTP client, WebSocket client, connection manager
└── Utils/              # UserDefaults helpers
```

The networking layer is ready to call the real backend once embedded into an Xcode project. For quick UI prototyping, the ChatView model exposes `attachMockFile()` to fabricate a file upload payload without using a file picker.
