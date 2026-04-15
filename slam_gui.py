import customtkinter as ctk
import subprocess
import threading
import os
import time

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class SLAM_App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ORB-SLAM3 Control Panel - v9.0 Perfect Stop")
        self.geometry("700x580") 
        self.resizable(False, False)

        self.title_label = ctk.CTkLabel(self, text="HỆ THỐNG ĐỊNH VỊ SLAM", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))
        
        self.subtitle_label = ctk.CTkLabel(self, text="Bản V9.0: Auto-Stop mô phỏng hành vi con người", font=ctk.CTkFont(size=14), text_color="gray")
        self.subtitle_label.pack(pady=(0, 15))

        self.available_datasets = [
            "KITTI - Sequence 00", "KITTI - Sequence 01", "KITTI - Sequence 02", 
            "KITTI - Sequence 03", "KITTI - Sequence 04", "KITTI - Sequence 05"
        ]

        self.dataset_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dataset_frame.pack(pady=5)

        self.dataset_var = ctk.StringVar(value="Chọn Dataset KITTI...")
        self.dataset_menu = ctk.CTkOptionMenu(
            self.dataset_frame, variable=self.dataset_var, values=self.available_datasets,
            width=300, height=40, font=ctk.CTkFont(size=14)
        )
        self.dataset_menu.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.btn_add = ctk.CTkButton(self.dataset_frame, text="+ Thêm Mới", width=145, height=35, fg_color="#8E44AD", hover_color="#9B59B6", command=self.add_dataset)
        self.btn_add.grid(row=1, column=0, padx=5)

        self.btn_del = ctk.CTkButton(self.dataset_frame, text="- Xóa Bỏ", width=145, height=35, fg_color="#E74C3C", hover_color="#C0392B", command=self.del_dataset)
        self.btn_del.grid(row=1, column=1, padx=5)

        self.run_button = ctk.CTkButton(
            self, text="▶ BẮT ĐẦU CHẠY", width=300, height=45, 
            font=ctk.CTkFont(size=15, weight="bold"), fg_color="#2ECC71", hover_color="#27AE60",
            command=self.start_slam_thread
        )
        self.run_button.pack(pady=(15, 5))

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.is_paused = False
        self.btn_pause = ctk.CTkButton(
            self.control_frame, text="⏸ TẠM DỪNG", width=140, height=40,
            fg_color="#F39C12", hover_color="#D68910", font=ctk.CTkFont(weight="bold"), command=self.toggle_pause
        )
        self.btn_pause.grid(row=0, column=0, padx=5)

        self.btn_midway_save = ctk.CTkButton(
            self.control_frame, text="💾 LƯU CHẶNG", width=140, height=40,
            fg_color="#3498DB", hover_color="#2980B9", font=ctk.CTkFont(weight="bold"), command=self.trigger_midway_save
        )
        self.btn_midway_save.grid(row=0, column=1, padx=5)

        self.btn_stop = ctk.CTkButton(
            self.control_frame, text="⏹ KẾT THÚC", width=140, height=40,
            fg_color="#E74C3C", hover_color="#C0392B", font=ctk.CTkFont(weight="bold"), command=self.force_stop_and_save
        )
        self.btn_stop.grid(row=0, column=2, padx=5)

        self.status_label = ctk.CTkLabel(self, text="Trạng thái: Đang chờ lệnh...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=15)

        self.progress_bar = ctk.CTkProgressBar(self, width=500, mode="indeterminate")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.midway_counter = 0

    # ==========================================
    # LOGIC CỐT LÕI 
    # ==========================================
    def toggle_pause(self):
        subprocess.run('wsl bash -c "pkill -SIGUSR2 stereo_kitti"', shell=True)
        if not self.is_paused:
            self.btn_pause.configure(text="▶ CHẠY TIẾP", fg_color="#2ECC71")
            self.status_label.configure(text="Trạng thái: ⏸ Xe đang đứng yên tuyệt đối...", text_color="#F39C12")
            self.is_paused = True
        else:
            self.btn_pause.configure(text="⏸ TẠM DỪNG", fg_color="#F39C12")
            self.status_label.configure(text="Trạng thái: Đang chạy...", text_color="#F1C40F")
            self.is_paused = False

    def trigger_midway_save(self):
        self.midway_counter += 1
        current_count = self.midway_counter
        seq_num = self.dataset_var.get()[-2:]
        
        self.status_label.configure(text=f"💾 Đang trích xuất chặng {current_count}...", text_color="#3498DB")
        subprocess.run('wsl bash -c "pkill -SIGUSR1 stereo_kitti"', shell=True)
        
        def fetch_midway_file():
            time.sleep(1.5) 
            wsl_dataset_path = f"/mnt/c/Users/ASUS/Downloads/data_odometry_gray/dataset/sequences/{seq_num}"
            midway_file = f"SavingCameraTrajectory_{seq_num}_STEP_{current_count}.txt"
            rename_cmd = f'wsl bash -c "cd {wsl_dataset_path} && if [ -f CameraTrajectory_Midway.txt ]; then mv CameraTrajectory_Midway.txt {midway_file}; fi"'
            subprocess.run(rename_cmd, shell=True)
            
            if self.is_paused:
                self.after(0, lambda: self.status_label.configure(text=f"✅ Đã lưu xong chặng {current_count}. Xe vẫn đang đứng yên!", text_color="#2ECC71"))
            else:
                self.after(0, lambda: self.status_label.configure(text=f"✅ Đã lưu xong chặng {current_count}. Xe đang chạy...", text_color="#2ECC71"))
        
        threading.Thread(target=fetch_midway_file, daemon=True).start()

    # BƯỚC NGOẶT: HÀM KẾT THÚC THÔNG MINH Y HỆT CON NGƯỜI
    def force_stop_and_save(self):
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")
        self.btn_midway_save.configure(state="disabled")
        
        def automated_human_stop():
            # Bước 1: ÉP DỪNG XE (Đưa C++ vào vùng an toàn)
            if not self.is_paused:
                self.after(0, lambda: self.status_label.configure(text="⏳ Bước 1/3: Đang hãm phanh để xe dừng hẳn...", text_color="#F1C40F"))
                subprocess.run('wsl bash -c "pkill -SIGUSR2 stereo_kitti"', shell=True)
                time.sleep(1.5) # Chờ 1.5 giây cho xe giải quyết nốt khung hình dở dang
                
            # Bước 2: TRÍCH XUẤT FILE
            self.after(0, lambda: self.status_label.configure(text="⏳ Bước 2/3: Đang trích xuất dữ liệu quỹ đạo...", text_color="#3498DB"))
            subprocess.run('wsl bash -c "pkill -SIGUSR1 stereo_kitti"', shell=True)
            time.sleep(2.0) # Cho ổ cứng 2 giây để copy dữ liệu thong thả
            
            # Bước 3: RÚT ĐIỆN HỆ THỐNG
            self.after(0, lambda: self.status_label.configure(text="⏳ Bước 3/3: Đang đóng luồng C++...", text_color="#E74C3C"))
            subprocess.run('wsl bash -c "pkill -9 stereo_kitti"', shell=True)
            
        # Chạy tiến trình ngầm để UI không bị đơ
        threading.Thread(target=automated_human_stop, daemon=True).start()

    # ==========================================
    # CÁC HÀM QUẢN LÝ (KHÔNG ĐỔI)
    # ==========================================
    def add_dataset(self):
        dialog = ctk.CTkInputDialog(text="Nhập số Sequence mới (VD: 06, 07):", title="Thêm Dataset")
        new_seq = dialog.get_input()
        if new_seq:
            new_seq = new_seq.strip()
            if not new_seq.isdigit():
                self.status_label.configure(text="❌ Lỗi: Vui lòng chỉ nhập các con số!", text_color="#E74C3C")
                return
            if len(new_seq) == 1: new_seq = "0" + new_seq
            if len(new_seq) > 2:
                self.status_label.configure(text="❌ Lỗi: Số Sequence chỉ từ 00 đến 21!", text_color="#E74C3C")
                return
            win_dataset_path = f"C:\\Users\\ASUS\\Downloads\\data_odometry_gray\\dataset\\sequences\\{new_seq}"
            if not os.path.exists(win_dataset_path):
                self.status_label.configure(text=f"❌ Lỗi: Bạn chưa tải bộ {new_seq}!", text_color="#E74C3C")
                return
            new_name = f"KITTI - Sequence {new_seq}"
            existing_seqs = [name[-2:] for name in self.available_datasets]
            if new_seq not in existing_seqs:
                self.available_datasets.append(new_name)
                self.available_datasets.sort()
                self.dataset_menu.configure(values=self.available_datasets)
                self.dataset_var.set(new_name)
                self.status_label.configure(text=f"✨ Đã thêm thành công: {new_name}", text_color="#3498DB")
            else:
                self.status_label.configure(text=f"⚠️ Bộ Sequence {new_seq} đã có sẵn!", text_color="#F39C12")

    def del_dataset(self):
        selected = self.dataset_var.get()
        if selected in self.available_datasets:
            self.available_datasets.remove(selected)
            self.dataset_menu.configure(values=self.available_datasets)
            if self.available_datasets:
                self.dataset_var.set(self.available_datasets[0])
            else:
                self.dataset_var.set("Trống...")
            self.status_label.configure(text=f"🗑️ Đã xóa: {selected}", text_color="#E74C3C")

    def start_slam_thread(self):
        selected = self.dataset_var.get()
        if "Chọn Dataset" in selected or selected == "Trống...":
            self.status_label.configure(text="❌ Lỗi: Vui lòng chọn hoặc thêm một Dataset trước!", text_color="#E74C3C")
            return

        self.run_button.pack_forget() 
        self.control_frame.pack(pady=5) 
        self.midway_counter = 0
        self.is_paused = False
        
        self.btn_pause.configure(state="normal", text="⏸ TẠM DỪNG", fg_color="#F39C12")
        self.btn_midway_save.configure(state="normal")
        self.btn_stop.configure(state="normal")
        
        self.status_label.configure(text=f"Trạng thái: Đang chạy {selected}...", text_color="#F1C40F")
        self.progress_bar.start()

        threading.Thread(target=self.run_orb_slam, args=(selected,), daemon=True).start()

    def run_orb_slam(self, dataset_name):
        seq_num = dataset_name[-2:]
        yaml_file = "KITTI00-02.yaml" 
        wsl_dataset_path = f"/mnt/c/Users/ASUS/Downloads/data_odometry_gray/dataset/sequences/{seq_num}"
        win_dataset_path = f"C:\\Users\\ASUS\\Downloads\\data_odometry_gray\\dataset\\sequences\\{seq_num}"
        output_file = f"SavingCameraTrajectory_{seq_num}.txt"

        try:
            run_cmd = f'wsl bash -c "cd {wsl_dataset_path} && ~/ORB_SLAM3/Examples/Stereo/stereo_kitti ~/ORB_SLAM3/Vocabulary/ORBvoc.txt ~/ORB_SLAM3/Examples/Stereo/{yaml_file} {wsl_dataset_path}"'
            process = subprocess.Popen(run_cmd, shell=True)
            
            # Python đứng đợi C++ bị giết ở Bước 3
            process.wait() 

            # Rút lưới an toàn
            subprocess.run('wsl bash -c "pkill -9 -f stereo_kitti"', shell=True)

            # Săn tìm cái file Midway mà C++ vừa chép ra ở Bước 2
            rename_cmd = f'wsl bash -c "cd {wsl_dataset_path} && if [ -f CameraTrajectory_Midway.txt ]; then mv CameraTrajectory_Midway.txt {output_file}; elif [ -f CameraTrajectory.txt ]; then mv CameraTrajectory.txt {output_file}; fi"'
            subprocess.run(rename_cmd, shell=True)

            # Check thành quả
            check_path = os.path.join(win_dataset_path, output_file)
            if os.path.exists(check_path):
                self.after(0, self.show_success, seq_num)
            else:
                self.after(0, self.show_error, "Dữ liệu trống! (Hãy đảm bảo xe đã chạy khởi tạo xong đoạn đầu trước khi bấm KẾT THÚC)")

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def show_success(self, seq_num):
        self.reset_ui()
        self.status_label.configure(text=f"✅ HOÀN TẤT! Đã chốt sổ: SavingCameraTrajectory_{seq_num}.txt", text_color="#2ECC71")

    def show_error(self, error_msg):
        self.reset_ui()
        self.status_label.configure(text=f"❌ LỖI / ĐÃ NGẮT: {error_msg}", text_color="#E74C3C")

    def reset_ui(self):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.control_frame.pack_forget() 
        self.run_button.pack(pady=(15, 5)) 
        self.run_button.configure(state="normal", text="▶ BẮT ĐẦU CHẠY LẠI")

if __name__ == "__main__":
    app = SLAM_App()
    app.mainloop()