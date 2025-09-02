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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
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
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 请求日志中间件
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            return response
    
    def setup_routes(self):
        """设置路由"""
        
        # 静态文件服务
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            """提供主页面"""
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="index.html not found")
        
        @self.app.get("/{file_path:path}")
        async def serve_static_files(file_path: str):
            """提供静态文件"""
            # 安全检查，防止路径遍历攻击
            if ".." in file_path or file_path.startswith("/"):
                raise HTTPException(status_code=403, detail="Access denied")
            
            file_full_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_full_path.exists() or not file_full_path.is_file():
                raise HTTPException(status_code=404, detail="File not found")
            
            # 根据文件扩展名设置Content-Type
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
            
            file_ext = file_full_path.suffix.lower()
            media_type = content_type_map.get(file_ext, "application/octet-stream")
            
            return FileResponse(file_full_path, media_type=media_type)
        
        # 支付结果页面
        @self.app.get("/payment/result", response_class=HTMLResponse)
        async def payment_result(request: Request):
            """支付结果页面"""
            query_params = dict(request.query_params)
            logger.info(f"Payment result page accessed with params: {query_params}")
            
            # 简单的结果页面HTML
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
                    .success {{ color: #52c41a; }}
                    .error {{ color: #ff4d4f; }}
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
        
        # 支付宝异步通知接口
        @self.app.post("/api/alipay/notify")
        async def alipay_notify(request: Request):
            """处理支付宝异步通知"""
            try:
                # 获取POST数据
                form_data = await request.form()
                notify_data = dict(form_data)
                
                logger.info(f"Received Alipay notify: {notify_data}")
                
                # 这里应该进行签名验证，但为了演示简化处理
                # 在实际项目中需要验证支付宝的签名
                
                # 返回success表示处理成功
                return Response(content="success", media_type="text/plain")
                
            except Exception as e:
                logger.error(f"Error processing Alipay notify: {str(e)}")
                return Response(content="fail", media_type="text/plain")
        
        # 配置管理API
        @self.app.post("/api/config")
        async def save_config(config: AlipayConfig):
            """保存配置"""
            try:
                # 验证必要参数
                if not config.app_id or not config.private_key:
                    raise HTTPException(status_code=400, detail="app_id and private_key are required")
                
                # 保存配置到内存（实际项目中可能需要持久化存储）
                self.current_config = config.dict()
                
                logger.info(f"Configuration saved for app_id: {config.app_id}")
                
                return JSONResponse({
                    "success": True,
                    "message": "配置保存成功",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error saving config: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config")
        async def load_config():
            """加载配置（不返回敏感信息）"""
            try:
                if not self.current_config:
                    return JSONResponse({
                        "success": False,
                        "message": "暂无配置信息"
                    })
                
                # 返回配置信息，但不包含敏感数据
                safe_config = {
                    "app_id": self.current_config.get("app_id", ""),
                    "gateway": self.current_config.get("gateway", ""),
                    "notify_url": self.current_config.get("notify_url", ""),
                    "return_url": self.current_config.get("return_url", ""),
                    "hasPrivateKey": bool(self.current_config.get("private_key")),
                    "hasPublicKey": bool(self.current_config.get("alipay_public_key"))
                }
                
                return JSONResponse({
                    "success": True,
                    "config": safe_config,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # 健康检查接口
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return JSONResponse({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            })
    
    def run(self):
        """启动服务器"""
        try:
            logger.info(f"Starting Alipay H5 Payment Server...")
            logger.info(f"Server will be available at:")
            logger.info(f"  - Main page: http://localhost:{self.port}")
            logger.info(f"  - Payment result: http://localhost:{self.port}/payment/result")
            logger.info(f"  - Notify URL: http://localhost:{self.port}/api/alipay/notify")
            logger.info(f"  - Health check: http://localhost:{self.port}/health")
            logger.info(f"Press Ctrl+C to stop the server")
            
            # 启动服务器
            uvicorn.run(
                self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="info",
                access_log=False  # 我们使用自定义的请求日志
            )
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise

def main():
    """主函数"""
    # 从环境变量获取端口，默认8000
    port = int(os.environ.get("PORT", 8000))
    
    # 创建并启动服务器
    server = AlipayH5Server(port=port)
    server.run()

if __name__ == "__main__":
    main()