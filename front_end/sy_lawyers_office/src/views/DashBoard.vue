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

        <el-menu-item index="/main/ai-analysis">
          <el-icon><MagicStick /></el-icon>
          <template #title>
            <span style="display: flex; align-items: center; gap: 6px;">
              智能分析
              <el-tag size="small" type="warning" effect="dark" style="height: 18px; line-height: 16px; font-size: 11px; padding: 0 5px; border: none;">试运行</el-tag>
            </span>
          </template>
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

        <el-menu-item index="/main/announcements">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>
            <span>公告中心</span>
            <el-badge :value="unreadCount" :hidden="unreadCount <= 0" class="menu-badge" />
          </template>
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

          <el-menu-item index="/main/ai-analysis">
            <el-icon><MagicStick /></el-icon>
            <template #title>
              <span style="display: flex; align-items: center; gap: 6px;">
                智能分析
                <el-tag size="small" type="warning" effect="dark" style="height: 18px; line-height: 16px; font-size: 11px; padding: 0 5px; border: none;">试运行</el-tag>
              </span>
            </template>
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

          <el-menu-item index="/main/announcements">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>
              <span>公告中心</span>
              <el-badge :value="unreadCount" :hidden="unreadCount <= 0" class="menu-badge" />
            </template>
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

    <el-dialog
      v-model="noticeDialogVisible"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="premium-notice-dialog"
      center
      align-center
    >
      <template #header>
        <div class="notice-header">
          <el-button
            class="notice-close-btn"
            type="default"
            text
            circle
            @click="closeNoticeDialog"
          >
            <el-icon :size="20"><Close /></el-icon>
          </el-button>
          <div class="notice-icon-wrapper" :class="currentNotice?.type">
            <el-icon v-if="currentNotice?.type === 'update_log'"><Promotion /></el-icon>
            <el-icon v-else-if="currentNotice?.type === 'case_review'"><Warning /></el-icon>
            <el-icon v-else><Notification /></el-icon>
          </div>
          <h2 class="notice-title">
            {{ currentNotice?.type === 'update_log' ? '🎉 系统更新说明' : currentNotice?.type === 'case_review' ? '⚠ 审核驳回通知' : '📢 系统公告' }}
          </h2>
          <span class="notice-version" v-if="currentNotice?.version"
            >v{{ currentNotice.version }}</span
          >
        </div>
      </template>

      <div class="notice-body" v-if="currentNotice">
        <h3 class="notice-subtitle">{{ currentNotice.title }}</h3>
        <div class="notice-meta">
          <span>发布人：{{ currentNotice.publisher_name || '系统管理员' }}</span>
          <span>发布时间：{{ formatDate(currentNotice.created_at) }}</span>
        </div>
        <el-divider border-style="dashed" />
        <div class="rich-text-notice-content" v-html="currentNotice.content"></div>
      </div>

      <template #footer>
        <div class="notice-footer">
          <div class="notice-progress" v-if="unreadNoticeQueue.length > 1">
            <el-tag effect="plain" type="info" round>
              第 {{ currentIndex + 1 }} / {{ unreadNoticeQueue.length }} 条
            </el-tag>
          </div>

          <div class="notice-actions">
            <el-button v-if="currentIndex > 0" @click="prevNotice" class="nav-btn" size="large">
              上一条
            </el-button>

            <el-button
              v-if="currentIndex < unreadNoticeQueue.length - 1"
              type="primary"
              @click="nextNotice"
              class="nav-btn"
              size="large"
            >
              下一条
            </el-button>

            <el-button
              v-else
              type="primary"
              size="large"
              @click="handleConfirmAllRead"
              class="confirm-btn"
            >
              全部标为已读并关闭
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
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
  ChatDotRound,
  Notification,
  Promotion,
  Close,
  Warning,
  MagicStick,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const currentUser = ref(localStorage.getItem('username'))
const activeMenu = computed(() => route.path)
const role = localStorage.getItem('role')

const isCollapse = ref(false)
const isMobile = ref(false)
const drawerVisible = ref(false)

