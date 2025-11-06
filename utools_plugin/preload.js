// uTools 插件预加载脚本
window.utools.onPluginReady(() => {
    console.log('商圈查找插件已加载');
    
    // 暴露文件操作函数给主窗口
    if (typeof require !== 'undefined') {
        try {
            const fs = require('fs');
            const path = require('path');
            const os = require('os');
            
            // 保存文件并打开的函数
            window.saveAndOpenHTML = function(htmlContent, filename) {
                try {
                    // 创建临时文件
                    const tempDir = os.tmpdir();
                    const filePath = path.join(tempDir, filename || `商圈地图_${Date.now()}.html`);
                    
                    // 写入文件
                    fs.writeFileSync(filePath, htmlContent, 'utf-8');
                    
                    // 使用 uTools API 打开文件
                    if (window.utools && window.utools.shellOpenPath) {
                        window.utools.shellOpenPath(filePath);
                        return true;
                    }
                    
                    return false;
                } catch (error) {
                    console.error('保存文件失败:', error);
                    return false;
                }
            };
            
            console.log('文件操作功能已启用');
        } catch (e) {
            console.log('Node.js 环境不可用，使用浏览器方案');
        }
    }
});

// 监听插件进入
window.utools.onPluginEnter((action) => {
    console.log('插件进入:', action);
});

// 监听插件退出
window.utools.onPluginOut(() => {
    console.log('插件退出');
});

