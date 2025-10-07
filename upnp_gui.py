import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import threading
import queue
import re

try:
    import miniupnpc
    UPNPC_AVAILABLE = True
except ImportError:
    UPNPC_AVAILABLE = False

class UPNPGui:
    def __init__(self, root):
        self.root = root
        self.root.title("UPnP 端口映射工具")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 设置最小窗口大小
        self.root.minsize(1000, 700)
        
        # 设置窗口居中
        self.center_window()
        
        # UPnP 对象
        self.upnp = None
        self.external_ip = None
        
        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_queue()
        
        # 自动发现设备
        self.discover_devices_async()
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        # 主标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="UPnP 端口映射工具", 
                              font=('Arial', 18, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # 创建主容器
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 创建左右分栏容器
        left_frame = tk.Frame(main_container, bg='#f0f0f0', width=450)
        left_frame.pack(side='left', fill='y', expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)  # 固定宽度
        
        right_frame = tk.Frame(main_container, bg='#f0f0f0')
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 左侧控制面板
        self.create_control_panel(left_frame)
        
        # 右侧信息面板
        self.create_info_panel(right_frame)
    
    def create_control_panel(self, parent):
        # 控制面板框架
        control_frame = tk.LabelFrame(parent, text="控制面板", 
                                    font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', fg='#2c3e50',
                                    relief='groove', bd=2)
        control_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 设备信息区域
        device_frame = tk.Frame(control_frame, bg='#f0f0f0')
        device_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(device_frame, text="UPnP 设备状态:", 
                font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w')
        
        self.device_status = tk.Label(device_frame, text="正在发现设备...", 
                                    font=('Arial', 9), bg='#f0f0f0', fg='#e67e22')
        self.device_status.pack(anchor='w', pady=(5, 0))
        
        self.external_ip_label = tk.Label(device_frame, text="", 
                                        font=('Arial', 9), bg='#f0f0f0', fg='#27ae60')
        self.external_ip_label.pack(anchor='w')
        
        # 分隔线
        tk.Frame(control_frame, height=2, bg='#bdc3c7').pack(fill='x', padx=10, pady=10)
        
        # 端口映射配置区域
        config_frame = tk.Frame(control_frame, bg='#f0f0f0')
        config_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(config_frame, text="端口映射配置:", 
                font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w')
        
        # 外部端口
        port_frame = tk.Frame(config_frame, bg='#f0f0f0')
        port_frame.pack(fill='x', pady=5)
        
        tk.Label(port_frame, text="外部端口:", bg='#f0f0f0').pack(side='left')
        self.external_port_var = tk.StringVar(value="8080")
        self.external_port_entry = tk.Entry(port_frame, textvariable=self.external_port_var,
                                          width=10, font=('Arial', 10))
        self.external_port_entry.pack(side='right')
        
        # 内部端口
        internal_port_frame = tk.Frame(config_frame, bg='#f0f0f0')
        internal_port_frame.pack(fill='x', pady=5)
        
        tk.Label(internal_port_frame, text="内部端口:", bg='#f0f0f0').pack(side='left')
        self.internal_port_var = tk.StringVar(value="8080")
        self.internal_port_entry = tk.Entry(internal_port_frame, textvariable=self.internal_port_var,
                                          width=10, font=('Arial', 10))
        self.internal_port_entry.pack(side='right')
        
        # 目标IP选择
        ip_frame = tk.Frame(config_frame, bg='#f0f0f0')
        ip_frame.pack(fill='x', pady=5)
        
        tk.Label(ip_frame, text="目标IP:", bg='#f0f0f0').pack(side='left')
        self.internal_ip_var = tk.StringVar()
        self.internal_ip_combo = ttk.Combobox(ip_frame, textvariable=self.internal_ip_var,
                                            width=15, font=('Arial', 10))
        self.internal_ip_combo.pack(side='right')
        
        # IP类型选择
        ip_type_frame = tk.Frame(config_frame, bg='#f0f0f0')
        ip_type_frame.pack(fill='x', pady=5)
        
        tk.Label(ip_type_frame, text="IP类型:", bg='#f0f0f0').pack(side='left')
        self.ip_type_var = tk.StringVar(value="本机IP")
        self.ip_type_combo = ttk.Combobox(ip_type_frame, textvariable=self.ip_type_var,
                                        values=["本机IP", "自定义IP"], width=12, font=('Arial', 10),
                                        state='readonly')
        self.ip_type_combo.pack(side='right')
        self.ip_type_combo.bind('<<ComboboxSelected>>', self.on_ip_type_changed)
        
        # 协议选择
        protocol_frame = tk.Frame(config_frame, bg='#f0f0f0')
        protocol_frame.pack(fill='x', pady=5)
        
        tk.Label(protocol_frame, text="协议:", bg='#f0f0f0').pack(side='left')
        self.protocol_var = tk.StringVar(value="TCP")
        self.protocol_combo = ttk.Combobox(protocol_frame, textvariable=self.protocol_var,
                                         values=["TCP", "UDP"], width=10, font=('Arial', 10),
                                         state='readonly')
        self.protocol_combo.pack(side='right')
        
        # 描述
        desc_frame = tk.Frame(config_frame, bg='#f0f0f0')
        desc_frame.pack(fill='x', pady=5)
        
        tk.Label(desc_frame, text="描述:", bg='#f0f0f0').pack(side='left')
        self.description_var = tk.StringVar(value="Python UPnP 映射")
        self.description_entry = tk.Entry(desc_frame, textvariable=self.description_var,
                                        width=20, font=('Arial', 10))
        self.description_entry.pack(side='right')
        
        # 按钮区域 - 第一行
        button_frame1 = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame1.pack(fill='x', padx=10, pady=(20, 5))
        
        # 添加映射按钮
        self.add_button = tk.Button(button_frame1, text="添加映射", 
                                  command=self.add_port_mapping,
                                  bg='#27ae60', fg='white', 
                                  font=('Arial', 9, 'bold'),
                                  relief='flat', padx=15, pady=6)
        self.add_button.pack(side='left', padx=(0, 5))
        
        # 删除映射按钮
        self.remove_button = tk.Button(button_frame1, text="删除映射", 
                                     command=self.remove_port_mapping,
                                     bg='#e74c3c', fg='white', 
                                     font=('Arial', 9, 'bold'),
                                     relief='flat', padx=15, pady=6)
        self.remove_button.pack(side='left', padx=(0, 5))
        
        # 刷新按钮
        self.refresh_button = tk.Button(button_frame1, text="刷新设备", 
                                      command=self.refresh_devices,
                                      bg='#3498db', fg='white', 
                                      font=('Arial', 9, 'bold'),
                                      relief='flat', padx=15, pady=6)
        self.refresh_button.pack(side='left', padx=(0, 5))
        
        # 扫描网络按钮
        self.scan_button = tk.Button(button_frame1, text="扫描网络", 
                                   command=self.scan_network,
                                   bg='#9b59b6', fg='white', 
                                   font=('Arial', 9, 'bold'),
                                   relief='flat', padx=15, pady=6)
        self.scan_button.pack(side='left')
        
        # 按钮区域 - 第二行
        button_frame2 = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame2.pack(fill='x', padx=10, pady=(5, 10))
        
        # 测试连接按钮
        self.test_button = tk.Button(button_frame2, text="测试连接", 
                                   command=self.test_connection,
                                   bg='#f39c12', fg='white', 
                                   font=('Arial', 9, 'bold'),
                                   relief='flat', padx=15, pady=6)
        self.test_button.pack(side='left', padx=(0, 5))
        
        # 查看映射按钮
        self.view_button = tk.Button(button_frame2, text="查看映射", 
                                   command=self.view_mappings,
                                   bg='#16a085', fg='white', 
                                   font=('Arial', 9, 'bold'),
                                   relief='flat', padx=15, pady=6)
        self.view_button.pack(side='left', padx=(0, 5))
        
        # 检查端口按钮
        self.check_button = tk.Button(button_frame2, text="检查端口", 
                                    command=self.check_port,
                                    bg='#e67e22', fg='white', 
                                    font=('Arial', 9, 'bold'),
                                    relief='flat', padx=15, pady=6)
        self.check_button.pack(side='left', padx=(0, 5))
        
        # 端口转发按钮
        self.forward_button = tk.Button(button_frame2, text="端口转发", 
                                      command=self.start_port_forward,
                                      bg='#8e44ad', fg='white', 
                                      font=('Arial', 9, 'bold'),
                                      relief='flat', padx=15, pady=6)
        self.forward_button.pack(side='left')
        
        # 初始状态
        self.update_button_states()
    
    def create_info_panel(self, parent):
        # 信息面板框架
        info_frame = tk.LabelFrame(parent, text="操作日志", 
                                 font=('Arial', 12, 'bold'),
                                 bg='#f0f0f0', fg='#2c3e50',
                                 relief='groove', bd=2)
        info_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(info_frame, 
                                                font=('Consolas', 9),
                                                bg='#2c3e50', fg='#ecf0f1',
                                                wrap=tk.WORD, height=25)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 配置日志文本颜色标签
        self.log_text.tag_configure("timestamp", foreground="#95a5a6")
        self.log_text.tag_configure("INFO", foreground="#3498db")
        self.log_text.tag_configure("SUCCESS", foreground="#27ae60")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("WARNING", foreground="#f39c12")
        
        # 底部按钮区域
        bottom_frame = tk.Frame(info_frame, bg='#f0f0f0')
        bottom_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # 清空日志按钮
        clear_button = tk.Button(bottom_frame, text="清空日志", 
                               command=self.clear_log,
                               bg='#95a5a6', fg='white', 
                               font=('Arial', 9),
                               relief='flat', padx=15, pady=5)
        clear_button.pack(side='left')
        
        # 状态标签
        self.status_label = tk.Label(bottom_frame, text="就绪", 
                                   font=('Arial', 9),
                                   bg='#f0f0f0', fg='#27ae60')
        self.status_label.pack(side='right')
        
        # 初始日志
        self.log_message("UPnP 端口映射工具已启动")
        self.log_message("正在初始化...")
        self.log_message("")
        self.log_message("使用说明:", "INFO")
        self.log_message("1. 本机IP模式：只能选择本机的IP地址", "INFO")
        self.log_message("2. 自定义IP模式：可以输入网络中的任意IP地址", "INFO")
        self.log_message("3. 点击'扫描网络'可以自动发现网络中的活跃设备", "INFO")
        self.log_message("4. 端口映射可以将外网端口转发到内网任意设备的端口", "INFO")
        self.log_message("5. 点击'测试连接'可以检查目标设备和端口的连通性", "INFO")
        self.log_message("6. 点击'查看映射'可以查看当前所有端口映射", "INFO")
        self.log_message("7. 点击'检查端口'可以检查端口是否可用", "INFO")
        self.log_message("8. 点击'端口转发'可以绕过路由器限制，实现转发", "INFO")
        self.log_message("9. 如果添加映射失败，程序会自动尝试多种参数组合", "INFO")
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "INFO": "#3498db",
            "SUCCESS": "#27ae60", 
            "ERROR": "#e74c3c",
            "WARNING": "#f39c12"
        }
        
        color = color_map.get(level, "#ecf0f1")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def update_status(self, message, color='#27ae60'):
        """更新状态栏"""
        self.status_label.config(text=message, fg=color)
    
    def get_local_ips(self):
        """获取本机IP地址列表"""
        ips = []
        try:
            # 获取本机IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                ips.append(local_ip)
        except:
            pass
        
        # 添加其他可能的IP
        try:
            hostname = socket.gethostname()
            local_ips = socket.gethostbyname_ex(hostname)[2]
            for ip in local_ips:
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except:
            pass
        
        if not ips:
            ips = ["127.0.0.1"]
        
        return ips
    
    def get_network_ips(self):
        """扫描网络中的其他设备IP"""
        network_ips = []
        local_ips = self.get_local_ips()
        
        if not local_ips:
            return network_ips
        
        # 获取网络段
        local_ip = local_ips[0]
        if '.' in local_ip:
            ip_parts = local_ip.split('.')
            network_base = '.'.join(ip_parts[:3])
            
            # 扫描网络段中的其他IP（1-254）
            for i in range(1, 255):
                test_ip = f"{network_base}.{i}"
                if test_ip != local_ip:
                    network_ips.append(test_ip)
        
        return network_ips
    
    def update_ip_options(self):
        """更新IP选项"""
        local_ips = self.get_local_ips()
        
        if self.ip_type_var.get() == "本机IP":
            self.internal_ip_combo['values'] = local_ips
            self.internal_ip_combo.config(state='readonly')
            if local_ips:
                self.internal_ip_var.set(local_ips[0])
        else:  # 自定义IP
            # 获取网络中的其他IP
            network_ips = self.get_network_ips()
            all_ips = ["127.0.0.1"] + local_ips + network_ips[:10]  # 限制显示数量
            self.internal_ip_combo['values'] = all_ips
            self.internal_ip_combo.config(state='normal')
            if local_ips:
                self.internal_ip_var.set(local_ips[0])
    
    def on_ip_type_changed(self, event=None):
        """IP类型改变时的处理"""
        self.update_ip_options()
        ip_type = self.ip_type_var.get()
        if ip_type == "本机IP":
            self.log_message("已切换到本机IP模式")
        else:
            self.log_message("已切换到自定义IP模式，可以输入任意网络IP")
    
    def discover_devices_async(self):
        """异步发现UPnP设备"""
        def discover():
            self.message_queue.put(("DISCOVER_START", None))
            
            if not UPNPC_AVAILABLE:
                self.message_queue.put(("DISCOVER_ERROR", "miniupnpc库未安装，请运行: pip install miniupnpc"))
                return
            
            try:
                upnp = miniupnpc.UPnP()
                upnp.discoverdelay = 200
                
                devices = upnp.discover()
                
                if devices == 0:
                    self.message_queue.put(("DISCOVER_ERROR", "未发现任何UPnP设备"))
                    return
                
                upnp.selectigd()
                external_ip = upnp.externalipaddress()
                
                # 检查UPnP功能支持
                self.check_upnp_capabilities(upnp)
                
                self.message_queue.put(("DISCOVER_SUCCESS", (upnp, external_ip, devices)))
                
            except Exception as e:
                self.message_queue.put(("DISCOVER_ERROR", f"发现设备失败: {str(e)}"))
        
        threading.Thread(target=discover, daemon=True).start()
    
    def check_upnp_capabilities(self, upnp):
        """检查UPnP功能支持"""
        try:
            # 检查路由器型号信息
            if hasattr(upnp, 'lanaddr'):
                self.log_message(f"路由器LAN地址: {upnp.lanaddr}", "INFO")
            if hasattr(upnp, 'wanaddr'):
                self.log_message(f"路由器WAN地址: {upnp.wanaddr}", "INFO")
            
            # 尝试获取端口映射数量（如果支持的话）
            try:
                mapping_count = 0
                i = 0
                while True:
                    try:
                        # 尝试获取端口映射条目
                        result = upnp.getgenericportmappingentry(i)
                        if result:
                            mapping_count += 1
                            i += 1
                        else:
                            break
                    except:
                        break
                
                self.log_message(f"当前已有 {mapping_count} 个端口映射", "INFO")
            except:
                self.log_message("无法获取现有端口映射信息", "WARNING")
            
            self.log_message("路由器UPnP功能检查完成", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"UPnP功能检查失败: {str(e)}", "WARNING")
    
    def process_queue(self):
        """处理消息队列"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                
                if message_type == "DISCOVER_START":
                    self.device_status.config(text="正在发现设备...", fg='#e67e22')
                    self.update_status("正在发现UPnP设备...", '#e67e22')
                    self.log_message("正在发现UPnP设备...")
                    
                elif message_type == "DISCOVER_SUCCESS":
                    self.upnp, self.external_ip, device_count = data
                    self.device_status.config(text=f"已连接 (发现{device_count}个设备)", fg='#27ae60')
                    self.external_ip_label.config(text=f"外网IP: {self.external_ip}")
                    self.update_status(f"已连接UPnP设备 ({device_count}个)", '#27ae60')
                    self.log_message(f"成功发现{device_count}个UPnP设备", "SUCCESS")
                    self.log_message(f"外网IP地址: {self.external_ip}", "SUCCESS")
                    
                    # 更新IP地址列表
                    self.update_ip_options()
                    
                    self.update_button_states()
                    
                elif message_type == "DISCOVER_ERROR":
                    self.device_status.config(text="设备连接失败", fg='#e74c3c')
                    self.external_ip_label.config(text="")
                    self.update_status("UPnP设备连接失败", '#e74c3c')
                    self.log_message(str(data), "ERROR")
                    self.update_button_states()
                    
                elif message_type == "OPERATION_SUCCESS":
                    self.log_message(str(data), "SUCCESS")
                    self.update_status("操作完成", '#27ae60')
                    
                elif message_type == "OPERATION_ERROR":
                    self.log_message(str(data), "ERROR")
                    self.update_status("操作失败", '#e74c3c')
                    
        except queue.Empty:
            pass
        
        # 每100ms检查一次队列
        self.root.after(100, self.process_queue)
    
    def update_button_states(self):
        """更新按钮状态"""
        if self.upnp is not None:
            self.add_button.config(state='normal')
            self.remove_button.config(state='normal')
        else:
            self.add_button.config(state='disabled')
            self.remove_button.config(state='disabled')
    
    def validate_ip(self, ip):
        """验证IP地址格式"""
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
        if not match:
            return False
        
        # 检查每个数字段是否在0-255范围内
        for group in match.groups():
            if int(group) > 255:
                return False
        
        return True
    
    def add_port_mapping(self):
        """添加端口映射"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        try:
            external_port = int(self.external_port_var.get())
            internal_port = int(self.internal_port_var.get())
            internal_ip = self.internal_ip_var.get()
            protocol = self.protocol_var.get()
            description = self.description_var.get()
            
            if not internal_ip:
                messagebox.showerror("错误", "请输入目标IP地址")
                return
            
            # 验证IP地址格式
            if not self.validate_ip(internal_ip):
                messagebox.showerror("错误", "IP地址格式不正确")
                return
            
            def add_mapping():
                try:
                    # 尝试不同的参数组合
                    success = False
                    error_msg = ""
                    
                    # 首先检查端口是否可能被占用
                    self.log_message(f"正在尝试添加端口映射...")
                    
                    # 方法1：标准参数
                    try:
                        result = self.upnp.addportmapping(external_port, protocol, internal_ip, 
                                                        internal_port, description, '')
                        if result:
                            success = True
                            self.log_message("使用标准参数成功", "SUCCESS")
                    except Exception as e1:
                        error_msg = str(e1)
                        self.log_message(f"标准参数失败: {str(e1)}", "WARNING")
                        
                        # 方法2：尝试不同的描述格式
                        try:
                            result = self.upnp.addportmapping(external_port, protocol, internal_ip, 
                                                            internal_port, description, '0')
                            if result:
                                success = True
                                self.log_message("使用修改后的远程主机参数成功", "SUCCESS")
                        except Exception as e2:
                            self.log_message(f"修改远程主机参数失败: {str(e2)}", "WARNING")
                            
                            # 方法3：尝试更简单的描述
                            try:
                                simple_desc = f"Port{external_port}"
                                result = self.upnp.addportmapping(external_port, protocol, internal_ip, 
                                                                internal_port, simple_desc, '')
                                if result:
                                    success = True
                                    self.log_message("使用简化描述成功", "SUCCESS")
                            except Exception as e3:
                                self.log_message(f"简化描述失败: {str(e3)}", "WARNING")
                                
                                # 方法4：尝试不同的端口
                                try:
                                    alt_port = external_port + 1
                                    result = self.upnp.addportmapping(alt_port, protocol, internal_ip, 
                                                                    internal_port, description, '')
                                    if result:
                                        success = True
                                        self.log_message(f"使用替代端口 {alt_port} 成功", "SUCCESS")
                                except Exception as e4:
                                    # 方法5：尝试最简参数
                                    try:
                                        result = self.upnp.addportmapping(external_port, protocol, internal_ip, 
                                                                        internal_port, "UPnP", '')
                                        if result:
                                            success = True
                                            self.log_message("使用最简参数成功", "SUCCESS")
                                    except Exception as e5:
                                        error_msg = f"所有方法都失败。主要错误: {str(e1)}"
                    
                    if success:
                        self.message_queue.put(("OPERATION_SUCCESS", 
                                              f"端口映射添加成功: {protocol} {external_port} -> {internal_ip}:{internal_port}"))
                    else:
                        # 提供智能建议
                        if "Invalid Args" in error_msg and internal_ip != "127.0.0.1":
                            self.log_message("💡 检测到路由器可能不支持映射到非本机IP", "WARNING")
                            self.log_message("建议解决方案:", "INFO")
                            self.log_message("1. 切换到'本机IP模式'，映射到本机", "INFO")
                            self.log_message("2. 在本机上设置端口转发服务", "INFO")
                            self.log_message("3. 使用SSH隧道或其他代理方式", "INFO")
                        
                        self.message_queue.put(("OPERATION_ERROR", f"添加端口映射失败: {error_msg}"))
                        
                except Exception as e:
                    self.message_queue.put(("OPERATION_ERROR", f"添加端口映射失败: {str(e)}"))
            
            threading.Thread(target=add_mapping, daemon=True).start()
            self.update_status("正在添加端口映射...", '#f39c12')
            self.log_message(f"正在添加端口映射: {protocol} {external_port} -> {internal_ip}:{internal_port}")
            
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
        except Exception as e:
            messagebox.showerror("错误", f"参数错误: {str(e)}")
    
    def remove_port_mapping(self):
        """删除端口映射"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        try:
            external_port = int(self.external_port_var.get())
            protocol = self.protocol_var.get()
            
            def remove_mapping():
                try:
                    result = self.upnp.deleteportmapping(external_port, protocol)
                    if result:
                        self.message_queue.put(("OPERATION_SUCCESS", 
                                              f"端口映射删除成功: {protocol} {external_port}"))
                    else:
                        self.message_queue.put(("OPERATION_ERROR", "端口映射删除失败"))
                except Exception as e:
                    self.message_queue.put(("OPERATION_ERROR", f"删除端口映射失败: {str(e)}"))
            
            threading.Thread(target=remove_mapping, daemon=True).start()
            self.log_message(f"正在删除端口映射: {protocol} {external_port}")
            
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
        except Exception as e:
            messagebox.showerror("错误", f"参数错误: {str(e)}")
    
    def refresh_devices(self):
        """刷新设备"""
        self.upnp = None
        self.external_ip = None
        self.device_status.config(text="正在发现设备...", fg='#e67e22')
        self.external_ip_label.config(text="")
        self.update_button_states()
        self.log_message("正在刷新设备...")
        self.discover_devices_async()
    
    def scan_network(self):
        """扫描网络中的活跃设备"""
        def scan():
            self.log_message("开始扫描网络中的活跃设备...")
            local_ips = self.get_local_ips()
            
            if not local_ips:
                self.log_message("无法获取本机IP，扫描终止", "ERROR")
                return
            
            local_ip = local_ips[0]
            if '.' not in local_ip:
                self.log_message("无法解析网络段，扫描终止", "ERROR")
                return
            
            ip_parts = local_ip.split('.')
            network_base = '.'.join(ip_parts[:3])
            
            active_ips = []
            self.log_message(f"扫描网络段: {network_base}.x")
            
            # 扫描前20个IP（避免扫描时间过长）
            for i in range(1, 21):
                test_ip = f"{network_base}.{i}"
                if test_ip == local_ip:
                    continue
                
                try:
                    # 使用ping检测设备是否在线
                    import subprocess
                    result = subprocess.run(['ping', '-n', '1', '-w', '1000', test_ip], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        active_ips.append(test_ip)
                        self.log_message(f"发现活跃设备: {test_ip}", "SUCCESS")
                except:
                    pass
            
            if active_ips:
                self.log_message(f"扫描完成，发现{len(active_ips)}个活跃设备", "SUCCESS")
                # 更新IP选项列表
                local_ips = self.get_local_ips()
                all_ips = ["127.0.0.1"] + local_ips + active_ips
                self.internal_ip_combo['values'] = all_ips
                if self.ip_type_var.get() == "自定义IP":
                    self.log_message("IP列表已更新，可以选择扫描到的设备IP")
            else:
                self.log_message("未发现其他活跃设备", "WARNING")
        
        threading.Thread(target=scan, daemon=True).start()
    
    def test_connection(self):
        """测试到目标IP的连接"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        target_ip = self.internal_ip_var.get()
        if not target_ip:
            messagebox.showerror("错误", "请输入目标IP地址")
            return
        
        if not self.validate_ip(target_ip):
            messagebox.showerror("错误", "IP地址格式不正确")
            return
        
        def test():
            self.log_message(f"正在测试到 {target_ip} 的连接...")
            
            # 测试ping连接
            try:
                import subprocess
                result = subprocess.run(['ping', '-n', '2', target_ip], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_message(f"Ping {target_ip} 成功", "SUCCESS")
                else:
                    self.log_message(f"Ping {target_ip} 失败", "ERROR")
            except Exception as e:
                self.log_message(f"Ping测试失败: {str(e)}", "ERROR")
            
            # 测试端口连接
            try:
                test_port = int(self.internal_port_var.get())
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((target_ip, test_port))
                sock.close()
                
                if result == 0:
                    self.log_message(f"端口 {test_port} 连接成功", "SUCCESS")
                else:
                    self.log_message(f"端口 {test_port} 连接失败 (可能端口未开放)", "WARNING")
            except Exception as e:
                self.log_message(f"端口测试失败: {str(e)}", "ERROR")
            
            # 测试UPnP端口映射功能
            try:
                # 尝试添加一个临时测试端口映射
                test_external_port = 9999
                result = self.upnp.addportmapping(test_external_port, "TCP", target_ip, 
                                                test_port, "TestConnection", '')
                if result:
                    self.log_message("UPnP端口映射功能正常", "SUCCESS")
                    # 立即删除测试映射
                    try:
                        self.upnp.deleteportmapping(test_external_port, "TCP")
                        self.log_message("测试端口映射已清理", "INFO")
                    except:
                        self.log_message("注意：测试端口映射可能未完全清理", "WARNING")
                else:
                    self.log_message("UPnP端口映射功能异常", "ERROR")
            except Exception as e:
                self.log_message(f"UPnP测试失败: {str(e)}", "ERROR")
                self.log_message("建议检查:", "WARNING")
                self.log_message("1. 目标设备是否在线", "WARNING")
                self.log_message("2. 目标端口是否开放", "WARNING")
                self.log_message("3. 路由器是否支持该端口的映射", "WARNING")
                self.log_message("4. 路由器是否允许映射到非本机IP", "WARNING")
                
                # 检测路由器限制
                if "Invalid Args" in str(e):
                    self.log_message("🔍 检测到可能的限制...", "WARNING")
                    self.log_message("建议：尝试映射到本机IP地址", "INFO")
        
        threading.Thread(target=test, daemon=True).start()
    
    def view_mappings(self):
        """查看当前所有端口映射"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        def view():
            try:
                self.log_message("正在获取当前端口映射...")
                
                mappings = []
                i = 0
                
                # 使用正确的方法获取端口映射
                while True:
                    try:
                        # 尝试获取端口映射条目
                        result = self.upnp.getgenericportmappingentry(i)
                        if result:
                            mappings.append(result)
                            i += 1
                        else:
                            break
                    except:
                        break
                
                if mappings:
                    self.log_message(f"发现 {len(mappings)} 个端口映射:", "INFO")
                    self.log_message("-" * 60, "INFO")
                    
                    for i, mapping in enumerate(mappings, 1):
                        if len(mapping) >= 6:
                            external_port = mapping[0]
                            protocol = mapping[1]
                            internal_ip = mapping[2]
                            internal_port = mapping[3]
                            description = mapping[4]
                            enabled = mapping[5] if len(mapping) > 5 else "未知"
                            
                            self.log_message(f"{i}. {protocol} {external_port} -> {internal_ip}:{internal_port}", "INFO")
                            self.log_message(f"   描述: {description}, 状态: {'启用' if enabled else '禁用'}", "INFO")
                        else:
                            self.log_message(f"{i}. {mapping}", "INFO")
                    
                    self.log_message("-" * 60, "INFO")
                else:
                    self.log_message("当前没有端口映射或路由器不支持查看功能", "INFO")
                    self.log_message("提示：某些路由器可能不支持查看现有端口映射", "WARNING")
                    
            except Exception as e:
                self.log_message(f"获取端口映射失败: {str(e)}", "ERROR")
                self.log_message("这可能是因为路由器不支持此功能", "WARNING")
        
        threading.Thread(target=view, daemon=True).start()
    
    def check_port(self):
        """检查端口是否可用"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        try:
            external_port = int(self.external_port_var.get())
            protocol = self.protocol_var.get()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的端口号")
            return
        
        def check():
            try:
                self.log_message(f"正在检查端口 {external_port} ({protocol}) 是否可用...")
                
                # 检查端口是否已被占用
                port_in_use = False
                try:
                    # 尝试获取该端口的映射信息
                    i = 0
                    while True:
                        try:
                            result = self.upnp.getgenericportmappingentry(i)
                            if result and len(result) >= 3:
                                if result[0] == external_port and result[1] == protocol:
                                    port_in_use = True
                                    self.log_message(f"端口 {external_port} 已被映射到: {result[2]}:{result[3] if len(result) > 3 else 'N/A'}", "WARNING")
                                    break
                            i += 1
                        except:
                            break
                except:
                    pass
                
                if not port_in_use:
                    self.log_message(f"端口 {external_port} ({protocol}) 可用", "SUCCESS")
                    
                    # 尝试测试添加一个临时映射来验证端口可用性
                    try:
                        test_result = self.upnp.addportmapping(external_port, protocol, "127.0.0.1", 
                                                             external_port, "PortCheck", '')
                        if test_result:
                            self.log_message("端口映射功能正常，端口可以添加", "SUCCESS")
                            # 立即删除测试映射
                            try:
                                self.upnp.deleteportmapping(external_port, protocol)
                                self.log_message("测试映射已清理", "INFO")
                            except:
                                self.log_message("注意：测试映射可能未完全清理", "WARNING")
                        else:
                            self.log_message("端口映射添加失败，端口可能不可用", "ERROR")
                    except Exception as e:
                        self.log_message(f"端口测试失败: {str(e)}", "ERROR")
                        if "Invalid Args" in str(e):
                            self.log_message("可能原因：端口已被占用或路由器不支持该端口", "WARNING")
                        elif "Conflict" in str(e):
                            self.log_message("端口冲突：该端口已被其他映射使用", "WARNING")
                else:
                    self.log_message(f"端口 {external_port} 不可用，已被占用", "ERROR")
                    
            except Exception as e:
                self.log_message(f"检查端口失败: {str(e)}", "ERROR")
        
        threading.Thread(target=check, daemon=True).start()
    
    def start_port_forward(self):
        """启动端口转发服务"""
        if not self.upnp:
            messagebox.showerror("错误", "未连接到UPnP设备")
            return
        
        try:
            external_port = int(self.external_port_var.get())
            internal_port = int(self.internal_port_var.get())
            target_ip = self.internal_ip_var.get()
            protocol = self.protocol_var.get()
            
            if not self.validate_ip(target_ip):
                messagebox.showerror("错误", "IP地址格式不正确")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的端口号")
            return
        
        # 获取本机IP
        local_ips = self.get_local_ips()
        if not local_ips:
            messagebox.showerror("错误", "无法获取本机IP地址")
            return
        
        local_ip = local_ips[0]
        
        def forward():
            try:
                self.log_message("🚀 启动端口转发解决方案...", "INFO")
                self.log_message(f"方案：映射到本机 {local_ip}:{external_port}，然后转发到 {target_ip}:{internal_port}", "INFO")
                
                # 第一步：映射到本机
                self.log_message("步骤1：添加端口映射到本机...")
                mapping_result = self.upnp.addportmapping(external_port, protocol, local_ip, 
                                                        external_port, f"Forward to {target_ip}:{internal_port}", '')
                
                if mapping_result:
                    self.log_message("✅ 端口映射到本机成功", "SUCCESS")
                    
                    # 第二步：启动端口转发服务
                    self.log_message("步骤2：启动本机端口转发服务...")
                    self.log_message(f"本机端口转发：{external_port} -> {target_ip}:{internal_port}", "INFO")
                    
                    # 创建端口转发服务
                    import threading
                    import time
                    
                    def port_forward_server():
                        try:
                            if protocol == "TCP":
                                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                server_socket.bind((local_ip, external_port))
                                server_socket.listen(5)
                                
                                self.log_message(f"✅ 端口转发服务已启动：{local_ip}:{external_port}", "SUCCESS")
                                self.log_message("按 Ctrl+C 停止转发服务", "INFO")
                                
                                while True:
                                    try:
                                        client_socket, addr = server_socket.accept()
                                        self.log_message(f"新连接来自: {addr}", "INFO")
                                        
                                        # 创建到目标服务器的连接
                                        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                        target_socket.connect((target_ip, internal_port))
                                        
                                        # 启动数据转发线程
                                        def forward_data(src, dst, direction):
                                            try:
                                                while True:
                                                    data = src.recv(4096)
                                                    if not data:
                                                        break
                                                    dst.send(data)
                                            except:
                                                pass
                                            finally:
                                                src.close()
                                                dst.close()
                                        
                                        threading.Thread(target=forward_data, args=(client_socket, target_socket, "->"), daemon=True).start()
                                        threading.Thread(target=forward_data, args=(target_socket, client_socket, "<-"), daemon=True).start()
                                        
                                    except Exception as e:
                                        if "KeyboardInterrupt" not in str(e):
                                            self.log_message(f"连接处理错误: {str(e)}", "ERROR")
                                        break
                                        
                        except Exception as e:
                            self.log_message(f"端口转发服务启动失败: {str(e)}", "ERROR")
                    
                    # 启动转发服务
                    forward_thread = threading.Thread(target=port_forward_server, daemon=True)
                    forward_thread.start()
                    
                    self.log_message("🎉 端口转发解决方案已启动！", "SUCCESS")
                    self.log_message(f"外部访问地址: {self.external_ip}:{external_port}", "SUCCESS")
                    self.log_message("转发路径: 外网 -> 本机 -> 目标设备", "INFO")
                    
                else:
                    self.log_message("❌ 端口映射到本机失败", "ERROR")
                    self.log_message("无法启动端口转发服务", "ERROR")
                    
            except Exception as e:
                self.log_message(f"端口转发启动失败: {str(e)}", "ERROR")
        
        threading.Thread(target=forward, daemon=True).start()

def main():
    if not UPNPC_AVAILABLE:
        messagebox.showerror("错误", "miniupnpc库未安装\n请运行: pip install miniupnpc")
        return
    
    root = tk.Tk()
    app = UPNPGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
