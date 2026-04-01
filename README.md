# Crystal Dashboard GPT - 每日水晶戰情室

這是一個可直接執行的 Streamlit 看板，用來做「每日水晶市場與友商監控」。

## 功能

- 世界/台灣/大陸/香港水晶趨勢與新聞雷達（Google News RSS）。
- 台灣 Top20 友商名單管理（可在側欄編輯）。
- 友商官網/IG 清單載入（CSV）。
- 貼文成效分析：
  - 點擊最高貼文 Top 10
  - 互動最高貼文 Top 10
  - 受歡迎產品/新品排序
  - 友商整體績效排行
- 自動產生每日戰情摘要，可下載成 Markdown。

## 可視化網頁要看哪裡？

### 本機直接看

```bash
pip install -r requirements.txt
streamlit run app.py
```

啟動後，終端機會出現類似：

- `Local URL: http://localhost:8501`

直接用瀏覽器打開 `http://localhost:8501` 就能看到看板。

## 這些檔案可以直接放 GitHub 嗎？

可以，建議把以下檔案直接放在 repo 根目錄：

- `app.py`
- `requirements.txt`
- `README.md`

然後你有兩種常見做法：

1. **只放程式碼在 GitHub（內部使用）**
   - 你和團隊成員 clone 下來後，照「本機直接看」步驟執行。

2. **放 GitHub + 直接部署成線上網址（推薦）**
   - 用 [Streamlit Community Cloud](https://streamlit.io/cloud) 連你的 GitHub repo。
   - 設定主檔為 `app.py`，它會自動讀 `requirements.txt` 安裝套件。
   - 部署完成後會有一個公開或受控的網址，打開就能看看板。

## CSV 欄位格式

### 友商清單 CSV

```csv
competitor,ig_account,website
友商A,https://www.instagram.com/xxx,https://xxx.com
```

### 貼文資料 CSV

```csv
date,competitor,platform,post_text,product,likes,comments,shares,clicks
2026-04-01,友商A,IG,新品上架貼文,紫水晶手鍊,100,20,5,400
```

## 注意

預設友商名稱與示範數據僅供展示流程，請替換成你的真實監控名單與每日匯出資料。
