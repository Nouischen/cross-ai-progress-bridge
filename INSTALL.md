# 安裝器說明｜Cross-AI Progress Bridge v1.0.0

這一頁是給使用者與審查者看的簡明規格。實際安裝由固定版本的 `bootstrap/install.py` 完成，不再要求 AI 解讀一份數萬字的安裝提示詞。

## 使用前

- 需要 Python 3.10 或更新版本；只用標準函式庫，不安裝額外套件。
- 先在 Windows「文件」或 macOS「Documents」建立單一、空白的測試資料夾，再讓 Claude Code 或 Codex 開啟它。
- 不要把磁碟根目錄、家目錄、桌面根目錄、多專案共同根目錄，或含病歷、未去識別化個資、密碼與金鑰的資料夾當測試目標。
- Claude Code 與 Codex 接力時，兩邊必須開啟同一個實體資料夾。Git 專案可以使用，但必須是同一個 checkout／worktree。

## 可直接貼給 Claude Code 或 Codex 的提示詞

**複製從這裡開始**

> 請直接在目前開啟的專案安裝 Cross-AI Progress Bridge，不要只解說。把 https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/bootstrap/install.py 下載到作業系統暫存資料夾（不要存進專案），先驗證 SHA-256 必須完全等於 F54D20B41681D9E1F044F78C3A0A2971537482F4216D5B2A2BAE01729EF8AC90；不符就停止，不得換來源。用 Python 3.10 或更新版本執行已驗證的 install.py，--target 指向目前專案的絕對路徑；若缺少合格的 Python，先停止、不要修改專案，並用白話教我從官方來源安裝。若回傳 INSTALL_NEEDS_CONSENT，只列出偵測名稱並問我；只有我明確同意後，才用同一檔案加上 --mode sidecar --accept-existing I_ACCEPT_SIDECAR 重跑。不要叫我手動下載、解壓或搬檔，也不要自行讀取、搬移或覆蓋舊進度；最後回報 INSTALL_OK 或錯誤。

**複製到這裡結束**

這段提示詞刻意不綁定 PowerShell、curl 或其他單一下載工具；Claude Code／Codex 應使用目前作業系統可用的方法，把安裝器放在系統暫存目錄。使用者不需要手動下載專案檔案。

## 固定來源與完整性

- URL：`https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/bootstrap/install.py`
- SHA-256：`F54D20B41681D9E1F044F78C3A0A2971537482F4216D5B2A2BAE01729EF8AC90`

雜湊必須在執行前比對，而且要完全相同。下載失敗、雜湊不同、找不到 Python 3.10 以上版本，或無法確認目前專案路徑時，都應停止，不得換用未指定來源。

## 安裝器的確定行為

`bootstrap/install.py` 是由 `bootstrap/install.py.in` 與版本庫內的 payload 產生的單檔安裝器。payload 內嵌在已驗證的安裝器裡；執行時不再下載相依項目，也不要求 AI 自行生成協定。

一般執行的等效介面是：

```text
python3 <暫存路徑>/install.py --target <目前專案絕對路徑>
```

Windows 上的 Python 3.10+ 命令可能是 `py -3` 或 `python`；由目前的 AI 依實際環境選擇並確認版本。`--target` 必須明確指向專案，不應依賴暫存檔所在位置。

### Fresh 模式

若專案最上層沒有偵測到既有 AI／進度名稱，安裝器會建立：

- `.ai-progress/bridge.py` 與 `.ai-progress/INSTRUCTIONS.md`
- `AI_PROGRESS/config.json`、`AI_PROGRESS/README.md`、`AI_PROGRESS/tasks/`，以及封存／草稿／備份／衝突子目錄與每任務鎖檔所在的 `AI_PROGRESS/locks/`
- Claude Code 的 `CLAUDE.md` 入口
- Codex 的 `AGENTS.md` 入口

成功時輸出 `INSTALL_OK`。再次執行相同版本會驗證 bridge-owned 檔案與入口標記；完全一致時回報 `ALREADY_INSTALLED`，不重複加入規則。

### 偵測到既有系統

安裝器先只盤點專案最上層的名稱，不讀舊任務內容。看到既有 `CLAUDE.md`、`AGENTS.md`、`AGENTS.override.md`，或名稱含 progress、state、tasks、handoff、進度、任務、交班等項目時，它會：

1. 輸出 `INSTALL_NEEDS_CONSENT` 與偵測到的名稱。
2. 以專用退出狀態停止，且不寫入專案。
3. 等使用者明確同意後，才允許同一個已驗證安裝器以以下參數重跑：

```text
--target <同一專案> --mode sidecar --accept-existing I_ACCEPT_SIDECAR
```

sidecar 建立自己的 `.ai-progress/` 與 `AI_PROGRESS/`，修改既有 Claude／Codex 入口前先備份；Codex 若已有 `AGENTS.override.md`，就沿用它而不另建 `AGENTS.md`。bridge 只處理以 `接力：` 開頭的自然語句。它不讀取、不搬移、不轉換、不覆蓋舊進度；這是隔離共存，不是舊系統遷移。

## 安全邊界

- 所有 bridge-owned 路徑必須留在 `--target` 之內。
- 安裝器拒絕磁碟／檔案系統根目錄、家目錄、桌面根目錄，以及 link、symlink、junction 或 reparse target。
- 新增 bridge-owned 檔案採只新增；修改入口前保存備份，錯誤時嘗試回復本次變更。
- 任務更新與封存由本機 bridge CLI 執行；它會先取得每任務的跨行程作業系統鎖，再進行 revision guard、備份與 conflict 保留。
- 本工具不是 AI sandbox，不能撤回平台已載入的上層指令，也不能阻止 Claude Code／Codex 本身依其權限讀取其他專案檔案。
- 不得將密碼、API key、未去識別化病歷或其他敏感個資寫入進度檔。

## 安裝後怎麼確認

功能測試比安裝訊息更重要：在一個對話建立並「記錄進度」，再讓開啟同一實體資料夾的新對話詢問「我有哪些進度還沒做完的？」。同模型換新對話與 Claude Code ↔ Codex 都適用。

若安裝結果是 sidecar mode，記錄時必須說 `接力：記錄進度`，查詢時必須說 `接力：我有哪些進度還沒做完的？`；兩個測試指令都要有 `接力：` 前綴。

## 可重現建置

維護者可在 repository root 執行：

```text
python tools/build_installer.py --check
python -m unittest discover -s tests -p "test_*.py" -v
python tests/validate_release.py
```

`tools/build_installer.py --check` 會確認公開的 `bootstrap/install.py` 與 template＋payload 產物一致；release validation 會再比對本頁、README、Security 與 landing page 所列的固定 URL／SHA-256。
