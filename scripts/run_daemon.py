import subprocess
import sys
import os
import time
import re

project_root = r"C:\Users\Edward\Desktop\CaseStudy"
os.chdir(project_root)

# 1. Start Uvicorn if not already on 8000
import socket
s = socket.socket()
try:
    s.connect(("127.0.0.1", 8000))
    backend_running = True
    s.close()
except:
    backend_running = False

if not backend_running:
    print("Starting Uvicorn backend...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
else:
    print("Uvicorn already running on port 8000.")

# 2. Start ngrok with pooling enabled
ngrok_bin = os.path.join(project_root, "tools", "ngrok.exe")
print("Starting ngrok permanent tunnel...")
subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], capture_output=True)
ngrok_proc = subprocess.Popen(
    [ngrok_bin, "http", "--url=https://anybody-cube-surprise.ngrok-free.dev", "--pooling-enabled", "8000", "--log=stdout"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# 3. Start Cloudflare Tunnel
subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)
cf_bin = os.path.join(project_root, "tools", "cloudflared.exe")
cf_proc = subprocess.Popen(
    [cf_bin, "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"],
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

cf_url = None
start_time = time.time()
while time.time() - start_time < 25:
    line = cf_proc.stderr.readline()
    if line:
        m = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
        if m:
            cf_url = m.group(1)
            break

tunnel_file = os.path.join(project_root, "scratch", "active_tunnel.txt")
with open(tunnel_file, "w", encoding="utf-8") as f:
    f.write(f"CLOUDFLARE_URL={cf_url}\n")
    f.write(f"NGROK_URL=https://anybody-cube-surprise.ngrok-free.dev\n")

print("=" * 60, flush=True)
print(f"BACKEND: http://127.0.0.1:8000", flush=True)
print(f"PERMANENT NGROK: https://anybody-cube-surprise.ngrok-free.dev", flush=True)
print(f"CLOUDFLARE TUNNEL: {cf_url}", flush=True)
print("=" * 60, flush=True)

# Keep alive
while True:
    time.sleep(2)
