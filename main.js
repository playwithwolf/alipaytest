/**
 * 主要的页面逻辑
 */

// 全局变量
let alipayInstance = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    
    // 初始化配置管理
    initConfigManager();
    
    // 加载保存的配置
    loadSavedConfig();
});

/**
 * 初始化页面
 */
function initializePage() {
    // 检查配置
    if (typeof ALIPAY_CONFIG === 'undefined') {
        showError('配置文件未加载，请检查 config.js 文件');
        return;
    }
    
    // 初始化支付宝实例
    try {
        alipayInstance = new AlipayH5(ALIPAY_CONFIG);
        console.log('支付宝SDK初始化成功');
    } catch (error) {
        showError('支付宝SDK初始化失败: ' + error.message);
        return;
    }
    
    // 绑定事件
    bindEvents();
    
    // 检查URL参数（支付返回）
    checkPaymentReturn();
}

/**
 * 绑定页面事件
 */
function bindEvents() {
    // 支付按钮
    const payBtn = document.getElementById('payBtn');
    if (payBtn) {
        payBtn.addEventListener('click', handlePayment);
    }
    

    
    // 支付方式选择
    const paymentOptions = document.querySelectorAll('.payment-option');
    paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
            // 移除其他选中状态
            paymentOptions.forEach(opt => opt.classList.remove('selected'));
            // 添加当前选中状态
            this.classList.add('selected');
        });
    });
    
    // 金额输入验证
    const amountInput = document.getElementById('orderAmount');
    if (amountInput) {
        amountInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (isNaN(value) || value <= 0) {
                this.setCustomValidity('请输入有效的金额');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // 配置相关事件
     const toggleConfig = document.getElementById('toggleConfig');
     if (toggleConfig) {
         toggleConfig.addEventListener('click', toggleConfigForm);
     }
     
     const saveConfigBtn = document.getElementById('saveConfig');
     if (saveConfigBtn) {
         saveConfigBtn.addEventListener('click', saveConfig);
     }
     
     const loadConfigBtn = document.getElementById('loadConfig');
     if (loadConfigBtn) {
         loadConfigBtn.addEventListener('click', loadConfig);
     }
     
     const clearConfigBtn = document.getElementById('clearConfig');
     if (clearConfigBtn) {
         clearConfigBtn.addEventListener('click', clearConfig);
     }
}

/**
 * 处理支付
 */
async function handlePayment() {
    try {
        // 获取订单信息
        const orderInfo = getOrderInfo();
        
        // 验证订单信息
        if (!validateOrderInfo(orderInfo)) {
            return;
        }
        
        // 获取动态配置
        const config = getCurrentConfig();
        if (!config) {
            showError('请先配置支付宝参数');
            return;
        }
        
        // 获取支付类型
        const paymentType = document.getElementById('payment_type')?.value || 'h5';
        
        // 显示加载状态
        showLoading(`正在创建${paymentType.toUpperCase()}支付订单...`);
        
        // 创建支付宝实例并发起支付
        const alipayInstance = new AlipayH5(config);
        
        let result;
        if (paymentType === 'app') {
            // 创建APP支付订单
            result = await alipayInstance.createAppPayment(orderInfo);
        } else {
            // 创建H5支付订单
            result = await alipayInstance.createH5Payment(orderInfo);
        }
        
        hideLoading();
        
        if (result.success) {
            if (paymentType === 'app') {
                // APP支付：显示订单字符串供客户端使用
                showAppPaymentResult(result);
            } else {
                // H5支付：跳转到支付页面
                window.location.href = result.payment_url;
            }
        } else {
            showError('支付订单创建失败: ' + result.error);
        }
        
    } catch (error) {
        hideLoading();
        showError('支付失败: ' + error.message);
    }
}



/**
 * 获取订单信息
 */
function getOrderInfo() {
    const subjectElement = document.getElementById('subject');
    const amountElement = document.getElementById('amount');
    const outTradeNoElement = document.getElementById('out_trade_no');
    
    if (!subjectElement || !amountElement) {
        throw new Error('找不到必要的表单元素');
    }
    
    const orderName = subjectElement.value.trim();
    const orderAmount = amountElement.value;
    const orderDesc = orderName; // 使用商品名称作为描述
    
    return {
        subject: orderName,
        total_amount: orderAmount,
        body: orderDesc,
        out_trade_no: null // 将自动生成
    };
}

/**
 * 验证订单信息
 */
function validateOrderInfo(orderInfo) {
    if (!orderInfo.subject) {
        showError('请输入商品名称');
        return false;
    }
    
    const amount = parseFloat(orderInfo.total_amount);
    if (isNaN(amount) || amount <= 0) {
        showError('请输入有效的支付金额');
        return false;
    }
    
    if (amount < 0.01) {
        showError('支付金额不能少于0.01元');
        return false;
    }
    
    return true;
}

/**
 * 检查支付返回
 */
function checkPaymentReturn() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // 检查是否有支付返回参数
    if (urlParams.has('out_trade_no')) {
        const result = {
            success: urlParams.get('trade_status') === 'TRADE_SUCCESS',
            order_no: urlParams.get('out_trade_no'),
            trade_no: urlParams.get('trade_no'),
            total_amount: urlParams.get('total_amount'),
            message: urlParams.get('trade_status') === 'TRADE_SUCCESS' ? '支付成功' : '支付失败'
        };
        
        showPaymentResult(result);
        
        // 清理URL参数
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

/**
 * 显示支付结果
 */
function showPaymentResult(result) {
    const resultArea = document.getElementById('resultArea');
    const resultContent = document.getElementById('resultContent');
    
    if (!resultArea || !resultContent) return;
    
    const statusClass = result.success ? 'success' : 'error';
    const statusText = result.success ? '支付成功' : '支付失败';
    
    resultContent.innerHTML = `
        <div class="result-item ${statusClass}">
            <div class="result-status">${statusText}</div>
            <div class="result-details">
                <p><strong>订单号:</strong> ${result.order_no || 'N/A'}</p>
                <p><strong>交易号:</strong> ${result.trade_no || 'N/A'}</p>
                <p><strong>支付金额:</strong> ¥${result.total_amount || 'N/A'}</p>
                <p><strong>状态信息:</strong> ${result.message || 'N/A'}</p>
            </div>
        </div>
    `;
    
    resultArea.style.display = 'block';
    resultArea.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 显示APP支付结果
 */
function showAppPaymentResult(result) {
    const resultDiv = document.createElement('div');
    resultDiv.className = 'app-payment-result';
    resultDiv.innerHTML = `
        <h3>📱 APP支付订单创建成功</h3>
        <div class="result-content">
            <p><strong>订单号:</strong> ${result.order_no}</p>
            <p><strong>支付类型:</strong> APP支付</p>
            <div class="order-string-section">
                <p><strong>订单字符串:</strong></p>
                <textarea id="orderStringText" readonly style="width: 100%; height: 120px; font-family: monospace; font-size: 12px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">${result.order_string}</textarea>
                <div style="margin-top: 10px;">
                    <button onclick="copyOrderString()" style="background: #1890ff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">复制订单字符串</button>
                    <button onclick="downloadOrderString()" style="background: #52c41a; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: 8px;">下载为文件</button>
                </div>
            </div>
            <div class="usage-info" style="margin-top: 15px; padding: 10px; background: #f6f8fa; border-radius: 4px;">
                <h4>📋 使用说明：</h4>
                <ul style="margin: 8px 0; padding-left: 20px; font-size: 14px;">
                    <li>将订单字符串传递给移动端APP</li>
                    <li>在APP中调用支付宝SDK进行支付</li>
                    <li>支付完成后会收到异步通知</li>
                </ul>
            </div>
        </div>
        <button onclick="this.parentElement.remove()" style="margin-top: 15px; background: #f5f5f5; border: 1px solid #d9d9d9; padding: 8px 16px; border-radius: 4px; cursor: pointer;">关闭</button>
    `;
    
    // 添加样式
    resultDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 1000;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    document.body.appendChild(resultDiv);
}

/**
 * 复制订单字符串
 */
function copyOrderString() {
    const textarea = document.getElementById('orderStringText');
    if (textarea) {
        textarea.select();
        document.execCommand('copy');
        showSuccess('订单字符串已复制到剪贴板');
    }
}

/**
 * 下载订单字符串为文件
 */
function downloadOrderString() {
    const textarea = document.getElementById('orderStringText');
    if (textarea) {
        const content = textarea.value;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `alipay_order_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showSuccess('订单字符串文件已下载');
    }
}

/**
 * 显示加载状态
 */
function showLoading(message = '处理中...') {
    // 创建或更新加载提示
    let loadingEl = document.getElementById('loadingOverlay');
    if (!loadingEl) {
        loadingEl = document.createElement('div');
        loadingEl.id = 'loadingOverlay';
        loadingEl.className = 'loading-overlay';
        document.body.appendChild(loadingEl);
    }
    
    loadingEl.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;
    
    loadingEl.style.display = 'flex';
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const loadingEl = document.getElementById('loadingOverlay');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

/**
 * 显示错误信息
 */
function showError(message) {
    alert('错误: ' + message);
    console.error('支付错误:', message);
}

/**
 * 显示成功信息
 */
function showSuccess(message) {
    alert('成功: ' + message);
    console.log('支付成功:', message);
}

/**
 * 格式化金额
 */
function formatAmount(amount) {
    return parseFloat(amount).toFixed(2);
}

/**
 * 复制文本到剪贴板
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('已复制到剪贴板');
        }).catch(err => {
            console.error('复制失败:', err);
        });
    } else {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showSuccess('已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
        }
        document.body.removeChild(textArea);
    }
}

/**
 * 初始化配置管理
 */
function initConfigManager() {
    console.log('配置管理器初始化完成');
}

/**
 * 切换配置表单显示/隐藏
 */
function toggleConfigForm() {
    const configForm = document.getElementById('configForm');
    if (configForm) {
        const isVisible = configForm.style.display !== 'none';
        configForm.style.display = isVisible ? 'none' : 'block';
        
        const toggleBtn = document.getElementById('toggleConfig');
        if (toggleBtn) {
            toggleBtn.textContent = isVisible ? '显示配置' : '隐藏配置';
        }
    }
}

/**
 * 保存配置到localStorage
 */
function saveConfig() {
     try {
         const privateKeyValue = document.getElementById('private_key')?.value || '';
         const publicKeyValue = document.getElementById('alipay_public_key')?.value || '';
         
         const config = {
             app_id: document.getElementById('app_id')?.value || '',
             private_key: formatPrivateKey(privateKeyValue),
             alipay_public_key: formatPublicKey(publicKeyValue),
             gateway: document.getElementById('gateway')?.value || '',
             return_url: document.getElementById('return_url')?.value || '',
             notify_url: document.getElementById('notify_url')?.value || ''
         };
        
        localStorage.setItem('alipay_config', JSON.stringify(config));
        showSuccess('配置保存成功');
    } catch (error) {
        showError('配置保存失败: ' + error.message);
    }
}

/**
 * 从localStorage加载配置
 */
function loadSavedConfig() {
     try {
         const savedConfig = localStorage.getItem('alipay_config');
         if (savedConfig) {
             const config = JSON.parse(savedConfig);
             
             if (document.getElementById('app_id')) document.getElementById('app_id').value = config.app_id || '';
             if (document.getElementById('private_key')) document.getElementById('private_key').value = extractKeyContent(config.private_key || '');
             if (document.getElementById('alipay_public_key')) document.getElementById('alipay_public_key').value = extractKeyContent(config.alipay_public_key || '');
             if (document.getElementById('gateway')) document.getElementById('gateway').value = config.gateway || '';
             if (document.getElementById('return_url')) document.getElementById('return_url').value = config.return_url || '';
             if (document.getElementById('notify_url')) document.getElementById('notify_url').value = config.notify_url || '';
            
            console.log('已加载保存的配置');
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

/**
 * 手动加载配置
 */
function loadConfig() {
    loadSavedConfig();
    showSuccess('配置加载成功');
}

/**
 * 清空配置
 */
function clearConfig() {
     try {
         localStorage.removeItem('alipay_config');
         
         // 清空表单
         if (document.getElementById('app_id')) document.getElementById('app_id').value = '';
         if (document.getElementById('private_key')) document.getElementById('private_key').value = '';
         if (document.getElementById('alipay_public_key')) document.getElementById('alipay_public_key').value = '';
         if (document.getElementById('gateway')) document.getElementById('gateway').value = '';
         if (document.getElementById('return_url')) document.getElementById('return_url').value = '';
         if (document.getElementById('notify_url')) document.getElementById('notify_url').value = '';
        
        showSuccess('配置清空成功');
    } catch (error) {
        showError('配置清空失败: ' + error.message);
    }
}

/**
 * 获取当前配置
 */
function getCurrentConfig() {
     try {
         const privateKeyValue = document.getElementById('private_key')?.value || '';
         const publicKeyValue = document.getElementById('alipay_public_key')?.value || '';
         
         const config = {
             app_id: document.getElementById('app_id')?.value || '',
             private_key: formatPrivateKey(privateKeyValue),
             alipay_public_key: formatPublicKey(publicKeyValue),
             gateway: document.getElementById('gateway')?.value || '',
             return_url: document.getElementById('return_url')?.value || '',
             notify_url: document.getElementById('notify_url')?.value || ''
         };
         
         // 检查必要参数
         if (!config.app_id || !config.private_key) {
             return null;
         }
        
        return config;
    } catch (error) {
        console.error('获取配置失败:', error);
        return null;
    }
}

/**
 * 格式化私钥，自动添加BEGIN和END标记
 */
function formatPrivateKey(key) {
    if (!key) return '';
    
    // 如果已经包含BEGIN和END标记，直接返回
    if (key.includes('-----BEGIN RSA PRIVATE KEY-----')) {
        return key;
    }
    
    // 清理输入的密钥内容
    const cleanKey = key.replace(/\s+/g, '\n').trim();
    
    return `-----BEGIN RSA PRIVATE KEY-----\n${cleanKey}\n-----END RSA PRIVATE KEY-----`;
}

/**
 * 格式化公钥，自动添加BEGIN和END标记
 */
function formatPublicKey(key) {
    if (!key) return '';
    
    // 如果已经包含BEGIN和END标记，直接返回
    if (key.includes('-----BEGIN PUBLIC KEY-----')) {
        return key;
    }
    
    // 清理输入的密钥内容
    const cleanKey = key.replace(/\s+/g, '\n').trim();
    
    return `-----BEGIN PUBLIC KEY-----\n${cleanKey}\n-----END PUBLIC KEY-----`;
}

/**
 * 提取密钥内容，去除BEGIN和END标记
 */
function extractKeyContent(key) {
    if (!key) return '';
    
    // 移除BEGIN和END标记以及换行符
    return key
        .replace(/-----BEGIN [A-Z ]+-----/g, '')
        .replace(/-----END [A-Z ]+-----/g, '')
        .replace(/\n/g, ' ')
        .trim();
}

/**
 * 获取默认配置
 */
function getDefaultConfig() {
     return {
         app_id: 'test_app_id',
         private_key: 'test_private_key',
         alipay_public_key: 'test_public_key',
         gateway: 'https://openapi.alipaydev.com/gateway.do',
         return_url: window.location.href,
         notify_url: ''
     };
 }