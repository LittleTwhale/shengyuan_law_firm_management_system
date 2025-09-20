<template>
  <div class="dashboard-container">
    <!-- 顶部栏 -->
    <header class="top-bar">
      <div class="logo-section">
        <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image">
      </div>
      <div class="user-section">
        <span>{{ currentUser }}</span>
        <el-button type="text" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="main-content">
      <!-- 左侧导航栏 -->
      <el-menu
        class="sidebar"
        :default-active="activeMenu"
        router
        background-color="#165DFF"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item index="/dashboard/cases">
          <i class="el-icon-document"></i>
          <span>案件管理</span>
        </el-menu-item>
        <el-menu-item
          index="/dashboard/lawyers"
          v-if="role === 'owner' || role === 'admin'"
        >
          <i class="el-icon-user"></i>
          <span>律师管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/statistics">
          <i class="el-icon-data-analysis"></i>
          <span>统计分析</span>
        </el-menu-item>
      </el-menu>

      <!-- 右侧操作区（路由出口） -->
      <div class="content-area">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentUser = ref(localStorage.getItem('username'))
const activeMenu = ref('/dashboard/cases')
const role = localStorage.getItem('role')

// 登出
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/')
  ElMessage.info('已退出登录')
}
</script>

<style scoped>
.dashboard-container {
  display:flex;
  flex-direction:column;
  height:100vh;
}
.top-bar {
  display:flex;
  justify-content:space-between;
  align-items:center;
  height:60px;
  background-color:#165DFF;
  color:#fff;
  padding:0 20px;
}
.logo-section {
  display:flex;
  align-items:center;
}
.logo-image {
  width:200px;
  height:50px;
  margin-right:10px;
  object-fit:contain;
}
.user-section span {
  margin-right:10px;
}
.main-content {
  display:flex;
  flex:1;
  overflow:hidden;
}
.sidebar {
  width:200px;
  min-width:200px;
  height:100%;
}
.content-area {
  flex:1;
  padding:20px;
  overflow-y:auto;
}
</style>
