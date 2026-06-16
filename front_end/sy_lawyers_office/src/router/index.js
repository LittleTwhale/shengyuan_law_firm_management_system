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
import PartyBuildingPage from '@/views/PartyBuildingPage.vue'
import PartyMaterialDetail from '@/views/PartyMaterialDetail.vue'
import VolumesPage from '@/views/VolumesPage.vue'
import StandaloneVolumePanel from '@/views/StandaloneVolumePanel.vue'
import AnnouncementCenter from '@/views/AnnouncementCenter.vue'
import AIAnalysisPage from '@/views/AIAnalysisPage.vue'
import LegalSearchPage from '@/views/LegalSearchPage.vue'
import ErrorAnalysisPage from '@/views/ErrorAnalysisPage.vue'
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
      { path: 'case_review', component: CaseReviewPage, meta: { requiresReview: true } },
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
      { path: 'party_building', component: PartyBuildingPage },
      { path: 'party_building/detail/:id', component: PartyMaterialDetail },
      { path: 'reminders', component: EventReminderPage },
      { path: 'volumes', component: VolumesPage, meta: { title: '电子卷宗中心' } },
      { path: 'standalone-volume/:volumeId', name: 'StandaloneVolume', component: StandaloneVolumePanel, meta: { title: '独立卷宗管理' } },
      {
        path: 'admin/settings',
        component: SystemSettingPage,
        meta: {
          requiresAdmin: true,
        },
      },
      { path: 'announcements', component: AnnouncementCenter, meta: { title: '公告中心' } },
      {
        path: 'ai-analysis',
        component: AIAnalysisPage,
        meta: { title: '智能分析（试运行）' },
      },
      {
        path: 'legal-search',
        component: LegalSearchPage,
        meta: { title: '法律知识库' },
      },
      {
        path: 'error-analyses',
        component: ErrorAnalysisPage,
        meta: { title: '错误分析' },
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

  // 安全地解析权限 JSON
  let permissions = {}
  try {
    permissions = JSON.parse(localStorage.getItem('permissions') || '{}')
  } catch (e) {
    console.error('解析权限失败', e)
  }

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

  // 后台管理员权限检查
  if (to.meta.requiresAdmin) {
    const hasAdminAccess = role === 'owner' || permissions.can_access_admin === true
    if (hasAdminAccess) {
      next()
    } else {
      ElMessage.error('权限不足，无法访问后台管理')
      next('/main') // 踢回工作台
    }
    return
  }

  // 业务审核权限检查
  if (to.meta.requiresReview) {
    const hasReviewAccess = role === 'owner' || permissions.can_review_case === true
    if (hasReviewAccess) {
      next()
    } else {
      ElMessage.error('权限不足，无法访问审核页面')
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
