import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/views/LoginPage.vue'
import DashBoard from '@/views/DashBoard.vue'
import CasesPage from '@/views/CasesPage.vue'
import LawyerManagePage from '@/views/LawyerManagePage.vue'
import CaseReviewPage from '@/views/CaseReviewPage.vue'
import CaseDetailPage from '@/views/CaseDetailPage.vue'
import BankCasesPage from '@/views/BankCasesPage.vue'
import UserProfilePage from '@/views/UserProfilePage.vue'
import DocumentPage from '@/views/DocumentPage.vue'
import ElectronicSealPage from '@/views/ElectronicSealPage.vue'
import EventReminderPage from '@/views/EventReminderPage.vue'
import SystemSettingPage from '@/views/SystemSettingPage.vue'
import FinancePage from '@/views/FinancePage.vue'
import { ElMessage } from 'element-plus'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage },
  {
    path: '/main',
    component: DashBoard,
    redirect: '/main/cases',
    children: [
      { path: 'cases', component: CasesPage },
      { path: 'lawyers', component: LawyerManagePage, meta: { roles: ['owner', 'admin'] } },
      { path: 'case_review', component: CaseReviewPage, meta: { roles: ['owner', 'admin'] } },
      {
        path: 'cases/:id',
        name: 'CaseDetail',
        component: CaseDetailPage,
        meta: { title: '案件详情' },
      },
      { path: 'cases/bank_cases', component: BankCasesPage },
      { path: 'user_profile', component: UserProfilePage },
      { path: 'document_template', component: DocumentPage },
      { path: 'electronic_seal', component: ElectronicSealPage },
      { path: 'finance', component: FinancePage },
      { path: 'reminders', component: EventReminderPage },
      {
        path: 'admin/settings',
        component: SystemSettingPage,
        meta: {
          requiresSuperAdmin: true, // 标记需要超级权限
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 白名单：不需要登录就能访问的路由
const whiteList = ['/login']

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  const userId = localStorage.getItem('user_id')

  if (!token && !whiteList.includes(to.path)) {
    // ❌ 没有登录，且访问的不是白名单页面 → 强制跳转到登录页
    next('/login')
    return
  }
  if (token && to.path === '/login') {
    // ✅ 已登录还去登录页 → 自动跳转到主界面
    next('/main')
    return
  }
  // 如果没有 Token 但在白名单 -> 放行
  if (!token && whiteList.includes(to.path)) {
    next()
    return
  }

  // 超级管理员权限检查
  if (to.meta.requiresSuperAdmin) {
    if (role === 'owner' && String(userId) === '1') {
      next()
    } else {
      ElMessage.error('您无权访问后台管理系统')
      next('/main')
    }
    return
  }

  // 检查是否有 roles 限制
  if (to.meta && to.meta.roles) {
    if (to.meta.roles.includes(role)) {
      next() // 有权限，放行
    } else {
      // 无权限，跳回首页或弹提示
      ElMessage.error('您没有权限访问该页面')
      next('/main')
    }
    return
  }
  next()
})

export default router
