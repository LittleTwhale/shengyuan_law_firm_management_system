<template>
  <div class="dashboard-container">
    <header class="top-bar">
      <div class="left-section">
        <el-icon class="toggle-btn" @click="toggleMenu">
          <Fold v-if="!isCollapse && !isMobile" />
          <Expand v-else-if="isCollapse && !isMobile" />
          <Operation v-else />
        </el-icon>

        <div class="logo-section">
          <img
            src="@/assets/img/logo.png"
            alt="湖南生元律师事务所Logo"
            class="logo-image"
            :class="{ 'mobile-logo': isMobile }"
          />
        </div>
      </div>

      <div class="user-section">
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="user-dropdown-link">
            <el-avatar
              :size="32"
              class="user-avatar"
              style="background-color: #ffd04b; color: #165dff; font-weight: bold"
            >
              {{ currentUser ? currentUser.charAt(0) : 'U' }}
            </el-avatar>
            <span v-if="!isMobile" class="username">{{ currentUser }}</span>
            <el-icon class="el-icon--right" v-if="!isMobile"><CaretBottom /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><Postcard /></el-icon>个人信息
              </el-dropdown-item>
              <el-dropdown-item divided command="logout" class="logout-item">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="main-content">
      <el-menu
        v-show="!isMobile"
        class="sidebar"
        :collapse="isCollapse"
        :default-active="activeMenu"
        router
        background-color="#165DFF"
        text-color="#c3d4ff"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/main/cases">
          <el-icon><Briefcase /></el-icon>
          <template #title><span>业务管理</span></template>
        </el-menu-item>

        <el-menu-item index="/main/case_review" v-if="hasReviewAccess">
          <el-icon><DocumentChecked /></el-icon>
          <template #title><span>业务审核</span></template>
        </el-menu-item>

        <el-menu-item index="/main/volumes">
          <el-icon><Collection /></el-icon>
          <template #title><span>电子卷宗</span></template>
        </el-menu-item>

        <el-menu-item index="/main/lawyers" v-if="role === 'owner' || role === 'admin'">
          <el-icon><User /></el-icon>
          <template #title><span>人员管理</span></template>
        </el-menu-item>

        <el-menu-item index="/main/cases/bank_cases">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title><span>银行案件</span></template>
        </el-menu-item>

        <el-menu-item index="/main/finance">
          <el-icon><Money /></el-icon>
          <template #title><span>财务管理</span></template>
        </el-menu-item>

        <el-menu-item index="/main/document_template">
          <el-icon><DocumentCopy /></el-icon>
          <template #title><span>文书模板</span></template>
        </el-menu-item>

        <el-menu-item index="/main/electronic_seal">
          <el-icon><Stamp /></el-icon>
          <template #title><span>电子用印</span></template>
        </el-menu-item>

        <el-menu-item index="/main/party_building">
          <el-icon><Flag /></el-icon>
          <template #title><span>党建资料</span></template>
        </el-menu-item>

        <el-menu-item index="/main/user_profile">
          <el-icon><Postcard /></el-icon>
          <template #title><span>个人信息</span></template>
        </el-menu-item>

        <el-menu-item index="/main/reminders">
          <el-icon><Bell /></el-icon>
          <template #title><span>事项提醒</span></template>
        </el-menu-item>

        <el-menu-item index="/main/admin/settings" v-if="hasAdminAccess">
          <el-icon><Setting /></el-icon>
          <template #title><span>后台管理</span></template>
        </el-menu-item>
      </el-menu>

      <el-drawer
        v-model="drawerVisible"
        direction="ltr"
        size="240px"
        :with-header="false"
        class="mobile-drawer"
      >
        <div class="drawer-logo">
          <img src="@/assets/img/logo.png" alt="Logo" class="logo-image mobile-drawer-logo" />
        </div>
        <el-menu
          class="mobile-sidebar"
          :default-active="activeMenu"
          router
          background-color="#165DFF"
          text-color="#c3d4ff"
          active-text-color="#ffffff"
          @select="drawerVisible = false"
        >
          <el-menu-item index="/main/cases">
            <el-icon><Briefcase /></el-icon>
            <template #title><span>业务管理</span></template>
          </el-menu-item>

          <el-menu-item index="/main/case_review" v-if="hasReviewAccess">
            <el-icon><DocumentChecked /></el-icon>
            <template #title><span>业务审核</span></template>
          </el-menu-item>

          <el-menu-item index="/main/volumes">
            <el-icon><Collection /></el-icon>
            <template #title><span>电子卷宗</span></template>
          </el-menu-item>

          <el-menu-item index="/main/lawyers" v-if="role === 'owner' || role === 'admin'">
            <el-icon><User /></el-icon>
            <template #title><span>人员管理</span></template>
          </el-menu-item>

          <el-menu-item index="/main/cases/bank_cases">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title><span>银行案件</span></template>
          </el-menu-item>

          <el-menu-item index="/main/finance">
            <el-icon><Money /></el-icon>
            <template #title><span>财务管理</span></template>
          </el-menu-item>

          <el-menu-item index="/main/document_template">
            <el-icon><DocumentCopy /></el-icon>
            <template #title><span>文书模板</span></template>
          </el-menu-item>

          <el-menu-item index="/main/electronic_seal">
            <el-icon><Stamp /></el-icon>
            <template #title><span>电子用印</span></template>
          </el-menu-item>

          <el-menu-item index="/main/party_building">
            <el-icon><Flag /></el-icon>
            <template #title><span>党建资料</span></template>
          </el-menu-item>

          <el-menu-item index="/main/user_profile">
            <el-icon><Postcard /></el-icon>
            <template #title><span>个人信息</span></template>
          </el-menu-item>

          <el-menu-item index="/main/reminders">
            <el-icon><Bell /></el-icon>
            <template #title><span>事项提醒</span></template>
          </el-menu-item>

          <el-menu-item index="/main/admin/settings" v-if="hasAdminAccess">
            <el-icon><Setting /></el-icon>
            <template #title><span>后台管理</span></template>
          </el-menu-item>
        </el-menu>
      </el-drawer>

      <div class="content-area">
        <div class="breadcrumb-container" v-if="!isMobile">
          <el-breadcrumb :separator-icon="ArrowRight">
            <el-breadcrumb-item
              v-for="(crumb, index) in currentBreadcrumbs"
              :key="index"
              :to="index === currentBreadcrumbs.length - 1 ? undefined : { path: crumb.path }"
            >
              {{ crumb.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import request from '@/utils/request'
import {
  Briefcase,
  DocumentChecked,
  Collection,
  User,
  OfficeBuilding,
  Money,
  DocumentCopy,
  Stamp,
  Flag,
  Postcard,
  Bell,
  Setting,
  Fold,
  Expand,
  Operation,
  CaretBottom,
  SwitchButton,
  ArrowRight,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute() // 实例化 route，用于监听当前路径
const currentUser = ref(localStorage.getItem('username'))
const activeMenu = computed(() => route.path)
const role = localStorage.getItem('role')

// --- 响应式适配状态 ---
const isCollapse = ref(false) // 是否折叠菜单 (用于PC/平板)
const isMobile = ref(false) // 是否为移动端屏幕
const drawerVisible = ref(false) // 移动端抽屉是否显示

// --- 动态面包屑导航计算逻辑 ---
// 路由路径到名称的映射字典 (兼容 router 中未配置 meta.title 的情况)
const menuTitleMap = {
  '/main/cases': '业务管理',
  '/main/case_review': '业务审核',
  '/main/volumes': '电子卷宗',
  '/main/lawyers': '人员管理',
  '/main/cases/bank_cases': '银行案件',
  '/main/finance': '财务管理',
  '/main/document_template': '文书模板',
  '/main/electronic_seal': '电子用印',
  '/main/party_building': '党建资料',
  '/main/user_profile': '个人信息',
  '/main/reminders': '事项提醒',
  '/main/admin/settings': '后台管理',
}

const currentBreadcrumbs = computed(() => {
  const path = route.path
  // 优先取 router 中配置的 meta.title，如果没有则从映射表里找，最后兜底为'页面详情'
  const title = route.meta?.title || menuTitleMap[path] || '页面详情'

  const crumbs = [{ title: '首页', path: '/main/cases' }] // 默认固定首层

  if (path !== '/main/cases') {
    // 针对具有层级关系的路由（如银行案件属于业务管理的子类）增加中间层级
    if (path === '/main/cases/bank_cases') {
      crumbs.push({ title: '业务管理', path: '/main/cases' })
    }
    crumbs.push({ title, path })
  }

  return crumbs
})
// --- 面包屑逻辑结束 ---

// 监听窗口大小变化以适配布局
const checkDeviceType = () => {
  const width = window.innerWidth
  if (width < 768) {
    // 移动端：隐藏固定侧边栏，启用抽屉
    isMobile.value = true
    isCollapse.value = false
  } else if (width >= 768 && width < 992) {
    // 平板端：显示固定侧边栏，但默认折叠
    isMobile.value = false
    isCollapse.value = true
    drawerVisible.value = false
  } else {
    // PC端：完全展开
    isMobile.value = false
    isCollapse.value = false
    drawerVisible.value = false
  }
}

// 切换菜单栏状态
const toggleMenu = () => {
  if (isMobile.value) {
    drawerVisible.value = !drawerVisible.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}
// --- 响应式代码结束 ---

// 解析权限
let permissions = {}
try {
  permissions = JSON.parse(localStorage.getItem('permissions') || '{}')
} catch (e) {
  console.error('解析权限失败', e)
  ElMessage.error('解析权限失败')
}

// 计算属性：是否有后台管理入口权限
const hasAdminAccess = computed(() => {
  return role === 'owner' || permissions.can_access_admin === true
})
// 是否有业务审核入口权限
const hasReviewAccess = computed(() => {
  return role === 'owner' || permissions.can_review_case === true
})

// 右上角下拉菜单事件处理
const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
  } else if (command === 'profile') {
    router.push('/main/user_profile')
  }
}

// 登出
const handleLogout = () => {
  const userId = localStorage.getItem('user_id')
  if (userId) {
    localStorage.removeItem(`has_shown_urgent_reminder_${userId}`)
  }

  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  localStorage.removeItem('userId')
  localStorage.removeItem('user_id')
  localStorage.removeItem('permissions')
  router.push('/')
  ElMessage.success('已退出登录')
}

// 检查紧急提醒
const checkUrgentReminders = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  const reminderKey = `has_shown_urgent_reminder_${userId}`
  if (localStorage.getItem(reminderKey)) {
    return
  }

  try {
    const res = await request.get('/user/profile/reminders', {
      params: { days: 7 },
    })

    const urgentEvents = res.data

    if (urgentEvents.length > 0) {
      // 构建更高级卡片式结构
      const messageHtml = `
        <div class="urgent-wrapper">
          ${urgentEvents
            .map(
              (e) => `
                <div class="urgent-card">
                  <div class="urgent-header">
                    <span class="urgent-type">${e.event_type}</span>
                    <span class="urgent-date">${e.event_date}</span>
                  </div>
                  <div class="urgent-body">
                    <div class="urgent-case">${e.case_number}</div>
                    <div class="urgent-client">${e.client_name}</div>
                  </div>
                  <div class="urgent-footer">
                    剩余 <span class="urgent-days">${e.days_remaining}</span> 天
                  </div>
                </div>
              `,
            )
            .join('')}
        </div>
      `

      ElNotification({
        title: `⚠ 紧急事项提醒（${urgentEvents.length}）`,
        dangerouslyUseHTMLString: true,
        message: messageHtml,
        duration: 0,
        type: 'warning',
        customClass: 'urgent-notification',
        showClose: true,
        onClick: () => {
          router.push('/main/reminders')
        },
      })
    }

    localStorage.setItem(reminderKey, 'true')
  } catch (error) {
    console.error('检查提醒失败', error)
  }
}

onMounted(() => {
  checkUrgentReminders()
  // 初始化及绑定窗口大小监听
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)
})

