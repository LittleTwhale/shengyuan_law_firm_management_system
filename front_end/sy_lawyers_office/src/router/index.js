import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/views/LoginPage.vue'
import DashBoard from '@/views/DashBoard.vue'
import CasesPage from '@/views/CasesPage.vue'
import LawyerManagePage from '@/views/LawyerManagePage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage },
  {
    path: '/main',
    component: DashBoard,
    redirect: '/main/cases',
    children: [
      { path: 'cases', component: CasesPage },
      { path: 'lawyers', component: LawyerManagePage, meta: { roles: ['owner', 'admin'] } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 白名单：不需要登录就能访问的路由
const whiteList = ['/login']

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (!token && !whiteList.includes(to.path)) {
    // ❌ 没有登录，且访问的不是白名单页面 → 强制跳转到登录页
    next('/login')
  } else if (token && to.path === '/login') {
    // ✅ 已登录还去登录页 → 自动跳转到主界面
    next('/main')
  } else {
    // ✅ 其他情况放行
    next()
  }
})

router.beforeEach((to, from, next) => {
  const role = localStorage.getItem('role')  // 从本地存储获取用户角色

  // 检查是否有 roles 限制
  if (to.meta && to.meta.roles) {
    if (to.meta.roles.includes(role)) {
      next()  // 有权限，放行
    } else {
      // 无权限，跳回 dashboard 首页或弹提示
      alert('您没有权限访问该页面')
      next('/main')
    }
  } else {
    next() // 没有角色限制的页面直接放行
  }
})

export default router
