let panel = {
    title: "My Public IP",
    content: "加载中...", // 初始显示内容
    icon: "network", // 网络图标
    "icon-color": "#007AFF"
};

// 从 Surge 的持久化存储中读取公共 IP 地址
let ip = $persistentStore.read("public_ip");

if (ip) {
    panel.content = `您的公共 IP 地址是：${ip}`;
} else {
    panel.content = "无法获取 IP 地址";
}

$done(panel);
