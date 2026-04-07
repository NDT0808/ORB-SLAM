import customtkinter as ctk
import subprocess
import threading
import os

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class SLAM_App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ORB-SLAM3 Control Panel - Autonomous Vehicle")
        self.geometry("650x500")
        self.resizable(False, False)

        self.title_label = ctk.CTkLabel(self, text="HỆ THỐNG ĐỊNH VỊ SLAM", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))
        
        self.subtitle_label = ctk.CTkLabel(self, text="Chọn Dataset để kết xuất quỹ đạo 3D (Bản chống sập C++)", font=ctk.CTkFont(size=14), text_color="gray")
        self.subtitle_label.pack(pady=(0, 20))

        self.dataset_var = ctk.StringVar(value="Chọn Dataset KITTI...")
        self.dataset_menu = ctk.CTkOptionMenu(
            self, variable=self.dataset_var,
            values=["KITTI - Sequence 00", "KITTI - Sequence 01", "KITTI - Sequence 02", "KITTI - Sequence 03", "KITTI - Sequence 04", "KITTI - Sequence 05"],
            width=300, height=40, font=ctk.CTkFont(size=14)
        )
        self.dataset_menu.pack(pady=10)

        # Nút Bắt đầu
        self.run_button = ctk.CTkButton(
            self, text="▶ BẮT ĐẦU CHẠY", width=300, height=45, 
            font=ctk.CTkFont(size=15, weight="bold"), fg_color="#2ECC71", hover_color="#27AE60",
            command=self.start_slam_thread
        )
        self.run_button.pack(pady=5)

        # Nút Hướng dẫn dừng
        self.stop_hint_button = ctk.CTkButton(
            self, text="💡 MUỐN DỪNG & LƯU? -> HÃY ĐÓNG CỬA SỔ 3D", width=300, height=45, 
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#34495E", hover_color="#2C3E50",
            state="disabled"
        )
        self.stop_hint_button.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="Trạng thái: Đang chờ...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=15)

        self.progress_bar = ctk.CTkProgressBar(self, width=400, mode="indeterminate")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

    def start_slam_thread(self):
        selected = self.dataset_var.get()
        if "Chọn Dataset" in selected:
            self.status_label.configure(text="❌ Lỗi: Vui lòng chọn một Dataset trước!", text_color="#E74C3C")
            return

        self.run_button.configure(state="disabled", text="⏳ ĐANG XỬ LÝ...")
        self.status_label.configure(text=f"Trạng thái: Đang chạy {selected}... Kết quả sẽ lưu tại thư mục bộ đó!", text_color="#F1C40F")
        self.progress_bar.start()

        threading.Thread(target=self.run_orb_slam, args=(selected,), daemon=True).start()

    def run_orb_slam(self, dataset_name):
        seq_num = dataset_name[-2:]
        
        yaml_file = "KITTI00-02.yaml"

        wsl_dataset_path = f"/mnt/c/Users/ASUS/Downloads/data_odometry_gray/dataset/sequences/{seq_num}"
        win_dataset_path = f"C:\\Users\\ASUS\\Downloads\\data_odometry_gray\\dataset\\sequences\\{seq_num}"
        output_file = f"SavingCameraTrajectory_{seq_num}.txt"

        try:
            # Chạy ORB-SLAM3 với file YAML chuẩn
            run_cmd = f'wsl bash -c "cd {wsl_dataset_path} && ~/ORB_SLAM3/Examples/Stereo/stereo_kitti ~/ORB_SLAM3/Vocabulary/ORBvoc.txt ~/ORB_SLAM3/Examples/Stereo/{yaml_file} {wsl_dataset_path}"'
            
            process = subprocess.Popen(run_cmd, shell=True)
            process.wait() # Chờ tiến trình kết thúc (Dù có sập thì cũng kệ nó)

            # BƯỚC NGOẶT: Không dùng returncode nữa. Cứ ép đổi tên file nếu nó tồn tại!
            rename_cmd = f'wsl bash -c "cd {wsl_dataset_path} && if [ -f CameraTrajectory.txt ]; then mv CameraTrajectory.txt {output_file}; fi"'
            subprocess.run(rename_cmd, shell=True)
            
            # Quét dọn tiến trình ngầm cho sạch RAM
            subprocess.run('wsl bash -c "pkill -9 -f stereo_kitti"', shell=True)

            # Kiểm tra thực tế trên Windows xem file đã có chưa
            check_path = os.path.join(win_dataset_path, output_file)
            fallback_path = os.path.join(win_dataset_path, "CameraTrajectory.txt")
            
            if os.path.exists(check_path) or os.path.exists(fallback_path):
                self.after(0, self.show_success, seq_num)
            else:
                self.after(0, self.show_error, "Không tìm thấy file kết quả. Thuật toán có thể đã sập quá sớm.")

        except Exception as e:
            self.after(0, self.show_error, str(e))

    def show_success(self, seq_num):
        self.reset_ui()
        self.status_label.configure(text=f"✅ HOÀN TẤT! Đã lưu: SavingCameraTrajectory_{seq_num}.txt \nngay bên trong thư mục sequences/{seq_num}/", text_color="#2ECC71")

    def show_error(self, error_msg):
        self.reset_ui()
        self.status_label.configure(text=f"❌ LỖI: {error_msg}", text_color="#E74C3C")

    def reset_ui(self):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.run_button.configure(state="normal", text="▶ BẮT ĐẦU CHẠY", fg_color="#3498DB")

if __name__ == "__main__":
    app = SLAM_App()
    app.mainloop()