// 组件销毁前移除监听，防止内存泄漏
onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})
</script>

<style>
/* 优化后的通知整体样式 */
.urgent-notification {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) scale(1);
  margin: 0 !important;
  z-index: 3000 !important;

  background: linear-gradient(135deg, #ffffff, #f5f9ff) !important;
  border: none !important;
  border-radius: 16px !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15) !important;
  max-width: 520px;
  /* 移动端适配通知弹窗宽度 */
  width: 90%;
  padding: 20px 24px !important;
  animation: fadeInScale 0.3s ease;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: translate(-50%, -48%) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.urgent-wrapper {
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.urgent-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 14px;
  border: 1px solid #eef2f7;
  transition: all 0.25s ease;
}

.urgent-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(22, 93, 255, 0.15);
}

.urgent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.urgent-type {
  background: #ffecec;
  color: #f56c6c;
  font-weight: 600;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 20px;
}

.urgent-date {
  font-size: 12px;
  color: #909399;
}

.urgent-body {
  margin-bottom: 8px;
}

.urgent-case {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.urgent-client {
  font-size: 13px;
  color: #606266;
}

.urgent-footer {
  font-size: 12px;
  color: #e6a23c;
}

.urgent-days {
  font-size: 14px;
  font-weight: bold;
  color: #f56c6c;
}

/* 抽屉无内边距样式覆盖 */
.mobile-drawer .el-drawer__body {
  padding: 0;
  background-color: #165dff;
  display: flex;
  flex-direction: column;
}
</style>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f4f5f7;
}

