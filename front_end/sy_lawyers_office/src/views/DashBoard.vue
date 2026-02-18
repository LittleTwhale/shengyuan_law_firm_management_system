<template>
  <div class="dashboard-container">
    <!-- 顶部栏 -->
    <header class="top-bar">
      <div class="logo-section">
        <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image" />
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
        <el-menu-item index="/main/cases">
          <i class="el-icon-cases"></i>
          <span>业务管理</span>
        </el-menu-item>
        <el-menu-item index="/main/case_review" v-if="role === 'owner' || role === 'admin'">
          <i class="el-icon-check"></i>
          <span>业务审核</span>
        </el-menu-item>
        <el-menu-item index="/main/volumes">
          <el-icon><Collection /></el-icon>
          <span>电子卷宗</span>
        </el-menu-item>
        <el-menu-item index="/main/lawyers" v-if="role === 'owner' || role === 'admin'">
          <i class="el-icon-user"></i>
          <span>人员管理</span>
        </el-menu-item>
        <el-menu-item index="/main/cases/bank_cases">
          <i class="el-icon-bank_cases"></i>
          <span>银行案件</span>
        </el-menu-item>
        <el-menu-item index="/main/finance">
          <i class="el-icon-finance"></i>
          <span>财务管理</span>
        </el-menu-item>
        <el-menu-item index="/main/document_template">
          <i class="el-icon-document-template"></i>
          <span>文书模板</span>
        </el-menu-item>
        <el-menu-item index="/main/electronic_seal">
          <i class="el-icon-electronic-seal"></i>
          <span>电子用印</span>
        </el-menu-item>
        <el-menu-item index="/main/party_building">
          <i class="el-icon-electronic-seal"></i>
          <span>党建资料</span>
        </el-menu-item>
        <el-menu-item index="/main/user_profile">
          <i class="el-icon-user-profile"></i>
          <span>个人信息</span>
        </el-menu-item>
        <el-menu-item index="/main/reminders">
          <el-icon><Bell /></el-icon> <span>事项提醒</span>
        </el-menu-item>
        <el-menu-item index="/main/admin/settings" v-if="role === 'owner'">
          <el-icon><Setting /></el-icon>
          <span>后台管理</span>
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Bell, Setting, Collection } from '@element-plus/icons-vue'

const router = useRouter()
const currentUser = ref(localStorage.getItem('username'))
const activeMenu = ref('/dashboard/cases')
const role = localStorage.getItem('role')

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
  router.push('/')
  ElMessage.info('已退出登录')
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
    const res = await axios.get('http://127.0.0.1:8002/user/profile/reminders', {
      params: { user_id: userId, days: 7 },
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
</style>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  background-color: #165dff;
  color: #fff;
  padding: 0 20px;
}
.logo-section {
  display: flex;
  align-items: center;
}
.logo-image {
  width: 200px;
  height: 50px;
  margin-right: 10px;
  object-fit: contain;
}
.user-section span {
  margin-right: 10px;
}
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  width: 200px;
  min-width: 200px;
  height: 100%;
}
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>
