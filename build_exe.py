#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChronoHelper - 打包工具
將應用程式打包為獨立執行檔
"""

import os
import subprocess
import sys
import importlib.util
import re
from pathlib import Path

def check_and_install_package(package_name):
    """檢查並安裝Python包"""

    package = re.split(r'[<>=]', package_name)[0].strip().replace('-', '_')
    
    try:
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"安裝 {package_name}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
            return True
        else:
            print(f"{package_name} 已安裝")
            return False
    except (ModuleNotFoundError, ValueError):
        print(f"嘗試安裝 {package_name}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
        return True

def ensure_icon_exists():
    """確保應用程式圖標存在，現在直接放在resources目錄下"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    icon_path = resources_dir / "chronohelper.ico"
    
    if not icon_path.exists():
        print("創建應用程式圖標...")
        # 安裝Pillow
        check_and_install_package('pillow')
        
        from PIL import Image, ImageDraw, ImageFont
        
        # 創建正方形圖像
        icon_size = 256
        img = Image.new('RGBA', (icon_size, icon_size), color=(0, 0, 0, 0))  # 透明背景
        draw = ImageDraw.Draw(img)
        
        # 繪製漸變藍色背景 - 使用圓形
        center_x, center_y = icon_size // 2, icon_size // 2
        radius = icon_size // 2
        
        # 繪製實心藍色圓形
        draw.ellipse(
            [(0, 0), (icon_size, icon_size)],
            fill=(52, 152, 219, 255)  # 藍色
        )
        
        # 繪製圓形邊框
        margin = 5
        draw.ellipse(
            [(margin, margin), (icon_size-margin, icon_size-margin)],
            outline=(255, 255, 255, 200),
            width=2
        )
        
        # 嘗試使用系統字體
        try:
            font_paths = [
                'C:\\Windows\\Fonts\\arialbd.ttf',  # Windows Arial Bold
                'C:\\Windows\\Fonts\\seguisb.ttf',  # Segoe UI Semibold
                'C:\\Windows\\Fonts\\calibrib.ttf',  # Calibri Bold
                'C:\\Windows\\Fonts\\ariblk.ttf',   # Arial Black
                '/Library/Fonts/Arial Bold.ttf',    # macOS
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            ]
            
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, size=120)
                    break
                except Exception:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
                
        except Exception:
            font = ImageFont.load_default()
        
        # 繪製文字 "CH"
        text = "CH"
        
        # 根據不同Pillow版本選擇適當的方法獲取文字大小
        try:
            if hasattr(font, 'getbbox'):
                # 新版Pillow中使用getbbox
                bbox = font.getbbox(text)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            elif hasattr(font, 'getsize'):
                text_width, text_height = font.getsize(text)
            elif hasattr(draw, 'textsize'):
                text_width, text_height = draw.textsize(text, font=font)
            else:
                # 最後的備用方案
                text_width, text_height = icon_size // 2, icon_size // 2
                
            # 計算視覺上居中的位置
            # 有時候需要微調垂直位置以實現視覺居中
            x_position = (icon_size - text_width) // 2 - 5  # 向左移動5個像素
            y_position = (icon_size - text_height) // 2 - 15  # 視覺調整，略微上移
            
            position = (x_position, y_position)
        except Exception as e:
            print(f"文字測量錯誤: {e}")
            # 備用定位
            position = (icon_size // 4, icon_size // 4)
        
        # 添加文字陰影效果
        shadow_offset = 2
        draw.text((position[0]+shadow_offset, position[1]+shadow_offset), text, font=font, fill=(0, 0, 0, 100))
        
        # 繪製主文字
        draw.text(position, text, font=font, fill=(255, 255, 255, 255))  # 白色文字
        
        # 保存多個尺寸的ICO文件
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(str(icon_path), format='ICO', sizes=sizes)
        
        # 同時保存PNG版本供Linux/macOS和Tkinter使用
        png_path = resources_dir / "chronohelper.png"
        img.save(str(png_path), format='PNG')
        
        print(f"圖標已創建並保存至: {icon_path}")
        print(f"PNG圖像已保存至: {png_path}")
    
    return str(icon_path)

def main():
    print("開始打包 ChronoHelper 為獨立執行檔...")
    
    # 確保圖標存在
    icon_path = ensure_icon_exists()
    print(f"使用圖標: {icon_path}")
    
    # 非常重要：驗證圖標文件
    if not os.path.isfile(icon_path):
        print(f"錯誤：圖標文件不存在: {icon_path}")
        return
    
    # 打印圖標文件信息以進行調試
    print(f"圖標文件大小: {os.path.getsize(icon_path)} 字節")
    
    # 構建PyInstaller命令，直接指定資源目錄
    command = [
        sys.executable, 
        '-m', 
        'PyInstaller',
        'main.py',                   # 主程序入口點
        '--name=ChronoHelper',       # 輸出文件名
        '--onefile',                 # 單一文件模式
        '--windowed',                # GUI模式，不顯示控制台
        '--clean',                   # 清理臨時檔案
        f'--icon={icon_path}',       # 應用圖標
        '--add-data=resources;resources',  # 資源目錄
        '--hidden-import=PIL._tkinter_finder'  # 確保PIL的tkinter功能正常工作
    ]
    
    # 執行命令
    subprocess.call(command)
    
    print("打包完成！")

if __name__ == "__main__":
    main()
