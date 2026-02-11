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
        <el-menu-item index="/main/lawyers" v-if="role === 'owner' || role === 'admin'">
          <i class="el-icon-user"></i>
          <span>人员管理</span>
        </el-menu-item>
        <el-menu-item index="/main/cases/bank_cases">
          <i class="el-icon-bank_cases"></i>
          <span>银行案件</span>
        </el-menu-item>
        <el-menu-item index="/main/document_template">
          <i class="el-icon-document-template"></i>
          <span>文书模板</span>
        </el-menu-item>
        <el-menu-item index="/main/electronic_seal">
          <i class="el-icon-electronic-seal"></i>
          <span>电子用印</span>
        </el-menu-item>
        <el-menu-item index="/main/user_profile">
          <i class="el-icon-user-profile"></i>
          <span>个人信息</span>
        </el-menu-item>
        <el-menu-item index="/main/reminders">
          <el-icon><Bell /></el-icon> <span>事项提醒</span>
        </el-menu-item>
        <el-menu-item index="/main/admin/settings" v-if="role === 'owner' ">
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
import axios from 'axios' // 引入axios
import { Bell,Setting } from '@element-plus/icons-vue'

const router = useRouter()
const currentUser = ref(localStorage.getItem('username'))
const activeMenu = ref('/dashboard/cases')
const role = localStorage.getItem('role')

// 登出
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  localStorage.removeItem('userId')
  router.push('/')
  ElMessage.info('已退出登录')
}

// 新增：检查紧急提醒
const checkUrgentReminders = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    // 查询未来3天内的事件
    const res = await axios.get('http://127.0.0.1:8002/user/profile/reminders', {
      params: { user_id: userId, days: 3 },
    })

    const urgentEvents = res.data

    if (urgentEvents.length > 0) {
      // 构建弹窗内容 HTML
      const messageHtml = urgentEvents
        .map(
          (e) =>
            `<div style="margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px dashed #eee;">
           <span style="color: #f56c6c; font-weight: bold;">[${e.event_type}]</span>
           <span style="margin-left: 5px;">${e.event_date}</span>
           <div style="font-size: 12px; color: #666; margin-top: 4px;">
             ${e.case_number} (${e.client_name})
           </div>
           <div style="font-size: 12px; color: #e6a23c;">
             剩余 ${e.days_remaining} 天
           </div>
         </div>`,
        )
        .join('')

      ElNotification({
        title: `有 ${urgentEvents.length} 个紧急事项即将到期`,
        dangerouslyUseHTMLString: true,
        message: `<div style="max-height: 300px; overflow-y: auto;">${messageHtml}</div>`,
        duration: 0, // 设置为 0 则不会自动关闭
        type: 'warning',
        customClass: 'center-notification',
        onClick: () => {
          router.push('/main/reminders') // 点击跳转到详情页
        },
      })
    }
  } catch (error) {
    console.error('检查提醒失败', error)
  }
}

onMounted(() => {
  checkUrgentReminders()
})
</script>

<style>
/* 非作用域样式：用于强制 ElNotification 居中和突出显示 */
.center-notification {
  /* 居中定位  */
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%);
  margin: 0 !important;
  z-index: 3000 !important;

  /* 自定义背景和边框，使其更醒目 */
  background-color: #e1f4fa !important; /* 浅蓝色背景 */
  border-left: 8px solid #ff0008 !important; /* 强烈红色左侧边框 */
  box-shadow:
    0 6px 16px rgba(17, 220, 255, 0.4),
    0 0 0 1px rgba(0, 0, 0, 0.1) !important; /* 加重阴影和轻微描边 */
  max-width: 450px;
  border-radius: 8px !important;
}

/* 确保通知体内的文字颜色正常 */
.center-notification .el-notification__title,
.center-notification .el-notification__content {
  color: #333;
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
