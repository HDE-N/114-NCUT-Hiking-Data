# 此程式用於將資料夾內數據轉換成可閱覽之csv

import os
import math
import pandas as pd
from tqdm import tqdm

INPUT_DIR = './data'
OUTPUT_DIR = './output'

def quat_to_euler(w, x, y, z):
    """將四元數轉換為尤拉角 (Roll, Pitch, Yaw)，單位為度"""
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))
    sinp = 2 * (w * y - z * x)
    pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

def process_file(infile: str, outfile: str) -> None:
    try:
        df = pd.read_csv(infile, encoding='utf-8')
        if 'data' not in df.columns: 
            return
            
        valid_rows = df['data'].dropna()
        if len(valid_rows) <= 1: 
            return
            
        # 排除第一列雜訊並串接資料
        full_data_str = ''.join(valid_rows.iloc[1:].astype(str))
        
        # 分割資料，並過濾掉因結尾 'end' 產生的純空字串，以確保分母(總列數)計算精準
        raw_segments = [s for s in full_data_str.split('end') if s.strip()]
        total_segments = len(raw_segments)
        
        if total_segments == 0: 
            return

        parsed_data = []
        for segment in raw_segments:
            vals = segment.strip().split('_')
            
            # 條件驗證：長度必須為13
            if len(vals) != 13:
                continue
                
            try:
                # 嘗試全數轉為浮點數，並檢查是否為合法數值 (排除 inf, NaN 等)
                f_vals = [float(v) for v in vals]
                if any(not math.isfinite(v) for v in f_vals):
                    continue
                    
                # 計算尤拉角並組合 17 個欄位 (利用 len(parsed_data) + 1 直接作為完美連續的 ID)
                roll, pitch, yaw = quat_to_euler(*f_vals[9:13])
                parsed_data.append([len(parsed_data) + 1] + f_vals + [roll, pitch, yaw])
                
            except ValueError:
                # 攔截包含 "3.2.2" 等無法轉換為浮點數的異常字串
                continue

        # 計算與輸出統計資訊
        valid_count = len(parsed_data)
        defective_count = total_segments - valid_count
        defective_ratio = (defective_count / total_segments) * 100
        
        # 使用 tqdm.write 避免與進度條的輸出發生畫面衝突
        msg = (f"[{os.path.basename(infile)}] 總數據: {total_segments} 列 | "
               f"正常: {valid_count} 列 | 瑕疵: {defective_count} 列 | "
               f"瑕疵占比: {defective_ratio:.2f}%")
        tqdm.write(msg)

        if not parsed_data:
            return

        # 寫入 CSV
        columns = [
            'ID', 'acceleration_X', 'acceleration_Y', 'acceleration_Z',
            'gyroscope_X', 'gyroscope_Y', 'gyroscope_Z',
            'magnetometer_X', 'magnetometer_Y', 'magnetometer_Z',
            'quaternion_w', 'quaternion_x', 'quaternion_y', 'quaternion_z',
            'euler_roll', 'euler_pitch', 'euler_yaw'
        ]
        pd.DataFrame(parsed_data, columns=columns).to_csv(outfile, index=False, encoding='utf-8')

    except Exception as e:
        tqdm.write(f"處理 {infile} 時發生錯誤: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(INPUT_DIR):
        print(f"Directory '{INPUT_DIR}' not found.")
        return
        
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
    for filename in tqdm(files, desc='Processing Files'):
        infile = os.path.join(INPUT_DIR, filename)
        outfile = os.path.join(OUTPUT_DIR, f'{os.path.splitext(filename)[0]}.csv')
        process_file(infile, outfile)

if __name__ == '__main__':
    main()
