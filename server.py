#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支付宝H5支付 - FastAPI服务器
提供本地HTTP服务以测试支付宝H5支付页面
支持动态配置管理功能
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 配置数据模型
class AlipayConfig(BaseModel):
    app_id: str
    private_key: str
    alipay_public_key: str
    notify_url: str
    return_url: str
    gateway: str

class PaymentRequest(BaseModel):
    subject: str
    total_amount: float
    out_trade_no: str

class AlipayH5Server:
    def __init__(self, port: int = 8000):
        self.port = port
        self.current_config: Optional[Dict[str, Any]] = None
        self.app = FastAPI(
            title="支付宝H5支付服务器",
            description="支持动态配置的支付宝H5支付测试服务器",
            version="1.0.0"
        )
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            return response
    
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="index.html not found")
        
        @self.app.get("/{file_path:path}")
        async def serve_static_files(file_path: str):
            if ".." in file_path or file_path.startswith("/"):
                raise HTTPException(status_code=403, detail="Access denied")
            file_full_path = Path(file_path)
            if not file_full_path.exists() or not file_full_path.is_file():
                raise HTTPException(status_code=404, detail="File not found")
            content_type_map = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon"
            }
            media_type = content_type_map.get(file_full_path.suffix.lower(), "application/octet-stream")
            return FileResponse(file_full_path, media_type=media_type)
        
        @self.app.get("/payment/result", response_class=HTMLResponse)
        async def payment_result(request: Request):
            query_params = dict(request.query_params)
            logger.info(f"Payment result page accessed with params: {query_params}")
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>支付结果</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .info {{ background: #f6f8fa; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                    pre {{ background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>支付结果</h1>
                    <div class="info">
                        <h3>返回参数：</h3>
                        <pre>{json.dumps(query_params, indent=2, ensure_ascii=False)}</pre>
                    </div>
                    <p><a href="/">返回首页</a></p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.post("/api/alipay/notify")
        async def alipay_notify(request: Request):
            try:
                form_data = await request.form()
                notify_data = dict(form_data)
                logger.info(f"Received Alipay notify: {notify_data}")
                return Response(content="success", media_type="text/plain")
            except Exception as e:
                logger.error(f"Error processing Alipay notify: {str(e)}")
                return Response(content="fail", media_type="text/plain")
        
        @self.app.post("/api/config")
        async def save_config(config: AlipayConfig):
            if not config.app_id or not config.private_key:
                raise HTTPException(status_code=400, detail="app_id and private_key are required")
            self.current_config = config.model_dump()
            logger.info(f"Configuration saved for app_id: {config.app_id}")
            return JSONResponse({
                "success": True,
                "message": "配置保存成功",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/api/config")
        async def load_config():
            if not self.current_config:
                return JSONResponse({"success": False, "message": "暂无配置信息"})
            safe_config = {
                "app_id": self.current_config.get("app_id", ""),
                "gateway": self.current_config.get("gateway", ""),
                "notify_url": self.current_config.get("notify_url", ""),
                "return_url": self.current_config.get("return_url", ""),
                "hasPrivateKey": bool(self.current_config.get("private_key")),
                "hasPublicKey": bool(self.current_config.get("alipay_public_key"))
            }
            return JSONResponse({"success": True, "config": safe_config, "timestamp": datetime.now().isoformat()})
        
        @self.app.get("/health")
        async def health_check():
            return JSONResponse({"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"})
    
    def run(self):
        """本地运行"""
        port = self.port
        logger.info(f"Starting server locally at http://localhost:{port}")
        uvicorn.run(self.app, host="0.0.0.0", port=port, log_level="info", access_log=False)


# ===== 方案1：Render 部署直接暴露 app =====
port = int(os.environ.get("PORT", 8000))
server_instance = AlipayH5Server(port=port)
app = server_instance.app  # uvicorn Render 部署可以直接访问

# ===== 本地运行 =====
if __name__ == "__main__":
    server_instance.run()
