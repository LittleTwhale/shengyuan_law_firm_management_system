<template>
  <div class="dashboard-container">
    <!-- 顶部栏 -->
    <header class="top-bar">
      <div class="logo-section">
        <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image">
        <el-button
          icon="el-icon-menu"
          class="menu-toggle"
          @click="isCollapsed = !isCollapsed"
        ></el-button>
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
        :collapse="isCollapsed"
      >
        <el-menu-item index="/main/cases">
          <i class="el-icon-document"></i>
          <span>案件管理</span>
        </el-menu-item>
        <el-menu-item
          index="/main/case_review"
          v-if="role === 'owner' || role === 'admin'"
        >
          <i class="el-icon-check"></i>
          <span>案件审核</span>
        </el-menu-item>
        <el-menu-item
          index="/main/lawyers"
          v-if="role === 'owner' || role === 'admin'"
        >
          <i class="el-icon-user"></i>
          <span>人员管理</span>
        </el-menu-item>
        <el-menu-item index="/main/cases/bank_cases">
          <i class="el-icon-bank_cases"></i>
          <span>银行案件</span>
        </el-menu-item>
        <el-menu-item index="/main/user_profile">
          <i class="el-icon-user-profile"></i>
          <span>个人信息</span>
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
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentUser = ref(sessionStorage.getItem('username'))
const activeMenu = ref('/dashboard/cases')
const role = sessionStorage.getItem('role')

// 登出
const handleLogout = () => {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('username')
  sessionStorage.removeItem('role')
  sessionStorage.removeItem('userId')
  router.push('/')
  ElMessage.info('已退出登录')
}

// 新增折叠状态管理
const isCollapsed = ref(false)

// 监听窗口大小变化
onMounted(() => {
  const handleResize = () => {
    // 移动端自动折叠
    isCollapsed.value = window.innerWidth < 768;
  }

  window.addEventListener('resize', handleResize)
  handleResize() // 初始化

  onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
  })
})
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
  width: 200px;
  min-width: 200px;
  height: 100%;
  transition: width 0.3s ease; /* 平滑过渡 */
}

/* 折叠状态样式 */
:deep(.el-menu--collapsed) {
  width: 64px;
  min-width: 64px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 10;
    height: calc(100vh - 60px);
  }

  .content-area {
    margin-left: 0;
  }

  .menu-toggle {
    display: block !important;
    color: white;
    margin-right: 10px;
  }
}

/* 隐藏默认的折叠按钮 */
:deep(.el-menu__collapse-transition) {
  display: none;
}

/* 菜单切换按钮样式 */
.menu-toggle {
  display: none;
  background: transparent;
  border: none;
}
</style>
