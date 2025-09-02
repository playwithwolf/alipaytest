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
        logger.info(f"Initializing AlipayH5Server with port={port}")
        self.app = FastAPI(
            title="支付宝H5支付服务器",
            description="支持动态配置的支付宝H5支付测试服务器",
            version="1.0.0"
        )
        logger.info("FastAPI app created")
        self.setup_middleware()
        self.setup_routes()
        logger.info("Middleware and routes setup completed")
        
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware added")
        
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            return response
    
    def setup_routes(self):
        logger.info("Setting up routes...")

        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            logger.info("Serving index.html")
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                logger.error("index.html not found")
                raise HTTPException(status_code=404, detail="index.html not found")
        
        @self.app.get("/{file_path:path}")
        async def serve_static_files(file_path: str):
            logger.info(f"Request for static file: {file_path}")
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
            logger.info("=" * 60)
            logger.info("支付结果页面被访问 - /payment/result")
            logger.info(f"访问时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"客户端IP: {request.client.host if request.client else 'Unknown'}")
            logger.info(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")
            logger.info(f"完整URL: {request.url}")
            logger.info(f"查询参数: {query_params}")
            
            # 解析支付宝返回的参数
            if query_params:
                logger.info("支付宝同步返回参数解析:")
                for key, value in query_params.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info("未收到任何查询参数")
            
            logger.info("=" * 60)
            html_content = f"<html><body><pre>{json.dumps(query_params, indent=2)}</pre></body></html>"
            return HTMLResponse(content=html_content)
        
        @self.app.post("/api/alipay/notify")
        async def alipay_notify(request: Request):
            try:
                logger.info("=" * 80)
                logger.info("收到支付宝异步通知 - /api/alipay/notify")
                logger.info(f"通知时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"客户端IP: {request.client.host if request.client else 'Unknown'}")
                logger.info(f"Content-Type: {request.headers.get('content-type', 'Unknown')}")
                logger.info(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")
                
                # 获取原始请求体
                body = await request.body()
                logger.info(f"原始请求体: {body.decode('utf-8') if body else 'Empty'}")
                
                # 重新创建request以获取form数据
                request._body = body
                form_data = await request.form()
                notify_data = dict(form_data)
                
                logger.info("支付宝异步通知参数:")
                for key, value in notify_data.items():
                    logger.info(f"  {key}: {value}")
                
                # 重点关注的参数
                important_params = ['out_trade_no', 'trade_no', 'trade_status', 'total_amount', 'subject']
                logger.info("重要参数摘要:")
                for param in important_params:
                    if param in notify_data:
                        logger.info(f"  {param}: {notify_data[param]}")
                
                logger.info("异步通知处理完成，返回success")
                logger.info("=" * 80)
                return Response(content="success", media_type="text/plain")
            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"处理支付宝异步通知时发生错误: {str(e)}")
                logger.error(f"错误时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.error("=" * 80)
                return Response(content="fail", media_type="text/plain")
        
        @self.app.post("/api/config")
        async def save_config(config: AlipayConfig):
            logger.info(f"Saving config for app_id: {config.app_id}")
            if not config.app_id or not config.private_key:
                raise HTTPException(status_code=400, detail="app_id and private_key are required")
            self.current_config = config.model_dump()
            return JSONResponse({
                "success": True,
                "message": "配置保存成功",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/api/config")
        async def load_config():
            logger.info("Loading config")
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
            logger.info("Health check requested")
            return JSONResponse({"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"})
    
    def run(self):
        # 切换到脚本所在目录，确保相对路径正确
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        logger.info(f"Changed working directory to: {script_dir}")
        
        port = self.port
        logger.info(f"Starting server locally at http://localhost:{port}")
        logger.info("Starting uvicorn...")
        uvicorn.run(self.app, host="0.0.0.0", port=port, log_level="info", access_log=True)


# ===== Render 部署 =====
logger.info(f"Environment PORT={os.environ.get('PORT')}")
port = int(os.environ.get("PORT", 8000))
server_instance = AlipayH5Server(port=port)
logger.info("Server instance created, FastAPI app exposed as 'app'")
app = server_instance.app  # Render 部署直接暴露 FastAPI app

# ===== 本地运行 =====
if __name__ == "__main__":
    logger.info("Running locally")
    server_instance.run()
