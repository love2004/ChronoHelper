# -*- coding: utf-8 -*-
"""
基礎UI元件
"""

import tkinter as tk
from chronohelper.config.colors import COLORS

class ModernButton(tk.Button):
    """現代化按鈕，帶有懸停效果"""
    def __init__(self, master=None, **kwargs):
        bg = kwargs.pop('bg', COLORS["primary"])
        fg = kwargs.pop('fg', 'white')
        activebackground = kwargs.pop('activebackground', COLORS["primary_dark"])
        
        # 保存原始顏色用於恢復
        self.orig_bg = bg
        self.orig_active_bg = activebackground
        
        # 額外的屬性用於控制懸停行為
        self.keep_color = kwargs.pop('keep_color', False)
        
        activeforeground = kwargs.pop('activeforeground', 'white')
        bd = kwargs.pop('bd', 0)
        relief = kwargs.pop('relief', tk.FLAT)
        padx = kwargs.pop('padx', 15)
        pady = kwargs.pop('pady', 8)
        
        super().__init__(master, bg=bg, fg=fg, activebackground=activebackground,
                         activeforeground=activeforeground, bd=bd, relief=relief,
                         padx=padx, pady=pady, **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, e):
        if not self.keep_color:
            if self.orig_bg == COLORS["warning"]:
                self.config(bg=COLORS["warning_dark"])
            else:
                self.config(bg=COLORS["primary_dark"])
    
    def _on_leave(self, e):
        if not self.keep_color:
            self.config(bg=self.orig_bg)
