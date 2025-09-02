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

# 导入支付宝SDK
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradeWapPayModel import AlipayTradeWapPayModel
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest
from alipay.aop.api.response.AlipayTradeWapPayResponse import AlipayTradeWapPayResponse
from alipay.aop.api.util.SignatureUtils import verify_with_rsa

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
        self.alipay_client: Optional[DefaultAlipayClient] = None
        logger.info(f"Initializing AlipayH5Server with port={port}")
        self.app = FastAPI(
            title="支付宝H5支付服务器",
            description="支持动态配置的支付宝H5支付测试服务器",
            version="1.0.0"
        )
        logger.info("FastAPI app created")
        self.init_alipay_sdk()
        self.setup_middleware()
        self.setup_routes()
        logger.info("Middleware and routes setup completed")
    
    def init_alipay_sdk(self):
        """初始化支付宝SDK"""
        try:
            # 默认配置（沙箱环境）
            default_config = {
                'app_id': '9021000151657305',  # 沙箱应用ID，请替换为实际的
                'private_key': '''-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAnNg6Lz+dffDTrtyuhuJzhdwoW2VBAzRfMz6qFlzDVmpyukJFgrP+axHTvkVLP/qYPGk6GmJHP9RotMk4i19efzwR7XY0fbp89sDMXqSQlRvOIxPgKGd6GavXvWcl9xtaPpFyoprBYg+E5Iybv5FgEgCDw4g2TDKAch39wfDfwc5PVOy8duncQudghnHi09Jd+N2lLQ4B+asKKuqSDuosov1TXo0Tl8VacUybJO3CZjjt/tJr2sbmDblE1ITlP4B+pLow0vZ+IhEw2rwMTbdSThO8qDt3llY2BzBHEFGcRs5dn5FlQeTSz+vQT4VIV8fVuIqn0DTjBIeERYo/7HbPrQIDAQABAoIBAQCR3BhIJl39aEBEBuCbee67FuHFFSXfqA28p1MgFsZmD/p/su/XvDInOl3zPZfceNyomac6MBlYh92T+umF23wS0TdO4TWxkwNxqhylC1+V+1S5lFtK1+haBVBNyKYq5poHQ9Ya19ZtrkcFEKoq/jQcqbPf3EW6mOCQv8lkWfCM1yZa3bA6VQMOpRg0RMUTSnnCoASx9cRDQPoZt5ecFUZ4SDZJaRLZ072w/ewT8T5hxa11GMSRP5mT9oE/zOIW62k4+Fn0vv4I8rTzg3tNPsJJOiUiLfRaGtDrPPhh4vBcqaUUSIc7dYMhtz66yvoJULiQz/FtWp4TmzoELL2ammahAoGBAPb3T1T7fOkl5vEAi8g2a4ukn4aEIGLajXpni9AFkPpguwZCvz4txVYJ/QDAAN30ZuZnu5ZdGRABnCKzkBbLA1jQS3PMuqwuFN8cwPSZ1djEAb6Q9PhJkwBn9zr5u6WGztxokPjrvcPonAoujz1XV6iqO6avcxKxQ7c9Trap7uk1AoGBAKKU++U3SC6jYAhSllQ+YfuIxxJOglOMYxn3DYRn5SIwqBULLFp+rQ7FbROp6TDC1kEXC00Xm/1OSlDZIjI14Vav2nP3hjFcTHig0wFJU1Ppl+LhKnQPNagoTn3ger6SW1e9neWqD2youXlyVgwgTZ/Oyuw4sd8eNn/6lz1WNJOZAoGBAIgkjXcrrBBa9JSm2GfmmCLC/a4J6FCWaqevrUNfziw4ZuFsqkB8uuxTVUW0ksXIlXEufhrF96r7ODdpBWWLRK0RJocPtVh1jsvv7e7pXxm/87Y58tFsvbzbk07PnMIDLsYSXtjaHCKDeIGkaRJHs+sm7PtWfPkw/0NkaKAJzcqBAoGBAKBb9KycP00JBdKPqwkC0uAng7rRxwgjQyg8HpAHbeCwP0kqUSAdLBKStkib4Y6fznY7BYGPlONe0jw2Pt1peY5oOz8A2NJc6GxerGDrcw4kLBSy5I2+5ryqrOjJfifz8bZ0J4Z8m2Qgc3iPRsIFJqtGa65dKUwZ38WRZJUyLv+ZAoGAdoY4H/WIB0q73cQs3OyMRg5vneQzaJsSnv5RYq2whz1hbJNQ29UHhDk8Sov7LeEwwM3NOJoa0hlcV3uIp90+IRO0qdli5JUCChAXDJhVdhMDDtApzqd9ejASEUWjrW62sVP/zc5t8o19VXCf7rlbRCUL0UxNg4qdmi4bDg/JblA=
-----END RSA PRIVATE KEY-----''',
                'alipay_public_key': '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqRUOzanbew6pZy9TriP6DmqyrMRuGqJ6KfbFBHzRvsPc+QY0D3kOnc+TIhJBi+ymfJPty2RdU+gZIJaoZRxHmHyKEdknz5HA/Lv2jHm6GK6wF3WcROb64k99CgsIUesIVCMjZ7r7RQEmEvsz+R4gAgh5kjhGAhGNO3TJK3i2obqPBQBxYdSKDxLryFhWZZWMChIhhwUpZtraJxQWqNOIz24yIhugdlAALYyvTAc8zSCftLr/Imp05apkHT36eKPo1gWbEHiB94haNvwyWqac0AI7lwYq+kLPudp+JYMg5AGrmFLnYwP+7XhMrmk483OfA9yoF4UObTaPBSQ91C7JGQIDAQAB
-----END PUBLIC KEY-----''',
                'gateway': 'https://openapi-sandbox.dl.alipaydev.com/gateway.do',
                'notify_url': 'http://localhost:8000/api/alipay/notify',
                'return_url': 'http://localhost:8000/payment/result'
            }
            
            # 尝试从环境变量或配置文件读取配置
            config = self.load_alipay_config() or default_config
            
            # 配置支付宝客户端
            alipay_client_config = AlipayClientConfig()
            alipay_client_config.server_url = config['gateway']
            alipay_client_config.app_id = config['app_id']
            alipay_client_config.app_private_key = config['private_key']
            alipay_client_config.alipay_public_key = config['alipay_public_key']
            
            # 初始化支付宝客户端
            self.alipay_client = DefaultAlipayClient(alipay_client_config=alipay_client_config, logger=logger)
            
            self.current_config = config
            logger.info("支付宝SDK初始化成功")
            
        except Exception as e:
            logger.error(f"支付宝SDK初始化失败: {e}")
            self.alipay_client = None
    
    def load_alipay_config(self) -> Optional[Dict[str, str]]:
        """从配置文件或环境变量加载支付宝配置"""
        try:
            # 尝试从环境变量读取
            if all(os.environ.get(key) for key in ['ALIPAY_APP_ID', 'ALIPAY_PRIVATE_KEY', 'ALIPAY_PUBLIC_KEY']):
                return {
                    'app_id': os.environ.get('ALIPAY_APP_ID'),
                    'private_key': os.environ.get('ALIPAY_PRIVATE_KEY'),
                    'alipay_public_key': os.environ.get('ALIPAY_PUBLIC_KEY'),
                    'gateway': os.environ.get('ALIPAY_GATEWAY', 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'),
                    'notify_url': os.environ.get('ALIPAY_NOTIFY_URL', 'http://localhost:8000/api/alipay/notify'),
                    'return_url': os.environ.get('ALIPAY_RETURN_URL', 'http://localhost:8000/payment/result')
                }
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
        
        return None
        
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
        
        @self.app.post("/api/alipay/create_order")
        async def create_alipay_order(payment_request: PaymentRequest):
            """创建支付宝支付订单"""
            try:
                if not self.alipay_client:
                    logger.error("支付宝SDK未初始化")
                    raise HTTPException(status_code=500, detail="支付宝SDK未初始化")
                
                logger.info(f"创建支付订单: {payment_request.dict()}")
                
                # 构建支付请求模型
                model = AlipayTradeWapPayModel()
                model.out_trade_no = payment_request.out_trade_no
                model.total_amount = str(payment_request.total_amount)
                model.subject = payment_request.subject
                model.product_code = "QUICK_WAP_WAY"
                
                # 创建支付请求
                request_obj = AlipayTradeWapPayRequest(biz_model=model)
                request_obj.return_url = self.current_config.get('return_url', 'http://localhost:8000/payment/result')
                request_obj.notify_url = self.current_config.get('notify_url', 'http://localhost:8000/api/alipay/notify')
                
                # 执行请求
                response_content = self.alipay_client.page_execute(request_obj, http_method="GET")
                
                logger.info(f"支付订单创建成功，订单号: {payment_request.out_trade_no}")
                
                return {
                    "success": True,
                    "message": "订单创建成功",
                    "data": {
                        "out_trade_no": payment_request.out_trade_no,
                        "pay_url": response_content,
                        "order_string": response_content
                    }
                }
                
            except Exception as e:
                logger.error(f"创建支付订单失败: {e}")
                raise HTTPException(status_code=500, detail=f"创建支付订单失败: {str(e)}")
        
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
                
                # 使用SDK验证签名
                if self.alipay_client and self.current_config:
                    try:
                        # 准备验签数据
                        sign = notify_data.pop('sign', '')
                        sign_type = notify_data.pop('sign_type', 'RSA2')
                        
                        # 构建待验签字符串
                        sorted_items = sorted(notify_data.items())
                        unsigned_string = '&'.join([f'{k}={v}' for k, v in sorted_items if v])
                        
                        # 验证签名
                        alipay_public_key = self.current_config.get('alipay_public_key', '')
                        sign_valid = verify_with_rsa(alipay_public_key, unsigned_string.encode('utf-8'), sign)
                        
                        logger.info(f"签名验证结果: {sign_valid}")
                        
                        if not sign_valid:
                            logger.warning("签名验证失败，可能是伪造的通知")
                            return Response(content="fail", media_type="text/plain")
                        
                        logger.info("签名验证成功")
                        
                        # 恢复sign和sign_type到notify_data中，供后续使用
                        notify_data['sign'] = sign
                        notify_data['sign_type'] = sign_type
                        
                    except Exception as verify_error:
                        logger.error(f"签名验证过程中发生错误: {verify_error}")
                        # 如果验证过程出错，为了安全起见返回fail
                        return Response(content="fail", media_type="text/plain")
                else:
                    logger.warning("支付宝SDK未初始化，跳过签名验证")
                
                # 重点关注的参数
                important_params = ['out_trade_no', 'trade_no', 'trade_status', 'total_amount', 'subject']
                logger.info("重要参数摘要:")
                for param in important_params:
                    if param in notify_data:
                        logger.info(f"  {param}: {notify_data[param]}")
                
                # 处理支付状态
                trade_status = notify_data.get('trade_status')
                out_trade_no = notify_data.get('out_trade_no')
                trade_no = notify_data.get('trade_no')
                total_amount = notify_data.get('total_amount')
                
                if trade_status == 'TRADE_SUCCESS':
                    logger.info(f"支付成功 - 订单号: {out_trade_no}, 交易号: {trade_no}, 金额: {total_amount}")
                    # 这里可以添加业务逻辑，如更新订单状态、发送通知等
                elif trade_status == 'TRADE_FINISHED':
                    logger.info(f"交易完成 - 订单号: {out_trade_no}, 交易号: {trade_no}, 金额: {total_amount}")
                    # 这里可以添加业务逻辑
                else:
                    logger.info(f"其他状态: {trade_status} - 订单号: {out_trade_no}")
                
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
