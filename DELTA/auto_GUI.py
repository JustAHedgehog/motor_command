import pyautogui
import time
import csv
import sys
import keyboard

# 1. 設定檔案與參數
csv_file = 'DELTA/motor_sine_0.3Hz_200to720_init200.csv'  # 請替換為你實際的 CSV 檔名
base_def = "0x00F00031" # 連續運動定義碼
end_def = "0x00F00011"  # 最後一步的終止定義碼

p6_targets = []
p7_targets = []

# 2. 讀取並將指令分流到 P6 (Step 0~48) 與 P7 (Step 49~98)
with open(csv_file, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        step_idx = int(row['step'])
        target_rpm = str(int(float(row['target_rpm']) * 10)) 
        
        if 0 <= step_idx <= 48:
            p6_targets.append(target_rpm)
        elif 49 <= step_idx <= 98:
            p7_targets.append(target_rpm)

# 3. 建立共用的打字執行函式
def auto_type_section(targets, start_cell_name, is_final_section):
    total = len(targets)
    print(f"\n⚠️ 請在 5 秒內，將滑鼠點擊 {start_cell_name} 的「數值」格子。")
    print("確認游標閃爍後放開滑鼠！(隨時可長按 ESC 緊急終止)")
    time.sleep(5)
    
    for i, rpm in enumerate(targets):
        if keyboard.is_pressed('esc'):
            print("\n🛑 偵測到 ESC 鍵！已緊急終止。")
            sys.exit()
            
        # 判斷是否為全局的最後一筆指令
        current_def = end_def if (is_final_section and i == total - 1) else base_def
        
        # 填寫定義碼
        pyautogui.write(current_def, interval=0.01)
        pyautogui.press('enter')
        pyautogui.press('down')
        time.sleep(0.05)
        
        if keyboard.is_pressed('esc'): sys.exit()
        
        # 填寫轉速
        pyautogui.write(rpm, interval=0.01)
        pyautogui.press('enter')
        pyautogui.press('down')
        time.sleep(0.05)

# 4. 執行 P6 區段 (PATH 1 ~ PATH 49)
if p6_targets:
    print(f"✅ 開始處理 P6 區段 (共 {len(p6_targets)} 組，對應 PATH 1 ~ {len(p6_targets)})...")
    # 如果 P7 沒有資料，P6 的最後一筆就是全局最後一筆
    auto_type_section(p6_targets, "P6.002", is_final_section=(len(p7_targets) == 0))
    print("🎉 P6 區段輸入完成！")

# 5. 執行 P7 區段 (PATH 50 ~ PATH 99)
if p7_targets:
    print(f"\n🔔 準備進入 P7 區段 (共 {len(p7_targets)} 組，對應 PATH 50 起)。")
    print("👉 請手動將 ASDA-Soft 頁籤切換至「P7」。")
    input("👉 切換好之後，請在此終端機按下 Enter 鍵繼續...") 
    
    # 這裡固定為 True，因為 P7 一定包含全局最後一筆
    auto_type_section(p7_targets, "P7.000", is_final_section=True)
    print("🎉 P7 區段輸入完成！")

print("\n✅ 所有參數自動填入完畢，請點擊上方工具列將參數寫入驅動器。")