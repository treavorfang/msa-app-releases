import subprocess
import time
import sys

print("🚀 Launching MSA for monitoring...")
subprocess.run(["open", "dist/MSA.app"])

print("📊 Monitoring startup metrics (10 seconds)...")
print(f"{'TIME':<8} {'PID':<8} {'CPU%':<8} {'MEM%':<8} {'RSS(MB)':<10}")
print("-" * 50)

target_pid = None
start_time = time.time()

for i in range(20):
    elapsed = time.time() - start_time
    
    # Find PID if not known
    if not target_pid:
        # pgrep -f "MSA.app/Contents/MacOS/MSA"
        res = subprocess.run(["pgrep", "-f", "MSA.app/Contents/MacOS/MSA"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pids = res.stdout.strip().split('\n')
            target_pid = pids[0]
    
    if target_pid:
        # Get stats: ps -p PID -o %cpu,%mem,rss
        # RSS is in KB, divide by 1024 for MB
        res = subprocess.run(["ps", "-p", target_pid, "-o", "%cpu,%mem,rss"], capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split('\n')
            if len(lines) > 1:
                # header is line 0, data is line 1
                try:
                    stats = lines[1].split()
                    if len(stats) >= 3:
                        cpu = stats[0]
                        mem_pct = stats[1]
                        rss_kb = int(stats[2])
                        rss_mb = rss_kb / 1024
                        print(f"{elapsed:<8.1f} {target_pid:<8} {cpu:<8} {mem_pct:<8} {rss_mb:<10.1f}")
                except:
                    pass
        else:
             print(f"{elapsed:<8.1f} Process {target_pid} stopped/not found")
             break
    else:
        print(f"{elapsed:<8.1f} Waiting for process...")
        
    time.sleep(0.5)

print("-" * 50)
print("Done.")
