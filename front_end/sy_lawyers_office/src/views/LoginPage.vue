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
let hue = 0 // 粒子全局色相基准（保留动态变化）
let mouseX = null
let mouseY = null
let gradientPhase = 0 // 用于背景渐变动画

// ===== 粒子类 =====
class Particle {
  constructor(canvasWidth, canvasHeight) {
    this.x = Math.random() * canvasWidth
    this.y = Math.random() * canvasHeight
    this.vx = (Math.random() - 0.5) * 0.75
    this.vy = (Math.random() - 0.5) * 0.75
    this.radius = Math.random() * 3 + 2
    this.hue = Math.random() * 360
    this.alpha = 0.7
    this.delta = Math.random() * 0.02
  }
  draw(ctx, mouseX, mouseY) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
    ctx.shadowBlur = 20
    ctx.shadowColor = `hsla(${this.hue}, 100%, 50%, 0.5)`
    this.alpha += this.delta
    if (this.alpha > 1 || this.alpha < 0.3) this.delta *= -1
    ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${this.alpha})`
    ctx.fill()

    // 鼠标交互：粒子排斥
    if (mouseX && mouseY) {
      const dx = this.x - mouseX
      const dy = this.y - mouseY
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 100) {
        this.vx += dx / dist * 0.03
        this.vy += dy / dist * 0.03
      }
    }
  }
  update(canvasWidth, canvasHeight) {
    this.x += this.vx
    this.y += this.vy
    this.hue += 0.5 // 粒子自身色相缓慢变化
    if (this.x < 0 || this.x > canvasWidth) this.vx *= -1
    if (this.y < 0 || this.y > canvasHeight) this.vy *= -1
  }
}

// ===== 初始化粒子 =====
const initParticles = (canvas) => {
  const count = 50
  particles = []
  for (let i = 0; i < count; i++) {
    particles.push(new Particle(canvas.width, canvas.height))
  }
}

// ===== 动态渐变背景 (始终浅蓝→深蓝) =====
const drawGradientBackground = (ctx, canvas) => {
  gradientPhase += 0.003 // 渐变变化速度
  /*
    只在蓝色区间摆动：
    200°~240° 大约是浅蓝到深蓝
    用 sin/cos 让 hue 在蓝色系轻微波动
  */
  const blueHue = 220 + Math.sin(gradientPhase) * 20 // 在200-240间摆动
  const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
  gradient.addColorStop(0, `hsl(${blueHue}, 80%, 85%)`) // 浅蓝
  gradient.addColorStop(1, `hsl(${blueHue + 10}, 80%, 40%)`) // 深蓝
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, canvas.width, canvas.height)
}

// ===== 动画循环 =====
const animate = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  drawGradientBackground(ctx, canvas)

  hue = (hue + 0.5) % 360 // 粒子 hue 保持动态变化并取模，避免无限增大

  particles.forEach(p => p.update(canvas.width, canvas.height))
  particles.forEach(p => p.draw(ctx, mouseX, mouseY))

  // 粒子彩色连线
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      let dx = particles[i].x - particles[j].x
      let dy = particles[i].y - particles[j].y
      let dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 120) {
        ctx.beginPath()
        const grad = ctx.createLinearGradient(
          particles[i].x, particles[i].y,
          particles[j].x, particles[j].y
        )
        grad.addColorStop(0, `hsla(${particles[i].hue},100%,50%,${1 - dist / 120})`)
        grad.addColorStop(1, `hsla(${particles[j].hue},100%,50%,${1 - dist / 120})`)
        ctx.strokeStyle = grad
        ctx.lineWidth = Math.min(2, (120 - dist) / 60)
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
  initParticles(canvas)
}

// ===== 鼠标交互 =====
const setupMouseInteraction = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.addEventListener('mousemove', (e) => {
    mouseX = e.clientX
    mouseY = e.clientY
  })
  canvas.addEventListener('mouseleave', () => {
    mouseX = null
    mouseY = null
  })
}

// ===== 生命周期 =====
onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  setupMouseInteraction()
  animate()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCanvas)
  cancelAnimationFrame(animationId)
})

// ===== 处理登录逻辑 =====
const handleLogin = async () => {
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    const res = await axios.post('http://127.0.0.1:8001/auth/login', {
      accounts: loginForm.value.username,
      password: loginForm.value.password
    }, {
      headers: { 'Content-Type': 'application/json' }
    })

    const token = res.data.access_token
    const username = res.data.user.real_name
    const role = res.data.user.role
    const user_id= res.data.user.id

    sessionStorage.setItem('token', token)
    sessionStorage.setItem('username', username)
    sessionStorage.setItem('role', role)
    sessionStorage.setItem('user_id', user_id)

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
.login-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  overflow: hidden;
}
.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  padding: 30px;
  box-sizing: border-box;
}
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
.login-form .el-form-item {
  margin-bottom: 20px;
}
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
.login-footer {
  margin-top: 30px;
  text-align: center;
  font-size: 12px;
  color: #999999;
}
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
