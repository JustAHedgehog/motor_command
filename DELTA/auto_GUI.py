import pyautogui
import time
import csv
import sys
import keyboard

# 1. 設定檔案與參數
csv_file = 'DELTA/motor_sine_0.3Hz_200to720_init200.csv'  # 請替換為你實際的 CSV 檔名
base_def = "0x00F00031" # 連續運動定義碼
end_def = "0x00F00011"  # 停止運動定義碼

all_steps = []

# 2. 讀取 CSV 原始資料
with open(csv_file, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        step_idx = int(row['step'])
        target_rpm = str(int(float(row['target_rpm']) * 10)) 
        all_steps.append((step_idx, target_rpm))

# 3. 自動追加一組 0 rpm 的停止指令
if all_steps:
    last_step_idx = all_steps[-1][0]
    new_step_idx = last_step_idx + 1
    all_steps.append((new_step_idx, "0")) # 目標轉速設為 0
    print(f"🔧 已自動在末端 (Step {new_step_idx}) 追加 0 rpm 停止指令。")

# 4. 將指令分流到 P6 (Step 0~48) 與 P7 (Step 49~98)
p6_targets = []
p7_targets = []

for step_idx, target_rpm in all_steps:
    if 0 <= step_idx <= 48:
        p6_targets.append(target_rpm)
    elif 49 <= step_idx <= 98:
        p7_targets.append(target_rpm)
    else:
        print(f"⚠️ 警告：第 {step_idx} 步已超過 PATH 99 (P7.098) 的硬體上限，將被忽略。")

# 5. 建立共用的打字執行函式
def auto_type_section(targets, start_cell_name, is_final_section):
    total = len(targets)
    print(f"\n⚠️ 請在 5 秒內，將滑鼠點擊 {start_cell_name} 的「數值」格子。")
    print("確認游標閃爍後放開滑鼠！(隨時可長按 ESC 緊急終止)")
    time.sleep(5)
    
    for i, rpm in enumerate(targets):
        if keyboard.is_pressed('esc'):
            print("\n🛑 偵測到 ESC 鍵！已緊急終止。")
            sys.exit()
            
        # 若為整個專案的最後一筆，則填入 end_def (0x00F00011)
        current_def = end_def if (is_final_section and i == total - 1) else base_def
        
        pyautogui.write(current_def, interval=0.01)
        pyautogui.press('enter')
        pyautogui.press('down')
        time.sleep(0.05)
        
        if keyboard.is_pressed('esc'): sys.exit()
        
        pyautogui.write(rpm, interval=0.01)
        pyautogui.press('enter')
        pyautogui.press('down')
        time.sleep(0.05)

# 6. 執行 P6 區段 (PATH 1 ~ PATH 49)
if p6_targets:
    print(f"\n✅ 開始處理 P6 區段 (共 {len(p6_targets)} 組，包含定義碼與轉速)...")
    auto_type_section(p6_targets, "P6.002", is_final_section=(len(p7_targets) == 0))
    print("🎉 P6 區段輸入完成！")

# 7. 執行 P7 區段 (PATH 50 ~ PATH 99)
if p7_targets:
    print(f"\n🔔 準備進入 P7 區段 (共 {len(p7_targets)} 組)。")
    print("👉 請手動將 ASDA-Soft 頁籤切換至「P7」。")
    input("👉 切換好之後，請在此終端機按下 Enter 鍵繼續...") 
    
    auto_type_section(p7_targets, "P7.000", is_final_section=True)
    print("🎉 P7 區段輸入完成！")

print("\n✅ 所有參數自動填入完畢，請點擊上方工具列將參數寫入驅動器。")