<template>
  <div class="login-container">
    <!-- 背景容器 -->
    <div ref="backgroundContainer" class="background-canvas"></div>

    <div class="login-card">
      <div class="firm-header">
        <div class="firm-logo">
          <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image" />
        </div>
      </div>

      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入登录账号"
            prefix-icon="User"
            size="large"
          ></el-input>
        </el-form-item>

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

      <div class="login-footer">
        <p>© {{ currentYear }} 湖南生元律师事务所 版权所有</p>
        <p style="font-size: 10px; opacity: 0.5;">渲染模式: {{ renderMode }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import * as THREE from 'three' // 引入 Three.js

// ===== 路由与状态 =====
const router = useRouter()
const currentYear = ref(new Date().getFullYear())
const loginForm = ref({ username: '', password: '' })
const loginLoading = ref(false)
const loginFormRef = ref(null)
const renderMode = ref('Detecting...') // 'WebGL' 或 'Canvas2D'

// ===== 表单验证规则 =====
const loginRules = ref({
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度需在3-20个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在6-20个字符之间', trigger: 'blur' },
  ],
})

// ==========================================
// ===== 背景动效管理器 (Three.js / Canvas 2D) =====
// ==========================================
const backgroundContainer = ref(null)
let animationId = null
let cleanupFunction = null // 用于存储清理函数

// 检测是否为移动端
const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 检测是否支持 WebGL
const isWebGLAvailable = () => {
  try {
    const canvas = document.createElement('canvas')
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')))
  } catch (e) {
    console.error('WebGL 不可用',e)
    return false
  }
}

// ------------------------------------------
// 策略 1: Three.js (高性能，桌面端)
// ------------------------------------------
let scene, camera, renderer, particlesMesh
let mouseX = 0
let mouseY = 0
let windowHalfX = window.innerWidth / 2
let windowHalfY = window.innerHeight / 2

const createSprite = () => {
  const canvas = document.createElement('canvas')
  canvas.width = 32
  canvas.height = 32
  const context = canvas.getContext('2d')
  const gradient = context.createRadialGradient(16, 16, 0, 16, 16, 16)
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1)')
  gradient.addColorStop(0.2, 'rgba(200, 230, 255, 1)')
  gradient.addColorStop(0.5, 'rgba(64, 150, 255, 0.4)')
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
  context.fillStyle = gradient
  context.fillRect(0, 0, 32, 32)
  return new THREE.CanvasTexture(canvas)
}

const onDocumentMouseMove = (event) => {
  mouseX = event.clientX - windowHalfX
  mouseY = event.clientY - windowHalfY
}

const initThreeJS = () => {
  if (!backgroundContainer.value) return

  // 1. 场景
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x050a14, 0.0008)

  // 2. 相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 3000)
  camera.position.z = 1000

  // 3. 渲染器
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(window.innerWidth, window.innerHeight)
  backgroundContainer.value.appendChild(renderer.domElement)

  // 4. 粒子几何体
  const particleCount = 2000
  const geometry = new THREE.BufferGeometry()
  const positions = []
  const colors = []
  const colorObj = new THREE.Color()
  const colorDeep = new THREE.Color('#d416ff')
  const colorLight = new THREE.Color('#b1ffa0')

  for (let i = 0; i < particleCount; i++) {
    const x = (Math.random() * 2 - 1) * 1500
    const y = (Math.random() * 2 - 1) * 1500
    const z = (Math.random() * 2 - 1) * 1500
    positions.push(x, y, z)
    const mixRatio = Math.random()
    colorObj.copy(colorDeep).lerp(colorLight, mixRatio)
    colors.push(colorObj.r, colorObj.g, colorObj.b)
  }

  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))

  // 5. 材质
  const material = new THREE.PointsMaterial({
    size: 18,
    map: createSprite(),
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    depthTest: false,
    transparent: true,
    opacity: 0.8,
  })

  // 6. 网格
  particlesMesh = new THREE.Points(geometry, material)
  scene.add(particlesMesh)

  // 7. 交互
  document.addEventListener('mousemove', onDocumentMouseMove)

  const animateThree = () => {
    animationId = requestAnimationFrame(animateThree)
    particlesMesh.rotation.x += 0.0003
    particlesMesh.rotation.y += 0.0005
    camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.05
    camera.position.y += (-mouseY * 0.5 - camera.position.y) * 0.05
    camera.lookAt(scene.position)
    renderer.render(scene, camera)
  }

  animateThree()

  // 返回清理函数
  return () => {
    if (renderer) {
      renderer.dispose()
      if (backgroundContainer.value && renderer.domElement) {
        backgroundContainer.value.removeChild(renderer.domElement)
      }
    }
    document.removeEventListener('mousemove', onDocumentMouseMove)
  }
}

