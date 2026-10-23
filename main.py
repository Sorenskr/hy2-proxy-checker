import os
import json
import time
import subprocess
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProxyReq(BaseModel):
    server: str
    port: int
    auth: str
    sni: str = "bing.com"
    skip_tls_verify: bool = True

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Proxy checker is running"}

@app.post("/test")
def test_node(data: ProxyReq):
    test_port = 19999
    config = {
        "log": {"level": "warn"},
        "inbounds": [{
            "type": "mixed",
            "tag": "mixed-in",
            "listen": "127.0.0.1",
            "listen_port": test_port
        }],
        "outbounds": [{
            "type": "hysteria2",
            "tag": "proxy",
            "server": data.server,
            "server_port": data.port,
            "password": data.auth,
            "tls": {
                "enabled": True,
                "server_name": data.sni,
                "insecure": data.skip_tls_verify
            }
        }]
    }

    config_path = "/tmp/temp_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)

    # 启动后台 sing-box 探针
    proc = subprocess.Popen(
        ["sing-box", "run", "-c", config_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.6)

    proxy_handler = urllib.request.ProxyHandler({
        "http": f"http://127.0.0.1:{test_port}",
        "https": f"http://127.0.0.1:{test_port}"
    })
    opener = urllib.request.build_opener(proxy_handler)

    start_time = time.time()
    result = {"online": False, "latency": 0, "error": ""}
    try:
        req = urllib.request.Request(
            "http://cp.cloudflare.com/generate_204",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        res = opener.open(req, timeout=3.5)
        if res.status in [200, 204]:
            result["online"] = True
            result["latency"] = int((time.time() - start_time) * 1000)
    except Exception:
        result["error"] = "连接超时/节点离线"
    finally:
        proc.terminate()
        if os.path.exists(config_path):
            os.remove(config_path)

    return result

if __name__ == "__main__":
    # Render 会注入 PORT 环境变量，默认取 10000
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)