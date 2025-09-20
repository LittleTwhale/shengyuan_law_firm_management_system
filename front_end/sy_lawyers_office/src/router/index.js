import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/views/LoginPage.vue'
import MainPage from '@/views/MainPage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage },
  { path: '/main', component: MainPage },
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

export default router
