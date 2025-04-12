# -*- coding: utf-8 -*-
"""
設定選項卡組件
"""

from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab
from chronohelper.ui.components.dialogs.settings.general_tab import GeneralTab
from chronohelper.ui.components.dialogs.settings.api_tab import APITab
from chronohelper.ui.components.dialogs.settings.network_tab import NetworkTab
from chronohelper.ui.components.dialogs.settings.user_tab import UserTab
from chronohelper.ui.components.dialogs.settings.time_tab import TimeTab
from chronohelper.ui.components.dialogs.settings.vpn_tab import VPNTab

__all__ = [
    'BaseSettingsTab', 
    'GeneralTab', 
    'APITab', 
    'NetworkTab', 
    'UserTab', 
    'TimeTab', 
    'VPNTab'
] 