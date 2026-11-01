import numpy as np
import matplotlib.pyplot as plt
import csv

def generate_custom_sine_commands(freq_hz, num_cycles=3, init_rpm=0, bottom_rpm=200, peak_rpm=720, min_dwell_ms=100, ramp_ms=100):
    """
    自訂初始/波谷/波峰轉速的正弦波馬達指令生成器 (包含獨立 Step 0)
    """
    # 計算週期與總時間 (毫秒)
    period_ms = (1.0 / freq_hz) * 1000
    total_duration_ms = period_ms * num_cycles
    min_step_duration = ramp_ms + min_dwell_ms
    num_steps = int(total_duration_ms // min_step_duration)
    
    # 99 段硬體限制處理
    if num_steps > 99:
        num_steps = 99
        actual_step_ms = total_duration_ms / 99.0
        actual_dwell_ms = int(actual_step_ms - ramp_ms)
        print(f"⚠️ [硬體限制觸發] 段數鎖定為 99 段。每段停留時間自動微調為: {actual_dwell_ms} ms")
    else:
        actual_step_ms = total_duration_ms / num_steps
        actual_dwell_ms = int(actual_step_ms - ramp_ms)
        print(f"✅ [段數正常] 共切分為 {num_steps} 段。每段停留時間微調為: {actual_dwell_ms} ms")

    # 根據波峰與波谷計算中心值與振幅
    center_rpm = (peak_rpm + bottom_rpm) / 2.0
    amp_rpm = (peak_rpm - bottom_rpm) / 2.0
    
    # 生成時間陣列與目標轉速 (-cos 確保從波谷啟動)
    total_time_s = total_duration_ms / 1000.0
    t = np.linspace(0, total_time_s, num_steps + 1)
    rpm_targets = center_rpm - amp_rpm * np.cos(2 * np.pi * freq_hz * t)
    
    commands = []
    
    # Step 0: 獨立初始轉速
    commands.append({
        "step": 0,
        "target_rpm": float(init_rpm),
        "ramp_ms": 0,   
        "dwell_ms": 0   
    })
    
    # Step 1 ~ N: 正弦波段數
    for i in range(1, len(rpm_targets)):
        target = round(rpm_targets[i], 1)
        commands.append({
            "step": i,
            "target_rpm": target,
            "ramp_ms": ramp_ms,
            "dwell_ms": actual_dwell_ms
        })
        
    return commands, total_time_s, center_rpm, amp_rpm

# ==========================================
# 參數設定區間
# ==========================================
freq_test = 0.3     # 正弦波頻率 (Hz)
cycles_test = 3     # 欲執行的週期數
initial_rpm = 200     # 初始啟動轉速 (與波谷脫鉤)
bottom_rpm = 200    # 正弦波波谷轉速
top_rpm = 720       # 正弦波波峰轉速
ramp_time_ms = 100  # 馬達爬坡時間 (ms)
min_dwell_time = 100# 最低停留時間 (ms)

# 1. 產生指令
commands, total_time, center_val, amp_val = generate_custom_sine_commands(
    freq_test,
    cycles_test,
    initial_rpm,
    bottom_rpm,
    top_rpm,
    min_dwell_time,
    ramp_time_ms
)

# ==========================================
# 2. 繪製擬合圖表 (供檢視波形品質)
# ==========================================
t_plot = [0]
rpm_plot = [float(initial_rpm)]

# 模擬馬達控制的實際時間路徑 (爬坡 -> 停留)
for cmd in commands[1:]:
    # 爬坡段
    t_plot.append(t_plot[-1] + cmd["ramp_ms"] / 1000.0)
    rpm_plot.append(cmd["target_rpm"])
    # 停留段
    t_plot.append(t_plot[-1] + cmd["dwell_ms"] / 1000.0)
    rpm_plot.append(cmd["target_rpm"])

plt.figure(figsize=(12, 6))
plt.plot(t_plot, rpm_plot, 'b.-', label=f"Motor Path ({len(commands)-1} Steps)")

# 疊合理想正弦波 (自波谷開始對齊)
ideal_t = np.linspace(0, total_time, 600)
ideal_rpm = center_val - amp_val * np.cos(2 * np.pi * freq_test * ideal_t)
plt.plot(ideal_t, ideal_rpm, 'r--', alpha=0.6, label="Ideal Sine Wave")

# 標註起始點與波峰波谷參考線
plt.axhline(top_rpm, color='gray', linestyle=':', label=f"Peak: {top_rpm} RPM")
plt.axhline(bottom_rpm, color='gray', linestyle=':', label=f"Bottom: {bottom_rpm} RPM")
plt.scatter([0], [initial_rpm], color='green', zorder=5, label=f"Init: {initial_rpm} RPM (Step 0)")

plt.title(f"Sine Wave Fitting Check: {freq_test} Hz | {cycles_test} Cycles | Range: {bottom_rpm}~{top_rpm} RPM")
plt.xlabel("Time (s)")
plt.ylabel("Speed (RPM)")
plt.grid(True)
plt.legend(loc="upper right")
plt.tight_layout()

print("\n📊 正在顯示擬合圖表，請檢視波形... (關閉圖表視窗後繼續)")
plt.show()

# ==========================================
# 3. 終端確認是否匯出 CSV
# ==========================================
user_choice = input("\n❓ 是否要將此指令配置匯出為 CSV 檔案？(y/n): ").strip().lower()

if user_choice in ['y', 'yes']:
    csv_filename = f"DELTA/motor_sine_{freq_test}Hz_{bottom_rpm}to{top_rpm}_init{initial_rpm}.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ["step", "target_rpm", "ramp_ms", "dwell_ms"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cmd in commands:
            writer.writerow(cmd)
    print(f"✅ 檔案已成功匯出至：{csv_filename}")
else:
    print("❌ 取消匯出，未建立任何 CSV 檔案。")