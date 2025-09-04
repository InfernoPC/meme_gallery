# Meme Gallery

🎉 **Meme Gallery** — 你的本地梗圖、貼圖、表情包管理神器！  
讓快樂、創意、日常吐槽都能井然有序，隨時召喚！

---

## ✨ 主要特色

- 🖼️ **資料夾瀏覽**：多層資料夾分類，支援 PNG、JPG、GIF、APNG、WEBP。
- 📋 **剪貼簿貼圖**：直接貼上剪貼簿圖片到指定資料夾，支援多種來源。
- 📦 **LINE 貼圖下載**：輸入 LINE 貼圖網址，一鍵批次下載整組貼圖，超方便！
- 🗂️ **檔案/資料夾管理**：搬移、重命名、刪除、建立新資料夾，管理超彈性。
- 🍞 **Breadcrumb 導覽**：路徑導覽不迷路，回上層一鍵到位。
- 🌈 **活潑介面**：可愛又直覺，支援自訂資料夾封面縮圖。

---

## 🚀 快速開始

### 方法 1（推薦）：使用 `start.bat` 一鍵啟動

1. **安裝 Python 3.8+**
2. **執行主程式**  
  直接雙擊或執行 `start.bat`，即可啟動 Meme Gallery。

---

### 方法 2：手動執行

1. **安裝 Python 3.8+**
2. **安裝必要套件**

    ```bash
    pip install -r requirements.txt
    ```

3. **執行主程式**

    ```bash
    python main.py
    ```

## 📁 目錄結構

- `img/`：你的梗圖、貼圖都放這裡，支援多層資料夾
- `static/`：前端介面資源（HTML/CSS/JS/字型）
- `util/`：LINE 貼圖下載核心
- `main.py`：主程式（PyQt6 GUI）
- `favicon.ico`：自訂視窗圖示
- `requirements.txt`：依賴套件清單

---

## 🛠️ 進階用法

- **支援拖曳圖片進資料夾**
- **支援多種貼圖格式，自動產生縮圖**
- **視窗圖示可自訂，換成你喜歡的圖示即可**
- **支援 Windows Python embed 免安裝包（CI/CD 打包）**

---

## 🎨 如何新增顏色主題

只要三步驟，輕鬆自訂你的新主題！

1. **新增 CSS 主題檔**
   - 參考 `static/theme/base.css`，建立一個新的主題檔（如 `mytheme.css`），放在 `static/theme/` 資料夾。
2. **在 style.css 中 import**
   - 在 `static/style.css` 最上方加上：

    ```css
    @import url('theme/mytheme.css');
    ```

   - 並確保主題 class 命名規則一致（如 `.theme-mytheme`）。

3. **在 HTML 新增主題選項**
   - 在 `static/template.html` 的主題切換區塊，新增一個按鈕或選單項目：

    ```html
    <p>選擇主題：</p>
    <ul class="options">
        <li data-value="">預設</li>
        ... 其他主題選項 ...
        <li data-value="theme-mytheme">我的主題</li>
    </ul>
    ```

   - 這樣就能在前端切換到你的新主題！

---

## 💡 小提醒

- 若圖片太多太大，請自行管理 img/ 內容，避免打包過大。

---

## 🦈 來打造屬於你的 Meme 圖庫，讓快樂無限延伸吧

> Made with ❤️ by Tim
