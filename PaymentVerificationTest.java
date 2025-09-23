/**
 * 支付验证接口集成测试示例
 * 展示如何在Android应用中调用服务器端的支付验证接口
 */

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import org.json.*;

public class PaymentVerificationTest {
    
    private static final String SERVER_URL = "http://localhost:8001";
    
    /**
     * 测试支付验证接口调用
     */
    public static void testPaymentVerification() {
        System.out.println("=== 支付验证接口集成测试 ===\n");
        
        // 测试用例
        String[][] testCases = {
            {"TEST_ORDER_001", "0.01", "测试订单1"},
            {"TEST_ORDER_002", null, "测试订单2（无金额）"},
            {"REAL_ALIPAY_ORDER", "1.00", "真实支付宝订单"}
        };
        
        for (int i = 0; i < testCases.length; i++) {
            String outTradeNo = testCases[i][0];
            String totalAmount = testCases[i][1];
            String description = testCases[i][2];
            
            System.out.println("测试 " + (i + 1) + ": " + description);
            
            try {
                JSONObject result = callVerifyPaymentAPI(outTradeNo, totalAmount);
                System.out.println("响应: " + result.toString(2));
                
                boolean success = result.optBoolean("success", false);
                if (success) {
                    System.out.println("✅ 验证成功");
                    // 在实际应用中，这里可以继续处理成功逻辑
                    handlePaymentSuccess(result);
                } else {
                    System.out.println("❌ 验证失败: " + result.optString("message"));
                    // 在实际应用中，这里可以处理失败逻辑
                    handlePaymentFailure(result);
                }
                
            } catch (Exception e) {
                System.out.println("❌ 调用失败: " + e.getMessage());
            }
            
            System.out.println("-".repeat(50));
        }
        
        System.out.println("\n=== 集成说明 ===");
        System.out.println("1. 将此代码集成到ALIPAYCNUtils.java的sendPaymentSuccess方法中");
        System.out.println("2. 在支付成功后调用验证接口进行二次确认");
        System.out.println("3. 只有验证通过才向客户端返回成功状态");
        System.out.println("4. 确保网络请求在后台线程中执行");
    }
    
    /**
     * 调用支付验证API
     */
    private static JSONObject callVerifyPaymentAPI(String outTradeNo, String totalAmount) 
            throws IOException, JSONException {
        
        URL url = new URL(SERVER_URL + "/api/alipay/verify_payment");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            // 设置请求方法和头部
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            
            // 构建请求体
            JSONObject requestBody = new JSONObject();
            requestBody.put("out_trade_no", outTradeNo);
            if (totalAmount != null) {
                requestBody.put("total_amount", Double.parseDouble(totalAmount));
            }
            
            // 发送请求
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = requestBody.toString().getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
            // 读取响应
            int responseCode = conn.getResponseCode();
            InputStream inputStream = (responseCode >= 200 && responseCode < 300) 
                ? conn.getInputStream() 
                : conn.getErrorStream();
            
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
            }
            
            return new JSONObject(response.toString());
            
        } finally {
            conn.disconnect();
        }
    }
    
    /**
     * 处理支付验证成功
     */
    private static void handlePaymentSuccess(JSONObject result) {
        System.out.println("处理支付成功逻辑:");
        System.out.println("- 订单号: " + result.optString("out_trade_no"));
        System.out.println("- 支付宝交易号: " + result.optString("trade_no"));
        System.out.println("- 交易金额: " + result.optString("total_amount"));
        System.out.println("- 可以安全地向客户端返回成功状态");
    }
    
    /**
     * 处理支付验证失败
     */
    private static void handlePaymentFailure(JSONObject result) {
        System.out.println("处理支付失败逻辑:");
        System.out.println("- 错误码: " + result.optString("error_code"));
        System.out.println("- 错误信息: " + result.optString("message"));
        System.out.println("- 不应向客户端返回成功状态");
    }
    
    public static void main(String[] args) {
        testPaymentVerification();
    }
}