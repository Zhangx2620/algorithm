import tkinter as tk
from tkinter import ttk, messagebox
import random

class QuickSortVisual:
    def __init__(self, root):
        self.root = root
        self.root.title("快速排序可视化演示器")
        self.root.geometry("1250x750")
        self.root.configure(bg="#efefef")
        self.root.bind("<Configure>", self.on_window_resize)

        # 排序状态
        self.arr = []
        self.compare_idx = []
        self.swap_idx = []
        self.pivot_idx = []
        self.sorted_indices = set()
        self.recursion_nodes = [] # (l, pivot, r, parent_id, level, x_pos)
        self.node_id = 0

        self.auto_run = False
        self.delay = 300
        self.compare_cnt = 0
        self.swap_cnt = 0
        self.is_running = False

        # 顶部控制面板
        top_frame = tk.Frame(root, bg="#efefef")
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="数组长度：", background="#efefef").pack(side=tk.LEFT, padx=4)
        self.len_entry = ttk.Entry(top_frame, width=12)
        self.len_entry.insert(0, "12")
        self.len_entry.pack(side=tk.LEFT, padx=4)

        ttk.Button(top_frame, text="随机生成", command=self.random_arr).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_frame, text="开始排序", command=self.start_sort).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_frame, text="单步", command=self.step_sort).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_frame, text="重置", command=self.reset).pack(side=tk.LEFT, padx=4)

        self.auto_btn = ttk.Button(top_frame, text="自动:关", command=self.toggle_auto)
        self.auto_btn.pack(side=tk.LEFT, padx=4)

        # 画布
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.reset()

    def on_window_resize(self, event):
        self.draw()

    def random_arr(self):
        try:
            n = int(self.len_entry.get())
        except:
            n = 12
        n = max(3, min(20, n))
        self.arr = [random.randint(10,90) for _ in range(n)]
        self.reset()

    def reset(self):
        self.compare_cnt = 0
        self.swap_cnt = 0
        self.sorted_indices = set()
        self.compare_idx = []
        self.swap_idx = []
        self.pivot_idx = []
        self.is_running = False
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if len(self.arr) == 0:
            return
        bar_w = w / (len(self.arr)+1)
        max_val = max(self.arr)
        for idx, val in enumerate(self.arr):
            x1 = idx * bar_w + 10
            x2 = x1 + bar_w - 4
            h_bar = (val / max_val) * (h*0.6)
            y2 = h*0.7
            y1 = y2 - h_bar
            # 颜色
            if idx in self.sorted_indices:
                color = "#44bb44"
            elif idx in self.swap_idx:
                color = "#ee4444"
            elif idx in self.compare_idx:
                color = "#ffcc00"
            elif idx in self.pivot_idx:
                color = "#4488ff"
            else:
                color = "#888888"
            self.canvas.create_rectangle(x1,y1,x2,y2,fill=color)
            self.canvas.create_text((x1+x2)/2, y1-10, text=str(val))
        self.canvas.create_text(w/2, 20, text=f"比较次数：{self.compare_cnt}  交换次数：{self.swap_cnt}", font=("SimHei",12))

    def start_sort(self):
        if self.is_running:
            return
        self.is_running = True
        self.quick_sort(0, len(self.arr)-1)

    def quick_sort(self, l, r):
        if l >= r:
            if l == r:
                self.sorted_indices.add(l)
                self.draw()
                if self.auto_run:
                    self.root.after(self.delay)
            return True
        # 选pivot
        pivot = self.arr[l]
        self.pivot_idx = [l]
        self.draw()
        if self.auto_run:
            self.root.after(self.delay)
        i = l
        j = r
        while i < j:
            while i<j and self.arr[j] >= pivot:
                self.compare_idx = [i,j]
                self.compare_cnt +=1
                self.draw()
                if self.auto_run:
                    self.root.after(self.delay)
                j -=1
            while i<j and self.arr[i] <= pivot:
                self.compare_idx = [i,j]
                self.compare_cnt +=1
                self.draw()
                if self.auto_run:
                    self.root.after(self.delay)
                i +=1
            if i<j:
                self.arr[i], self.arr[j] = self.arr[j], self.arr[i]
                self.swap_idx = [i,j]
                self.swap_cnt +=1
                self.draw()
                if self.auto_run:
                    self.root.after(self.delay)
                self.swap_idx = []
        # pivot归位
        self.arr[l], self.arr[i] = self.arr[i], self.arr[l]
        self.swap_idx = [l,i]
        self.swap_cnt +=1
        self.sorted_indices.add(i)
        self.draw()
        if self.auto_run:
            self.root.after(self.delay)
        self.swap_idx = []
        self.pivot_idx = []
        self.compare_idx = []
        self.quick_sort(l, i-1)
        self.quick_sort(i+1, r)
        return True

    def step_sort(self):
        messagebox.showinfo("提示","单步版本需要额外状态栈，当前版本直接用自动模式即可")

    def toggle_auto(self):
        self.auto_run = not self.auto_run
        if self.auto_run:
            self.auto_btn.config(text="自动:开")
        else:
            self.auto_btn.config(text="自动:关")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickSortVisual(root)
    root.mainloop()
