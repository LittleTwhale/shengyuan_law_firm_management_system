<template>
  <div id="app">
    <!-- 路由出口：所有页面将在这里渲染 -->
    <router-view />
  </div>
</template>

<script setup>
// 无需额外逻辑，主要提供路由出口
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
</style>

