# -*- coding: utf-8 -*-
"""
任務數據模型
"""

import uuid
import datetime

class Task:
    """任務類，表示一個簽到/簽退任務"""
    
    def __init__(self, name, date, sign_in_time, sign_out_time, notify=True, task_id=None):
        self.id = task_id if task_id else str(uuid.uuid4())
        self.name = name
        self.date = date  # 格式: YYYY-MM-DD
        self.sign_in_time = sign_in_time  # 格式: HH:MM
        self.sign_out_time = sign_out_time  # 格式: HH:MM
        self.notify = notify
        self.sign_in_done = False
        self.sign_out_done = False
        # 新增屬性用於記錄環境限制狀態
        self.campus_restricted = False
        self.last_attempt_time = None  # 上次嘗試的時間
    
    def to_dict(self):
        """將任務轉換為字典格式以便序列化"""
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'sign_in_time': self.sign_in_time,
            'sign_out_time': self.sign_out_time,
            'notify': self.notify,
            'sign_in_done': self.sign_in_done,
            'sign_out_done': self.sign_out_done,
            'campus_restricted': getattr(self, 'campus_restricted', False),
            'last_attempt_time': getattr(self, 'last_attempt_time', None)
        }
    
    @classmethod
    def from_dict(cls, data):
        """從字典創建任務實例"""
        task = cls(
            name=data['name'],
            date=data['date'],
            sign_in_time=data['sign_in_time'],
            sign_out_time=data['sign_out_time'],
            notify=data.get('notify', True),
            task_id=data['id']
        )
        task.sign_in_done = data.get('sign_in_done', False)
        task.sign_out_done = data.get('sign_out_done', False)
        task.campus_restricted = data.get('campus_restricted', False)
        task.last_attempt_time = data.get('last_attempt_time', None)
        return task
