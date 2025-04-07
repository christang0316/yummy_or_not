# 🌟 Yummy or Not

一個使用 Gemini AI 搭配 IG Reels 分析的食讞幫手，將網路評論、地點、情緒評算與語氣展現組合，自動產生「有語氣、有笑點、有感觸」的簡介。

---

## 🚀 項目特色

- 使用 Gemini Pro (1.5 & 2.0) 及時摘要 IG Reels 内容與相關網路評價
- 使用現在流行的社交軟體 Instagram 作為主要使用平台，提升民眾接觸的可能性
- 自動抓取 PTT 食物版的網路評論
- 支援不同語氣：普通 / 迷因風格 / 情緒化 / 簡短
- 擴充簡介設計：😍 優點、😓 缺點、👋 推薦群組

---

## 🎓 開發工具與技術

- **Google Generative AI SDK**: Gemini Pro 1.5 / 2.0 解析與生成回覆
- **Meta for Developer (Instagram API): 連結機器人帳號並讀取使用者訊息
- **BeautifulSoup**: 爬取 PTT 網路評論
- **JSON 資料檔**: 存儲用戶使用情形
- **Flask**: 後端開發，Webhook API 主程式
- **GitHub**: 多人協作與版本控制
- **Render**: 部屬程式

---

## 📂 目錄組織

- `main.py` - 主程式，處理 Webhook 週期上傳 IG reels、快速回覆
- `Gemini_tone_module.py` - 擺放不同語氣解析與 Gemini 互動模塊
- `style_module.py` - 簡介形式模板與主 prompt 管理
- `rating_system.py` - 真實性評分模型
- `find_comments_on_web.py` - 爬取 PTT 食物版關聯評論
- `replies.json` - 預先定義好的 quick_reply 及 tone 語言
- `constants.py` - 密鑰與 token
- `user_data.json` - 持續性儲存用戶資料

---

## ✨ 啟動項目

1. 確保已安裝 Python >= 3.10
2. 安裝相關契會

```bash
pip install -r requirements.txt
```

3. 啟動 Flask 服務

```bash
python main.py
```

---

## 🔧 TODO / 未來計畫

- [ ] 移轉用戶資料到 PostgreSQL 保持性更高符合 cloud-ready
- [ ] 整合更多食讞資料源 (e.g. Google 評分)
- [ ] 支援圖片認識餐點和加工 Gemini Vision API

---

## ✉️ 聯絡我們

如果你對該項目有興趣或想了解更多，歡迎聯絡我們！
Email: christang426859@gmail.com 

