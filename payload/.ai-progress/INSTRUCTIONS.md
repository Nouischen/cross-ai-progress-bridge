# Cross-AI Progress Bridge instructions

你正在一個已安裝 Cross-AI Progress Bridge 的專案內。所有命令都使用安裝在本專案的程式：

`python .ai-progress/bridge.py <command>`

程式會從自身所在的 `.ai-progress` 推導專案位置，不接受 `--root`，也不能用參數把資料寫到別處。先執行 `python .ai-progress/bridge.py status`。`AI_PROGRESS/tasks/*.md` 是唯一任務真相來源，不可直接覆寫。

寫入時，先在 `AI_PROGRESS/drafts/` 建立 JSON 草稿，再執行：

`python .ai-progress/bridge.py save --draft task.json`

草稿必有字串欄位：`title`、`status`（只能是 `active`、`blocked`、`completed`）、`goal`、`progress`、`next_steps`、`blockers`、`decisions`、`verification`、`related_files`、`rerun`。封存只能使用 `archive` 指令，不可在草稿填入 `archived`。`verification` 是任務內容的一部分，不代表系統或模型驗證狀態。所有內文欄位都不可包含以 `## ` 開頭的行。

新任務可省略 `id` 與 `expected_revision`；程式會從 title 產生穩定、可讀的 ASCII id，並以短雜湊避免不同中文或特殊字元標題撞名。更新既有任務前先 `show <id>`，草稿必填該任務目前的整數 `expected_revision`。已封存的 id 永不重用：需要重開工作時，建立新任務（不填舊 id）。revision 不一致時會保留 conflict，不會蓋掉新版。每個任務另有跨行程作業系統鎖，鎖會在程式結束或異常離開時自動釋放；`AI_PROGRESS/locks/` 中留下的安全鎖檔不要刪除。

自然語句的固定操作：

- 「記錄進度」：先問最少必要問題；依 schema 寫草稿並 `save`。若有同名任務，先 `show <id>`，用其 revision 更新。
- 「繼續上次」：`list --open`；若多於一件，列出簡短選項請使用者選擇；只有一件才 `show <id>` 後接續。
- 「繼續某任務」：先 `list --open`，用使用者給的名稱比對完整 id 或 title；只有唯一符合時才 `show <id>`，找不到或有多筆符合就列出簡短選項請使用者確認。
- 「我有哪些進度還沒做完的？」或「列出進行中」：只呼叫 `list --open`，簡短列出每件 active 與 blocked 的 id、title、status、updated_at、next_steps，不要倒出整份 Markdown。
- 要封存任務：先 `show <id>` 取得 revision，再執行 `python .ai-progress/bridge.py archive <id> --expected-revision <revision>`。

相容模式：讀取 `AI_PROGRESS/config.json` 的 `trigger_prefix`。只有當它是非空字串、而且使用者以該前綴開頭時，才把這套 bridge 指令套進既有系統；空字串表示可直接使用。其餘情況完全保留原本工作流。遇到已有同名檔案、不同資料結構或不清楚 mapping 時，停止並請使用者確認；不要搬移、刪除、讀取或覆寫對方的進度系統。

安全：不可把 `AI_PROGRESS`、`.ai-progress` 或 bridge 程式改成 symlink、捷徑、junction/reparse point；不可把 bridge 檔案寫到專案外；不得把密碼、金鑰、未去識別化病歷或其他敏感個資放入任務。不要以 shell、git、IDE 或聊天紀錄作為任務 metadata；一律以 bridge 命令與專案內檔案為準。
