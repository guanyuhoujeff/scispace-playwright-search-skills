# SciSpace Playwright Search Skill

這是一個透過 Playwright MCP 自動化執行 SciSpace (scispace.com) 文獻搜尋的 Skill。它能夠根據預設的期刊列表 (`journal-slugs.json`) 自動過濾搜尋結果，並將結果匯出為結構化的 JSON 格式。

## 功能特點

- **自動化搜尋**：直接導航至帶有查詢參數的 SciSpace 搜尋頁面。
- **期刊過濾**：支援透過 `journal-slugs.json` 檔案指定預設的期刊列表（Whitelist），確保搜尋結果來自特定的高品質來源。
- **資料匯出**：自動擷取並匯出論文的關鍵資訊，包括標題、作者、期刊、發表日期、摘要、連結與 DOI。
- **自動載入**：支援自動點擊 "Load more papers" 以獲取指定數量的搜尋結果。
- **互動檢查**：內建登入狀態檢查與人機驗證（MFA/CAPTCHA）暫停機制，確保流程順暢。

## 前置需求 (Prerequisites)

1. **Python 3**：用於執行 URL 建構腳本。
2. **Playwright MCP**：此 Skill 依賴 Playwright MCP 進行瀏覽器操作。
3. **SciSpace 帳號**：
   - 執行前請確保瀏覽器 **已經登入** SciSpace。
   - 此 Skill **不會** 自動輸入帳號密碼，若未登入會暫停提示使用者手動登入。

## 設定 (Configuration)

### 1. 期刊列表 (`journal-slugs.json`)
此 Skill 會自動搜尋 `journal-slugs.json` 檔案，搜尋順序如下（找到即停止）：
1. **當前工作目錄** (`./journal-slugs.json`)  <-- *您目前已在此位置建立檔案，此為最優先載入的路徑。*
2. 使用者家目錄 (`~/journal-slugs.json`)
3. 指定路徑 (`~/Desktop/workspace/skills/scispace/journal-slugs.json`)

**支援的 JSON 格式**：
腳本會自動讀取 `journals` 鍵值下的所有巢狀結構，並遞迴收集所有字串形式的 slug。您可以使用簡單列表或依照類別分組的複雜結構。

**簡單列表範例**：
```json
{
  "journals": [
    "nature",
    "science"
  ]
}
```

**分組結構範例（如您目前的檔案）**：
```json
{
  "journals": {
    "Top Tier": {
      "Nature": "nature",
      "Science": "science"
    },
    "Finance": {
      "Journal of Finance": "journal-of-finance-yjgcepyl",
      "Review of Financial Studies": "review-of-financial-studies-2apmvr5d"
    }
  }
}
```
*注意：只要位於 `journals` 鍵值下的任何層級，所有的 slug 字串都會被收集並加入過濾條件。*

## 使用方法 (Usage)

在對話中直接要求 Agent 進行搜尋，例如：

> "幫我搜尋關於 'LLM reasoning' 的論文，並匯出前 10 筆結果。"

或者指定使用期刊過濾：

> "使用預設的期刊列表搜尋 'Quantum Computing'。"

### 執行流程
1. Agent 呼叫 Python 腳本讀取 `journal-slugs.json` 並產生搜尋 URL。
2. 開啟瀏覽器導航至 SciSpace。
3. 檢查登入狀態（若未登入則提示）。
4. 切換至 "High Quality" 標籤（預設）。
5. 擷取搜尋結果並匯出。

## 輸出格式 (Output)

匯出的 JSON 資料包含以下欄位：
- `title`: 論文標題
- `authors`: 作者列表
- `journal`: 期刊名稱
- `publication_date`: 發表日期
- `summarized_abstract`: 摘要總結
- `paper_link`: 論文連結
- `doi_url`: DOI 連結

## 疑難排解 (Troubleshooting)

- **Login Prompt Displayed**: 如果 Agent 停在登入畫面，請手動在瀏覽器視窗中完成登入，然後通知 Agent 繼續。
- **Journal Filter Not Applied**: 確認 `journal-slugs.json` 檔案位置正確且格式無誤。
- **No Results**: 可能是期刊過濾器太嚴格，可以嘗試不使用期刊過濾重新搜尋。
