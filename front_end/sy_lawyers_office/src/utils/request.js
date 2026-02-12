// src/utils/request.js
import axios from 'axios'
import router from '@/router' // 引入路由，用于401跳转
import { ElMessage } from 'element-plus' // 引入 Element Plus 的提示框

// 1. 创建 axios 实例
const service = axios.create({
  // 根据你的报错日志，后端地址是这个
  baseURL: 'http://127.0.0.1:8002',
  timeout: 5000, // 请求超时时间
})

// 2. 请求拦截器：自动加 Token
service.interceptors.request.use(
  (config) => {
    // 假设你的 token 存放在 localStorage 的 'token' 键中
    // 如果你的 token 叫 'access_token' 或其他名字，请修改这里
    const token = localStorage.getItem('token')

    if (token) {
      // ⚠️ 重点：这里就是解决 401 的关键
      // 大部分后端需要 Bearer 前缀，具体看后端文档
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 3. 响应拦截器：处理错误
service.interceptors.response.use(
  (response) => {
    // 如果后端返回的不是 200，可以在这里统一处理
    return response
  },
  (error) => {
    // 处理 401 错误
    if (error.response && error.response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 清除本地过期的 token
      localStorage.removeItem('token')
      // 跳转到登录页
      router.push('/login')
    } else {
      ElMessage.error(error.message || '请求失败')
    }
    return Promise.reject(error)
  },
)

export default service
