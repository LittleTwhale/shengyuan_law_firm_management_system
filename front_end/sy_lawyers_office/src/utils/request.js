// src/utils/request.js
import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'
import { handleErrorAnalysis } from './errorAnalysisNotify'

// 1. 创建 axios 实例
const service = axios.create({
  baseURL: 'http://127.0.0.1:8002/api',
  timeout: 60000, // 请求超时时间
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

      const userId = localStorage.getItem('user_id')
      if (userId) {
        localStorage.removeItem(`has_shown_urgent_reminder_${userId}`)
      }

      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
      localStorage.removeItem('permissions')

      router.push('/login')
    } else if (error.response && error.response.status === 500) {
      // 500 错误：检查是否携带 analysis_id（错误分析系统）
      const data = error.response.data
      if (data && data.analysis_id) {
        // 触发错误分析通知流程（轮询 + 弹窗）
        handleErrorAnalysis(data, data.detail)
      } else {
        // 普通 500 错误，显示服务器返回的消息
        ElMessage.error(data?.detail || '服务器内部错误')
      }
    } else if (error.response) {
      // 其他 HTTP 错误（4xx 等）：优先使用服务器返回的 detail 消息
      const serverMsg = error.response.data?.detail || error.response.data?.message
      ElMessage.error(serverMsg || error.message || '请求失败')
    } else {
      // 无响应（网络断开、超时等）
      ElMessage.error('网络连接失败，请检查网络后重试')
    }
    return Promise.reject(error)
  },
)

export default service
