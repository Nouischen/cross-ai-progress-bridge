# Cross-AI Progress Bridge｜跨 AI 進度接力

> 換新對話、換模型，進度不用重講。

[繁體中文](#繁體中文) · [English](#english) · [Landing page](https://cross-ai-progress-bridge.pages.dev) · [MIT License](LICENSE)

## 繁體中文

Cross-AI Progress Bridge 把工作進度存成專案裡可讀的 Markdown。Claude Code、Codex，以及同一工具的新對話，只要開啟**同一個實體資料夾**，就能依序接手。

你可以直接說：

- `記錄進度`
- `繼續上次進度`
- `我有哪些進度還沒做完的？`
- `列出進行中`

它保存任務目標、目前成果、下一步、卡點、決策、驗證方式與相關檔案；不會把整段聊天記錄重新塞進下一個對話。

### 適合哪些情況

- **同模型換新對話**：Claude Code 換到新的 Claude Code 對話，或 Codex 換到新的 Codex 對話。
- **跨模型交班**：在 Claude Code 與 Codex 之間切換，讓不同工具接續、實作或審查。
- **一次管理多件事**：問「我有哪些進度還沒做完的？」即可列出 active 與 blocked 任務。
- **保留既有系統**：偵測到原有 AI 規則或進度名稱時，先停止並詢問；同意後只以隔離的 sidecar 模式共存。
- **純本機、可讀格式**：不需要 Obsidian、資料庫、帳號或專案後端；安裝後的 bridge 本身不連網，也沒有遙測。

這不是聊天記錄同步，也不是兩個 AI 同時修改同一份工作。它做的是**依序交班**；一次只讓一個 AI 更新同一任務。

## 新手安裝

### 先確認 Python 3.10 或更新版本

安裝器只使用 Python 3.10 以上版本的標準函式庫，不需要另外安裝套件。你可以先請 Claude Code 或 Codex「只檢查這台電腦是否有 Python 3.10 或更新版本，不要安裝也不要改檔」。

- Windows 可檢查 `py -3 --version` 或 `python --version`。
- macOS 可檢查 `python3 --version`。

如果沒有，請從 [Python 官方網站](https://www.python.org/downloads/)安裝後再繼續。專案本身仍不用手動下載 ZIP、解壓或搬檔。

### 第一次請用安全的空資料夾

不要直接在「桌面」本身、家目錄或放著很多專案的共同資料夾安裝。也不要拿含病歷、未去識別化個資、密碼、API key 或其他機密的資料夾測試。

**Windows**

1. 打開「檔案總管」。
2. 左邊點「文件」。
3. 在空白處按滑鼠右鍵，選「新增」→「資料夾」。
4. 命名為 `AI進度接力測試`。
5. 在 Claude Code 或 Codex 使用「開啟資料夾／開啟專案」功能，選剛才的資料夾。

**macOS**

1. 打開 Finder。
2. 左邊點「文件」（Documents）。
3. 選「檔案」→「新增檔案夾」。
4. 命名為 `AI進度接力測試`。
5. 在 Claude Code 或 Codex 開啟剛才的資料夾。

不同版本的按鈕名稱可能略有差異。重點只有一個：畫面裡的目前專案，必須是剛建立的資料夾，而不是「文件」、桌面或家目錄本身。

### 複製這段提示詞

同一段可以貼給 Claude Code 或 Codex。選一邊安裝一次即可；不要讓兩邊同時執行安裝。

**複製從這裡開始**

> 請直接在目前開啟的專案安裝 Cross-AI Progress Bridge，不要只解說。把 https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/bootstrap/install.py 下載到作業系統暫存資料夾（不要存進專案），先驗證 SHA-256 必須完全等於 F54D20B41681D9E1F044F78C3A0A2971537482F4216D5B2A2BAE01729EF8AC90；不符就停止，不得換來源。用 Python 3.10 或更新版本執行已驗證的 install.py，`--target` 指向目前專案的絕對路徑；若缺少合格的 Python，先停止、不要修改專案，並用白話教我從官方來源安裝。若回傳 `INSTALL_NEEDS_CONSENT`，只列出偵測名稱並問我；只有我明確同意後，才用同一檔案加上 `--mode sidecar --accept-existing I_ACCEPT_SIDECAR` 重跑。不要叫我手動下載、解壓或搬檔，也不要自行讀取、搬移或覆蓋舊進度；最後回報 `INSTALL_OK` 或錯誤。

**複製到這裡結束**

這不是手動下載流程：下載、驗證與執行都由目前的 Claude Code 或 Codex 完成。SHA-256 不符時必須停止。

## 第一次接力測試

安裝顯示 `INSTALL_OK` 後：

如果安裝結果寫的是 sidecar mode，下面第 1 句要改成 `接力：建立一筆「接力測試」任務，下一步寫「請另一個對話列出未完成進度」，然後記錄進度。`，第 3 句要改成 `接力：我有哪些進度還沒做完的？`。兩句都不能漏掉 `接力：`。

1. 在第一個 AI 說：`建立一筆「接力測試」任務，下一步寫「請另一個對話列出未完成進度」，然後記錄進度。`
2. 關掉該對話，或改用另一個 AI；讓新的 Claude Code／Codex 開啟**同一個實體資料夾**。
3. 在新對話問：`我有哪些進度還沒做完的？`

能看到「接力測試」才是功能上的成功。這個流程同樣適用於同模型換新對話，以及 Claude Code ↔ Codex 的跨模型交班。

## 日常用法

| 你說 | 系統會做什麼 |
|---|---|
| `記錄進度` | 新增或更新目前任務的 Markdown 進度 |
| `繼續上次進度` | 只有一筆未完成時直接讀取；多筆時列出讓你選 |
| `繼續某任務` | 依任務 ID 或標題（title）比對，只有唯一符合時才接續 |
| `我有哪些進度還沒做完的？` | 精簡列出 active 與 blocked 任務 |
| `列出進行中` | 顯示未完成工作的簡短清單 |

## 已有自己的系統怎麼辦

安裝器會先看專案最上層的**名稱**。若看到 `CLAUDE.md`、`AGENTS.md`，或名稱含 progress、tasks、進度、交班等項目，就輸出 `INSTALL_NEEDS_CONSENT`，列出名稱並停止；此時不會寫入專案。

你明確同意後，AI 才能以 `--mode sidecar --accept-existing I_ACCEPT_SIDECAR` 重跑。sidecar 會：

- 建立獨立的 `.ai-progress/` 與 `AI_PROGRESS/`。
- 在 Claude／Codex 入口加入有清楚標記、可移除的 bridge 規則；修改既有入口前先備份。
- 只回應帶有 `接力：` 前綴的指令，例如 `接力：記錄進度`、`接力：我有哪些進度還沒做完的？`。
- 不讀取、不搬移、不轉換、不覆蓋原本的進度內容。

這叫「隔離共存」，不是「自動整合」。如果之後要遷移舊資料，應另做人工確認，不在本安裝器的承諾內。

## 檔案結構

```text
.ai-progress/
├── bridge.py
├── INSTRUCTIONS.md
└── backups/install/
AI_PROGRESS/
├── config.json
├── README.md
├── tasks/          # 進行中的 Markdown 任務
├── archive/
├── drafts/
├── backups/
├── conflicts/
└── locks/          # 每筆任務的跨行程作業系統鎖檔
CLAUDE.md
AGENTS.md 或既有的 AGENTS.override.md
```

`AI_PROGRESS/tasks/*.md` 是任務的唯一真相來源；`.ai-progress/bridge.py` 是兩個 AI 共用的本機操作程式。JSON 只用於設定、草稿與衝突副本。

兩個入口沿用平台的官方專案指令機制：[Claude Code 讀取 `CLAUDE.md`](https://code.claude.com/docs/en/memory)，[Codex 依序尋找 `AGENTS.override.md`／`AGENTS.md`](https://developers.openai.com/codex/guides/agents-md)。bridge 的任務資料只維護一份，避免兩套規則分岔。

## Git、遠端與多台電腦

Git 專案可以使用，不必改成空白的非 Git 資料夾；但 Claude Code 與 Codex 必須指向**同一個 checkout／worktree**。如果一邊開主工作目錄，另一邊開隔離 worktree，它們看到的就不是同一份未提交進度。

這套工具不會自動跨電腦同步。要跨電腦接力，必須用 Git 或可信任的檔案同步方式同步**整個專案**，包含 `.ai-progress/`、`AI_PROGRESS/`、Claude／Codex 入口與任務相關檔案；兩邊仍要開啟同步後的同一份 checkout，並避免同時修改同一任務。

## 安全與限制

- 不要把密碼、金鑰、未去識別化病歷或敏感個資寫進進度檔。
- 安裝器限制目標在目前專案內，拒絕磁碟根目錄、家目錄、桌面根目錄，以及 bridge-owned 的 symlink／junction／reparse path。
- 儲存或封存任務時，bridge 會先取得該任務在 `AI_PROGRESS/locks/` 的跨行程作業系統鎖，再檢查 revision 並備份；revision 不符時保留 conflict，而不是蓋掉較新的版本。
- Claude Code、Codex 與其上層指令仍有自己的權限與資料政策；本工具不是 AI sandbox，無法阻止平台或其他規則讀取專案。
- 一般 claude.ai／ChatGPT 網頁聊天框若無法共同存取同一個本機專案資料夾，就不能直接使用。

更多細節見 [INSTALL.md](INSTALL.md) 與 [SECURITY.md](SECURITY.md)。

## English

Cross-AI Progress Bridge stores concise handoff state as Markdown inside a project. Fresh Claude Code or Codex conversations—and fresh conversations of the same tool—can resume work when they open the same physical folder.

Requirements: Python 3.10 or newer, local project-file access, and one safe project folder. The AI downloads the pinned installer to the operating-system temporary directory, verifies its SHA-256, and runs it; the user does not manually download, unzip, or move project files.

Paste the Chinese installer prompt above into either Claude Code or Codex once. Then create a test task in one conversation and ask `我有哪些進度還沒做完的？` in a fresh same-model or cross-model conversation that has opened the same physical folder.

If existing AI/progress names are detected, installation stops before writing. After explicit consent, sidecar mode uses the `接力：` prefix and a separate data directory. It does not read, migrate, transform, or overwrite legacy progress records. Git is supported, but both tools must use the same checkout/worktree.

## Author

Dr. Yu-Chieh Chen（陳昱傑醫師）

## License

[MIT](LICENSE)
