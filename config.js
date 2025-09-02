/**
 * 支付宝支付配置文件
 * 请根据您的实际情况修改以下配置
 */

// 支付宝配置
const ALIPAY_CONFIG = {
    // 应用ID - 必填
    // 在支付宝开放平台创建应用后获得
    app_id: '', // 请替换为您的真实应用ID
    
    // 商户私钥 - 必填
    // 用于签名，请妥善保管，不要泄露
    // 注意：在生产环境中，私钥应该保存在服务端，不应该暴露在前端
    private_key: `-----BEGIN RSA PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9
-----END RSA PRIVATE KEY-----`,
    
    // 支付宝公钥 - 必填
    // 用于验证支付宝返回的数据
    alipay_public_key: `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ
-----END PUBLIC KEY-----`,
    
    // 支付宝网关地址
    // gateway: 'https://openapi.alipay.com/gateway.do', // 正式环境
     gateway: 'https://openapi-sandbox.dl.alipaydev.com/gateway.do', // 沙箱环境
    
    // 异步通知地址 - 可选
    // 支付完成后，支付宝会向这个地址发送支付结果
    notify_url: 'https://alipaytest.onrender.com/api/alipay/notify',
    
    // 同步返回地址 - 可选
    // 支付完成后，用户会被重定向到这个地址
    return_url: 'https://alipaytest.onrender.com/payment/result',
    
    // 字符编码
    charset: 'UTF-8',
    
    // 签名类型
    sign_type: 'RSA2',
    
    // 数据格式
    format: 'JSON',
    
    // 接口版本
    version: '1.0'
};

// 开发环境配置（用于测试）
const ALIPAY_CONFIG_DEV = {
    app_id: '2021000000000000', // 沙箱应用ID
    private_key: `-----BEGIN RSA PRIVATE KEY-----
// 沙箱环境私钥
-----END RSA PRIVATE KEY-----`,
    alipay_public_key: `-----BEGIN PUBLIC KEY-----
// 沙箱环境支付宝公钥
-----END PUBLIC KEY-----`,
    gateway: 'https://openapi-sandbox.dl.alipaydev.com/gateway.do', // 沙箱网关
    notify_url: 'https://alipaytest.onrender.com/api/alipay/notify',
    return_url: 'https://alipaytest.onrender.com/payment/result',
    charset: 'UTF-8',
    sign_type: 'RSA2',
    format: 'JSON',
    version: '1.0'
};

// 根据环境选择配置
// 您可以通过修改这里来切换正式环境和沙箱环境
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// 导出配置（当前使用开发配置作为示例）
window.ALIPAY_CONFIG = isDevelopment ? ALIPAY_CONFIG_DEV : ALIPAY_CONFIG;

// 配置验证函数
function validateConfig(config) {
    const required = ['app_id', 'private_key', 'alipay_public_key'];
    const missing = required.filter(key => !config[key] || config[key].includes('请替换'));
    
    if (missing.length > 0) {
        console.warn('⚠️ 支付宝配置不完整，缺少以下参数:', missing);
        console.warn('请在 config.js 文件中配置正确的参数');
        return false;
    }
    
    return true;
}

// 页面加载时验证配置
document.addEventListener('DOMContentLoaded', function() {
    if (!validateConfig(window.ALIPAY_CONFIG)) {
        // 显示配置提示
        const notice = document.createElement('div');
        notice.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff3cd;
            color: #856404;
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid #ffeaa7;
            z-index: 10000;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        `;
        notice.innerHTML = '⚠️ 请先在 config.js 中配置支付宝参数';
        document.body.appendChild(notice);
        
        // 3秒后自动隐藏
        setTimeout(() => {
            if (notice.parentNode) {
                notice.parentNode.removeChild(notice);
            }
        }, 5000);
    }
});

/**
 * 配置说明：
 * 
 * 1. app_id: 支付宝应用ID
 *    - 登录支付宝开放平台 (https://open.alipay.com/)
 *    - 创建应用并获取应用ID
 * 
 * 2. private_key: 应用私钥
 *    - 使用支付宝提供的密钥生成工具生成RSA2密钥对
 *    - 私钥用于签名，请妥善保管
 * 
 * 3. alipay_public_key: 支付宝公钥
 *    - 在支付宝开放平台应用详情页面获取
 *    - 用于验证支付宝返回的数据
 * 
 * 4. notify_url: 异步通知地址
 *    - 支付完成后支付宝会POST支付结果到此地址
 *    - 必须是公网可访问的HTTPS地址
 * 
 * 5. return_url: 同步返回地址
 *    - 支付完成后用户浏览器会跳转到此地址
 *    - 可以是HTTP或HTTPS地址
 * 
 * 安全提示：
 * - 私钥不应该暴露在前端代码中
 * - 在生产环境中，建议将签名逻辑放在服务端
 * - 本示例仅用于演示，实际使用时请注意安全性
 */