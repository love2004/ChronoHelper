# ChronoHelper 打包說明

這個目錄包含了將 ChronoHelper 打包成可獨立執行的 EXE 文件的所有必要腳本。

## 打包步驟

1. 確保您已安裝 Python 3.8 或更高版本
2. 執行 `build.bat` 批處理文件
3. 等待打包過程完成
4. 打包完成後，您可以在 `dist` 目錄中找到 `ChronoHelper.exe` 文件

## 文件說明

- `build.bat`: Windows 批處理文件，用於啟動打包過程
- `build_exe.py`: Python 打包腳本，自動安裝依賴並執行 PyInstaller
- `ChronoHelper.spec`: PyInstaller 規格文件，定義了如何打包應用程式

## 常見問題

### 打包過程中出現錯誤

如果打包過程中出現錯誤，請檢查:

1. 確保您已安裝 Python 3.8 或更高版本
2. 確保 Python 已添加到系統路徑
3. 確保您有足夠的權限來安裝 PyInstaller 及相關依賴

### 打包後的程式無法啟動

如果打包後的程式無法啟動，請檢查:

1. 確保您的系統已安裝最新的 Microsoft Visual C++ Redistributable
2. 檢查 `dist` 目錄中是否有 `README.txt` 文件，其中包含使用說明
3. 如果使用單文件模式，確保程式有足夠的權限創建臨時文件

## 其他打包選項

如果您需要自定義打包過程，請編輯 `ChronoHelper.spec` 文件，可以修改以下選項:

- 更改 `console=False` 為 `console=True` 以顯示控制台窗口（便於調試）
- 修改 `datas` 列表以包含其他資源文件
- 添加 `icon='path_to_icon.ico'` 到 EXE 定義中設定程式圖示 