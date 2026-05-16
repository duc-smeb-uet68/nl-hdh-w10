"""
Giao diện Tkinter cho chương trình mô phỏng thay thế trang.

Giao diện gồm:
    - Ô nhập chuỗi trang và số frame
    - Nút chọn thuật toán (FIFO / Optimal / LRU / Second Chance)
    - Nút "Chạy" (từng bước), "Chạy tất" (toàn bộ), "Reset"
    - Bảng hiển thị kết quả từng bước
    - Thống kê tổng page fault / hit / tỉ lệ
"""

import tkinter as tk
from tkinter import ttk, messagebox

from algorithms import ALGORITHMS


class PageReplacementGUI:
    """Cửa sổ chính của chương trình."""

    def __init__(self, root):
        self.root = root
        self.root.title("Mô phỏng thay thế trang")
        self.root.geometry("850x550")

        # --- Trạng thái chương trình ---
        self.steps_data = []        # Kết quả từng bước từ thuật toán
        self.total_faults = 0       # Tổng page fault (sau khi chạy xong toàn bộ)
        self.current_step = 0       # Bước hiện tại (cho chế độ chạy từng bước)
        self.fault_count = 0        # Đếm fault khi chạy từng bước

        # Tạo giao diện
        self._create_title()
        self._create_input_section()
        self._create_algorithm_selector()
        self._create_buttons()
        self._create_result_table()
        self._create_stats_label()

    # =========================================================================
    # Tạo giao diện
    # =========================================================================

    def _create_title(self):
        """Tiêu đề chương trình."""
        tk.Label(
            self.root,
            text="MÔ PHỎNG THAY THẾ TRANG",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

    def _create_input_section(self):
        """Ô nhập chuỗi trang và số frame."""
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Chuỗi trang
        tk.Label(frame, text="Chuỗi trang:").grid(row=0, column=0, padx=5)
        self.entry_pages = tk.Entry(frame, width=50)
        self.entry_pages.grid(row=0, column=1, padx=5)
        self.entry_pages.insert(0, "7 0 1 2 0 3 0 4 2 3 0 3 2")

        # Số frame
        tk.Label(frame, text="Số frame:").grid(row=1, column=0, padx=5)
        self.entry_frames = tk.Entry(frame, width=10)
        self.entry_frames.grid(row=1, column=1, sticky="w")
        self.entry_frames.insert(0, "3")

        # Reference bits cho Second Chance
        tk.Label(frame, text="Ref bits (Second Chance):").grid(row=2, column=0, padx=5)
        self.entry_ref_bits = tk.Entry(frame, width=50)
        self.entry_ref_bits.grid(row=2, column=1, padx=5)
        self.entry_ref_bits.insert(0, "1 0 1 0 0 1 0 1 0 1 0 1 0")

    def _create_algorithm_selector(self):
        """Nút radio chọn thuật toán."""
        self.algo_var = tk.StringVar(value="FIFO")

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        for algo_name in ALGORITHMS:
            tk.Radiobutton(
                frame,
                text=algo_name,
                variable=self.algo_var,
                value=algo_name,
                command=self._on_algorithm_changed
            ).pack(side=tk.LEFT, padx=10)

        self._on_algorithm_changed()

    def _create_buttons(self):
        """Ba nút: Chạy từng bước, Chạy tất cả, Reset."""
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Nút chạy từng bước
        tk.Button(
            frame, text="Chạy", font=("Arial", 12),
            bg="lightgreen", command=self._on_step
        ).pack(side=tk.LEFT, padx=5)

        # Nút chạy tất cả
        tk.Button(
            frame, text="Chạy tất", font=("Arial", 12),
            bg="lightblue", command=self._on_run_all
        ).pack(side=tk.LEFT, padx=5)

        # Nút reset
        tk.Button(
            frame, text="Reset", font=("Arial", 12),
            bg="lightyellow", command=self._on_reset
        ).pack(side=tk.LEFT, padx=5)

    def _create_result_table(self):
        """Bảng hiển thị kết quả từng bước."""
        columns = ("Bước", "Trang", "Frame", "Ref Bits", "Victim", "Trạng thái")

        self.tree = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=15
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.pack(pady=10)

    def _create_stats_label(self):
        """Nhãn hiển thị thống kê page fault / hit / tỉ lệ."""
        self.label_stats = tk.Label(
            self.root,
            text="",
            font=("Arial", 13, "bold"),
            fg="red"
        )
        self.label_stats.pack(pady=10)

    # =========================================================================
    # Đọc input và chạy thuật toán
    # =========================================================================

    def _parse_input(self):
        """
        Đọc chuỗi trang và số frame từ giao diện.
        Trả về (pages, frames_count) hoặc None nếu input không hợp lệ.
        """
        try:
            pages = list(map(int, self.entry_pages.get().split()))
            frames_count = int(self.entry_frames.get())

            if frames_count <= 0:
                raise ValueError("Số frame phải > 0")
            if len(pages) == 0:
                raise ValueError("Chuỗi trang trống")

            return pages, frames_count
        except ValueError:
            messagebox.showerror("Lỗi", "Hãy nhập đúng dữ liệu!\n"
                                         "- Chuỗi trang: các số nguyên cách nhau bởi dấu cách\n"
                                         "- Số frame: số nguyên dương")
            return None

    def _parse_ref_bits(self, pages):
        """Đọc và kiểm tra reference bits cho Second Chance."""
        try:
            raw_bits = self.entry_ref_bits.get().split()
            if not raw_bits:
                raise ValueError("Hãy nhập ref bits cho Second Chance")

            ref_bits = list(map(int, raw_bits))
            if len(ref_bits) != len(pages):
                raise ValueError("Số ref bit phải bằng số trang trong chuỗi")
            if any(bit not in (0, 1) for bit in ref_bits):
                raise ValueError("Ref bits chỉ được là 0 hoặc 1")

            page_bits = {}
            for page, bit in zip(pages, ref_bits):
                if page in page_bits and page_bits[page] != bit:
                    raise ValueError(f"Trang {page} có ref bit không nhất quán")
                page_bits[page] = bit

            return ref_bits
        except ValueError as error:
            messagebox.showerror("Lỗi", str(error))
            return None

    def _run_algorithm(self):
        """
        Chạy thuật toán đã chọn, lưu kết quả vào self.steps_data.
        Trả về True nếu thành công, False nếu lỗi input.
        """
        parsed = self._parse_input()
        if parsed is None:
            return False

        pages, frames_count = parsed
        algo_name = self.algo_var.get()
        algorithm = ALGORITHMS[algo_name]

        # Chạy thuật toán, lưu kết quả
        if algo_name == "Second Chance":
            ref_bits = self._parse_ref_bits(pages)
            if ref_bits is None:
                return False
            self.steps_data, self.total_faults = algorithm(pages, frames_count, ref_bits)
        else:
            self.steps_data, self.total_faults = algorithm(pages, frames_count)

        self.current_step = 0
        self.fault_count = 0

        # Xóa bảng cũ và thống kê
        self._clear_table()
        self._update_stats_label()

        return True

    # =========================================================================
    # Hiển thị kết quả
    # =========================================================================

    def _add_step_to_table(self, step_number, step_data):
        """
        Thêm một bước vào bảng kết quả.
            step_number: số thứ tự (bắt đầu từ 1)
            step_data:   tuple (page, frames, ref_bits, status, victim)
        """
        page, frames, ref_bits, status, victim = step_data

        frame_text = " | ".join(map(str, frames))
        ref_text = " | ".join(map(str, ref_bits)) if ref_bits else ""
        victim_text = str(victim) if victim is not None else "-"

        self.tree.insert(
            "", "end",
            values=(step_number, page, frame_text, ref_text, victim_text, status)
        )

    def _update_stats_label(self):
        """Cập nhật nhãn thống kê với số fault hiện tại."""
        if not self.steps_data:
            self.label_stats.config(text="")
            return

        # Tổng số bước đã hiển thị
        total_steps = self.current_step
        if total_steps == 0:
            self.label_stats.config(text="")
            return

        hits = total_steps - self.fault_count
        hit_rate = (hits / total_steps) * 100
        fault_rate = (self.fault_count / total_steps) * 100

        self.label_stats.config(
            text=f"Page Fault: {self.fault_count}  |  "
                 f"Page Hit: {hits}  |  "
                 f"Tỉ lệ Hit: {hit_rate:.1f}%  |  "
                 f"Tỉ lệ Fault: {fault_rate:.1f}%"
        )

    def _clear_table(self):
        """Xóa toàn bộ dữ liệu trong bảng."""
        for row in self.tree.get_children():
            self.tree.delete(row)

    # =========================================================================
    # Xử lý sự kiện nút bấm
    # =========================================================================

    def _on_algorithm_changed(self):
        """Bật ô ref bit khi chọn Second Chance."""
        state = "normal" if self.algo_var.get() == "Second Chance" else "disabled"
        self.entry_ref_bits.config(state=state)

    def _on_step(self):
        """Nút "Chạy" — hiển thị từng bước một."""
        # Lần đầu bấm → chạy thuật toán
        if not self.steps_data:
            if not self._run_algorithm():
                return

        # Đã hết bước → thông báo
        if self.current_step >= len(self.steps_data):
            messagebox.showinfo("Thông báo", "Đã chạy hết các bước!")
            return

        # Lấy dữ liệu bước hiện tại
        step_data = self.steps_data[self.current_step]

        # Đếm fault
        if step_data[3] == "Fault":     # step_data[3] = status
            self.fault_count += 1

        # Hiển thị bước
        self._add_step_to_table(self.current_step + 1, step_data)
        self.current_step += 1

        # Cập nhật thống kê
        self._update_stats_label()

    def _on_run_all(self):
        """Nút "Chạy tất" — hiển thị toàn bộ các bước."""
        if not self._run_algorithm():
            return

        # Thêm tất cả các bước vào bảng
        for i, step_data in enumerate(self.steps_data):
            self._add_step_to_table(i + 1, step_data)

        # Cập nhật thống kê (dùng tổng fault từ thuật toán)
        self.fault_count = self.total_faults
        self.current_step = len(self.steps_data)
        self._update_stats_label()

    def _on_reset(self):
        """Nút "Reset" — xóa kết quả, quay về trạng thái ban đầu."""
        self._clear_table()
        self.steps_data = []
        self.current_step = 0
        self.fault_count = 0
        self.label_stats.config(text="")


# =============================================================================
# Hàm khởi tạo cửa sổ (được gọi từ main.py)
# =============================================================================

def create_window():
    """Tạo và chạy cửa sổ chính."""
    root = tk.Tk()
    PageReplacementGUI(root)
    root.mainloop()
