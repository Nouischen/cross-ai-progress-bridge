# AI Progress

這個資料夾是專案內的跨 AI 進度真相來源。

- `tasks/`：進行中或已完成的 Markdown 任務（唯一 canonical record）
- `archive/`：已封存任務
- `drafts/`：AI 先寫入的 JSON 草稿，再由 bridge 套用
- `conflicts/`：revision 不一致時保留的草稿，絕不覆蓋原任務
- `backups/`：更新與封存前的可回復備份
- `locks/`：每任務跨行程鎖檔；程式結束或異常離開會自動釋放作業系統鎖，鎖檔本身可永久保留
- `config.json`：安裝 ID、模式與自然語句前綴

不要手動刪除 `config.json`、鎖檔或改寫 task front matter。任務中的 `Verification` 只是該任務的驗收紀錄，不是 AI surface 的 READY 狀態。
