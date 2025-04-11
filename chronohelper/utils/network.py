# -*- coding: utf-8 -*-
"""
網絡檢測功能
"""

import socket
import subprocess
import platform
import re
import time
import threading
import contextlib
from typing import Dict, Tuple, List, Any, Optional

def get_local_ip() -> Optional[str]:
    """獲取本機的區域網路IP地址
    
    Returns:
        Optional[str]: 成功時返回IP地址，失敗時返回None
    """
    try:
        # 創建一個UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 連接一個外部地址（不需要實際連接）
            s.connect(('8.8.8.8', 80))
            # 獲取本機IP
            ip = s.getsockname()[0]
            return ip
        finally:
            s.close()
    except Exception:
        return None

class NetworkUtils:
    """網絡工具類，用於檢測網絡環境和校內網絡連接狀態"""
    
    def __init__(self, logger: Any, settings: Optional[Dict[str, Any]] = None) -> None:
        """初始化網絡工具
        
        Args:
            logger: 日誌記錄器實例，需要實現log方法
            settings: 設定字典，若提供則使用設定中的配置
        """
        self.logger = logger
        self.settings = settings or {}
        self.cache: Dict[str, Any] = {
            'is_campus': None,
            'ip_address': None,
            'hop_info': None,
            'last_check_time': 0,
            'check_in_progress': False
        }
        self.cache_timeout = 60  # 緩存有效期（秒）
        self.lock = threading.RLock()  # 使用可重入鎖，更安全
        self.shutdown_flag = False  # 關閉標記，用於中止進行中的操作
        self.active_processes: List[subprocess.Popen] = []  # 跟踪活動的子進程
        self.active_threads: List[threading.Thread] = []    # 跟踪活動的線程
        self.hop_check_timeout = self.settings.get("hop_check_timeout", 3)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新設定，無需重啟應用程式
        
        Args:
            settings: 新的設定字典
        """
        # 保存新設定
        self.settings = settings or {}
        
        # 讀取最新的超時設定
        self.hop_check_timeout = self.settings.get("hop_check_timeout", 3)
        
        # 清除緩存，強制下次檢測使用新設定
        self.clear_cache()
        self.logger.log("網絡檢測設定已更新")
    
    def clear_cache(self) -> None:
        """清除檢測結果緩存"""
        with self.lock:
            self.cache['last_check_time'] = 0
    
    def shutdown(self) -> None:
        """關閉和清理所有網絡操作
        
        在應用程式關閉前調用，確保所有資源被釋放
        """
        self.logger.log("正在停止所有網絡檢測操作...")
        self.shutdown_flag = True
        
        # 中止所有活動子進程
        for proc in self.active_processes[:]:  # 使用副本進行迭代
            try:
                if proc.poll() is None:  # 如果進程仍在運行
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.0)  # 等待進程終止
                    except subprocess.TimeoutExpired:
                        proc.kill()  # 如果無法正常終止，強制結束
                    self.logger.log("已終止進程")
            except Exception as e:
                self.logger.log(f"終止進程時發生錯誤: {str(e)}")
        
        # 清空進程列表
        self.active_processes.clear()
        
        # 等待所有線程完成（最多等待3秒）
        for thread in self.active_threads[:]:  # 使用副本進行迭代
            if thread.is_alive():
                thread.join(3.0)
        
        # 清空線程列表
        self.active_threads.clear()
        
        # 確保鎖被釋放
        with contextlib.suppress(Exception):
            if hasattr(self.lock, '_is_owned') and self.lock._is_owned():
                self.lock.release()
        
        self.logger.log("網絡檢測操作已全部停止")
    
    def check_campus_network(self, verbose: bool = True, check_second_hop: Optional[bool] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """檢測是否在校內網絡環境（163.23.x.x）
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            check_second_hop: 是否檢查第二躍點，如果為None則使用設定中的值
            
        Returns:
            tuple: (is_campus, ip_address, hop_info) 是否在校內網絡、當前IP地址和躍點信息
        """
        # 檢查是否已關閉
        if self.shutdown_flag:
            return False, "已關閉", {}
            
        # 如果未提供check_second_hop參數，使用設定中的值
        if check_second_hop is None:
            check_second_hop = self.settings.get("enable_second_hop", False)
        
        # 檢查緩存是否有效
        current_time = time.time()
        if (current_time - self.cache['last_check_time'] < self.cache_timeout and 
            self.cache['ip_address'] is not None):
            if verbose:
                self.logger.log("使用緩存的網絡檢測結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        # 檢測處理中標記
        if self.cache['check_in_progress']:
            if verbose:
                self.logger.log("另一個網絡檢測正在進行，使用緩存結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        # 嘗試獲取線程鎖，最多等待100毫秒
        if not self.lock.acquire(blocking=True, timeout=0.1):
            if verbose:
                self.logger.log("無法獲取鎖，使用緩存結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        try:
            self.cache['check_in_progress'] = True
            
            # 獲取區域網路IP
            ip_address = get_local_ip()
            
            if not ip_address:
                # 如果無法獲取區域網路IP，嘗試其他方法
                hostname = socket.gethostname()
                try:
                    ip_list = socket.gethostbyname_ex(hostname)[2]
                    # 過濾掉本地迴環地址
                    ip_list = [ip for ip in ip_list if not ip.startswith('127.')]
                    # 優先選擇163.23開頭的IP
                    campus_ips = [ip for ip in ip_list if ip.startswith('163.23.')]
                    if campus_ips:
                        ip_address = campus_ips[0]
                    elif ip_list:
                        ip_address = ip_list[0]
                    else:
                        ip_address = "未知"
                except socket.gaierror:
                    ip_address = "未知"
            
            # 更新緩存
            self.cache['ip_address'] = ip_address
            self.cache['last_check_time'] = current_time
            
            # 檢查IP地址是否符合校內網絡特徵
            is_campus = isinstance(ip_address, str) and ip_address.startswith('163.23.')
            self.cache['is_campus'] = is_campus
            
            if verbose:
                self.logger.log(f"檢測到區域網路IP地址: {ip_address}")
                if is_campus:
                    self.logger.log("網絡檢測結果: 校內網絡 ✓")
                else:
                    self.logger.log("當前不是校內網絡")
            
            # 如果是校內網絡，直接返回結果，不需要檢查第二躍點
            if is_campus:
                # 更新hop_info為None，但保留之前的is_campus標記
                # 這是因為本機IP現在是校內網絡，不需要依賴第二躍點檢測
                self.cache['is_campus'] = True
                
                # 釋放鎖並返回結果
                self.cache['check_in_progress'] = False
                self.lock.release()
                return True, ip_address, self.cache['hop_info'] or {}
                
            # 如果不需要檢查第二躍點，直接返回本機檢測結果
            if not check_second_hop:
                if verbose and not is_campus:
                    self.logger.log("註: 第二躍點檢測已禁用，不進行進一步檢查")
                
                # 確保將狀態設為非校內，因為第二躍點檢測已禁用
                self.cache['is_campus'] = False
                
                # 釋放鎖並返回結果
                self.cache['check_in_progress'] = False
                self.lock.release()
                return False, ip_address, {}
            
            # 到這裡表示：本機IP不是校內網絡，但需要檢查第二躍點
            # 啟動一個線程進行第二躍點檢測，不阻塞主線程
            if verbose:
                self.logger.log("本機IP不是校內網絡，在背景檢查第二躍點...")
            
            # 先獲取緩存中可能的第二躍點信息，以便返回給調用者
            cached_hop_info = self.cache['hop_info'] or {}
            cached_is_campus = cached_hop_info.get('is_campus', False)
            
            # 記錄當前網絡狀態（用於檢測變更）
            prev_is_campus = self.cache['is_campus'] or cached_is_campus
            
            # 創建檢測線程函數
            def check_hop_thread() -> None:
                try:
                    # 使用設定中的超時值
                    timeout = self.settings.get("hop_check_timeout", 3)
                    
                    # 檢測第二躍點
                    second_hop_info = self.check_second_hop(verbose, timeout)
                    
                    # 檢查是否已關閉
                    if self.shutdown_flag:
                        return
                        
                    # 更新緩存中的躍點信息和校內網絡狀態
                    with contextlib.suppress(Exception):
                        with self.lock:
                            # 更新緩存
                            self.cache['hop_info'] = second_hop_info
                            
                            # 檢查第二躍點是否表明在校內網絡
                            new_is_campus = second_hop_info.get('is_campus', False)
                            
                            # 如果第二躍點是校內網絡，更新is_campus標記
                            if new_is_campus:
                                self.cache['is_campus'] = True
                                if verbose:
                                    self.logger.log(f"網絡檢測結果: 通過第二躍點識別為校內網絡 ✓")
                                
                                # 如果之前不是校內網絡，但現在是，發送通知
                                if not prev_is_campus and new_is_campus:
                                    hop_ip = second_hop_info.get('ip', '未知')
                                    self.logger.log(f"網絡環境已變更: 校外 -> 校內")
                                    self.logger.log(f"通過第二躍點識別為校內網絡 (第二躍點IP: {hop_ip})")
                            else:
                                # 維持本機檢測結果，在第二躍點檢測失敗時不要覆蓋
                                if verbose:
                                    self.logger.log(f"網絡檢測結果: 非校內網絡 ✗")
                except Exception as e:
                    if verbose:
                        self.logger.log(f"第二躍點檢測異常: {type(e).__name__} - {str(e)}")
                finally:
                    # 確保標記被正確設置
                    with contextlib.suppress(Exception):
                        self.cache['check_in_progress'] = False
                    
                    # 從活動線程列表中移除自己
                    with contextlib.suppress(Exception):
                        if thread in self.active_threads:
                            self.active_threads.remove(thread)
            
            # 創建線程
            thread = threading.Thread(target=check_hop_thread, daemon=True)
            
            # 添加到活動線程列表
            self.active_threads.append(thread)
            
            # 啟動線程
            thread.start()
            
            # 釋放鎖，讓方法可以立即返回結果
            self.lock.release()
            
            # 返回最佳的當前狀態（優先使用已有的第二躍點檢測結果）
            if cached_is_campus:
                return True, ip_address, cached_hop_info
            else:
                return False, ip_address, cached_hop_info
            
        except Exception as e:
            if verbose:
                self.logger.log(f"IP地址檢測失敗: {str(e)}")
            return False, "未知", {}
    
    def check_second_hop(self, verbose: bool = True, timeout: Optional[float] = None) -> Dict[str, Any]:
        """檢測第二躍點是否在校內網絡環境
        
        使用路由追蹤確定第二躍點位置，判斷是否在校內網絡。
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            timeout: 檢測命令超時時間（秒），默認使用設定中的值或3秒
            
        Returns:
            Dict[str, Any]: 包含躍點資訊的字典
        """
        # 檢查是否已關閉
        if self.shutdown_flag:
            return {'is_campus': False, 'ip': '已關閉', 'method': 'shutdown'}
            
        # 使用參數或實例屬性中的超時值
        if timeout is None:
            timeout = getattr(self, 'hop_check_timeout', self.settings.get("hop_check_timeout", 6))
            
        hop_info: Dict[str, Any] = {
            'is_campus': False,
            'ip': '未知',
            'hop_number': 2,
            'method': 'unknown',
            'check_time': time.time()
        }
        
        try:
            # 使用tracert/traceroute
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows使用tracert命令
                target = '8.8.8.8'  # Google DNS服務器作為目標
                cmd = f'tracert -h 2 -w 500 {target}'
                
                if verbose:
                    self.logger.log(f"執行命令: {cmd}")
                
                # 執行命令並處理結果
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, text=True)
                # 跟踪進程
                self.active_processes.append(process)
                
                try:
                    # 等待進程完成，設置超時
                    stdout, stderr = process.communicate(timeout=timeout)
                    
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    
                    # 解析tracert輸出以獲取第二躍點信息
                    lines = stdout.split('\n')
                    for line in lines:
                        # 找到包含 "  2 " 的行，表示第二躍點
                        if "  2 " in line or "  2\t" in line:
                            # 使用正則表達式提取IP地址
                            ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
                            if ip_match:
                                hop_ip = ip_match.group(0)
                                hop_info['ip'] = hop_ip
                                hop_info['is_campus'] = hop_ip.startswith('163.23.')
                                hop_info['method'] = 'tracert'
                                
                                if verbose:
                                    self.logger.log(f"第二躍點IP: {hop_ip}")
                                    if hop_info['is_campus']:
                                        self.logger.log(f"第二躍點IP識別為校內網絡")
                                    else:
                                        self.logger.log(f"第二躍點IP不是校內網絡")
                                break
                except subprocess.TimeoutExpired:
                    # 超時時中止進程
                    if process.poll() is None:
                        process.terminate()
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    if verbose:
                        self.logger.log(f"tracert命令超時（{timeout}秒）")
                    hop_info['method'] = 'timeout'
            else:
                # Linux/Mac使用traceroute命令
                target = '8.8.8.8'  # Google DNS服務器作為目標
                cmd = f'traceroute -m 2 -w 1 {target}'
                
                if verbose:
                    self.logger.log(f"執行命令: {cmd}")
                
                # 執行命令並獲取輸出
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, text=True)
                # 跟踪進程
                self.active_processes.append(process)
                
                try:
                    # 等待進程完成，設置超時
                    stdout, stderr = process.communicate(timeout=timeout)
                    
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    
                    # 解析traceroute輸出以獲取第二躍點信息
                    lines = stdout.split('\n')
                    if len(lines) >= 3:  # 確保至少有3行（標題行+兩個躍點）
                        # 第二躍點在第3行（索引2）
                        second_hop_line = lines[2]
                        # 使用正則表達式提取IP地址
                        ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', second_hop_line)
                        if ip_match:
                            hop_ip = ip_match.group(0)
                            hop_info['ip'] = hop_ip
                            hop_info['is_campus'] = hop_ip.startswith('163.23.')
                            hop_info['method'] = 'traceroute'
                            
                            if verbose:
                                self.logger.log(f"第二躍點IP: {hop_ip}")
                                if hop_info['is_campus']:
                                    self.logger.log(f"第二躍點IP識別為校內網絡")
                                else:
                                    self.logger.log(f"第二躍點IP不是校內網絡")
                except subprocess.TimeoutExpired:
                    # 超時時中止進程
                    if process.poll() is None:
                        process.terminate()
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    if verbose:
                        self.logger.log(f"traceroute命令超時（{timeout}秒）")
                    hop_info['method'] = 'timeout'
            
            return hop_info
            
        except subprocess.TimeoutExpired:
            if verbose:
                self.logger.log(f"第二躍點檢測超時（{timeout}秒限制）")
            hop_info['method'] = 'timeout'
            return hop_info
        except Exception as e:
            if verbose:
                self.logger.log(f"第二躍點檢測失敗: {str(e)}")
            hop_info['method'] = 'error'
            return hop_info


if __name__ == "__main__":
    print("========== 網絡檢測測試 ==========")
    print("本機IP:", get_local_ip())
    
    class SimpleLogger:
        def log(self, message):
            print(f"[測試日誌] {message}")
    
    # 建立具有日誌功能的測試實例
    network_utils = NetworkUtils(SimpleLogger(), {"hop_check_timeout": 10})
    
    print("\n開始檢測第二躍點...")
    result = network_utils.check_second_hop(verbose=True)
    
    print("\n========== 檢測結果 ==========")
    print(f"完整結果: {result}")
    print(f"躍點IP: {result.get('ip', '未知')}")
    print(f"是否校內網絡: {result.get('is_campus', False)}")
    print(f"檢測方法: {result.get('method', '未知')}")
    print(f"檢測時間: {time.ctime(result.get('check_time', 0))}")
    print("==============================")