const menuTitleMap = {
  '/main/cases': '业务管理',
  '/main/case_review': '业务审核',
  '/main/volumes': '电子卷宗',
  '/main/ai-analysis': '智能分析',
  '/main/lawyers': '人员管理',
  '/main/cases/bank_cases': '银行案件',
  '/main/finance': '财务管理',
  '/main/document_template': '文书模板',
  '/main/electronic_seal': '电子用印',
  '/main/party_building': '党建资料',
  '/main/user_profile': '个人信息',
  '/main/reminders': '事项提醒',
  '/main/announcements': '公告中心',
  '/main/admin/settings': '后台管理',
}

const currentBreadcrumbs = computed(() => {
  const path = route.path
  const title = route.meta?.title || menuTitleMap[path] || '页面详情'

  const crumbs = [{ title: '首页', path: '/main/cases' }]

  if (path !== '/main/cases') {
    if (path === '/main/cases/bank_cases') {
      crumbs.push({ title: '业务管理', path: '/main/cases' })
    }
    crumbs.push({ title, path })
  }

  return crumbs
})

const checkDeviceType = () => {
  const width = window.innerWidth
  if (width < 768) {
    isMobile.value = true
    isCollapse.value = false
  } else if (width >= 768 && width < 992) {
    isMobile.value = false
    isCollapse.value = true
    drawerVisible.value = false
  } else {
    isMobile.value = false
    isCollapse.value = false
    drawerVisible.value = false
  }
}

const toggleMenu = () => {
  if (isMobile.value) {
    drawerVisible.value = !drawerVisible.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

let permissions = {}
try {
  permissions = JSON.parse(localStorage.getItem('permissions') || '{}')
} catch (e) {
  console.error('解析权限失败', e)
  ElMessage.error('解析权限失败')
}

const hasAdminAccess = computed(() => {
  return role === 'owner' || permissions.can_access_admin === true
})
const hasReviewAccess = computed(() => {
  return role === 'owner' || permissions.can_review_case === true
})

const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
  } else if (command === 'profile') {
    router.push('/main/user_profile')
  }
}

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

const checkUrgentReminders = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  const reminderKey = `has_shown_urgent_reminder_${userId}`
  if (localStorage.getItem(reminderKey)) {
    return
  }

  try {
    const res = await request.get('/user/profile/reminders', {
      params: { days: 7, limit: 100 },
    })

    let urgentEvents = []
    if (res.data && res.data.items !== undefined) {
      urgentEvents = res.data.items
    } else {
      urgentEvents = res.data || []
    }

    if (urgentEvents.length > 0) {
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
                    <div class="urgent-case">${e.case_number ? e.case_number : e.source === 'custom' ? '自定义日程' : '--'}</div>
                    <div class="urgent-client">${e.client_name ? e.client_name : e.description || '无详细备注'}</div>
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
        duration: 0, // 不自动关闭
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

// === 公告相关状态（已重构为走马灯序列逻辑） ===
const noticeDialogVisible = ref(false)
const unreadNoticeQueue = ref([])
const currentIndex = ref(0) // 当前浏览的公告索引
const currentNotice = computed(() => unreadNoticeQueue.value[currentIndex.value] || null) // 动态计算当前展示内容
const unreadCount = ref(0) // 菜单角标用
let pollingTimer = null

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const fetchUnreadCount = async () => {
  try {
    const res = await request.get('/system/announcements/unread/count')
    unreadCount.value = res.data?.count || 0
  } catch (error) {
    // 静默失败，角标不更新
    console.error('获取未读公告数量失败', error)
  }
}

const checkSystemAnnouncements = async () => {
  // 如果弹窗已打开，或者当前页面不在用户的可视层（被隐藏或切到后台），则不发请求
  if (noticeDialogVisible.value || document.hidden) return

  try {
    const res = await request.get('/system/announcements/unread')
    const unreadList = res.data || []
    unreadCount.value = unreadList.length
    if (unreadList.length > 0) {
      unreadNoticeQueue.value = unreadList
      currentIndex.value = 0
      noticeDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取系统未读公告失败', error)
  }
}

// 翻页操作：上一条
const prevNotice = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

// 翻页操作：下一条
const nextNotice = () => {
  if (currentIndex.value < unreadNoticeQueue.value.length - 1) {
    currentIndex.value++
  }
}

// 直接关闭弹窗（不标记已读）
const closeNoticeDialog = () => {
  noticeDialogVisible.value = false
}

// 翻到底部时的操作：全部标记已读
const handleConfirmAllRead = async () => {
  if (!unreadNoticeQueue.value.length) return

  try {
    // 遍历队列中所有未读公告，并发请求标记已读
    const promises = unreadNoticeQueue.value.map((notice) =>
      request.post(`/system/announcements/${notice.id}/read`),
    )
    await Promise.all(promises)
  } catch (e) {
    console.error('批量标记公告已读失败', e)
  }

  // 清空队列并关闭弹窗
  unreadNoticeQueue.value = []
  currentIndex.value = 0
  unreadCount.value = 0
  noticeDialogVisible.value = false
}

onMounted(() => {
  checkUrgentReminders()
  checkSystemAnnouncements()
  fetchUnreadCount()

  // 轮询时间为 5 分钟 (300000 毫秒)
  pollingTimer = setInterval(checkSystemAnnouncements, 300000)

  // 监听页面可见性变化：用户切回标签页时，主动查一次
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      checkSystemAnnouncements()
      fetchUnreadCount()
    }
  })

  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
  // 移除监听器
  document.removeEventListener('visibilitychange', checkSystemAnnouncements)
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
})
</script>

