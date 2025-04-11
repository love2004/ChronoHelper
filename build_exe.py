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
import logging
from pathlib import Path
from typing import Tuple

# 設置日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChronoHelper-Builder')

def check_and_install_package(package_name: str) -> bool:
    """
    檢查並安裝Python包
    
    Args:
        package_name: 要檢查的套件名稱，可以包含版本要求
        
    Returns:
        bool: 如果安裝了新的套件返回True，否則返回False
        
    Raises:
        subprocess.CalledProcessError: 安裝套件時出錯
    """
    # 提取基本包名（移除版本要求等）
    package = re.split(r'[<>=]', package_name)[0].strip().replace('-', '_')
    
    try:
        spec = importlib.util.find_spec(package)
        if spec is None:
            logger.info(f"安裝 {package_name}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
            return True
        else:
            logger.info(f"{package_name} 已安裝")
            return False
    except (ModuleNotFoundError, ValueError) as e:
        logger.warning(f"找不到模組 {package}: {e}")
        logger.info(f"嘗試安裝 {package_name}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"安裝 {package_name} 失敗: {e}")
            raise
    except subprocess.CalledProcessError as e:
        logger.error(f"安裝 {package_name} 失敗: {e}")
        raise

def ensure_icon_exists() -> str:
    """
    確保應用程式圖標存在，必要時創建
    
    Returns:
        str: 圖標文件的路徑
        
    Raises:
        IOError: 如果無法創建或保存圖標文件
    """
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    icon_path = resources_dir / "chronohelper.ico"
    
    if not icon_path.exists():
        logger.info("應用圖標不存在，正在創建...")
        
        try:
            # 嘗試導入腳本模塊直接使用
            from script import create_app_icon
            
            try:
                icon_path_str, png_path_str = create_app_icon(str(resources_dir))
                return icon_path_str
            except Exception as e:
                logger.warning(f"無法使用script模組創建圖標: {e}")
                # 繼續使用內置方法創建
        except ImportError:
            logger.info("無法導入script模塊，使用內置方法創建圖標")
        
        check_and_install_package('pillow')
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            icon_size = 256
            img = Image.new('RGBA', (icon_size, icon_size), color=(0, 0, 0, 0))  # 透明背景
            draw = ImageDraw.Draw(img)
            
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
            
            # 嘗試載入系統字體
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
                    logger.info(f"已成功載入字體: {path}")
                    break
                except Exception:
                    continue
            
            if font is None:
                logger.warning("無法載入自定義字體，使用默認字體")
                font = ImageFont.load_default()
            
            # 繪製文字 "CH"
            text = "CH"
            
            # 根據不同Pillow版本選擇適當的方法獲取文字大小
            try:
                # 計算文字位置
                position = calculate_text_position(draw, font, text, icon_size)
                
                # 添加文字陰影效果
                shadow_offset = 2
                draw.text((position[0]+shadow_offset, position[1]+shadow_offset), text, font=font, fill=(0, 0, 0, 100))
                
                # 繪製主文字
                draw.text(position, text, font=font, fill=(255, 255, 255, 255))  # 白色文字
            except Exception as e:
                logger.error(f"繪製文字時出錯: {e}")
                # 繼續創建圖標，即使文字可能有問題
            
            # 保存多個尺寸的ICO文件
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(str(icon_path), format='ICO', sizes=sizes)
            
            # 同時保存PNG版本供Linux/macOS和Tkinter使用
            png_path = resources_dir / "chronohelper.png"
            img.save(str(png_path), format='PNG')
            
            logger.info(f"圖標已創建並保存至: {icon_path}")
            logger.info(f"PNG圖像已保存至: {png_path}")
            
        except Exception as e:
            logger.error(f"創建圖標時出現錯誤: {e}")
            raise IOError(f"無法創建應用圖標: {e}")
    
    return str(icon_path)

def calculate_text_position(draw, font, text: str, icon_size: int) -> Tuple[int, int]:
    """
    計算文字在圖標中的最佳位置
    
    Args:
        draw: PIL的ImageDraw對象
        font: PIL的ImageFont對象
        text: 要繪製的文字
        icon_size: 圖標尺寸
        
    Returns:
        Tuple[int, int]: (x, y)位置坐標
    """
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
            logger.warning("無法確定文字大小，使用估計值")
            
        # 計算視覺上居中的位置
        # 有時候需要微調垂直位置以實現視覺居中
        x_position = (icon_size - text_width) // 2 - 5  # 向左移動5個像素
        y_position = (icon_size - text_height) // 2 - 15  # 視覺調整，略微上移
        
        return (x_position, y_position)
    except Exception as e:
        logger.error(f"計算文字位置時出錯: {e}")
        # 備用定位
        return (icon_size // 4, icon_size // 4)

def build_executable(icon_path: str, version: str = "1.1.0") -> bool:
    """
    使用PyInstaller打包應用程式
    
    Args:
        icon_path: 圖標文件路徑
        version: 應用程式版本號
        
    Returns:
        bool: 是否成功打包
    """
    logger.info(f"正在打包ChronoHelper v{version}...")
    
    # 驗證圖標文件
    if not os.path.isfile(icon_path):
        logger.error(f"圖標文件不存在: {icon_path}")
        return False
    
    # 打印圖標文件信息以進行調試
    try:
        icon_size = os.path.getsize(icon_path)
        logger.info(f"圖標文件大小: {icon_size} 字節")
        if icon_size == 0:
            logger.warning("警告：圖標文件大小為0字節")
    except OSError as e:
        logger.warning(f"無法獲取圖標文件大小: {e}")
    
    # 確保PyInstaller可用
    check_and_install_package('pyinstaller')
    
    # 構建PyInstaller命令，直接指定資源目錄
    command = [
        sys.executable, 
        '-m', 
        'PyInstaller',
        'main.py',                   # 主程序入口點
        f'--name=ChronoHelper v{version}',  # 輸出文件名
        '--onefile',                 # 單一文件模式
        '--windowed',                # GUI模式，不顯示控制台
        '--clean',                   # 清理臨時檔案
        f'--icon={icon_path}',       # 應用圖標
        '--add-data=resources;resources',  # 資源目錄
        '--hidden-import=PIL._tkinter_finder'  # 確保PIL的tkinter功能正常工作
    ]
    
    try:
        # 執行命令
        logger.info(f"執行PyInstaller命令: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info("PyInstaller執行成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller執行失敗: {e}")
        logger.error(f"錯誤輸出: {e.stderr}")
        return False

def main() -> int:
    """
    主程序入口點
    
    Returns:
        int: 退出碼，0表示成功，非0表示失敗
    """
    try:
        logger.info("開始打包 ChronoHelper 為獨立執行檔...")
        
        # 檢測版本號參數
        version = "2.2.0" 
        if len(sys.argv) > 1 and sys.argv[1].startswith("v"):
            version = sys.argv[1].lstrip("v")
            logger.info(f"使用指定版本號: {version}")
        
        # 確保圖標存在
        icon_path = ensure_icon_exists()
        logger.info(f"使用圖標: {icon_path}")
        
        # 執行打包
        if build_executable(icon_path, version):
            logger.info("打包成功完成！")
            return 0
        else:
            logger.error("打包失敗！")
            return 1
    except Exception as e:
        logger.error(f"打包過程中發生錯誤: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
