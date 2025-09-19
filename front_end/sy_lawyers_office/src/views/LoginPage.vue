<template>
  <div class="login-container">
    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 律所Logo区域 -->
      <div class="firm-header">
        <div class="firm-logo">
          <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image">
        </div>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入登录账号"
            prefix-icon="User"
            size="large"
          ></el-input>
        </el-form-item>

        <!-- 密码输入框 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入登录密码"
            prefix-icon="Lock"
            size="large"
            @keydown.enter.prevent="handleLogin"
          ></el-input>
        </el-form-item>

        <!-- 记住账号 -->
        <el-form-item>
          <el-checkbox v-model="rememberMe">记住账号</el-checkbox>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            @click="handleLogin"
            :loading="loginLoading"
          >
            登录系统
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部信息 -->
      <div class="login-footer">
        <p>© {{ currentYear }} 湖南生元律师事务所 版权所有</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref } from 'vue'
import { ElForm, ElFormItem, ElInput, ElButton, ElMessage, ElCheckbox } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'

// ===== 路由实例 =====
const router = useRouter()

// ===== 当前年份 =====
const currentYear = ref(new Date().getFullYear())

// ===== 登录表单数据 =====
const loginForm = ref({
  username: '', // 律师账号
  password: ''  // 登录密码
})

// ===== 记住账号状态 =====
const rememberMe = ref(false)

// ===== 登录按钮加载状态 =====
const loginLoading = ref(false)

// ===== 表单验证规则 =====
const loginRules = ref({
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度需在3-20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在6-20个字符之间', trigger: 'blur' }
  ]
})

// ===== 表单引用 =====
const loginFormRef = ref(null)

/**
 * 处理登录逻辑
 */
const handleLogin = async () => {
  try {
    // 表单验证
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    // 发送POST请求到FastAPI后端登录接口
    const res = await axios.post('http://127.0.0.1:8000/login', {
      username: loginForm.value.username,
      password: loginForm.value.password
    }, {
      headers: { 'Content-Type': 'application/json' }
    })

    // 登录成功，获取 JWT Token
    const token = res.data.access_token
    const username = res.data.username
    const role = res.data.role

    // 保存 Token 到 localStorage，用于后续接口请求
    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    localStorage.setItem('role', role)

    // 处理记住账号
    if (rememberMe.value) {
      localStorage.setItem('rememberMe', 'true')
      localStorage.setItem('savedUsername', username)
    } else {
      localStorage.removeItem('rememberMe')
      localStorage.removeItem('savedUsername')
    }

    // 显示成功消息
    ElMessage.success(`欢迎 ${username} 登录系统！`)

    // 跳转到主界面
    await router.push('/main')

  } catch (err) {
    // 登录失败处理
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '登录失败')
  } finally {
    loginLoading.value = false
  }
}

/**
 * 页面初始化 - 读取记住的账号
 */
const initPage = () => {
  const savedRemember = localStorage.getItem('rememberMe') === 'true'
  const savedUsername = localStorage.getItem('savedUsername')

  if (savedRemember && savedUsername) {
    loginForm.value.username = savedUsername
    rememberMe.value = true
  }
}

// 页面初始化
initPage()
</script>

<style scoped>
/* 登录容器 - 居中显示 */
.login-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

/* 登录卡片样式 */
.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  padding: 30px;
  box-sizing: border-box;
}

/* 律所头部 */
.firm-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.firm-logo {
  width: 260px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 登录表单 */
.login-form .el-form-item {
  margin-bottom: 20px;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  background-color: #165DFF;
  border: none;
}

.login-btn:hover {
  background-color: #0E42D2;
}

/* 底部信息 */
.login-footer {
  margin-top: 30px;
  text-align: center;
  font-size: 12px;
  color: #999999;
}

/* 响应式调整 */
@media (max-width: 375px) {
  .login-card {
    padding: 20px;
  }
  .firm-header {
    flex-direction: column;
    text-align: center;
  }
}
</style>
