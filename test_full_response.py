#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试支付宝完整响应验证接口
"""

import requests
import json
import time

# 服务器地址
BASE_URL = "http://localhost:8001"

def test_health_check():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_full_response_verification():
    """测试完整响应验证接口"""
    print("\n=== 测试完整响应验证接口 ===")
    
    # 用户提供的完整支付宝响应数据
    test_data = {
        "alipay_trade_app_pay_response": {
            "code": "10000",
            "msg": "Success",
            "app_id": "2021005194600693",
            "auth_app_id": "2021005194600693",
            "charset": "utf-8",
            "timestamp": "2025-09-23 17:31:55",
            "out_trade_no": "ID1758619906315",
            "total_amount": "0.01",
            "trade_no": "2025092322001413541402923238",
            "seller_id": "2088151008240524"
        },
        "sign": "CFfDiMDEByN4a+Mi07vMNosIEAD4UF4vPlOG+mZs8Hz7p0TWMQoyOu6SiaHL7YEMIjuN311MZYuGR5sQXCTD3FydVeG+Ba56LIiVvPNsXx6FgGVRWRqFmKHQYnS4XCoDfSY5mefpG+qD6ZdElaVzdLn+TFtnkLrxz4RGFw+gg6vTVCmX/4aXXrG6Cl8QflSbtbMpdkXBzbW9cV7pKo67L/b2/UJ14zo+6TpmTs1Z2YGdCrgkClVV5IGX793hq2iLCn/wyvSvh73+qSeesCcqCxt+/XtgmjT605LJnch+p0coUl8OQTmqb5iSRVh5VqPZ7owB1n7VfRQi0Pb8a7VEug==",
        "sign_type": "RSA2"
    }
    
    try:
        print("发送验证请求...")
        print(f"请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/alipay/verify_response",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 完整响应验证成功!")
                return True
            else:
                print(f"❌ 验证失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_invalid_response_code():
    """测试无效响应码"""
    print("\n=== 测试无效响应码 ===")
    
    test_data = {
        "alipay_trade_app_pay_response": {
            "code": "40004",  # 无效的响应码
            "msg": "Business Failed",
            "app_id": "2021005194600693",
            "out_trade_no": "TEST123",
            "total_amount": "0.01",
            "trade_no": "TEST_TRADE_NO"
        },
        "sign": "test_sign",
        "sign_type": "RSA2"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/alipay/verify_response",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if not result.get("success") and result.get("error_code") == "INVALID_RESPONSE_CODE":
            print("✅ 无效响应码检测正常!")
            return True
        else:
            print("❌ 无效响应码检测失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_missing_fields():
    """测试缺少必要字段"""
    print("\n=== 测试缺少必要字段 ===")
    
    test_data = {
        "alipay_trade_app_pay_response": {
            "code": "10000",
            "msg": "Success",
            # 缺少 out_trade_no, total_amount, trade_no
        },
        "sign": "test_sign",
        "sign_type": "RSA2"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/alipay/verify_response",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if not result.get("success") and result.get("error_code") == "MISSING_FIELD":
            print("✅ 缺少字段检测正常!")
            return True
        else:
            print("❌ 缺少字段检测失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试支付宝完整响应验证接口...")
    print("=" * 50)
    
    # 等待服务器启动
    time.sleep(2)
    
    tests = [
        ("健康检查", test_health_check),
        ("完整响应验证", test_full_response_verification),
        ("无效响应码", test_invalid_response_code),
        ("缺少必要字段", test_missing_fields),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
        
        print("-" * 30)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查日志")
    
    print("\n接口说明:")
    print("- /api/alipay/verify_response: 验证完整的支付宝响应数据")
    print("- 支持签名验证和API二次验证")
    print("- 提供详细的错误码和错误信息")
    print("- 确保支付数据的完整性和真实性")

if __name__ == "__main__":
    main()