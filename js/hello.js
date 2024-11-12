/*
* 脚本名称：HelloWorld Panel
* 功能：显示一些基本系统信息
* 使用方法：配合 Surge Panel 使用
*/

// 封装格式化时间的函数
function formatTime() {
    let now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0') + ':' + 
           now.getSeconds().toString().padStart(2, '0');
}

// 主函数
let hello = async () => {
    let panel = {}
    
    // 标题
    panel.title = 'Hello World'
    
    // 获取基本信息
    let time = formatTime()
    let hello = 'Hello Surge!'
    let device = $device.name
    let systemVersion = $device.systemVersion
    
    // 组装内容
    panel.content = `
时间：${time}
设备：${device}
系统：${systemVersion}
问候：${hello}
`
    panel.icon = 'paintbrush.fill'
    panel.backgroundColor = '#663399'
    
    $done(panel)
}

// 运行主函数
hello()
