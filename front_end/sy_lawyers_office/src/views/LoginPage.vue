<template>
  <div class="login-container">
    <!-- 粒子背景Canvas -->
    <canvas ref="canvasRef" class="particle-canvas"></canvas>

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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'

// ===== 路由实例 =====
const router = useRouter()

// ===== 当前年份 =====
const currentYear = ref(new Date().getFullYear())

// ===== 登录表单数据 =====
const loginForm = ref({
  username: '',
  password: ''
})

// ===== 登录按钮加载状态 =====
const loginLoading = ref(false)

// ===== 表单引用 =====
const loginFormRef = ref(null)

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

// ===== Canvas 粒子效果引用 =====
const canvasRef = ref(null)
let particles = []
let animationId = null

// ===== 粒子类 =====
class Particle {
  constructor(canvasWidth, canvasHeight) {
    this.x = Math.random() * canvasWidth
    this.y = Math.random() * canvasHeight
    this.vx = (Math.random() - 0.5)
    this.vy = (Math.random() - 0.5)
    this.radius = Math.random() * 2 + 1
  }

  // 绘制粒子
  draw(ctx) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(22, 93, 255, 0.7)'
    ctx.fill()
  }

  // 更新位置
  update(canvasWidth, canvasHeight) {
    this.x += this.vx
    this.y += this.vy
    if (this.x < 0 || this.x > canvasWidth) this.vx *= -1
    if (this.y < 0 || this.y > canvasHeight) this.vy *= -1
  }
}

// ===== 初始化粒子 =====
const initParticles = (canvas) => {
  const count = 80 // 粒子数量
  particles = []
  for (let i = 0; i < count; i++) {
    particles.push(new Particle(canvas.width, canvas.height))
  }
}

// ===== 动画循环 =====
const animate = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 更新和绘制粒子
  particles.forEach(p => p.update(canvas.width, canvas.height))
  particles.forEach(p => p.draw(ctx))

  // 粒子连线
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      let dx = particles[i].x - particles[j].x
      let dy = particles[i].y - particles[j].y
      let dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 100) {
        ctx.beginPath()
        ctx.strokeStyle = `rgba(22,93,255,${1 - dist / 100})`
        ctx.lineWidth = 0.5
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.stroke()
      }
    }
  }

  animationId = requestAnimationFrame(animate)
}

// ===== 窗口缩放处理 =====
const resizeCanvas = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  initParticles(canvas, canvas.getContext('2d'))
}

// ===== 生命周期 =====
onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  animate()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCanvas)
  cancelAnimationFrame(animationId)
})

// ===== 处理登录逻辑 =====
const handleLogin = async () => {
  try {
    // 表单验证
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    // 发送POST请求到FastAPI后端登录接口
    const res = await axios.post('http://127.0.0.1:8001/auth/login', {
      accounts: loginForm.value.username,
      password: loginForm.value.password
    }, {
      headers: { 'Content-Type': 'application/json' }
    })

    const token = res.data.access_token
    const username = res.data.user.real_name
    const role = res.data.user.role

    // 保存到本地存储
    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    localStorage.setItem('role', role)

    ElMessage.success(`欢迎 ${username} 登录系统！`)
    await router.push('/main')

  } catch (err) {
    console.error("登录错误详情：", err.response?.data)
    ElMessage.error(
      typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : JSON.stringify(err.response?.data?.detail) || '登录失败'
    )
  } finally {
    loginLoading.value = false
  }
}
</script>

<style scoped>
/* 登录容器 - 居中显示 */
.login-container {
  width: 100vw;
  height: 100vh;
  position: relative; /* 为粒子背景定位做准备 */
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  overflow: hidden;
}

/* 粒子Canvas样式 */
.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0; /* 粒子在卡片下方 */
}

/* 登录卡片样式 */
.login-card {
  position: relative;
  z-index: 1; /* 确保卡片在粒子层上方 */
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
