try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except (ImportError, ModuleNotFoundError):
    tk = None

import threading
import sys
import os


# Fix UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from .checker import EVNBillChecker
from .cli import extract_customer_codes

class EVNCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Tool Tra Cứu Hóa Đơn Điện EVN (Toàn Quốc)")
        self.root.geometry("850x650")
        self.root.minsize(700, 500)

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        # Frame 1: Input
        input_frame = ttk.LabelFrame(root, text=" 📝 Dán đoạn văn bản chứa Mã KH vào đây ", padding=10)
        input_frame.pack(fill="both", expand=False, padx=15, pady=10)

        self.txt_input = tk.Text(input_frame, height=7, font=("Consolas", 10))
        self.txt_input.pack(fill="both", expand=True)
        self.txt_input.insert("1.0", "PC01BB0290022  1,530,403\nPC01BB0308544  1,536,207\nPC01BB0316537  1,549,087\nPC01BB0270441  1,552,824\nPC01BB0271511  1,556,561\nPC01BB0303518  1,564,405")

        # Frame 2: Control Buttons & Progress
        control_frame = ttk.Frame(root, padding=5)
        control_frame.pack(fill="x", padx=15)

        self.btn_check = ttk.Button(control_frame, text="🔍 Bắt Đầu Tra Cứu", command=self.start_checking_thread)
        self.btn_check.pack(side="left", padx=5)

        self.btn_clear = ttk.Button(control_frame, text="🗑️ Xóa Nhập Liệu", command=self.clear_input)
        self.btn_clear.pack(side="left", padx=5)

        self.lbl_status = ttk.Label(control_frame, text="Sẵn sàng", font=("Arial", 10, "italic"))
        self.lbl_status.pack(side="right", padx=10)

        # Frame 3: Output Table
        output_frame = ttk.LabelFrame(root, text=" 📋 Kết Quả Tra Cứu ", padding=10)
        output_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("stt", "code", "region", "status", "debt", "msg")
        self.tree = ttk.Treeview(output_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("stt", text="STT")
        self.tree.heading("code", text="Mã KH")
        self.tree.heading("region", text="Khu Vực EVN")
        self.tree.heading("status", text="Trạng Thái Hóa Đơn")
        self.tree.heading("debt", text="Số Tiền Nợ")
        self.tree.heading("msg", text="Ghi Chú")

        self.tree.column("stt", width=50, anchor="center")
        self.tree.column("code", width=130, anchor="center")
        self.tree.column("region", width=180, anchor="w")
        self.tree.column("status", width=170, anchor="center")
        self.tree.column("debt", width=110, anchor="e")
        self.tree.column("msg", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags for row coloring
        self.tree.tag_configure("paid", background="#E8F8F5", foreground="#117864")
        self.tree.tag_configure("unpaid", background="#FDEDEC", foreground="#C0392B")
        self.tree.tag_configure("error", background="#FEF9E7", foreground="#7D6608")

        self.checker = EVNBillChecker(use_playwright_fallback=True)

    def clear_input(self):
        self.txt_input.delete("1.0", tk.END)

    def start_checking_thread(self):
        raw_text = self.txt_input.get("1.0", tk.END)
        codes = extract_customer_codes(raw_text)

        if not codes:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy Mã Khách Hàng EVN hợp lệ trong văn bản nhập vào!")
            return

        self.btn_check.config(state="disabled")
        self.lbl_status.config(text=f"Đang tra cứu {len(codes)} mã...")
        
        # Clear existing table rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Run checking in background thread to avoid freezing GUI
        thread = threading.Thread(target=self._run_check, args=(codes,))
        thread.daemon = True
        thread.start()

    def _run_check(self, codes):
        for idx, code in enumerate(codes, 1):
            self.lbl_status.config(text=f"Đang kiểm tra {idx}/{len(codes)}: {code}...")
            result = self.checker.check(code)
            dict_res = result.to_dict()

            if not dict_res["success"]:
                tag = "error"
                status_str = "❌ Lỗi tra cứu"
                debt_str = "N/A"
            elif dict_res["is_paid"]:
                tag = "paid"
                status_str = "✅ Đã thanh toán"
                debt_str = "0 VNĐ"
            else:
                tag = "unpaid"
                status_str = "⚠️ Chưa thanh toán"
                debt_str = dict_res["total_debt_formatted"]

            self.root.after(0, self._add_tree_row, (
                idx,
                dict_res["customer_code"],
                dict_res["region"],
                status_str,
                debt_str,
                dict_res["raw_message"] or dict_res.get("error", "")
            ), tag)

        self.root.after(0, self._finish_check, len(codes))

    def _add_tree_row(self, values, tag):
        self.tree.insert("", tk.END, values=values, tags=(tag,))

    def _finish_check(self, count):
        self.btn_check.config(state="normal")
        self.lbl_status.config(text=f"Hoàn thành tra cứu {count} mã KH!")
        messagebox.showinfo("Thành công", f"Đã hoàn thành tra cứu {count} mã khách hàng!")

def launch_gui():
    root = tk.Tk()
    app = EVNCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
