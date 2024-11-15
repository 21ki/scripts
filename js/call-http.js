// 配置请求 URL 和请求体数据
// https://george.betterde.com/technology/20230412.html
const url = "http://7b367ed3.proxy.webhookapp.com";
const requestData = {
  id: "surge-http",
  name: "surge",
  port: 6152,
  address: $network.v4.primaryAddress,
  check: {
    Name: "Surge HTTP proxy service check",
    TCP: $network.v4.primaryAddress + ":6152",
    Interval: "60s"
  }
};

// 使用 JSON 格式发送 POST 请求
$httpClient.post({
  url: url,
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(requestData)
}, function(error, response, data) {
  if (error) {
    // 将错误信息打印到 Surge 面板事件
    $notification.post("HTTP Request Failed", "Error Message:", error);
    $done(error);
  } else {
    // 将成功的请求状态和数据打印到 Surge 面板事件
    $notification.post("HTTP Request Success", `Status: ${response.status}`, `Response Data: ${data}`);
    $done({response});
  }
});
