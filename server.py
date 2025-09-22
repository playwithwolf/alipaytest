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
import time
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
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest
from alipay.aop.api.domain.AlipayTradeWapPayModel import AlipayTradeWapPayModel
from alipay.aop.api.request.AlipayTradeAppPayRequest import AlipayTradeAppPayRequest
from alipay.aop.api.domain.AlipayTradeAppPayModel import AlipayTradeAppPayModel
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
            # default_config = {
            #                 'app_id': '9021000151657305',  # 沙箱应用ID，请替换为实际的
            #                 'private_key': '''-----BEGIN RSA PRIVATE KEY-----
            # MIIEpQIBAAKCAQEAnNg6Lz+dffDTrtyuhuJzhdwoW2VBAzRfMz6qFlzDVmpyukJFgrP+axHTvkVLP/qYPGk6GmJHP9RotMk4i19efzwR7XY0fbp89sDMXqSQlRvOIxPgKGd6GavXvWcl9xtaPpFyoprBYg+E5Iybv5FgEgCDw4g2TDKAch39wfDfwc5PVOy8duncQudghnHi09Jd+N2lLQ4B+asKKuqSDuosov1TXo0Tl8VacUybJO3CZjjt/tJr2sbmDblE1ITlP4B+pLow0vZ+IhEw2rwMTbdSThO8qDt3llY2BzBHEFGcRs5dn5FlQeTSz+vQT4VIV8fVuIqn0DTjBIeERYo/7HbPrQIDAQABAoIBAQCR3BhIJl39aEBEBuCbee67FuHFFSXfqA28p1MgFsZmD/p/su/XvDInOl3zPZfceNyomac6MBlYh92T+umF23wS0TdO4TWxkwNxqhylC1+V+1S5lFtK1+haBVBNyKYq5poHQ9Ya19ZtrkcFEKoq/jQcqbPf3EW6mOCQv8lkWfCM1yZa3bA6VQMOpRg0RMUTSnnCoASx9cRDQPoZt5ecFUZ4SDZJaRLZ072w/ewT8T5hxa11GMSRP5mT9oE/zOIW62k4+Fn0vv4I8rTzg3tNPsJJOiUiLfRaGtDrPPhh4vBcqaUUSIc7dYMhtz66yvoJULiQz/FtWp4TmzoELL2ammahAoGBAPb3T1T7fOkl5vEAi8g2a4ukn4aEIGLajXpni9AFkPpguwZCvz4txVYJ/QDAAN30ZuZnu5ZdGRABnCKzkBbLA1jQS3PMuqwuFN8cwPSZ1djEAb6Q9PhJkwBn9zr5u6WGztxokPjrvcPonAoujz1XV6iqO6avcxKxQ7c9Trap7uk1AoGBAKKU++U3SC6jYAhSllQ+YfuIxxJOglOMYxn3DYRn5SIwqBULLFp+rQ7FbROp6TDC1kEXC00Xm/1OSlDZIjI14Vav2nP3hjFcTHig0wFJU1Ppl+LhKnQPNagoTn3ger6SW1e9neWqD2youXlyVgwgTZ/Oyuw4sd8eNn/6lz1WNJOZAoGBAIgkjXcrrBBa9JSm2GfmmCLC/a4J6FCWaqevrUNfziw4ZuFsqkB8uuxTVUW0ksXIlXEufhrF96r7ODdpBWWLRK0RJocPtVh1jsvv7e7pXxm/87Y58tFsvbzbk07PnMIDLsYSXtjaHCKDeIGkaRJHs+sm7PtWfPkw/0NkaKAJzcqBAoGBAKBb9KycP00JBdKPqwkC0uAng7rRxwgjQyg8HpAHbeCwP0kqUSAdLBKStkib4Y6fznY7BYGPlONe0jw2Pt1peY5oOz8A2NJc6GxerGDrcw4kLBSy5I2+5ryqrOjJfifz8bZ0J4Z8m2Qgc3iPRsIFJqtGa65dKUwZ38WRZJUyLv+ZAoGAdoY4H/WIB0q73cQs3OyMRg5vneQzaJsSnv5RYq2whz1hbJNQ29UHhDk8Sov7LeEwwM3NOJoa0hlcV3uIp90+IRO0qdli5JUCChAXDJhVdhMDDtApzqd9ejASEUWjrW62sVP/zc5t8o19VXCf7rlbRCUL0UxNg4qdmi4bDg/JblA=
            # -----END RSA PRIVATE KEY-----''',
            #                 'alipay_public_key': '''-----BEGIN PUBLIC KEY-----
            # MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqRUOzanbew6pZy9TriP6DmqyrMRuGqJ6KfbFBHzRvsPc+QY0D3kOnc+TIhJBi+ymfJPty2RdU+gZIJaoZRxHmHyKEdknz5HA/Lv2jHm6GK6wF3WcROb64k99CgsIUesIVCMjZ7r7RQEmEvsz+R4gAgh5kjhGAhGNO3TJK3i2obqPBQBxYdSKDxLryFhWZZWMChIhhwUpZtraJxQWqNOIz24yIhugdlAALYyvTAc8zSCftLr/Imp05apkHT36eKPo1gWbEHiB94haNvwyWqac0AI7lwYq+kLPudp+JYMg5AGrmFLnYwP+7XhMrmk483OfA9yoF4UObTaPBSQ91C7JGQIDAQAB
            # -----END PUBLIC KEY-----''',
            #                 'gateway': 'https://openapi-sandbox.dl.alipaydev.com/gateway.do',
            #                 'notify_url': 'https://alipaytest.onrender.com/api/alipay/notify',
            #                 'return_url': 'https://alipaytest.onrender.com/payment/result'
            #   }
