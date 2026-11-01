import numpy as np
import matplotlib.pyplot as plt
import csv

def generate_optimal_sine_commands(
    freq_hz=None,         # 頻率 f (Hz)
    num_cycles=3,         # 週期數
    init_rpm=0,           # Step 0 初始待命轉速 (可隨意自訂)
    bottom_rpm=200,       # 正弦波波谷轉速 (RPM)
    peak_rpm=720,         # 正弦波波峰轉速 (RPM)
    min_dwell_ms=100      # 馬達硬體最低停留時間 (ms)
):
    """
    自動選定理論最佳 ramp_time 以最優貼合正弦波的馬達指令生成器
    """
    if freq_hz is None or freq_hz <= 0:
        raise ValueError("請輸入大於 0 的頻率 freq_hz！")

    f = float(freq_hz)
    T_s = 1.0 / f
    period_ms = T_s * 1000.0
    total_duration_ms = period_ms * num_cycles
    total_time_s = total_duration_ms / 1000.0

    # 1. 計算硬體步階與段數 (上限 99 段)
    # 假設最短加減速需至少 10ms，故單步最小極限時間為 min_dwell_ms + 10ms
    theoretical_steps = int(total_duration_ms // (min_dwell_ms + 10))

    if theoretical_steps > 99:
        num_steps = 99
        actual_step_ms = total_duration_ms / 99.0
        print(f"⚠️ [硬體限制] 已達上限，段數鎖定為 99 段。")
    else:
        num_steps = theoretical_steps
        actual_step_ms = total_duration_ms / num_steps
        print(f"✅ [段數分配] 總共切分 {num_steps} 段。")

    # 2. 自動演化最佳 ramp_ms (最佳化演算法核心)
    # 為了使階梯連線與正弦波誤差 (RMSE) 最小化，將停留時間壓縮至硬體極限 100ms，其餘時間全部分配給爬坡
    auto_dwell_ms = int(min_dwell_ms)
    auto_ramp_ms = int(actual_step_ms - auto_dwell_ms)

    # 防呆：確保加減速時間至少為 1ms
    if auto_ramp_ms < 1:
        auto_ramp_ms = 1
        auto_dwell_ms = int(actual_step_ms - auto_ramp_ms)

    print("==================================================")
    print(f"📌 [參數自動擬合結果]")
    print(f"   頻率 (f)        : {f:.4f} Hz (週期 T = {T_s:.2f} s)")
    print(f"   總執行時間      : {total_time_s:.2f} s ({num_cycles} 週期)")
    print(f"   每段總時長      : {actual_step_ms:.1f} ms")
    print(f"   自動最佳爬坡時間 : {auto_ramp_ms} ms (Auto-Ramp)")
    print(f"   硬體極限停留時間 : {auto_dwell_ms} ms (Dwell)")
    print("==================================================")

    # 3. 離散化正弦波目標轉速
    center_rpm = (peak_rpm + bottom_rpm) / 2.0
    amp_rpm = (peak_rpm - bottom_rpm) / 2.0

    t = np.linspace(0, total_time_s, num_steps + 1)
    rpm_targets = center_rpm - amp_rpm * np.cos(2 * np.pi * f * t)

    commands = []
    # Step 0: 初始待命轉速
    commands.append({
        "step": 0,
        "target_rpm": float(init_rpm),
        "ramp_ms": 0,
        "dwell_ms": 0
    })

    # Step 1 ~ N: 後續正弦波階段
    for i in range(1, len(rpm_targets)):
        commands.append({
            "step": i,
            "target_rpm": round(rpm_targets[i], 1),
            "ramp_ms": auto_ramp_ms,
            "dwell_ms": auto_dwell_ms
        })

    return commands, total_time_s, center_rpm, amp_rpm, f, T_s, auto_ramp_ms, auto_dwell_ms

# ==========================================
# 參數輸入區 (可自由修改頻率與初始轉速)
# ==========================================
freq_test = 0.1     # 正弦波頻率 (Hz)
cycles_test = 3     # 欲執行的週期數
initial_rpm = 200    # 測試修改初始轉速 (此處修改作圖必定連動)
bottom_rpm = 200    # 正弦波波谷轉速
top_rpm = 720       # 正弦波波峰轉速

# 1. 執行自動最佳化配比指令生成
commands, total_time, center_val, amp_val, f_val, T_val, best_ramp, best_dwell = generate_optimal_sine_commands(
    freq_hz=freq_test,
    num_cycles=cycles_test,
    init_rpm=initial_rpm,
    bottom_rpm=bottom_rpm,
    peak_rpm=top_rpm,
    min_dwell_ms=100
)

# ==========================================
# 2. 繪圖檢視 (修正 initial_rpm 作圖未同步問題)
# ==========================================
# 嚴格綁定 Step 0 的 initial_rpm，避免數值寫死
t_plot = [0]
rpm_plot = [float(commands[0]["target_rpm"])]

for cmd in commands[1:]:
    # 爬坡段
    t_plot.append(t_plot[-1] + cmd["ramp_ms"] / 1000.0)
    rpm_plot.append(cmd["target_rpm"])
    # 停留段
    t_plot.append(t_plot[-1] + cmd["dwell_ms"] / 1000.0)
    rpm_plot.append(cmd["target_rpm"])

plt.figure(figsize=(12, 6))
# 繪製馬達階梯控制折線
plt.plot(t_plot, rpm_plot, 'b.-', label=f"Motor Path (Auto-Ramp: {best_ramp}ms, Dwell: {best_dwell}ms)")

# 繪製理論連續正弦波
ideal_t = np.linspace(0, total_time, 600)
ideal_rpm = center_val - amp_val * np.cos(2 * np.pi * f_val * ideal_t)
plt.plot(ideal_t, ideal_rpm, 'r--', alpha=0.7, label="Ideal Continuous Sine Wave")

# 標註關鍵點與基準線
plt.axhline(top_rpm, color='gray', linestyle=':', label=f"Peak: {top_rpm} RPM")
plt.axhline(bottom_rpm, color='gray', linestyle=':', label=f"Bottom: {bottom_rpm} RPM")
plt.scatter([0], [float(commands[0]["target_rpm"])], color='green', s=70, zorder=5, 
            label=f"Step 0 Init: {commands[0]['target_rpm']} RPM")

plt.title(f"Optimal Sine Wave Profile: f = {f_val} Hz (T = {T_val:.1f} s) | {cycles_test} Cycles")
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
user_choice = input("\n❓ 是否要將此最佳化配置匯出為 CSV 檔案？(y/n): ").strip().lower()

if user_choice in ['y', 'yes']:
    csv_filename = f"DELTA/motor_sine_{f_val}Hz_{bottom_rpm}to{top_rpm}_init{int(initial_rpm)}.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ["step", "target_rpm", "ramp_ms", "dwell_ms"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cmd in commands:
            writer.writerow(cmd)
    print(f"✅ 檔案已成功匯出至：{csv_filename}")
else:
    print("❌ 取消匯出，未建立任何 CSV 檔案。")