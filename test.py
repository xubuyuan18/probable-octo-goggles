import tkinter as tk
from tkinter import ttk, messagebox
import ipaddress
import math

class SubnetCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("子网划分计算器")
        self.root.geometry("800x600")
        
        # 初始化样式配置
        self.setup_basic_style()
        
        # 构建界面组件
        self.create_widgets()
        
        # 绑定事件
        self.root.bind("<Return>", lambda e: self.start_calculation())

    def setup_basic_style(self):
        """配置基础样式"""
        self.style = ttk.Style()
        self.style.configure(".", font=("Helvetica", 10))
        self.style.configure("TButton", padding=6, background="#4A90E2", foreground="white")
        self.style.map("TButton",
                      background=[("active", "#63A5F1"), ("disabled", "#BBD3FB")])

    def create_widgets(self):
        """创建核心界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text=" 输入参数 ")
        input_frame.pack(fill=tk.X, pady=5)

        # 网络地址输入行
        ip_row = ttk.Frame(input_frame)
        ip_row.pack(fill=tk.X, pady=5)
        ttk.Label(ip_row, text="主网络地址 (CIDR格式):").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(ip_row, width=25)
        self.ip_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.ip_entry.insert(0, "192.168.1.0/24")

        # 模式选择行
        mode_row = ttk.Frame(input_frame)
        mode_row.pack(fill=tk.X, pady=5)
        self.mode_var = tk.StringVar(value="subnets")
        ttk.Radiobutton(mode_row, text="按子网数量划分", variable=self.mode_var, 
                       value="subnets").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_row, text="按主机数量划分", variable=self.mode_var,
                       value="hosts").pack(side=tk.LEFT, padx=10)

        # 数量输入行
        num_row = ttk.Frame(input_frame)
        num_row.pack(fill=tk.X, pady=5)
        ttk.Label(num_row, text="数量:").pack(side=tk.LEFT)
        self.num_entry = ttk.Entry(num_row, width=10)
        self.num_entry.pack(side=tk.LEFT, padx=5)

        # 操作按钮行
        btn_row = ttk.Frame(input_frame)
        btn_row.pack(fill=tk.X, pady=10)
        self.calc_btn = ttk.Button(btn_row, text="开始计算", command=self.start_calculation)
        self.calc_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="清空", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # 结果展示区域
        result_frame = ttk.LabelFrame(main_frame, text=" 计算结果 ")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 结果表格
        self.tree = ttk.Treeview(
            result_frame,
            columns=("subnet", "mask", "hosts", "range"),
            show="headings",
            selectmode="browse"
        )
        
        # 配置表格列
        columns_config = [
            ("subnet", "子网地址", 200),
            ("mask", "子网掩码", 150),
            ("hosts", "可用主机数", 100),
            ("range", "可用IP范围", 250)
        ]
        for col_id, col_text, col_width in columns_config:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=col_width, anchor=tk.W)

        # 添加滚动条
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局表格和滚动条
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # 配置自适应布局
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 状态栏
        self.status = ttk.Label(main_frame, text="就绪", anchor=tk.W)
        self.status.pack(fill=tk.X)

    def start_calculation(self):
        """启动计算流程"""
        try:
            # 验证输入有效性
            if not self.validate_inputs():
                return

            # 获取输入参数
            network = ipaddress.IPv4Network(self.ip_entry.get().strip(), strict=False)
            num = int(self.num_entry.get())
            mode = self.mode_var.get()

            # 执行计算
            if mode == "subnets":
                new_prefix = network.prefixlen + math.ceil(math.log2(num))
            else:
                new_prefix = 32 - math.ceil(math.log2(num + 2))

            # 生成子网信息
            subnets = list(network.subnets(new_prefix=new_prefix))
            netmask = str(ipaddress.IPv4Network(f"0.0.0.0/{new_prefix}").netmask)

            # 更新界面
            self.update_result_table(netmask, new_prefix, subnets, network.prefixlen)
            self.status.config(text=f"计算完成，共生成 {len(subnets)} 个子网")

        except Exception as e:
            messagebox.showerror("计算错误", f"发生错误：{str(e)}")
            self.status.config(text="计算出错，请检查输入")

    def update_result_table(self, netmask, new_prefix, subnets, original_prefix):
        """更新结果表格"""
        self.tree.delete(*self.tree.get_children())
        
        # 添加表头信息
        total_subnets = 2 ** (new_prefix - original_prefix)
        self.tree.insert("", "end", values=(
            f"主网络：{self.ip_entry.get()}",
            f"{netmask} (/{new_prefix})",
            f"总子网数：{total_subnets}",
            ""
        ), tags=("header",))
        
        # 添加子网数据
        for subnet in subnets:
            hosts = subnet.num_addresses - 2
            self.tree.insert("", "end", values=(
                str(subnet.network_address),
                str(subnet.netmask),
                f"{hosts} 台" if hosts > 0 else "无效",
                f"{subnet.network_address + 1} - {subnet.broadcast_address - 1}"
            ))
        
        # 配置表头样式
        self.tree.tag_configure("header", background="#E3F2FD")

    def validate_inputs(self):
        """验证输入有效性"""
        try:
            # 检查CIDR格式
            ipaddress.IPv4Network(self.ip_entry.get().strip(), strict=False)
            
            # 检查数量值
            num = int(self.num_entry.get())
            if num <= 0:
                raise ValueError("数量必须大于0")
                
            return True
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效输入：{str(e)}")
            self.status.config(text="输入错误，请检查输入框")
            return False

    def clear_all(self):
        """清空所有内容"""
        self.ip_entry.delete(0, tk.END)
        self.num_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.status.config(text="就绪")

if __name__ == "__main__":
    root = tk.Tk()
    app = SubnetCalculator(root)
    root.mainloop()
