import cv2
import numpy as np
import open3d as o3d
import os
import matplotlib.cm as cm # Thư viện tô màu cao cấp
from scipy.spatial.transform import Rotation as R

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ==========================================
seq_num = "05" # Chạy bộ 05 khổng lồ
dataset_dir = f"C:\\Users\\ASUS\\Downloads\\data_odometry_gray\\dataset\\sequences\\{seq_num}"
traj_file = os.path.join(dataset_dir, f"SavingCameraTrajectory_{seq_num}.txt")
times_file = os.path.join(dataset_dir, "times.txt")

# Thông số Camera KITTI
focal_length = 718.856
baseline = 0.53716
cx, cy = 607.193, 185.216

# ==========================================
# 2. ĐỌC DỮ LIỆU ĐỒNG BỘ
# ==========================================
print("1. Đang chuẩn bị hệ thống xây dựng bản đồ OctoMap có màu...")
with open(times_file, "r") as f:
    kitti_times = [float(line.strip()) for line in f.readlines()]

with open(traj_file, "r") as f:
    traj_lines = f.readlines()

global_pcd = o3d.geometry.PointCloud()
# Nâng cấp: Tăng độ chính xác của depth nhưng chậm hơn tí
stereo = cv2.StereoSGBM_create(minDisparity=0, numDisparities=64, blockSize=9, P1=8*3*9**2, P2=32*3*9**2)

# CẤU HÌNH TỐI ƯU CỰC HẠN ĐỂ GHÉP 2000+ FRAMES
stride = 5 # Cứ 5 frame lấy 1. GIÚP LƯU TRAJECTORY DÀI NGOẰNG
count = 0

print(f"2. Bắt đầu mô phỏng ghép TOÀN BỘ sequence {seq_num}...")

for i in range(0, len(traj_lines), stride):
    line = traj_lines[i]
    data = line.strip().split()
    if len(data) < 8: continue
    
    timestamp = float(data[0])
    tx, ty, tz = float(data[1]), float(data[2]), float(data[3])
    qx, qy, qz, qw = float(data[4]), float(data[5]), float(data[6]), float(data[7])

    # Tìm Index của bức ảnh
    img_idx = min(range(len(kitti_times)), key=lambda idx: abs(kitti_times[idx] - timestamp))
    img_name = f"{img_idx:06d}.png"
    
    imgL_path = os.path.join(dataset_dir, "image_0", img_name)
    imgR_path = os.path.join(dataset_dir, "image_1", img_name)
    
    if not os.path.exists(imgL_path): continue

    # Đọc ảnh và tính Depth
    imgL = cv2.imread(imgL_path, 0)
    imgR = cv2.imread(imgR_path, 0)
    
    disparity = stereo.compute(imgL, imgR).astype(np.float32) / 16.0
    disparity[disparity <= 0] = 0.1
    depth = (focal_length * baseline) / disparity

    # NÂNG CẤP: Lấy dày đặc điểm hơn (nhảy v=2, u=2) để bản đồ trông vững chãi hơn
    points = []
    height, width = imgL.shape
    for v in range(0, height, 2): 
        for u in range(0, width, 2):
            z = depth[v, u]
            if 2.0 < z < 25.0:  # Lấy xa hơn tí (25m)
                x = (u - cx) * z / focal_length
                y = (v - cy) * z / focal_length
                points.append([x, y, z])

    if not points: continue
    
    local_pcd = o3d.geometry.PointCloud()
    local_pcd.points = o3d.utility.Vector3dVector(np.array(points))
    # Chỉnh trục tọa độ chuẩn nhìn của người (Y hướng âm)
    local_pcd.transform([[1,0,0,0], [0,-1,0,0], [0,0,-1,0], [0,0,0,1]])

    # Áp dụng ma trận tọa độ thực tế
    rot_matrix = R.from_quat([qx, qy, qz, qw]).as_matrix()
    pose_matrix = np.eye(4)
    pose_matrix[:3, :3] = rot_matrix
    pose_matrix[:3, 3] = [tx, ty, tz]

    local_pcd.transform(pose_matrix)
    
    # Gộp và nén ngay lập tức để giữ RAM ổn định (Nén ở mức 0.3m)
    global_pcd += local_pcd
    if i % (stride * 10) == 0: # Cứ sau 10 bước gộp thì nén bản đồ tổng lại
        global_pcd = global_pcd.voxel_down_sample(voxel_size=0.3) 
    
    count += 1
    if count % 20 == 0:
        print(f"   -> Đã ghép xong frame thực tế thứ {i}. Bản đồ dài dần ra...")

# ==========================================
# 3. NÂNG CẤP TỐI THƯỢNG: TÔ MÀU ĐỘ CAO & XÂY KHỐI MINECRAFT
# ==========================================
print("3. Đang dọn dẹp RAM lần cuối và tô màu cho bản đồ tổng...")
# Nén bản đồ tổng lần cuối để xây khối đẹp
global_pcd = global_pcd.voxel_down_sample(voxel_size=0.3)

# PHÉP MÀU NẰM Ở ĐÂY: Tô màu từ Xanh dương -> Xanh lá dựa theo độ cao (Z-axis)
# Lấy độ cao tối đa và tối thiểu của bản đồ
# Vì đã transform trục Y là Up, nên ta lấy trục Y (cột index 1) làm độ cao
points_np = np.asarray(global_pcd.points)
z_vals = points_np[:, 1]
min_z = np.min(z_vals)
max_z = np.max(z_vals)

# Chuẩn hóa độ cao về khoảng 0-1
norm = (z_vals - min_z) / (max_z - min_z)
# Dùng colormap 'terrain' để ra màu giống OctoMap (Xanh dương thấp, xanh lá cao)
colors = cm.terrain(norm)[:, :3] # Chỉ lấy kênh màu RGB
global_pcd.colors = o3d.utility.Vector3dVector(colors)

print("4. Đang dựng OctoMap từ 2000+ frames...")
# NÂNG CẤP: Dùng Voxel to (0.5m) để nhìn y hệt khối Minecraft
global_voxel = o3d.geometry.VoxelGrid.create_from_point_cloud(global_pcd, voxel_size=0.5)

print("5. MỞ BẢN ĐỒ OCTOMAP SEMANTIC CÓ MÀU! (Nền đen cho đẹp)")
vis = o3d.visualization.Visualizer()
# Tạo cửa sổ full HD
vis.create_window(window_name=f"Full OctoMap Sequence {seq_num} - Elevation Colored", width=1920, height=1080)
vis.add_geometry(global_voxel)

# Cấu hình Visualizer cao cấp có chiếu sáng
opt = vis.get_render_option()
opt.background_color = np.asarray([0, 0, 0]) # Nền đen huyền bí
opt.point_size = 5 # Tăng kích thước điểm để nhìn vững chãi hơn
# Bật tính năng chiếu sáng (Shading) để các khối block nổi bật 3D
opt.light_on = True 
vis.run()
vis.destroy_window()