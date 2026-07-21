<template>
  <div id="app">
    <!-- 路由出口：所有页面将在这里渲染 -->
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { startBackgroundPolling, stopBackgroundPolling } from '@/utils/errorAnalysisNotify'

// 挂载时启动后台兜底轮询（内部会检查 token，无 token 时静默跳过）
onMounted(() => {
  startBackgroundPolling()
})

onUnmounted(() => {
  stopBackgroundPolling()
})
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 全局字体设置 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #f5f7fa;
}

/* 消除路由切换时的闪烁 */
#app {
  min-height: 100vh;
}

/* ================================================================
   错误分析弹窗全局样式（ElMessageBox 渲染在 body 下，无法 scoped）
   ================================================================ */
.error-analysis-notify-dialog {
  max-width: 520px;
}
.error-analysis-notify-dialog .el-message-box__title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}
.error-analysis-notify-dialog .el-message-box__message {
  max-height: 380px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
  color: #4e5969;
}
.error-analysis-notify-dialog .el-message-box__message h1,
.error-analysis-notify-dialog .el-message-box__message h2,
.error-analysis-notify-dialog .el-message-box__message h3 {
  margin: 14px 0 6px;
  color: #165dff;
  font-size: 15px;
}
.error-analysis-notify-dialog .el-message-box__message p {
  margin: 6px 0;
}
.error-analysis-notify-dialog .el-message-box__message ul,
.error-analysis-notify-dialog .el-message-box__message ol {
  padding-left: 18px;
  margin: 6px 0;
}
.error-analysis-notify-dialog .el-message-box__message li {
  margin: 4px 0;
}
.error-analysis-notify-dialog .el-message-box__message strong {
  color: #1d2129;
}
.error-analysis-notify-dialog .el-message-box__message code {
  background: #f2f3f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #165dff;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
.error-analysis-notify-dialog .el-message-box__message pre {
  background: #f6f8fa;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  padding: 10px 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.error-analysis-notify-dialog .el-message-box__message pre code {
  background: transparent;
  color: #4e5969;
  padding: 0;
}
.error-analysis-notify-dialog .el-message-box__btns {
  padding-top: 8px;
}
</style>