/* 顶部导航栏高级感优化 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  background-color: #165dff;
  color: #fff;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.2); /* 添加质感阴影 */
  z-index: 10; /* 确保悬浮在侧边栏和内容之上 */
}

/* 新增左侧包裹层 */
.left-section {
  display: flex;
  align-items: center;
}

/* 汉堡按钮样式 */
.toggle-btn {
  font-size: 22px;
  cursor: pointer;
  margin-right: 20px;
  transition:
    transform 0.3s ease,
    color 0.3s ease;
}
.toggle-btn:hover {
  color: #ffd04b;
  transform: scale(1.1); /* 点击区域微动效 */
}

.logo-section {
  display: flex;
  align-items: center;
}
.logo-image {
  height: 36px; /* 稍微缩小让出呼吸空间 */
  object-fit: contain;
  transition: width 0.3s;
}

/* 右侧用户下拉菜单设计 */
.user-section {
  display: flex;
  align-items: center;
}
.user-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #fff;
  transition: opacity 0.3s;
}
.user-dropdown-link:hover {
  opacity: 0.8;
}
.user-avatar {
  margin-right: 8px;
  border: 2px solid rgba(255, 255, 255, 0.3); /* 头像描边增加精致感 */
}
.username {
  font-size: 14px;
  font-weight: 500;
  margin-right: 4px;
}
.logout-item {
  color: #f56c6c;
}
.logout-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 依靠Element Plus原生类名处理宽度 */
.sidebar {
  height: 100%;
  border-right: none;
}
/* 展开状态的宽度 */
.sidebar:not(.el-menu--collapse) {
  width: 220px; /* 稍微加宽一点，现代系统通常在200-240px之间 */
}

