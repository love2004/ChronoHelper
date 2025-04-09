# -*- coding: utf-8 -*-
"""
應用程式預設設定
"""

# 全局設定
APP_SETTINGS = {
    "global_notify": True,    # 全局通知開關
    "check_interval": 30,     # 任務檢查間隔（秒）
    "api_url": "https://adm_acc.dyu.edu.tw/entrance/index.php",  # API基礎URL
    "login_url": "https://adm_acc.dyu.edu.tw/entrance/save_id.php", # 登入URL
    "sign_in_url": "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy", # 簽到URL
    "sign_out_url": "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy", # 簽退URL
    "username": "",           # 用戶名
    "password": "",           # 密碼
    "name": "",               # 用戶姓名
    "auto_start": True,       # 自動啟動調度器
    "default_sign_in": "09:00", # 默認簽到時間
    "default_sign_out": "18:00", # 默認簽退時間
    "session_refresh_interval": 240, # 會話刷新間隔（秒），默認4分鐘
    "session_valid_time": 270  # 會話有效時間（秒），默認4.5分鐘
}
