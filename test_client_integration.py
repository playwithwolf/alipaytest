#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端集成测试脚本
测试修改后的客户端代码是否能正确传递完整的支付宝响应数据
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://localhost:8001"

def test_health_check():
    """测试服务器健康检查"""
    print("=== 测试服务器健康检查 ===")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"健康检查响应: {response.status_code}")
        print(f"响应内容: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_verify_response_with_complete_data():
    """测试使用完整支付宝响应数据的验证接口"""
    print("\n=== 测试完整响应验证接口 ===")
    
    # 模拟客户端传递的完整支付宝响应数据
    # 这是客户端从支付宝SDK获得的完整响应
    complete_response_data = {
        "resultStatus": "9000",
        "result": {
            "alipay_trade_app_pay_response": {
                "code": "10000",
                "msg": "Success",
                "app_id": "9021000140690016",
                "out_trade_no": "TEST_ORDER_20241220_001",
                "trade_no": "2024122022001234567890123456",
                "total_amount": "0.01",
                "seller_id": "2088721034567890",
                "charset": "utf-8",
                "timestamp": "2024-12-20 15:30:45"
            },
            "sign": "mock_signature_for_testing_purposes_only",
            "sign_type": "RSA2"
        },
        "memo": "处理成功"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/alipay/verify_response",
            json=complete_response_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"验证响应状态码: {response.status_code}")
        print(f"验证响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 完整响应验证测试通过")
                return True
            else:
                print(f"❌ 验证失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_verify_response_with_url_encoded_format():
    """测试URL编码格式的支付宝响应数据"""
    print("\n=== 测试URL编码格式响应验证 ===")
    
    # 模拟客户端传递的URL编码格式数据（支付宝SDK的原始返回格式）
    url_encoded_data = {
        "resultStatus": "9000",
        "result": '{"alipay_trade_app_pay_response":{"code":"10000","msg":"Success","app_id":"9021000140690016","out_trade_no":"TEST_ORDER_20241220_002","trade_no":"2024122022001234567890123457","total_amount":"0.01","seller_id":"2088721034567890","charset":"utf-8","timestamp":"2024-12-20 15:35:45"},"sign":"mock_signature_for_testing_purposes_only","sign_type":"RSA2"}',
        "memo": "处理成功"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/alipay/verify_response",
            json=url_encoded_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"验证响应状态码: {response.status_code}")
        print(f"验证响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ URL编码格式验证测试通过")
                return True
            else:
                print(f"❌ 验证失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_invalid_response_data():
    """测试无效响应数据"""
    print("\n=== 测试无效响应数据 ===")
    
    invalid_data = {
        "resultStatus": "6001",  # 用户取消
        "result": "",
        "memo": "用户中途取消"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/alipay/verify_response",
            json=invalid_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"验证响应状态码: {response.status_code}")
        print(f"验证响应内容: {response.text}")
        
        if response.status_code == 400:
            print("✅ 无效数据正确被拒绝")
            return True
        else:
            print(f"❌ 预期400错误，但得到: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始客户端集成测试...")
    print("=" * 50)
    
    # 等待服务器启动
    time.sleep(2)
    
    test_results = []
    
    # 执行测试
    test_results.append(("服务器健康检查", test_health_check()))
    test_results.append(("完整响应验证", test_verify_response_with_complete_data()))
    test_results.append(("URL编码格式验证", test_verify_response_with_url_encoded_format()))
    test_results.append(("无效数据处理", test_invalid_response_data()))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！客户端集成成功！")
    else:
        print("⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()