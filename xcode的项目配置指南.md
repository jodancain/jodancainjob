# Xcode 项目配置指南

本指南说明如何把 `ios/` 目录下的 SwiftUI 代码放入一个新的 Xcode 项目，并保证 AppState、Features、Models、Networking 与 Utils 模块能够正常编译运行。

## 1. 环境要求
1. **Xcode 15.4+**：该代码面向 iOS 17 及以上系统，请使用支持 iOS 17 SDK 的 Xcode 版本。
2. **Swift 5.9+**：RemoteDev iOS Skeleton 使用最新的 Swift 并依赖 SwiftUI。
3. **Apple Developer 账户（可选）**：如需在真机或 TestFlight 上运行，需要有效的签名证书。

## 2. 创建基础工程
1. 打开 Xcode → `File > New > Project...` → 选择 **App** 模板。
2. 填写以下字段：
   - **Product Name**：如 `RemoteDevClient`
   - **Team**：选择你的 Apple ID 团队（或稍后配置）
   - **Organization Identifier**：如 `com.example`
   - **Interface**：`SwiftUI`
   - **Language**：`Swift`
   - **Use Core Data / Tests**：可全部关闭
3. 将 **Deployment Target** 设置为 **iOS 17.0**（`TARGETS > <App Target> > General > Deployment Info`）。

## 3. 导入源码结构
`ios/` 目录包含如下模块：

```
ios/
├── App/                # AppState 和入口
├── Features/
│   ├── Connect/        # 连接视图与 ViewModel
│   └── Chat/           # 聊天界面、消息、命令解析
├── Models/             # 连接与消息模型
├── Networking/         # HTTP、WebSocket、连接管理
└── Utils/              # UserDefaults 工具
```

将这些文件夹拖入 Xcode 项目的根 `Group`（勾选 *Copy items if needed*，Target 选择你的 App）。

## 4. Project/Target 配置
1. **AppState 与入口**：将 `ios/App/RemoteDevApp.swift` 设为项目主入口（确保 `@main` 的 struct 位于该文件）。
2. **Bundle Identifier**：在 `Signing & Capabilities` 中设置唯一的 Bundle ID，并选择 Team。
3. **Entitlements**：如需网络通信，启用 `Outgoing Connections (Client)` 网络权限（默认 `App Sandbox` 之外无需特殊配置）。
4. **Info.plist**：
   - 添加 `NSAppTransportSecurity > NSAllowsArbitraryLoads = YES`（如果要连接非 HTTPS 服务，建议仅限开发环境）。
   - 根据业务需要新增 `Privacy` 权限描述（如将来接入文件选择、相机等）。
5. **Build Settings**：
   - `Swift Language Version` 设为 `Swift 5.9` 或 `Swift 5` 最新版本。
   - `Enable Testing Search Paths` 等默认设置保持即可。
6. **Schemes**：使用默认 `Run` Scheme，若有多环境可复制并配置不同的 `Arguments/Environment Variables`（例如服务器 Host/Port）。

## 5. 依赖与资源
1. **无需外部包管理器**：当前代码仅依赖 Foundation/SwiftUI。若未来集成第三方库，可通过 Swift Package Manager：`File > Add Packages...`。
2. **资源文件**：如需添加 App 图标、颜色或预览数据，请在 `Assets.xcassets` 中配置，并在 SwiftUI 视图引用。

## 6. 运行与调试
1. 在 `ConnectView` 中输入服务器 Host、Port 与用户名，点击 Connect 触发 HTTP 测试请求与 WebSocket 引导。
2. `ChatView` 支持命令解析、附件处理与 AI 模式，可使用 `ChatViewModel.attachMockFile()` 在无系统文件选择器时生成附件测试。
3. 如需调试网络层，可在 `Networking/HTTPClient.swift` 与 `Networking/WebSocketClient.swift` 中添加断点。

## 7. 真机部署注意事项
1. 连接真机后，Xcode 会提示信任与安装开发证书。
2. 若服务器位于局域网，需要确保 iPhone 与 Mac 在同一网络，并在 `Settings > Developer` 中启用 `Local Network` 权限（若 App 请求）。
3. 调试完成后，可在 `Product > Archive` 生成 IPA，结合 TestFlight 或 Ad Hoc 分发。

## 8. 常见问题排查
| 问题 | 可能原因 | 解决方案 |
| --- | --- | --- |
| 连接失败 | ATS 拒绝非 HTTPS | 确认 `Info.plist` 的 `NSAppTransportSecurity` 设置或使用 HTTPS |
| WebSocket 断开 | 服务器 Host/Port 配置错误 | 在 `ConnectView` 中确认输入，与后端日志交叉验证 |
| 构建报错找不到文件 | 未勾选 *Copy items if needed* 或 Target 未选中 | 重新将 `ios/` 文件夹添加到项目并勾选目标 |
| 模拟器运行无响应 | Deployment Target 与模拟器系统不匹配 | 选择 iOS 17+ 模拟器或降低 Deployment Target（若代码兼容） |

遵循以上步骤即可将仓库中的 SwiftUI 模块快速嵌入新的 Xcode 项目，完成基础配置并开始开发。