// ------------------------------------------
// 策略 2: Canvas 2D (低功耗，移动端/老旧PC)
// ------------------------------------------
const initCanvas2D = () => {
  if (!backgroundContainer.value) return

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  backgroundContainer.value.appendChild(canvas)

  let width, height
  const particles = []
  const particleCount = 200

  const resize = () => {
    width = window.innerWidth
    height = window.innerHeight
    canvas.width = width
    canvas.height = height
  }

  resize()

  // 简单的粒子类
  class Particle2D {
    constructor() {
      this.reset()
    }

    reset() {
      this.x = Math.random() * width
      this.y = Math.random() * height
      this.vx = (Math.random() - 0.5)
      this.vy = (Math.random() - 0.5)
      this.size = Math.random() * 3 + 1
      this.alpha = Math.random() * 0.5 + 0.1
      // 随机分配颜色，模拟 Three.js 的渐变色
      this.color = Math.random() > 0.5 ? '177, 255, 160' : '212, 22, 255' // RGB 对应 #b1ffa0 和 #d416ff
    }

    update() {
      this.x += this.vx
      this.y += this.vy

      // 边界检查，超出屏幕重置
      if (this.x < 0 || this.x > width || this.y < 0 || this.y > height) {
        this.reset()
      }
    }

    draw() {
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${this.color}, ${this.alpha})`
      ctx.fill()

      // 简单的发光效果
      ctx.shadowBlur = 10
      ctx.shadowColor = `rgba(${this.color}, ${this.alpha})`
    }
  }

  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle2D())
  }

  const animateCanvas = () => {
    animationId = requestAnimationFrame(animateCanvas)
    ctx.clearRect(0, 0, width, height)

    // 启用 additive blending 模拟 Three.js 效果
    ctx.globalCompositeOperation = 'lighter'

    particles.forEach(p => {
      p.update()
      p.draw()
    })
  }

  animateCanvas()

  return () => {
    if (backgroundContainer.value && canvas) {
      backgroundContainer.value.removeChild(canvas)
    }
  }
}

// ------------------------------------------
// 公共逻辑
// ------------------------------------------

// 窗口大小调整监听 (通用)
const onWindowResizeCommon = () => {
  windowHalfX = window.innerWidth / 2
  windowHalfY = window.innerHeight / 2

  if (renderMode.value === 'WebGL' && camera && renderer) {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  } else if (renderMode.value === 'Canvas2D') {
    const canvas = backgroundContainer.value.querySelector('canvas')
    if(canvas) {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
  }
}

// ===== 生命周期 =====
onMounted(() => {
  // 策略选择逻辑
  const mobile = isMobileDevice()
  const webgl = isWebGLAvailable()

  if (!mobile && webgl) {
    renderMode.value = 'WebGL'
    cleanupFunction = initThreeJS()
  } else {
    // 移动端 或 不支持 WebGL 的老电脑 -> 使用 2D Canvas
    renderMode.value = 'Canvas2D'
    cleanupFunction = initCanvas2D()
  }

  window.addEventListener('resize', onWindowResizeCommon)
})

onBeforeUnmount(() => {
  // 清理资源
  if (cleanupFunction) cleanupFunction()
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', onWindowResizeCommon)
})

// ===== 处理登录逻辑 (保持不变) =====
const handleLogin = async () => {
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    const res = await axios.post(
      'http://127.0.0.1:8002/auth/login',
      {
        accounts: loginForm.value.username,
        password: loginForm.value.password,
      },
      {
        headers: { 'Content-Type': 'application/json' },
      },
    )

    const token = res.data.access_token
    const username = res.data.user.real_name
    const role = res.data.user.role
    const user_id = res.data.user.id

    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    localStorage.setItem('role', role)
    localStorage.setItem('user_id', user_id)

    ElMessage.success(`欢迎 ${username} 登录系统！`)
    await router.push('/main')
  } catch (err) {
    console.error('登录错误详情：', err.response?.data)
    ElMessage.error(
      typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : JSON.stringify(err.response?.data?.detail) || '登录失败',
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
  /* 深空背景色，作为底色 */
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
}

.background-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none; /* 确保不阻挡交互 */
}

.login-card {
  position: relative;
  z-index: 1; /* 确保卡片浮在粒子之上 */
  width: 100%;
  max-width: 420px;
  /* 增加卡片背景透明度，让背后的 3D/2D 粒子隐约可见 */
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px); /* 毛玻璃效果 */
  -webkit-backdrop-filter: blur(10px); /* Safari 兼容 */
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  padding: 30px;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.firm-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
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
  background-color: #165dff;
  border: none;
  transition: all 0.3s;
}

.login-btn:hover {
  background-color: #0e42d2;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  font-size: 12px;
  color: #666;
}

@media (max-width: 375px) {
  .login-card {
    padding: 20px;
  }
}
</style>