#             default_config = {
#                 'app_id': '9021000149662306',  # 沙箱应用ID，请替换为实际的
#                 'private_key': '''-----BEGIN RSA PRIVATE KEY-----
# MIIEowIBAAKCAQEAp3zk1C98qsWf3DEPfmITm1TK3N3uqlhO0MkoJ9CxazlcVCu/r3cl2lNfL3QVsoIzTV4StZVJmK/jMu4LoQlP91DbRWt+1mI9/CnD0MPm9JtzmnDUCbGyWsOivs9lCuA5YC5QYHtBibUmWpoCQrWce7TB9PWZrCe4gUvfGlWs58qhlpFT5Ut3nvioG5ADVIuNSHZtB0RrgA0qNLRrRwfaJPb6VXCUyFeXhxaJWJqBRoaKkLJQjyBNwT3biOWShJVF4sQH6E7YVjMr35tcZf5zi0XKKOvgTDcfTz/o+hrCpUm///ZzgqJnXLTYm7dJR5JVZDL6bs+m2zMcB9+0RV1bIwIDAQABAoIBAG9C+IA8S4TmY5vSu4gpfvzhByJSDAn9P95SwuowKKwiHsOLjHrzm6G9YK4VX5SGCa6Ln8IguhNERJnAqNkBZq3UeNVU451nBeZNmFdGzFYSLmmaKkGGWgURkTtQar8e1P6fxaVSO+dO/3uQc4/9NUa4fWBNBxjmChtaW4sS/xm625CDOHHzwn7MrOkDQlHqyHoxXzldcZzfxtLXFMtY4V8Hz9I5Tm1Nz7xeW5VZRSvKdQCWHZ8x2KX7edF0VtljAtTlPh9zw5iWlXhfQ6YvXJxWf6jxQAYr+ljgHAae7EIMPb02iEP06jT99C7J662WYdEHKcp2N7b/D3YdyKjQL4ECgYEA8y2issGRCTsE5rRugFkyF1jPtbDlSDdPAgWUOnfYD6nGgdG8XQhr5tmNNAX5PILcE8UKYxJ3wUE0jM6K1zmewqvKTkf1VnZN+mgroOq5KsHIw8G6JNa9QT+7/PzPlXTl2aKfEQjiMkMBRvZpi8+xojj2EOQIn686PTVjeK0Ui/cCgYEAsFGbUDKdnZrmzBhJzoAGCr8L5OePttb8+5LFo0tLwL5/sgjHH+hmA/nBRBVyiqNlx1waJ7FxLo8o05ddyZtYkcBKDeWtgWz1w2VAJlPtHK/5PPl88ivtNc/CdU+lYp9bt0R6cggddFwrkKFE7chmlWUj6qlaucH+qmMzg4eUZzUCgYBxabY4kkg3OtxVUI88stzGwLfWsBKu9ISXl8yC3EPbQj3/a7bi2LuiJZJSUfrkes9zNPFcNU++xM9iYC2mpQvjFMW8bpkAYxqJD65RVUdYppogmihbZ/9KABSHr8yMksFkGBEBm9gKwu9EjkW5W/snglNYm1FeUBXkWBL1RBuSDwKBgB8FHHgNj6FMwVIi68lCyM1XMzaAbs5SIIv6FH9YHem5GiouVSoN7vTAGfpqc45klOFwGMHm++yfDyW6uatgg0KRO/YZ9F6S1uIbjB+yIEMtyoGpuwu4IrGW7bVJ3+Tr+GzTxV8OgnAYTynQ1Zmn6jRaaOk+BlIsCSvc7BE15ywJAoGBAJZNoP0xktTHISG0CWyQ2N8F1OJxWRIj2w3rgHUSI63Y6uzMi2Eds29a7zI1qLUyJpM58reiAyaznyakk+EK6nYYdWL01fctAJVi7SL4anAg9CFDICqHjY5HlVW0FR3yS6qF72bbWOCXiVIAVcnqC1SUO0ZpvfJ6d2LYg8mDvUZu
# -----END RSA PRIVATE KEY-----''',
#                 'alipay_public_key': '''-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1YJLtGccnNJdE3HXQ5gvRr2N434ULwI2/U7EoF+z6CiJ0i64KWl9UdX7bLb7Sluj2OQjdCAFvJi1EVEyLf5vPKUxAnBPHmpG7oCTpt/FW26G+Lo7XvvBATGzT9sCdk1w8kgbWwpQbUoivXf/8zo6djYgyPByoWL2afuPMusTDX8GEalCvxIOK4aFhWssN7rfMUsXJapd1a3uGX2AV7y+rK6QlzDHEYkj7I8aVIZCxfqyu7QxgBRXsqhLXBX7HunrDN8EvUKX2IX7ExChRl8m7itCmZFdMmpH4li/8SybgRLbiBDe1U1uaZZQjFGDda2Fx4m2Q76GO5OFER6tbC+s+wIDAQAB
# -----END PUBLIC KEY-----''',
#                 'gateway': 'https://openapi.alipay.com/gateway.do',
#                 'notify_url': 'https://alipaytest.onrender.com/api/alipay/notify',
#                 'return_url': 'https://alipaytest.onrender.com/payment/result'
#             }


            default_config = {
                'app_id': '2021005194600693',  # 沙箱应用ID，请替换为实际的
                'private_key': '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAijTPs8PyvGwWiLFzqDU1wWG9rVgPXlXrIoDcCoyvlS+9cnaPhbzdt1+ovS0daQJFWQJey7h/N/az7gvo5JmjfRe5/1WMHQZopS/qLwPnyz50SCPMHl0xFaxyEvKFhszw6Nucim3zFJwcOV2WRgJds/kPYnTL+UwcteTtK0LEbnOu0MuU7Zol963ogglLjRh75O9wNihbv2TDfjxf75NbDE6RSyXbQTlqId6QBgmetbj3V0tAhqYekyM5zZxSScb4cep5xTEh6sdno3eowMpaFkfzSAQL3B0ZqvevBLFnYVyVOXCT39G2xwfMnJHfrihxRlG3M/MgzsVrck9NhOYHpQIDAQABAoIBAH2TDKGeyf/wCe17psXQSx6Bi5FkMNqbIIGCKeyf9a2M6gqFtVRjzeSe0zfINS/Dc3UzlSRvZ5BW5RfG1H5ZJtYzZ7mbZiq9NvnYdmTvnH3sKkWd2QpBzKaPwDp9B1v6/G3nlO2mhzZTvcVVxoOoBLHQ++yOiQLj6DZRYjlregWMWtCWi9OO6w4HBSEg7SH06o1gKtXC+0Bchzq5F+Itdsq8QS8OLt+s4ZSMt8MonrFU2ny21V+zCdmxw+XG2iURAiTzlynmQxVzSnWKzqS1NdcL3EAsGWvdSfAPvZpXxdrXX2x7ll4gI+28YCbZRy3+weObNP9RpRjiZQld/DZlPUECgYEAw/2Z4oDcJ4lMfZdibzfF64rbDyTLifjbMZ+DZl4Uf6LHlIW9rQ/LVM+wNai1inoD4x5saYVosHP1a4s2h1DJKh1N1WdkPvRCcIm8a7kiEIoFlBhZCB+6NENZmV6dbbiRcUBKKYKVa2eAeZNko95dLR/uQzNfsrHs8iLdFr+Y7rECgYEAtIXhpCSDf1G1mAW7U+NepGkLyvxVAOn53EPp+l3nj/mAIFc7UKjnXEoEB/NsEZxo1bTFFnUnzrhQvxb4DKeucXcdDnH5a9ktHyFg3rfBJHm1t1BXAdPFP4AA59vAQNMNjWE7WTvBjMSG0mRkyFK4Rwh5ihj1MMDXmxS7n5GfrTUCgYEAwIrkIyF1J2I7Qyb2DU09o6lGjBoZ2/IfZSDQdkD24m2IpOC+9sYNe8SN2ClmMCSurPG2j/QAZVmGQaECcO1ss3MWhBCO60oL+4NVGH9Id/cgg91nmhORWsbPv1y0TJaGTDxcn2sqX9nO3aFvvY02/J3h9SMDYQprPXYCvdZ86AECgYB2gflp9yp4F5zdys16OaY0yl0aiWIIMpF7nv3oBWNxqboKARoITolrlY9l5NBKE2LjAEPuBUT3uRoRCDQYoq+q/yYNCJdTzIOJjzD3pKvflSLMz6n+ohY4JIDztNhV9fdMm8sJPmhGT/GuBof+1gbxYsfe95lmwwIHZanyC/hGDQKBgQCpvPyTRcbsm1Vcd3VTTTmkyj/p0lCVV6qr0rDHpAw0mGDT7R5URz7Fz9ukeB6XpRSL8HhOKg20vqies7eyOEsdi+CEsr3dEVryJ7ER9v2Ag3CJTGyXqkF/HCqaFbf/azIdzyBDfosg9dJdhFAr+cDMksEvPJPfGgY3eRzPgPFeHw==
-----END RSA PRIVATE KEY-----''',
                'alipay_public_key': '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgrluf8ZIERvuHr6P2zRGvX6dm8iQJrJACfHh1zdUEDWTxuNz3RBDGMXRTu8iZ3szGVtaWVBz5g5/fyMRCmWDAKRMkppSmm0F5jxI8xHxdWyIJ+6ab8QcpLaqTbQSJXRzt1lsGkPcMu69dLp7/FSemJAxbZ4N2ZtSqGAroTJtmTUGPsGxDV7BqBUdNU2AbKSyU6TlU4Tib/K21dQABftnTffj7VrVtAhuLhuDqBxmDWlc5vjACNnBcs8p83xLg4RLyyd0zhsmS5EscSubB/DKkZ7xPoWjGKqSDN3Hyh6pZRVIo9CEcZL9T7f3z0g+ho7EXWRbVMz3EKpZ5LmR19bMpQIDAQAB
-----END PUBLIC KEY-----''',
                'gateway': 'https://openapi.alipay.com/gateway.do',
                'notify_url': 'https://alipaytest.onrender.com/api/alipay/notify',
                'return_url': 'https://alipaytest.onrender.com/payment/result'
            }
            
            # 尝试从环境变量或配置文件读取配置
            # config = self.load_alipay_config() or default_config
            config = default_config
            
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
                    'notify_url': os.environ.get('ALIPAY_NOTIFY_URL', 'https://alipaytest.onrender.com/api/alipay/notify'),
                    'return_url': os.environ.get('ALIPAY_RETURN_URL', 'https://alipaytest.onrender.com/payment/result')
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
            logger.info(f"[REQUEST] {request.method} {request.url.path} - Query: {dict(request.query_params)}")
            logger.info(f"[REQUEST] Headers: {dict(request.headers)}")
            
            response = await call_next(request)
            
            process_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
            return response
    
    def setup_routes(self):
        logger.info("Setting up routes...")

        # 首先定义API路由，确保它们优先于静态文件路由
        @self.app.get("/payment/result", response_class=HTMLResponse)
        async def payment_result(request: Request):
            logger.info("[ROUTE] 进入 /payment/result 路由处理函数")
            query_params = dict(request.query_params)
            logger.info("=" * 60)
            logger.info("[PAYMENT_RESULT] 支付结果页面被访问 - /payment/result")
            logger.info(f"[PAYMENT_RESULT] 访问时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"[PAYMENT_RESULT] 客户端IP: {request.client.host if request.client else 'Unknown'}")
            logger.info(f"[PAYMENT_RESULT] User-Agent: {request.headers.get('user-agent', 'Unknown')}")
            logger.info(f"[PAYMENT_RESULT] 完整URL: {request.url}")
            logger.info(f"[PAYMENT_RESULT] 查询参数: {query_params}")
            
            # 解析支付宝返回的参数
            if query_params:
                logger.info("支付宝同步返回参数解析:")
                for key, value in query_params.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info("未收到任何查询参数")
            
            logger.info("[PAYMENT_RESULT] 准备返回HTML响应")
            logger.info("=" * 60)
            
            # 读取支付结果页面模板
            try:
                with open("payment_result.html", "r", encoding="utf-8") as f:
                    html_content = f.read()
                logger.info("[PAYMENT_RESULT] 支付结果页面模板加载成功")
                return HTMLResponse(content=html_content)
            except FileNotFoundError:
                logger.error("payment_result.html not found, using fallback")
                # 如果模板文件不存在，使用简单的回退页面
                fallback_html = f"""
                <!DOCTYPE html>
                <html><head><title>支付结果</title></head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h1>支付结果</h1>
                    <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{json.dumps(query_params, indent=2, ensure_ascii=False)}</pre>
                    <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">返回首页</a>
                </body></html>
                """
                return HTMLResponse(content=fallback_html)

        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            logger.info("[ROUTE] 访问根路径 /")
            logger.info("Serving index.html")
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except FileNotFoundError:
                logger.error("index.html not found")
                raise HTTPException(status_code=404, detail="index.html not found")
        
        # 静态文件路由放在最后，避免覆盖API路由
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
            """创建支付宝H5支付订单"""
            try:
                if not self.alipay_client:
                    logger.error("支付宝SDK未初始化")
                    raise HTTPException(status_code=500, detail="支付宝SDK未初始化")
                
                logger.info(f"创建H5支付订单: {payment_request.dict()}")
                
                # 构建支付请求模型
                model = AlipayTradeWapPayModel()
                model.out_trade_no = payment_request.out_trade_no
                model.total_amount = str(payment_request.total_amount)
                model.subject = payment_request.subject
                model.product_code = "QUICK_WAP_WAY"
                
                # 创建支付请求
                request_obj = AlipayTradeWapPayRequest(biz_model=model)
                request_obj.return_url = self.current_config.get('return_url', 'https://alipaytest.onrender.com/payment/result')
                request_obj.notify_url = self.current_config.get('notify_url', 'https://alipaytest.onrender.com/api/alipay/notify')
                
                # 执行请求
                response_content = self.alipay_client.page_execute(request_obj, http_method="GET")
                
                logger.info(f"H5支付订单创建成功，订单号: {payment_request.out_trade_no}")
                
                return {
                    "success": True,
                    "message": "H5订单创建成功",
                    "data": {
                        "out_trade_no": payment_request.out_trade_no,
                        "pay_url": response_content,
                        "order_string": response_content,
                        "payment_type": "h5"
                    }
                }
                
            except Exception as e:
                logger.error(f"创建H5支付订单失败: {e}")
                raise HTTPException(status_code=500, detail=f"创建H5支付订单失败: {str(e)}")
        
        @self.app.post("/api/alipay/create_app_order")
        async def create_alipay_app_order(payment_request: PaymentRequest):
            """创建支付宝APP支付订单"""
            try:
                if not self.alipay_client:
                    logger.error("支付宝SDK未初始化")
                    raise HTTPException(status_code=500, detail="支付宝SDK未初始化")
                
                # 打印接收到的支付请求
                logger.info(f"接收到的支付请求: {payment_request.dict()}")
                
                # 构建APP支付请求模型
                model = AlipayTradeAppPayModel()

                # 确保所有数字字段为字符串类型
                model.timeout_express = "90m"
                model.total_amount = str(payment_request.total_amount)  # 确保 total_amount 是字符串类型
                model.seller_id = str("2088301194649043")  # 确保 seller_id 是字符串类型
                model.product_code = "QUICK_MSECURITY_PAY"
                model.body = "Iphone6 16G"
                model.subject = "iphone"
                model.out_trade_no = "201800000001201"
                
                # 打印每个字段的类型
                logger.info(f"total_amount type: {type(model.total_amount)}, value: {model.total_amount}")
                logger.info(f"body type: {type(model.body)}, value: {model.body}")
                logger.info(f"out_trade_no type: {type(model.out_trade_no)}, value: {model.out_trade_no}")
                logger.info(f"product_code type: {type(model.product_code)}, value: {model.product_code}")
                logger.info(f"seller_id type: {type(model.seller_id)}, value: {model.seller_id}")
                logger.info(f"subject type: {type(model.subject)}, value: {model.subject}")
                logger.info(f"timeout_express type: {type(model.timeout_express)}, value: {model.timeout_express}")
                
                # 创建APP支付请求
                logger.info(f"创建APP支付订单模型: {model.to_alipay_dict()}")

                # 获取模型的字典，并打印出 biz_content 字典的类型
                biz_content_dict = model.to_alipay_dict()
                logger.info(f"biz_content_dict: {json.dumps(biz_content_dict, ensure_ascii=False, sort_keys=True)}")
                logger.info(f"biz_content_dict type: {type(biz_content_dict)}")

                # 创建支付宝请求对象
                request_obj = AlipayTradeAppPayRequest(model)

                # 设置通知 URL
                request_obj.notify_url = self.current_config.get('notify_url', 'https://alipaytest.onrender.com/api/alipay/notify')
                logger.info(f"notify_url: {request_obj.notify_url}")

                # 打印请求参数
                params = request_obj.get_params()
                logger.info(f"请求参数: {json.dumps(params, ensure_ascii=False, sort_keys=True)}")
                
                # 执行请求，获取订单字符串
                try:
                    order_string = self.alipay_client.sdk_execute(request_obj)
                    logger.info(f"支付宝订单字符串: {order_string}")
                except Exception as e:
                    logger.error(f"支付宝SDK执行失败: {e}")
                    raise HTTPException(status_code=500, detail=f"支付宝SDK执行失败: {str(e)}")

                # 返回成功信息
                logger.info(f"APP支付订单创建成功，订单号: {payment_request.out_trade_no}")
                return {
                    "success": True,
                    "message": "APP订单创建成功",
                    "data": {
                        "out_trade_no": payment_request.out_trade_no,
                        "order_string": order_string,
                        "payment_type": "app"
                    }
                }

            except Exception as e:
                logger.error(f"创建APP支付订单失败: {e}")
                raise HTTPException(status_code=500, detail=f"创建APP支付订单失败: {str(e)}")


        
        @self.app.get("/payment/result", response_class=HTMLResponse)
        async def payment_result(request: Request):
            logger.info("[ROUTE] 进入 /payment/result 路由处理函数")
            query_params = dict(request.query_params)
            logger.info("=" * 60)
            logger.info("[PAYMENT_RESULT] 支付结果页面被访问 - /payment/result")
            logger.info(f"[PAYMENT_RESULT] 访问时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"[PAYMENT_RESULT] 客户端IP: {request.client.host if request.client else 'Unknown'}")
            logger.info(f"[PAYMENT_RESULT] User-Agent: {request.headers.get('user-agent', 'Unknown')}")
            logger.info(f"[PAYMENT_RESULT] 完整URL: {request.url}")
            logger.info(f"[PAYMENT_RESULT] 查询参数: {query_params}")
            
            # 解析支付宝返回的参数
            if query_params:
                logger.info("支付宝同步返回参数解析:")
                for key, value in query_params.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info("未收到任何查询参数")
            
            logger.info("[PAYMENT_RESULT] 准备返回HTML响应")
            logger.info("=" * 60)
            html_content = f"<html><body><h1>支付结果</h1><pre>{json.dumps(query_params, indent=2)}</pre></body></html>"
            logger.info("[PAYMENT_RESULT] HTML内容已生成，返回响应")
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
