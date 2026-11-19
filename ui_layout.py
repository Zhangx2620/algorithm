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

        self.arr = []
        self.compare_idx = []
        self.swap_idx = []
        self.pivot_idx = []
        self.sorted_indices = set()
        self.compare_cnt = 0
        self.swap_cnt = 0

        self.step_queue = []
        self.is_running = False
        self.auto_run = False
        self.delay = 300

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
        self.step_queue.clear()
        self.is_running = False
        self.auto_run = False
        self.auto_btn.config(text="自动:关")
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

    # 在副本数组上模拟快排，生成步骤队列（不会碰界面数组self.arr）
    def build_step_queue(self, arr_copy, l, r):
        q = []
        stack = [(l, r)]
        while stack:
            cl, cr = stack.pop()
            if cl >= cr:
                if cl == cr:
                    q.append(("mark_sorted", cl))
                continue
            pivot_pos = cl
            q.append(("set_pivot", pivot_pos))
            i = cl
            j = cr
            while i < j:
                while i < j and arr_copy[j] >= arr_copy[pivot_pos]:
                    q.append(("cmp", i, j))
                    j -= 1
                while i < j and arr_copy[i] <= arr_copy[pivot_pos]:
                    q.append(("cmp", i, j))
                    i += 1
                if i < j:
                    arr_copy[i], arr_copy[j] = arr_copy[j], arr_copy[i]
                    q.append(("swap", i, j))
            # pivot归位
            arr_copy[cl], arr_copy[i] = arr_copy[i], arr_copy[cl]
            q.append(("swap", cl, i))
            q.append(("mark_sorted", i))
            stack.append((i+1, cr))
            stack.append((cl, i-1))
        return q

    def exec_one_step(self):
        if not self.step_queue:
            self.is_running = False
            return False
        act = self.step_queue.pop(0)
        typ = act[0]
        self.compare_idx = []
        self.swap_idx = []
        self.pivot_idx = []
        if typ == "set_pivot":
            _, pos = act
            self.pivot_idx = [pos]
        elif typ == "cmp":
            _, a, b = act
            self.compare_idx = [a, b]
            self.compare_cnt += 1
        elif typ == "swap":
            _, a, b = act
            self.arr[a], self.arr[b] = self.arr[b], self.arr[a]
            self.swap_idx = [a, b]
            self.swap_cnt += 1
        elif typ == "mark_sorted":
            _, pos = act
            self.sorted_indices.add(pos)
        self.draw()
        return True

    def start_sort(self):
        if self.is_running:
            return
        self.is_running = True
        self.compare_cnt = 0
        self.swap_cnt = 0
        self.sorted_indices.clear()
        tmp = self.arr.copy()
        self.step_queue = self.build_step_queue(tmp, 0, len(tmp)-1)
        if self.auto_run:
            self.auto_loop()

    def auto_loop(self):
        if not self.is_running or not self.auto_run:
            return
        has_more = self.exec_one_step()
        if has_more:
            self.root.after(self.delay, self.auto_loop)

    def step_sort(self):
        if not self.is_running and len(self.step_queue) == 0:
            messagebox.showinfo("提示", "请先点击【开始排序】初始化排序流程，再点单步")
            return
        self.exec_one_step()

    def toggle_auto(self):
        self.auto_run = not self.auto_run
        if self.auto_run:
            self.auto_btn.config(text="自动:开")
            if self.is_running:
                self.auto_loop()
        else:
            self.auto_btn.config(text="自动:关")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickSortVisual(root)
    root.mainloop()