<style>
/* 全局样式区域，无 scoped */

/* 优化后的通知整体样式，保留深度适配移动端 */
.urgent-notification {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) scale(1);
  margin: 0 !important;
  z-index: 3000 !important;

  background: linear-gradient(135deg, #ffffff, #fafdff) !important;
  border: 1px solid #eef2f7 !important;
  border-radius: 16px !important;
  box-shadow: 0 24px 56px rgba(0, 0, 0, 0.16) !important;
  max-width: 480px;
  width: 90%; /* 移动端自适应宽度 */
  padding: 24px 28px !important;
  animation: fadeInScale 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
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
  max-height: 380px;
  overflow-y: auto;
  padding-right: 8px;
  margin-top: 10px;
}

/* 自定义紧急提醒滚动条 */
.urgent-wrapper::-webkit-scrollbar {
  width: 6px;
}
.urgent-wrapper::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
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
  margin-top: 2px;
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

/* --- 高级系统公告弹窗样式保留自适应 --- */
.premium-notice-dialog {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2) !important;
  width: 650px !important;
  max-width: 92vw !important; /* 核心：限制最大宽度供移动端适配 */
}

.premium-notice-dialog .el-dialog__header {
  padding: 0 !important;
  margin: 0 !important;
}

.premium-notice-dialog .el-dialog__body {
  padding: 0 !important;
}

