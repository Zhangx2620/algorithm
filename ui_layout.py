import tkinter as tk
from tkinter import ttk, messagebox
import random

class QuickSortVisual:
    def __init__(self, root):
        self.root = root
        self.root.title("快速排序可视化演示器")
        self.root.geometry("1250x750")
        self.root.configure(bg="#f8f9fa")
        self.root.bind("<Configure>", self.on_window_resize)

        # 排序状态
        self.arr = []
        self.compare_idx = -1
        self.swap_idx = -1
        self.pivot_idx = -1
        self.sorted_indices = set()
        self.recursion_nodes = []  # (l, pivot, r, parent_id, level, x_pos)
        self.node_id = 0

        self.auto_run = False
        self.delay = 300
        self.compare_cnt = 0
        self.swap_cnt = 0
        self.is_running = False

        # 顶部控制面板
        top_frame = tk.Frame(root, bg="#f8f9fa")
        top_frame.pack(fill=tk.X, padx=12, pady=6)

        ttk.Label(top_frame, text="数组长度：", background="#f8f9fa").pack(side=tk.LEFT, padx=4)
        self.len_entry = ttk.Entry(top_frame, width=8)
        self.len_entry.insert(0, "12")
        self.len_entry.pack(side=tk.LEFT, padx=4)

        self.btn_gen = ttk.Button(top_frame, text="生成随机数组", command=self.generate_arr)
        self.btn_gen.pack(side=tk.LEFT, padx=6)

        self.btn_step = ttk.Button(top_frame, text="单步执行", command=self.step_sort)
        self.btn_step.pack(side=tk.LEFT, padx=4)

        self.btn_auto = ttk.Button(top_frame, text="自动播放", command=self.toggle_auto)
        self.btn_auto.pack(side=tk.LEFT, padx=4)

        self.btn_reset = ttk.Button(top_frame, text="重置", command=self.reset_all)
        self.btn_reset.pack(side=tk.LEFT, padx=4)

        ttk.Label(top_frame, text="速度(ms)：", background="#f8f9fa").pack(side=tk.LEFT, padx=(18, 4))
        self.speed_slider = ttk.Scale(top_frame, from_=50, to=1500, orient=tk.HORIZONTAL,
                                      command=self.set_delay)
        self.speed_slider.set(300)
        self.speed_slider.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.stat_text = tk.Label(top_frame, text=f"比较次数：0 | 交换次数：0", bg="#f8f9fa", font=("SimSun",11))
        self.stat_text.pack(side=tk.RIGHT, padx=12)

        # 中间区域：柱状图 + 递归树
        mid_frame = tk.Frame(root, bg="#f8f9fa")
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        self.bar_canvas = tk.Canvas(mid_frame, bg="#ffffff", highlightthickness=1, highlightcolor="#cbd5e1")
        self.bar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_canvas = tk.Canvas(mid_frame, bg="#ffffff", highlightthickness=1, highlightcolor="#cbd5e1", width=420)
        self.tree_canvas.pack(side=tk.RIGHT, fill=tk.BOTH)

        # 底部日志面板
        log_frame = tk.Frame(root, bg="#f8f9fa")
        log_frame.pack(fill=tk.X, padx=12, pady=6)
        ttk.Label(log_frame, text="运行日志：", background="#f8f9fa").pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, bg="#f1f5f9", font=("SimSun",10))
        self.log_text.pack(fill=tk.X)

    def set_delay(self, val):
        self.delay = int(float(val))

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_stat(self):
        self.stat_text.config(text=f"比较次数：{self.compare_cnt} | 交换次数：{self.swap_cnt}")

    def set_btn_state(self, running: bool):
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL
        self.btn_gen.config(state=state)
        self.len_entry.config(state=state)

    def generate_arr(self):
        try:
            n = int(self.len_entry.get())
        except ValueError:
            self.log("⚠️ 错误：请输入合法整数！")
            return
        if n < 3 or n > 20:
            self.log("⚠️ 范围限制：数组长度请输入 3~20 之间！")
            return
        self.arr = [random.randint(5, 95) for _ in range(n)]
        self.reset_all(keep_arr=True)
        self.log(f"✅ 生成新数组：{self.arr}")
        self.draw_bars()
        self.draw_tree()

    def reset_all(self, keep_arr=False):
        self.auto_run = False
        self.btn_auto.config(text="自动播放")
        self.set_btn_state(False)
        self.compare_idx = -1
        self.swap_idx = -1
        self.pivot_idx = -1
        self.sorted_indices = set()
        self.recursion_nodes = []
        self.node_id = 0
        if not keep_arr:
            self.arr = []
        self.compare_cnt = 0
        self.swap_cnt = 0
        self.update_stat()
        self.log_text.delete(1.0, tk.END)
        self.draw_bars()
        self.draw_tree()

    def on_window_resize(self, event):
        self.draw_bars()
        self.draw_tree()

    # 柱状图渲染
    def draw_bars(self):
        c = self.bar_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if len(self.arr) == 0 or w < 20 or h < 20:
            return
        gap = 4
        bar_w = (w - gap * len(self.arr)) / len(self.arr)
        max_val = max(self.arr)

        for i, val in enumerate(self.arr):
            x1 = i * (bar_w + gap)
            x2 = x1 + bar_w
            bar_h = val / max_val * (h - 45)
            y1 = h - bar_h - 12
            y2 = h - 12

            if i == self.pivot_idx:
                color = "#a855f7"
            elif i in self.sorted_indices:
                color = "#22c55e"
            elif i == self.compare_idx:
                color = "#fbbf24"
            elif i == self.swap_idx:
                color = "#ef4444"
            else:
                color = "#60a5fa"
            c.create_rectangle(x1, y1, x2, y2, fill=color, outline="#1f2937", width=1)
            c.create_text((x1 + x2)/2, y1 - 6, text=str(val), fill="#1f2937", font=("SimSun",9))

    # 递归树渲染（优化：自动均分，节点不重叠）
    def draw_tree(self):
        c = self.tree_canvas
        c.delete("all")
        level_height = 85
        node_w = 105
        node_h = 42
        if not self.recursion_nodes:
            return
        # 按层级分组
        level_dict = {}
        for nid, item in enumerate(self.recursion_nodes):
            l, pv, r, parent, level, x = item
            if level not in level_dict:
                level_dict[level] = []
            level_dict[level].append(nid)
        # 同一层均匀分布
        canvas_w = c.winfo_width()
        for lv, node_list in level_dict.items():
            count = len(node_list)
            step = canvas_w / (count + 1)
            for idx, nid in enumerate(node_list):
                l, pv, r, parent, level, _ = self.recursion_nodes[nid]
                x = step * (idx + 1)
                y = 35 + lv * level_height
                fill_color = "#d8c4f0" if pv != -1 else "#e2e8f0"
                c.create_rectangle(x-node_w/2, y-node_h/2, x+node_w/2, y+node_h/2, fill=fill_color, outline="#1f2937")
                c.create_text(x, y, text=f"[{l}, {pv}, {r}]", font=("SimSun",9))
                # 绘制父子连线
                if parent is not None:
                    pl, ppv, pr, ppid, plv, px = self.recursion_nodes[parent]
                    py = 35 + plv * level_height
                    c.create_line(px, py + node_h/2, x, y - node_h/2, fill="#64748b", width=1.2)
                # 更新坐标
                self.recursion_nodes[nid] = (l, pv, r, parent, level, x)

    # 【对外接口｜给算法同学调用】
    def set_sort_state(self, arr, compare=-1, swap=-1, pivot=-1, sorted_set=None, log_msg=""):
        self.arr = arr.copy()
        self.compare_idx = compare
        self.swap_idx = swap
        self.pivot_idx = pivot
        if sorted_set is not None:
            self.sorted_indices = sorted_set
        if log_msg:
            self.log(log_msg)
        self.draw_bars()
        self.root.update()

    def add_tree_node(self, l, pivot, r, parent_id=None):
        level = 0
        if parent_id is not None:
            _, _, _, _, level_p, _ = self.recursion_nodes[parent_id]
            level = level_p + 1
        # 初始x，draw_tree会自动重排
        self.recursion_nodes.append((l, pivot, r, parent_id, level, 200))
        nid = self.node_id
        self.node_id += 1
        self.draw_tree()
        return nid

    def finish_sort(self):
        self.auto_run = False
        self.btn_auto.config(text="自动播放")
        self.set_btn_state(False)
        self.log("🎉 排序全部完成！")
        messagebox.showinfo("完成", "快速排序执行完毕！")

    def step_sort(self):
        """留给算法接入，UI层仅触发回调"""
        self.log("💡 单步触发：等待算法模块接入排序逻辑")

    def toggle_auto(self):
        self.auto_run = not self.auto_run
        if self.auto_run:
            self.btn_auto.config(text="暂停")
            self.set_btn_state(True)
            self.auto_loop()
        else:
            self.btn_auto.config(text="自动播放")
            self.set_btn_state(False)

    def auto_loop(self):
        if not self.auto_run:
            return
        self.step_sort()
        self.root.after(self.delay, self.auto_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickSortVisual(root)
    root.mainloop()
