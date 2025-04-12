# ChronoHelper

![License](https://img.shields.io/badge/license-MIT-orange)

ChronoHelper 是一款專為大葉大學設計的自動化簽到/簽退工具，具有簡潔優雅的現代界面、智能任務管理和自動執行功能，幫助您輕鬆管理日常考勤需求。

![ChronoHelper主界面](https://zhijings.com/wp-content/uploads/2025/04/chronohelper-v2.2.1.png)


## 📋 功能特色

- **自動化簽到/簽退**：根據設定的時間自動執行簽到簽退操作
- **優雅的現代UI界面**：簡潔直觀的操作體驗，適配深淺主題
- **智能網絡環境檢測**：自動識別校內/校外網絡環境，智能調整任務執行策略
- **多任務管理**：支持創建、編輯和刪除多個簽到/簽退任務
- **桌面通知**：任務執行結果實時推送桌面通知
- **會話自動維護**：定期刷新會話避免過期，確保任務順利執行
- **安全性設計**：敏感信息加密存儲，保障賬號安全
- **環境適應性**：自動處理校內環境限制，合理安排任務重試
- **詳細日誌記錄**：完整追踪操作歷史和執行結果

## 🚀 安裝指南

### 系統需求

- Python 3.7 或更高版本
- 支持 Windows、macOS 和 Linux

### 方法一：從源代碼安裝

```bash
# 克隆存儲庫
git clone https://github.com/love2004/chronohelper.git
cd chronohelper

# 安裝依賴
pip install -r requirements.txt

# 運行程序
python main.py
```

### 方法二：使用編譯好的執行檔（僅Windows）

1. 從 [Releases](https://github.com/love2004/chronohelper/releases) 頁面下載最新版本的執行檔
2. 解壓縮到任意位置
3. 運行 `ChronoHelper.exe`

## 📝 使用指南

### 初次設定

1. 首次啟動時，點擊頂部的「設定」按鈕
2. 在「API設定」頁籤中，輸入您的大葉大學帳號和密碼
3. 點擊「測試登入」確認帳號信息正確
4. 點擊「儲存設定」完成初始設定

### 建立簽到/簽退任務

1. 點擊主界面上的「+ 新增任務」按鈕
2. 輸入任務名稱（如：「工讀生簽到」）
3. 設定日期（可選擇今日或未來日期）
4. 設定簽到和簽退時間
5. 勾選是否需要通知
6. 點擊「儲存」完成任務建立

### 管理任務

- **手動執行**：點擊任務卡片上的「簽到」或「簽退」按鈕
- **編輯任務**：點擊任務卡片上的「編輯」按鈕
- **刪除任務**：點擊任務卡片上的「刪除」按鈕
- **狀態管理**：勾選「已完成簽到」或「已完成簽退」複選框，或使用右鍵菜單

### 自動執行模式

ChronoHelper 會根據設定的時間自動檢查並執行任務，無需人工干預。系統會在以下情況自動執行任務：

- 當前時間到達或超過任務設定的簽到/簽退時間
- 處於校內網絡環境
- 任務尚未被標記為完成

## 🔧 高級功能

### 網絡環境管理

- ChronoHelper 會自動檢測您是否處於校內網絡環境
- 支持第二躍點檢測，即使使用VPN或非校內IP，只要路由經過校內網絡，也能識別為校內環境
- 在校外環境下，任務執行會暫停，避免無效嘗試
- 重新連接到校內網絡時，系統會自動恢復任務執行

### 右鍵菜單功能

在任務卡片上點擊右鍵可以訪問更多功能：

- **任務狀態管理**：快速標記/取消標記任務完成狀態
- **重置環境限制**：清除任務的環境受限標記
- **一鍵設為完成**：立即將任務標記為全部完成

### 會話維護

ChronoHelper 具有智能會話維護機制，可以：

- 自動維持登入狀態
- 定期刷新會話避免過期（默認每240分鐘）
- 檢測到會話失效時自動重新登入

## 🛠️ 配置選項

ChronoHelper 提供以下可自定義配置：

- **全局通知設置**：控制是否接收所有任務的通知
- **檢查間隔**：任務檢查的時間間隔（默認30秒）
- **會話刷新間隔**：自動刷新登入會話的時間間隔
- **默認簽到/簽退時間**：新任務的預設時間
- **自動啟動**：控制程序啟動時是否自動開始任務監控
- **第二躍點檢測**：啟用更深入的網絡環境檢測，支持複雜網絡環境下的校內識別

## 📊 系統架構

ChronoHelper 採用模塊化設計，主要組件包括：

- **任務管理器**：負責任務的創建、存儲和調度
- **網絡檢測器**：實時監控網絡環境變化
- **會話管理器**：維護系統登入狀態
- **安全模塊**：處理敏感信息的加密解密
- **UI系統**：提供現代化、直觀的用戶界面

### 技術實現

- 使用 Python Tkinter 構建跨平台桌面應用
- 採用現代設計風格提升用戶體驗
- 實現多線程執行確保UI響應性
- 使用加密技術保護用戶敏感數據
- 使用 PyInstaller 打包為獨立執行檔

## 🔒 隱私聲明

ChronoHelper尊重您的隱私：
- 所有敏感數據都在本地加密存儲
- 不會收集或發送任何個人信息
- 網絡連接僅用於您設置的任務執行
- 帳號密碼僅用於與大葉大學系統交互

## ⚠️ 免責聲明

使用 ChronoHelper 自動簽到/簽退工具完全由使用者自行承擔風險。本工具可能違反校規或單位政策，開發者不對任何可能的處分或後果負責。軟體按「現狀」提供，無任何形式擔保。下載使用即表示您接受這些條件並同意後果自負。如有疑慮，請勿使用。

## 🤝 參與貢獻

我們歡迎各種形式的貢獻，包括但不限於功能建議、Bug報告、代碼貢獻等。

### 貢獻步驟

1. Fork 本倉庫
2. 創建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟一個 Pull Request

### 功能請求和Bug報告

如果您有功能建議或發現了Bug，請在 Issues 頁面提交，並使用相應的標籤進行標記。

## 📜 開源協議

本項目基於 MIT 協議開源 - 詳情請參閱 [LICENSE](LICENSE) 文件

## 📞 聯絡方式

- 項目維護者：[zhijing](mailto:zhijing041215@gmail.com)
- 項目主頁：[GitHub](https://github.com/love2004/chronohelper)

## 🙏 致謝

- 感謝所有為本項目做出貢獻的開發者
- 特別感謝 [大葉大學](https://www.dyu.edu.tw/) 提供的系統支持
