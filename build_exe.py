import os
import subprocess
import shutil
import sys

print("開始打包 ChronoHelper 為獨立執行檔...")

# 確保目錄存在
if not os.path.exists('dist'):
    os.makedirs('dist')

# 如果有舊的打包檔案，先刪除
if os.path.exists('dist/ChronoHelper.exe'):
    os.remove('dist/ChronoHelper.exe')

if os.path.exists('build'):
    shutil.rmtree('build')

# 檢查是否安裝了PyInstaller
try:
    import PyInstaller
    print("已發現 PyInstaller，繼續打包過程...")
except ImportError:
    print("未發現 PyInstaller，正在安裝...")
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    print("PyInstaller 安裝完成")

# 檢查應用程式依賴的套件
dependencies = [
    'schedule', 'pillow', 'beautifulsoup4', 'requests', 'cryptography'
]

print("檢查並安裝必要的依賴套件...")
for package in dependencies:
    try:
        __import__(package.replace('-', '_').split('==')[0])
        print(f"{package} 已安裝")
    except ImportError:
        print(f"安裝 {package}...")
        subprocess.call([sys.executable, '-m', 'pip', 'install', package])

# 使用PyInstaller打包
print("開始使用 PyInstaller 打包應用程式...")

# 使用spec文件打包
pyinstaller_command = [
    sys.executable, '-m', 'PyInstaller',
    'ChronoHelper.spec',
    '--clean',         # 清除臨時檔案
    '--noconfirm',     # 不詢問確認
]

# 執行打包命令
print("執行命令:", ' '.join(pyinstaller_command))
subprocess.call(pyinstaller_command)

# 創建一個簡單的安裝說明
readme_content = """# ChronoHelper 使用說明

## 安裝方式
1. 解壓縮檔案到您想要的目錄
2. 直接點擊 ChronoHelper.exe 執行程式

## 注意事項
- 首次執行時，可能需要等待幾秒鐘程式才會啟動
- 如果遇到任何問題，請確保您的電腦已安裝最新的 Microsoft Visual C++ Redistributable
- 程式會在同一目錄下創建配置文件，請確保該目錄有寫入權限

## 更新方式
下載新版本後，直接替換舊的執行檔即可，您的設定和任務資料將會保留。
"""

with open('dist/README.txt', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("打包完成！")
print("執行檔位於: dist/ChronoHelper.exe")
print("已創建使用說明文件: dist/README.txt") 