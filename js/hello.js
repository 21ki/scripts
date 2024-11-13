// 创建面板
let panel = {
    title: "My Public IP",
    content: "加载中...", // 初始显示内容
    icon: "network", // 网络图标
    "icon-color": "#007AFF"
};

// 使用外部服务获取公共 IP 地址
$http.get("https://api.ipify.org?format=json").then(response => {
    if (response.status === 200) {
        // 更新面板的内容为获取到的 IP 地址
        panel.content = `您的公共 IP 地址是：${response.body.ip}`;
    } else {
        panel.content = "无法获取 IP 地址";
    }
    $done(panel);
}).catch(error => {
    panel.content = "请求失败";
    $done(panel);
});