/* 选中菜单的样式优化 */
:deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  border-left: 4px solid #ffd04b;
}

.mobile-sidebar {
  border-right: none;
  flex: 1;
}
.drawer-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 15px;
}
.mobile-drawer-logo {
  height: 32px;
}

/* 内容区域高级排版 */
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 面包屑导航样式 */
.breadcrumb-container {
  margin-bottom: 16px;
  padding: 0 4px;
}
:deep(.el-breadcrumb__inner),
:deep(.el-breadcrumb__inner a) {
  color: #606266;
  font-weight: 500;
  transition: color 0.3s;
}
:deep(.el-breadcrumb__inner a:hover) {
  color: #165dff;
}
:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #303133;
  font-weight: 600;
}

/* 给各个路由组件一个纯白色的卡片底座 */
.content-wrapper {
  background-color: #ffffff;
  border-radius: 12px;
  min-height: calc(100% - 30px); /* 减去面包屑的高度，保持满屏感 */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
  padding: 24px;
  box-sizing: border-box;
  overflow-x: hidden;
}

/* 路由切换过渡动画 */
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s cubic-bezier(0.55, 0, 0.1, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-15px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(15px);
}
/* 优化 PC/平板侧边栏滚动 */
.sidebar {
  height: 100%;
  border-right: none;
  overflow-y: auto; /* 开启垂直滚动 */
}

/* 优化移动端抽屉菜单滚动 */
.mobile-sidebar {
  border-right: none;
  flex: 1;
  overflow-y: auto; /* 开启垂直滚动 */
}

/* 隐藏原生滚动条，保持界面整洁高级 (Webkit浏览器) */
.sidebar::-webkit-scrollbar,
.mobile-sidebar::-webkit-scrollbar {
  width: 4px; /* 缩小滚动条宽度 */
}

.sidebar::-webkit-scrollbar-thumb,
.mobile-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2); /* 使用半透明白色滚动条 */
  border-radius: 4px;
}

.sidebar::-webkit-scrollbar-track,
.mobile-sidebar::-webkit-scrollbar-track {
  background: transparent;
}
/* --- 媒体查询：移动端极致适配 --- */
@media (max-width: 768px) {
  .top-bar {
    padding: 0 15px;
  }
  .toggle-btn {
    margin-right: 15px;
  }
  .content-area {
    padding: 10px;
  }
  .content-wrapper {
    padding: 16px;
    border-radius: 8px;
    min-height: 100%;
  }
}
</style>
