/**
 * 支付宝支付 H5 SDK
 * 提供支付宝支付相关功能
 */

class AlipayH5 {
    constructor(config = {}) {
        // 使用传入的配置或默认配置
        this.config = {
            app_id: config.app_id || '',
            private_key: config.private_key || '',
            alipay_public_key: config.alipay_public_key || '',
           //gateway: config.gateway || 'https://openapi-sandbox.dl.alipaydev.com/gateway.do',
            gateway:  'https://openapi-sandbox.dl.alipaydev.com/gateway.do',
            notify_url: config.notify_url || '',
            return_url: config.return_url || '',
            charset: 'UTF-8',
            sign_type: 'RSA2',
            version: '1.0',
            format: 'JSON'
        };
        
        // 验证配置
        this.validateConfig();
        
        console.log('支付宝H5支付实例初始化完成', this.config);
    }
    
    /**
     * 验证配置参数
     */
    validateConfig() {
        const requiredFields = ['app_id', 'private_key', 'gateway'];
        
        for (const field of requiredFields) {
            if (!this.config[field]) {
                console.warn(`缺少配置参数: ${field}，将使用默认值或跳过验证`);
            }
        }
        
        // 对于测试环境，允许部分参数为空
        if (this.config.app_id && this.config.private_key) {
            console.log('配置验证通过');
        } else {
            console.log('使用测试配置模式');
        }
    }
    
    /**
     * 创建支付订单（使用后端API）
     * @param {Object} orderInfo 订单信息
     * @returns {Promise} 支付结果
     */
    async createPayment(orderInfo) {
        try {
            // 准备订单数据
            const paymentRequest = {
                out_trade_no: orderInfo.out_trade_no || this.generateOrderNo(),
                total_amount: parseFloat(orderInfo.total_amount),
                subject: orderInfo.subject
            };
            
            console.log('发送支付请求到后端API:', paymentRequest);
            
            // 调用后端API创建订单
            const response = await fetch('/api/alipay/create_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(paymentRequest)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: '网络错误' }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('后端API响应:', result);
            
            if (result.success) {
                return {
                    success: true,
                    payment_url: result.data.pay_url,
                    order_no: result.data.out_trade_no,
                    order_string: result.data.order_string
                };
            } else {
                throw new Error(result.message || '创建订单失败');
            }
            
        } catch (error) {
            console.error('创建支付订单失败:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * 发起支付
     * @param {Object} orderInfo 订单信息
     */
    async pay(orderInfo) {
        const result = await this.createPayment(orderInfo);
        
        if (result.success) {
            // 在当前页面跳转到支付宝支付页面
            window.location.href = result.payment_url;
        } else {
            throw new Error(result.error || '支付创建失败');
        }
    }
    
    /**
     * 模拟支付（测试用）
     * @param {Object} orderInfo 订单信息
     */
    async mockPay(orderInfo) {
        return new Promise((resolve) => {
            setTimeout(() => {
                const success = Math.random() > 0.2; // 80% 成功率
                resolve({
                    success: success,
                    order_no: orderInfo.out_trade_no || this.generateOrderNo(),
                    trade_no: 'MOCK_' + Date.now(),
                    total_amount: orderInfo.total_amount,
                    message: success ? '支付成功' : '支付失败'
                });
            }, 2000);
        });
    }
    
    /**
     * 生成订单号
     */
    generateOrderNo() {
        const timestamp = Date.now();
        const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
        return `ORDER_${timestamp}_${random}`;
    }
    
    /**
     * 获取时间戳
     */
    getTimestamp() {
        return new Date().toISOString().replace(/T/, ' ').replace(/\..+/, '');
    }
    
    /**
     * 生成签名
     * @param {Object} params 参数对象
     */
    generateSign(params) {
        // 注意：这里是简化版本，实际项目中需要使用真实的RSA签名
        // 在生产环境中，签名应该在服务端完成
        
        if (!this.config.private_key) {
            console.warn('缺少私钥，使用模拟签名');
            return 'MOCK_SIGNATURE_' + Date.now();
        }
        
        // 排序参数
        const sortedParams = Object.keys(params)
            .filter(key => key !== 'sign' && params[key])
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        
        // 这里应该使用RSA私钥签名，当前返回模拟签名
        return 'RSA2_SIGNATURE_' + btoa(sortedParams).substring(0, 32);
    }
    
    /**
     * 构建支付URL
     * @param {Object} params 参数对象
     */
    buildPaymentUrl(params) {
        const queryString = Object.keys(params)
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
            .join('&');
        
        return `${this.config.gateway}?${queryString}`;
    }
    
    /**
     * 验证支付结果
     * @param {Object} result 支付结果
     */
    verifyPaymentResult(result) {
        // 这里应该验证支付宝返回的签名
        // 在实际项目中，验证应该在服务端完成
        return true;
    }
}

// 导出类
window.AlipayH5 = AlipayH5;