.notice-header {
  padding: 30px 20px 20px;
  background: linear-gradient(135deg, #f4f7ff 0%, #ffffff 100%);
  text-align: center;
  position: relative;
  border-bottom: 1px solid #ebeef5;
}

.notice-close-btn {
  position: absolute !important;
  top: 12px;
  right: 12px;
  z-index: 10;
  color: #909399 !important;
  transition: all 0.25s ease;
}
.notice-close-btn:hover {
  color: #303133 !important;
  background-color: rgba(0, 0, 0, 0.06) !important;
  transform: rotate(90deg);
}

.notice-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 15px;
  color: #fff;
}
.notice-icon-wrapper.update_log {
  background: linear-gradient(135deg, #85d655, #67c23a);
  box-shadow: 0 8px 16px rgba(103, 194, 58, 0.3);
}
.notice-icon-wrapper.general_notice {
  background: linear-gradient(135deg, #4080ff, #165dff);
  box-shadow: 0 8px 16px rgba(22, 93, 255, 0.3);
}
.notice-icon-wrapper.case_review {
  background: linear-gradient(135deg, #f6a742, #e6a23c);
  box-shadow: 0 8px 16px rgba(230, 162, 60, 0.35);
}

.notice-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.notice-version {
  position: absolute;
  top: 20px;
  right: 20px;
  background: #e1eaff;
  color: #165dff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.notice-body {
  padding: 24px 30px;
}

.notice-subtitle {
  font-size: 18px;
  color: #303133;
  margin-top: 0;
  margin-bottom: 12px;
  text-align: center;
}

.notice-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 13px;
  color: #909399;
}

.rich-text-notice-content {
  max-height: 40vh;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 10px 10px 0;
  color: #303133;
  line-height: 1.8;
  font-size: 15px;
}

/* 彻底解决富文本内部图片溢出弹窗的问题 */
.rich-text-notice-content img,
.rich-text-notice-content video,
.rich-text-notice-content iframe {
  max-width: 100% !important;
  height: auto !important;
  border-radius: 8px;
  margin: 10px auto;
  display: block;
  object-fit: contain;
}

.rich-text-notice-content p {
  margin: 10px 0;
}
.rich-text-notice-content h1,
.rich-text-notice-content h2,
.rich-text-notice-content h3 {
  margin: 15px 0 10px;
  color: #1f2329;
}

/* 自定义滚动条 */
.rich-text-notice-content::-webkit-scrollbar {
  width: 6px;
}
.rich-text-notice-content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.notice-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px 24px;
}

.notice-progress {
  margin-bottom: 16px;
}

.notice-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  width: 100%;
}

.nav-btn {
  width: 120px;
  border-radius: 20px;
  font-weight: bold;
}

.confirm-btn {
  flex: 1;
  max-width: 260px;
  border-radius: 20px;
  font-weight: bold;
  background: linear-gradient(135deg, #165dff, #4080ff) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3) !important;
  color: #fff !important;
  transition: all 0.3s ease;
}

.confirm-btn:hover {
  box-shadow: 0 6px 16px rgba(22, 93, 255, 0.4) !important;
  transform: translateY(-2px);
}

/* 针对公告弹窗的专属移动端优化 */
@media (max-width: 768px) {
  .notice-body {
    padding: 20px;
  }
  .notice-meta {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .notice-version {
    top: 8px;
    right: 40px;
    padding: 4px 8px;
    font-size: 12px;
  }
  .notice-close-btn {
    top: 6px !important;
    right: 6px !important;
  }
  .rich-text-notice-content {
    max-height: 55vh;
  }
  .notice-actions {
    flex-direction: row;
  }
  .nav-btn {
    flex: 1;
    width: auto;
  }
}
</style>

<style scoped>
/* ====== 完全还原最初的作用域样式，恢复丝滑折叠 ====== */
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f4f5f7;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  background-color: #165dff;
  color: #fff;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.2);
  z-index: 10;
}

.left-section {
  display: flex;
  align-items: center;
}

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
  transform: scale(1.1);
}

.logo-section {
  display: flex;
  align-items: center;
}
.logo-image {
  height: 36px;
  object-fit: contain;
  transition: width 0.3s;
}

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
  border: 2px solid rgba(255, 255, 255, 0.3);
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

.sidebar {
  height: 100%;
  border-right: none;
}
.sidebar:not(.el-menu--collapse) {
  width: 220px;
}

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

.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  box-sizing: border-box;
}

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

.content-wrapper {
  background-color: #ffffff;
  border-radius: 12px;
  min-height: calc(100% - 30px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
  padding: 24px;
  box-sizing: border-box;
  overflow-x: hidden;
}

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

.sidebar {
  height: 100%;
  border-right: none;
  overflow-y: auto;
}

.mobile-sidebar {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

.sidebar::-webkit-scrollbar,
.mobile-sidebar::-webkit-scrollbar {
  width: 4px;
}

.sidebar::-webkit-scrollbar-thumb,
.mobile-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.sidebar::-webkit-scrollbar-track,
.mobile-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

/* 菜单角标样式 */
.menu-badge {
  margin-left: 8px;
}
.menu-badge :deep(.el-badge__content) {
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 5px;
}

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
