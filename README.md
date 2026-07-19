# Cross-AI Progress Bridge｜跨 AI 進度接力

> 換視窗、換模型，進度不用重講。

[繁體中文](#繁體中文) · [English](#english) · [Landing page](https://cross-ai-progress-bridge.pages.dev) · [MIT License](LICENSE)

## 繁體中文

Cross-AI Progress Bridge 是一套放在**你自己的專案資料夾**裡的 Markdown 進度系統。它讓 Claude Code 與 Codex，以及同一套 AI 的不同新對話，都能讀取同一份工作進度。

你可以直接說：

- `記錄進度`
- `繼續上次進度`
- `我有哪些進度還沒做完的？`
- `列出進行中`

它會保存任務目標、已完成內容、下一步、卡點、重要決策、驗證狀態、相關檔案與重跑方式。不是複製整段聊天記錄，也不是把所有上下文塞回新視窗。

### 它解決什麼

- **同模型換新對話**：Claude Code 換到另一個 Claude Code session，或 Codex 換到另一個 Codex task。
- **跨模型交班**：Claude Code 做完研究，交給 Codex 實作；或反過來利用另一個模型做審查。
- **查詢未完成事項**：不用記 task ID，直接問「我有哪些進度還沒做完的？」。
- **保留原本系統**：偵測到既有 `CLAUDE.md`、`AGENTS.md` 或進度系統時，先列出並詢問；未經同意不搬資料、不覆蓋原內容。
- **純本機 Markdown**：不需要 Obsidian、資料庫或另外註冊服務；本專案沒有遙測。

> 這不是聊天記錄同步，也不是兩個 AI 同時協作。它是**依序交班**：一邊記錄完成後，另一邊再接手。

## 三步驟開始

### 1. 先準備一個安全的測試資料夾

第一次使用，請不要直接拿正在工作的專案測試。

**Windows**

1. 打開「檔案總管」。
2. 左邊點「文件」。
3. 在空白處按滑鼠右鍵 →「新增」→「資料夾」。
4. 把資料夾命名為 `AI進度接力測試`。
5. 在 Claude Code 選 **Local / Select folder**，或在 Codex 新增 **local project**，選取這個資料夾。

**macOS**

1. 打開 Finder。
2. 左邊點「文件」（Documents）。
3. 選單「檔案」→「新增檔案夾」。
4. 命名為 `AI進度接力測試`。
5. 在 Claude Code 或 Codex 開啟這個資料夾。

不要用桌面本身、家目錄，或同時放很多專案的共同資料夾。也不要用含病歷、未去識別化個資、密碼、金鑰或其他敏感資料的資料夾測試。

### 2. 把這一句貼給 Claude Code 或 Codex

只要貼在其中一邊一次；你不用下載、解壓或搬任何檔案。

> 請把 https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/INSTALL.md 下載到系統暫存資料夾，確認 SHA-256 為 62B052F6791BDA02C6749B3FD8FEDF320C3A4EE969EC8D32C432E438032C4FA2，完整讀取後，在目前專案逐條執行。不要只說明步驟，請直接安裝；無法完整讀取或雜湊不符就停止，不要猜測或改用其他來源。

安裝器會自行建立 Claude Code 與 Codex 兩邊的入口。若偵測到既有系統，它會先詢問，不會擅自改寫。

### 3. 用兩個全新對話完成驗證

安裝完成後會顯示 `NOT READY`，這是正常的。接著：

1. 在**全新的 Claude Code 對話**，第一句輸入：`驗證接力`
2. 在**全新的 Codex 對話**，第一句輸入：`驗證接力`
3. 兩邊都完成後，回到任一邊輸入：`完成驗證`

看到 `READY` 才代表兩邊真的讀到同一組本機檔案。完整安裝提示詞不用貼第二次。

## 日常用法

| 你說 | 系統會做什麼 |
|---|---|
| `記錄進度` | 建立或更新目前任務的 Markdown 進度檔 |
| `繼續上次進度` | 讀取唯一未完成任務；若有多筆就列出讓你選 |
| `繼續某任務` | 依 task ID 或標題接續指定任務 |
| `我有哪些進度還沒做完的？` | 列出 active 與 blocked 任務的狀態、更新日與下一步 |
| `列出進行中` | 以精簡清單顯示未完成工作 |
| `驗證接力` | 在全新 session 證明目前 AI 讀到同一個專案 |
| `完成驗證` | 兩邊都通過後，把狀態切為 READY |
| `重設驗證` | 重新建立一輪雙引擎驗證 |

## 與既有系統相容

本安裝器採「先偵測、再詢問、最後才整合」：

1. 先只看檔名，不讀任務內容。
2. 發現既有規則或進度來源時，列出準備讀取的檔案。
3. 只有你回覆「允許」後才讀取並嘗試對應。
4. 沿用原路徑、格式與封存方式；不能可靠對應狀態時會停止詢問，不會自創規則。

因此它適合當外掛，但不能誠實保證每一套自製系統都能零判斷自動合併。遇到語意不明的狀態或多套互相衝突的規則，停下來請使用者拍板才是正確行為。

## 檔案結構

Fresh 模式預設建立：

```text
AI_SYSTEM/
├── manifest.md
├── progress-bridge.md
├── backups/runtime/
└── verification/
progress/
├── archive/
└── conflicts/
CLAUDE.md
AGENTS.md 或 AGENTS.override.md
```

- `AI_SYSTEM/manifest.md`：路徑、版本、模式與驗證狀態。
- `AI_SYSTEM/progress-bridge.md`：Claude Code 與 Codex 共用的操作協定。
- `progress/*.md`：目前未完成任務。
- `progress/archive/`：已完成或封存內容。
- `progress/conflicts/`：偵測到同時修改時保留候選內容，不覆蓋原檔。

## 安全與限制

- **不要存放**密碼、API key、未去識別化病歷或其他敏感個資。
- 安裝與進度檔都在使用者自己的專案資料夾；本專案沒有伺服器、帳號或遙測。
- 新手第一次請使用**不在 Git repository 裡**的空白資料夾。Claude Code Desktop 對 Git 專案可能使用隔離 worktree；如果兩邊不是同一個實體 checkout，就不會共用進度。
- 熟悉 Git 的使用者可在 Claude Code CLI／IDE 與 Codex Local 中使用，但要自行確認兩邊明確指向同一個 checkout。
- 平台若禁止必要的檔案 metadata 檢查或本機寫入，安裝器會安全停止。
- 一次只讓一個 AI 修改同一任務；這不是即時同步或衝突自動合併工具。
- 一般 claude.ai／ChatGPT 網頁聊天框無法直接使用，因為它們沒有共同的本機專案資料夾。

## 為什麼不是只有一張手動交班單？

像 [CONTINUE.md](https://continue.md/) 這類單檔慣例很輕巧，但通常仍要自己維護、只有一個當前狀態，也沒有 Claude Code／Codex 的雙入口與 fresh-session 驗證。完整的多代理任務平台則常需要額外 CLI、資料庫或複雜 lifecycle。

本專案刻意落在中間：仍是可讀的 Markdown，卻加入多任務、自然語言查詢、相容模式、衝突保留與可驗證的雙引擎接力。

技術基礎是兩個平台原生支援的專案指令檔：[Claude Code 讀取 `CLAUDE.md`](https://docs.anthropic.com/en/docs/claude-code/memory)，[Codex 可由 `AGENTS.md` 指引](https://openai.com/index/introducing-codex/)。協定與進度本體只維護一份，避免 Claude／Codex 各寫一套後逐漸分岔。

## 完整安裝規格與驗證

- [INSTALL.md](INSTALL.md)：公開、固定且可稽核的完整安裝提示詞。
- [SECURITY.md](SECURITY.md)：威脅模型、回報方式與隱私界線。
- `tests/validate_release.py`：檢查 Landing page、短安裝指令、版本鎖定、安全聲明與必要檔案。
- 公開套件 `v1.0.0` 內含已通過 Claude Code／Codex 端到端驗證的 Progress Bridge protocol 3.9。

## English

Cross-AI Progress Bridge is a local, Markdown-based handoff system for Claude Code, Codex, and fresh sessions of the same tool. It records goals, completed work, next steps, blockers, decisions, evidence, relevant files, and rerun instructions—without copying the entire chat history.

The beginner flow is intentionally conversational: create a clean test folder, paste one short installer sentence into either Claude Code or Codex, then verify both tools from fresh sessions. No manual download, extraction, database, Obsidian vault, account, or telemetry is required.

Key commands include `record progress`, `continue the last task`, `list unfinished progress`, `verify handoff`, and `complete verification`. The Traditional Chinese phrases above are the fully tested public interface in v1.0.0.

For existing project systems, the installer is additive and consent-gated: it inventories file names first, asks before reading or integrating legacy progress, preserves existing content, and stops when it cannot map semantics safely.

See the [landing page](https://cross-ai-progress-bridge.pages.dev) for the guided setup and [INSTALL.md](INSTALL.md) for the auditable installer specification.

## Author

Dr. Yu-Chieh Chen（陳昱傑醫師）

## License

[MIT](LICENSE)
