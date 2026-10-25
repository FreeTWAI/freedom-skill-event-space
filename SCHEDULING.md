# 空間排程與預約規範

本文檔整理了空間預約的排程工作流、場地預約規則以及結構化資料定義。

## 1. 空間排程工作流 (Scheduling Workflows)

根據 [實作手冊](SKILL.md)，排程工作流包含以下步驟：

1. **需求整理**：填寫 `templates/event-brief.md`，確認活動目的、人數、日期與場地需求。
2. **場地評估**：比較候選場地，記錄報價、進撤場時段、無障礙設施及其他待確認項目。
3. **流程規劃**：使用 `templates/run-of-show.csv` 安排活動流程（報到、開場、討論、收尾），並指派每一段的負責角色。
4. **計畫結構化**：將容量、人數與分工寫入 `templates/event-plan.json`，進行資料驗證。
5. **確認與反饋**：主辦人核對未決事項。活動後記錄實際變更，刪除所有個人資料，並提交模板改善 PR。

## 2. 預約規則 (Reservation Rules)

- **隱私與個資保護**：公開範例必須使用虛構/合成資料。不得讀取或提交任何真實姓名、私人名單、聯絡電話、客戶紀錄、付款資料或未授權的教材。
- **邊界限制**：本模組不負責直接預訂場地、簽約、收款或確認現場安全（如容量限制、逃生動線、器材或用電安全）。
- **權限控制**：模板與指令碼不直接呼叫平台寫入 API，不取得使用者 Token。場地合約與對外邀請需由當事人透過既有授權管道操作。
- **安全性與真實性**：未經人工現場驗證的事項（例如無障礙動線、實際場地條件）必須明確標示，不得將模板驗證通過視為已確認的實體事實。

## 3. JSON 結構定義 (Schema Definitions)

活動企劃的結構化資料儲存於 `event-plan.json` 中，並透過 `scripts/validate.py` 進行檢查。主要的欄位定義如下：

- `data_classification` (String): 必填，公開範例必須固定填寫 `"synthetic"`，私人真實紀錄不會放入此 repo。
- `kind` (String): 必填，固定為 `"event-space"`。
- `title` (String): 必填，非空字串，活動的名稱。
- `expected_attendees` (Integer): 必填，正整數，預期參與人數。
- `venue_capacity` (Integer): 必填，正整數，場地最大容納人數。必須大於或等於 `expected_attendees`。
- `roles` (Array of Strings): 必填，包含非空字串的陣列，列出活動中所有指派的角色。
- `agenda` (Array of Objects): 必填，至少包含一個流程項目。每個項目包含：
  - `start_minute` (Number): 必填，非負數，開始分鐘數。
  - `duration_minutes` (Number): 必填，正數，持續時間。
  - `title` (String): 必填，非空字串，流程名稱。
  - `owner_role` (String): 必填，負責此流程的角色，必須存在於上方的 `roles` 清單中。
  - *(注意：流程時間不可重疊，且必須依時間順序排列。)*
- `unresolved` (Array of Strings): 選填，列出尚未向場地確認的事項。
