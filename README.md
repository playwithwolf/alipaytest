# 支付宝H5支付 - Python FastAPI版本

这是一个基于Python FastAPI框架的支付宝H5支付演示项目，提供了完整的支付宝支付功能和动态配置管理。

## 功能特性

- ✅ **支付宝H5支付集成** - 完整的支付宝手机网站支付功能
- ✅ **支付宝APP支付集成** - 完整的支付宝移动应用支付功能
- ✅ **FastAPI后端服务** - 高性能的Python异步Web框架
- ✅ **双支付模式支持** - 同时支持H5网页支付和APP移动支付
- ✅ **动态配置管理** - 支持在线配置支付宝参数，无需重启服务
- ✅ **配置持久化** - 配置自动保存到本地存储
- ✅ **支付结果处理** - 支持同步返回和异步通知
- ✅ **现代化UI界面** - 响应式设计，支持移动端
- ✅ **安全特性** - 敏感信息过滤，配置验证
- ✅ **开发友好** - 详细的日志记录和错误处理

## 技术栈

- **后端**: Python 3.8+ + FastAPI + Uvicorn
- **前端**: HTML5 + CSS3 + JavaScript (ES6+)
- **支付**: 支付宝开放平台 SDK
- **依赖管理**: pip + requirements.txt

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 2. 安装依赖

```bash
# 进入项目目录
cd h5python

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 启动FastAPI服务器
python server.py

# 或者使用uvicorn直接启动
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问应用

打开浏览器访问: http://localhost:8000

## 配置说明

### 支付宝配置参数

在页面上可以动态配置以下参数：

| 参数名称 | 说明 | 是否必填 |
|---------|------|----------|
| app_id | 支付宝应用ID | 是 |
| private_key | 应用私钥 | 是 |
| alipay_public_key | 支付宝公钥 | 是 |
| gateway | 支付宝网关地址 | 是 |
| notify_url | 异步通知地址 | 否 |
| return_url | 同步返回地址 | 否 |

### 获取支付宝配置

1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 创建应用并获取 `app_id`
3. 生成RSA2密钥对，获取应用私钥和支付宝公钥
4. 配置应用网关和回调地址

### 环境配置

- **沙箱环境**: `https://openapi.alipaydev.com/gateway.do`
- **正式环境**: `https://openapi.alipay.com/gateway.do`

## 动态配置功能

### 配置管理

- **保存配置**: 将当前配置保存到浏览器本地存储
- **加载配置**: 从本地存储加载之前保存的配置
- **清空配置**: 清除所有配置信息
- **配置验证**: 自动验证配置参数的完整性

### 配置安全

- 敏感信息（私钥、公钥）在API返回时会被过滤
- 配置仅存储在浏览器本地，不会上传到服务器
- 支持配置的实时验证和错误提示

## API接口

### 配置管理接口

#### 保存配置
```http
POST /api/config
Content-Type: application/json

{
  "app_id": "your_app_id",
  "private_key": "your_private_key",
  "alipay_public_key": "your_alipay_public_key",
  "gateway": "https://openapi.alipaydev.com/gateway.do",
  "notify_url": "https://your-domain.com/api/alipay/notify",
  "return_url": "https://your-domain.com/payment/result"
}
```

#### 加载配置
```http
GET /api/config
```

### 支付接口

#### 创建H5支付订单
```http
POST /api/alipay/create_order
Content-Type: application/json

{
  "subject": "商品名称",
  "total_amount": "0.01",
  "out_trade_no": "20240101123456"
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "H5支付订单创建成功",
  "payment_url": "https://openapi.alipaydev.com/gateway.do?...",
  "payment_type": "h5",
  "out_trade_no": "20240101123456"
}
```

#### 创建APP支付订单
```http
POST /api/alipay/create_app_order
Content-Type: application/json

{
  "subject": "商品名称",
  "total_amount": "0.01",
  "out_trade_no": "20240101123456"
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "APP支付订单创建成功",
  "order_string": "alipay_sdk=alipay-sdk-java-4.38.10.ALL&app_id=2021000...",
  "payment_type": "app",
  "out_trade_no": "20240101123456"
}
```

#### 异步通知回调
```http
POST /api/alipay/notify
Content-Type: application/x-www-form-urlencoded
```

**说明**: 支付宝服务器会在支付完成后向此接口发送异步通知，用于确认支付结果。

**重要参数**:
- `out_trade_no`: 商户订单号
- `trade_no`: 支付宝交易号
- `trade_status`: 交易状态（TRADE_SUCCESS=支付成功，TRADE_FINISHED=交易完成）
- `total_amount`: 交易金额
- `subject`: 商品名称
- `sign`: 签名
- `sign_type`: 签名类型（通常为RSA2）

**响应格式**:
- 验证成功且处理完成: 返回 `success`
- 验证失败或处理异常: 返回 `fail`

