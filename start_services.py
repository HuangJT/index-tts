#!/usr/bin/env python3
"""
启动IndexTTS服务脚本
可以同时启动API服务和Gradio Web界面
"""

import os
import sys
import time
import subprocess
import threading
import argparse
from pathlib import Path

def start_api_server(host="0.0.0.0", port=8000):
    """启动API服务器"""
    print(f"🚀 启动API服务器 - http://{host}:{port}")
    cmd = [sys.executable, "api_server.py", "--host", host, "--port", str(port)]
    subprocess.run(cmd)

def start_gradio_webui(host="127.0.0.1", port=7860):
    """启动Gradio Web界面"""
    print(f"🌐 启动Gradio界面 - http://{host}:{port}")
    
    # 修改webui.py中的启动参数
    import webui
    webui.demo.queue(20)
    webui.demo.launch(server_name=host, server_port=port, share=False)

def main():
    parser = argparse.ArgumentParser(description="IndexTTS服务启动器")
    parser.add_argument("--mode", choices=["api", "webui", "both"], default="both",
                       help="启动模式: api(仅API), webui(仅Web界面), both(同时启动)")
    parser.add_argument("--api-host", default="0.0.0.0", help="API服务器地址")
    parser.add_argument("--api-port", type=int, default=8000, help="API服务器端口")
    parser.add_argument("--webui-host", default="127.0.0.1", help="Web界面地址")
    parser.add_argument("--webui-port", type=int, default=7860, help="Web界面端口")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎤 IndexTTS 服务启动器")
    print("=" * 60)
    
    if args.mode in ["api", "both"]:
        if args.mode == "both":
            # 在单独线程中启动API服务器
            api_thread = threading.Thread(
                target=start_api_server,
                args=(args.api_host, args.api_port),
                daemon=True
            )
            api_thread.start()
            time.sleep(3)  # 等待API服务器启动
        else:
            start_api_server(args.api_host, args.api_port)
            return
    
    if args.mode in ["webui", "both"]:
        start_gradio_webui(args.webui_host, args.webui_port)

if __name__ == "__main__":
    main()