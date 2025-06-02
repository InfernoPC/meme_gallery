# Meme Gallery

Meme Gallery 是一個簡單的圖片管理應用程式，允許用戶快速瀏覽、複製圖片到剪貼簿，並能自動偵測 `img/` 目錄中的變化。

## 預覽

![預覽圖片](app_demo_1.gif)

## 功能

- 顯示 `img/` 目錄內的所有圖片（支援 PNG、JPG、JPEG、GIF）
- 點擊圖片即可複製到剪貼簿
- 自動監控 `img/` 目錄變更，新增圖片時即時顯示
- 依據視窗大小調整圖片排列方式
- 滑鼠滾輪可快速上下捲動
- 可手動點擊按鈕重新載入圖片
- 保存剪貼簿圖片到 `img/` 目錄，並以時間戳命名
- 搜尋圖片檔名
- 右鍵選單刪除或重命名圖片

## 安裝與使用

### 1. 安裝所需套件

使用以下指令安裝必要的 Python 套件：

```sh
pip install -r requirements.txt
```

如果沒有 `requirements.txt`，你也可以手動安裝這些套件：

```sh
pip install pillow pywin32 watchdog
```

### 2. 下載並安裝 NaikaiFont

從 [NaikaiFont](https://github.com/max32002/naikaifont) 下載字體並安裝。

### 3. 建立 `img/` 目錄並放入圖片

確保專案目錄內有 `img/` 資料夾，並在裡面放入要顯示的圖片。

```sh
mkdir img
```

### 4. 啟動應用程式

執行 `app.py` 來啟動 Meme Gallery。

```sh
python app.py
```

## 專案結構

```plain
meme_gallery/
│
├── app.py
├── config_manager.py
├── font_manager.py
├── image_manager.py
├── config.json
├── requirements.txt
└── README.md
```

## 注意事項

- **Windows 使用者**：確保 `pywin32` 正常安裝，否則剪貼簿功能可能無法運作。
- **Linux/Mac 使用者**：`pywin32` 主要適用於 Windows，Linux 和 Mac 可能需要其他方式來存取剪貼簿。

## 未來改進

- 增加更多的圖片管理功能（如拖曳排序、自訂標籤）
- 支援 GIF 動畫播放
- 讓 UI 更美觀 😃