**Postman测试示例**:
```
POST http://localhost:8000/api/alipay/notify
Content-Type: application/x-www-form-urlencoded

out_trade_no=TEST_ORDER_123&trade_no=2024012212345678901&trade_status=TRADE_SUCCESS&total_amount=0.01&subject=测试商品&app_id=your_app_id&sign=mock_signature&sign_type=RSA2
```

**注意事项**:
1. 异步通知同时适用于H5支付和APP支付
2. 系统会验证支付宝的签名确保通知真实性
3. 只有返回`success`，支付宝才会停止重复通知
4. 建议在生产环境中添加幂等性处理，避免重复处理同一笔订单

### 其他接口

#### 健康检查
```http
GET /health
```

## 项目结构

```
h5python/
├── server.py              # FastAPI服务器主文件
├── requirements.txt       # Python依赖文件
├── README.md             # 项目说明文档
├── index.html            # 主页面
├── styles.css            # 样式文件
├── main.js               # 主要JavaScript逻辑
├── alipay.js             # 支付宝SDK封装
└── config.js             # 配置文件
```

## 使用说明

### H5支付使用

1. **网页端使用**:
   - 访问 `http://localhost:8000`
   - 选择支付类型为 "H5支付"
   - 填写订单信息并点击支付
   - 系统会跳转到支付宝支付页面

2. **API调用**:
   ```javascript
   // 创建H5支付订单
   const response = await fetch('/api/alipay/create_order', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       subject: '测试商品',
       total_amount: '0.01',
       out_trade_no: 'ORDER_' + Date.now()
     })
   });
   
   const result = await response.json();
   if (result.success) {
     // 跳转到支付页面
     window.location.href = result.payment_url;
   }
   ```

### APP支付使用

1. **网页端测试**:
   - 访问 `http://localhost:8000`
   - 选择支付类型为 "APP支付"
   - 填写订单信息并点击支付
   - 系统会显示订单字符串，可复制或下载

2. **移动应用集成**:
   ```javascript
   // 创建APP支付订单
   const response = await fetch('/api/alipay/create_app_order', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       subject: '测试商品',
       total_amount: '0.01',
       out_trade_no: 'ORDER_' + Date.now()
     })
   });
   
   const result = await response.json();
   if (result.success) {
     // 将订单字符串传递给移动端SDK
     const orderString = result.order_string;
     // 调用移动端支付宝SDK
     // Android: AlipayAPI.pay(orderString)
     // iOS: [[AlipaySDK defaultService] payOrder:orderString]
   }
   ```

3. **UniApp集成示例**:
   ```javascript
   // UniApp中使用APP支付
   uni.request({
     url: 'http://your-server.com/api/alipay/create_app_order',
     method: 'POST',
     data: {
       subject: '测试商品',
       total_amount: '0.01',
       out_trade_no: 'ORDER_' + Date.now()
     },
     success: (res) => {
       if (res.data.success) {
         // 调用支付宝支付
         uni.requestPayment({
           provider: 'alipay',
           orderInfo: res.data.order_string,
           success: (payRes) => {
             console.log('支付成功', payRes);
           },
           fail: (err) => {
             console.log('支付失败', err);
           }
         });
       }
     }
   });
   ```

### 支付类型选择

- **H5支付**: 适用于手机浏览器、微信内置浏览器等网页环境
- **APP支付**: 适用于原生移动应用、UniApp、React Native等移动应用环境

系统会根据选择的支付类型调用对应的API接口，并返回相应的支付信息。

## 开发说明

### 本地开发

1. 修改代码后，FastAPI会自动重载（使用 `--reload` 参数）
2. 前端文件修改后直接刷新浏览器即可
3. 查看控制台日志了解运行状态

### 部署说明

1. **生产环境部署**:
   ```bash
   # 使用gunicorn部署
   pip install gunicorn
   gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Docker部署**:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

### 安全注意事项

1. **私钥安全**: 生产环境中不要将私钥暴露在前端代码中
2. **HTTPS**: 生产环境必须使用HTTPS协议
3. **域名配置**: 确保回调地址域名已在支付宝后台配置
4. **签名验证**: 生产环境中必须验证支付宝返回的签名

## 常见问题

### Q: 支付时提示"系统繁忙"？
A: 检查支付宝配置参数是否正确，特别是app_id和网关地址。

### Q: 异步通知收不到？
A: 确保notify_url是公网可访问的HTTPS地址，且已在支付宝后台配置。

### Q: 签名验证失败？
A: 检查私钥格式是否正确，确保使用的是RSA2格式的密钥。

### Q: 页面样式异常？
A: 检查CSS文件是否正确加载，确保静态文件路径配置正确。

## 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 初始版本发布
- ✅ 支持支付宝H5支付
- ✅ 动态配置管理
- ✅ FastAPI后端服务
- ✅ 现代化UI界面

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**注意**: 本项目仅用于学习和演示目的，生产环境使用前请确保安全性配置。