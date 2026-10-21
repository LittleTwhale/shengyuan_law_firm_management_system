<template>
  <div ref="pageEl" class="login-page">
    <!-- ==================================================
         水墨背景舞台
         ================================================== -->
    <div class="scene" aria-hidden="true">
      <!-- SVG 滤镜与渐变定义 -->
      <svg class="svg-defs" width="0" height="0" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <!-- 山体墨色：靠近山脊处浓，往下逐渐化开 -->
          <linearGradient id="grad-far" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#231f1a" stop-opacity=".15" />
            <stop offset="55%" stop-color="#231f1a" stop-opacity=".06" />
            <stop offset="100%" stop-color="#231f1a" stop-opacity=".01" />
          </linearGradient>
          <linearGradient id="grad-mid" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#231f1a" stop-opacity=".26" />
            <stop offset="48%" stop-color="#231f1a" stop-opacity=".13" />
            <stop offset="100%" stop-color="#231f1a" stop-opacity=".03" />
          </linearGradient>
          <linearGradient id="grad-near" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#231f1a" stop-opacity=".34" />
            <stop offset="52%" stop-color="#231f1a" stop-opacity=".24" />
            <stop offset="100%" stop-color="#231f1a" stop-opacity=".14" />
          </linearGradient>

          <!-- 书法字的墨色渐变：模拟笔锋含墨量的变化 -->
          <linearGradient id="ink-word-fill" x1="0" y1="0" x2="0.25" y2="1">
            <stop offset="0%" stop-color="#0a0806" />
            <stop offset="42%" stop-color="#241e18" />
            <stop offset="100%" stop-color="#584f43" />
          </linearGradient>

          <!-- 山脊毛边：位移滤镜让边缘不再是干净的折线 -->
          <filter id="ink-edge" x="-10%" y="-20%" width="120%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.006 0.018" numOctaves="4" seed="6" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="16" xChannelSelector="R" yChannelSelector="G" />
            <feGaussianBlur stdDeviation="0.4" />
          </filter>
          <filter id="ink-edge-soft" x="-10%" y="-20%" width="120%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.004 0.012" numOctaves="3" seed="11" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="20" xChannelSelector="R" yChannelSelector="G" />
            <feGaussianBlur stdDeviation="1" />
          </filter>

          <!-- 书法艺术字：毛边 + 飞白（用高频噪点啃出枯墨） -->
          <filter id="ink-word-bleed" x="-30%" y="-30%" width="160%" height="160%">
            <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="4" seed="9" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="11" xChannelSelector="R" yChannelSelector="G" result="warped" />
            <feTurbulence type="fractalNoise" baseFrequency="0.68" numOctaves="3" seed="3" result="grain" />
            <feColorMatrix
              in="grain"
              type="matrix"
              values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 2.8 -0.92"
              result="grainMask"
            />
            <feComposite in="warped" in2="grainMask" operator="in" result="dry" />
            <feGaussianBlur in="dry" stdDeviation="1.1" />
          </filter>
        </defs>
      </svg>

      <!-- 远日：山后一团极淡暖光 -->
      <div class="sun"></div>

      <!-- 三层山脊 -->
      <div class="mountain-layer mountain-far">
        <svg viewBox="0 0 1600 480" preserveAspectRatio="none">
          <path
            filter="url(#ink-edge-soft)"
            d="M0 352 L 88 308 L 148 266 L 214 298 L 302 202
               L 364 252 L 428 220 L 508 150 L 572 208 L 638 184 L 716 238 L 796 172
               L 866 226 L 948 198 L 1028 246 L 1108 210 L 1190 250 L 1278 214
               L 1368 254 L 1458 222 L 1546 250 L 1600 230 L 1600 480 L 0 480 Z"
          />
        </svg>
      </div>
      <div class="mountain-layer mountain-mid">
        <svg viewBox="0 0 1600 480" preserveAspectRatio="none">
          <path
            filter="url(#ink-edge)"
            d="M0 402 L 96 376 L 176 340 L 262 360 L 350 300
               L 432 332 L 516 312 L 604 266 L 686 306 L 764 288 L 852 324 L 934 292
               L 1014 332 L 1096 306 L 1180 340 L 1264 312 L 1348 344 L 1436 318
               L 1524 346 L 1600 330 L 1600 480 L 0 480 Z"
          />
        </svg>
      </div>
      <div class="mountain-layer mountain-near">
        <svg viewBox="0 0 1600 480" preserveAspectRatio="none">
          <path
            filter="url(#ink-edge)"
            d="M0 442 L 118 426 L 220 410 L 332 424 L 444 400
               L 556 416 L 668 398 L 782 418 L 902 402 L 1022 420 L 1142 404
               L 1262 422 L 1382 408 L 1502 424 L 1600 412 L 1600 480 L 0 480 Z"
          />
        </svg>
      </div>

      <!-- 云雾 -->
      <div class="mist mist-a"></div>
      <div class="mist mist-b"></div>
      <div class="mist mist-c"></div>

      <!-- 飞鸟 -->
      <svg class="birds" viewBox="0 0 300 96">
        <path d="M22 38 Q 33 26 44 38 Q 55 26 66 38" />
        <path d="M104 22 Q 112 13 120 22 Q 128 13 136 22" />
        <path d="M168 52 Q 175 44 182 52 Q 189 44 196 52" />
        <path d="M226 30 Q 232 23 238 30 Q 244 23 250 30" />
        <path d="M268 62 Q 273 57 278 62 Q 283 57 288 62" />
      </svg>

      <!-- 书法艺术字「生元」：已转为矢量路径，不依赖字体 -->
      <div class="ink-word">
        <svg class="ink-char" viewBox="163 93 751 823">
          <g transform="translate(0,802) scale(1,-1)">
            <path fill="url(#ink-word-fill)" d="M602 15Q656 27 676.0 27.0Q696 27 727.0 20.0Q758 13 774.5 -17.5Q791 -48 791.0 -57.5Q791 -67 777.0 -75.5Q763 -84 746.5 -84.0Q730 -84 718 -81Q661 -69 605 -69Q510 -69 442 -103Q420 -114 398.5 -114.0Q377 -114 363.5 -96.0Q350 -78 350 -47Q350 -23 373.5 -3.0Q397 17 472 53Q429 84 400.0 98.0Q371 112 371 136Q371 155 404.5 188.5Q438 222 537 274L539 334Q481 300 394 233Q387 228 381.5 228.0Q376 228 365.0 231.5Q354 235 311 239Q294 241 278.5 274.0Q263 307 263 335Q263 342 265 347Q304 458 304.0 471.0Q304 484 301.0 494.5Q298 505 298.0 510.5Q298 516 301 516Q307 516 346.0 469.0Q385 422 385 387Q385 374 381 354Q404 356 548 439Q567 594 567.0 620.0Q567 646 558.5 658.5Q550 671 550.0 682.5Q550 694 556.5 701.5Q563 709 574 709Q600 709 633.0 658.5Q666 608 666 586Q666 576 658 556Q656 550 656.0 540.5Q656 531 665.0 516.5Q674 502 694.5 502.0Q715 502 733.5 484.5Q752 467 752.0 450.5Q752 434 718.5 421.5Q685 409 615 376Q610 348 602 275Q648 262 674.0 238.0Q700 214 700 188Q700 178 696.5 169.0Q693 160 663.5 126.5Q634 93 602 60ZM503 79Q537 109 537 130Q537 141 527 141Q524 141 509.0 136.0Q494 131 486.5 129.5Q479 128 459.0 128.0Q439 128 430.0 124.0Q421 120 421 115Q421 104 446.5 91.0Q472 78 503 79Z" />
          </g>
        </svg>
        <svg class="ink-char" viewBox="163 93 751 823">
          <g transform="translate(0,802) scale(1,-1)">
            <path fill="url(#ink-word-fill)" d="M402 488Q371 520 349.5 559.5Q328 599 328.0 607.0Q328 615 333.5 615.0Q339 615 347.0 610.5Q355 606 367 606Q398 606 447.0 625.0Q496 644 525 668Q542 682 569.5 682.0Q597 682 623.0 663.0Q649 644 649 611Q649 594 641.5 581.0Q634 568 614.0 561.5Q594 555 583.5 549.5Q573 544 553.5 526.5Q534 509 460.0 455.0Q386 401 298.0 367.0Q210 333 205.5 333.0Q201 333 201 334Q201 342 402 488ZM533 316Q543 317 552 317Q582 317 599.0 303.5Q616 290 616.0 270.5Q616 251 604 236Q559 180 536.0 129.5Q513 79 513.0 55.5Q513 32 524.5 20.0Q536 8 555.5 7.0Q575 6 618.0 6.0Q661 6 723.0 13.0Q785 20 806.0 56.5Q827 93 827 152L823 211Q823 222 827 222Q833 222 845.0 188.5Q857 155 864.0 121.0Q871 87 875.0 75.5Q879 64 889 54Q914 28 914 6Q914 -30 841.0 -50.5Q768 -71 658 -71Q576 -71 543.0 -66.0Q510 -61 488.0 -47.5Q466 -34 453.5 -7.5Q441 19 441.0 47.0Q441 75 455.5 116.0Q470 157 509 238Q518 256 518.0 269.0Q518 282 507 292Q469 260 426.0 211.5Q383 163 362 132Q289 23 256.0 -12.0Q223 -47 207 -47Q188 -47 188 -9Q188 7 191.0 24.5Q194 42 197.0 45.0Q200 48 212 48Q228 48 253.5 77.0Q279 106 337 199Q281 176 253.0 176.0Q225 176 194.0 214.5Q163 253 163.0 288.0Q163 323 182 323Q188 323 188.0 319.0Q188 315 186.5 312.5Q185 310 185 306Q185 288 215 288Q231 288 279.5 305.5Q328 323 385.5 348.0Q443 373 486.5 396.0Q530 419 543.0 428.0Q556 437 563.0 449.0Q570 461 576.0 464.0Q582 467 598 467Q688 467 688 429Q688 408 679.0 399.0Q670 390 640.0 380.5Q610 371 589.5 359.5Q569 348 533 316Z" />
          </g>
        </svg>
        <i class="splash"></i>
      </div>

      <!-- 鼠标墨迹 -->
      <canvas ref="trailCanvas" class="trail"></canvas>

      <!-- 纸纹 -->
      <div class="grain"></div>
    </div>

    <!-- ==================================================
         品牌区
         ================================================== -->
    <div class="brand">
      <img class="brand-logo" src="@/assets/img/logo.png" alt="湖南生元律师事务所" />
      <div class="brand-rule"></div>
      <div class="brand-en">HUNAN SHENGYUAN LAW FIRM</div>
      <div class="seal" aria-hidden="true"><span>生</span><span>元</span></div>
    </div>

    <!-- ==================================================
         登录卡片
         ================================================== -->
    <main class="card">
      <h1>律所办公系统</h1>
      <p class="card-sub">请使用您的账号登录</p>

      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入登录账号"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入登录密码"
            :prefix-icon="Lock"
            size="large"
            @keydown.enter.prevent="handleLogin"
          />
        </el-form-item>

        <el-form-item class="submit-item">
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loginLoading"
            @click="handleLogin"
          >
            登录系统
          </el-button>
        </el-form-item>
      </el-form>

      <p class="copyright">© {{ currentYear }} 湖南生元律师事务所 版权所有</p>
    </main>

    <!-- ==================================================
         页脚
         ================================================== -->
    <div class="footer">
      <i></i>
      <span>湖南 · 湘西</span>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
// 图标以组件形式传入：Element Plus 的 prefix-icon 传字符串时需要图标已全局注册，
// 而项目只在 main.js 里 use(ElementPlus)，没有注册图标库，直接引进来最稳妥
import { Lock, User } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// ===== 路由与状态 =====
const router = useRouter()
const currentYear = ref(new Date().getFullYear())
const loginForm = ref({ username: '', password: '' })
const loginLoading = ref(false)
/** @type {import('vue').Ref<import('element-plus').FormInstance | undefined>} */
const loginFormRef = ref()
/** @type {import('vue').Ref<HTMLDivElement | undefined>} */
const pageEl = ref()
/** @type {import('vue').Ref<HTMLCanvasElement | undefined>} */
const trailCanvas = ref()

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
// 水墨背景：鼠标墨迹
// ==========================================
let rafTrail = null

/**
 * 每个墨点都是一条独立记录，带固定寿命，逐帧全量重绘。
 * 不能用 destination-out 逐帧擦除：alpha 降到 1/255 后会被舍入卡住，
 * 边缘会永久残留成一圈轮廓。
 */
const initInkTrail = (canvas) => {
  if (!canvas) return null

  const ctx = canvas.getContext('2d')
  let w = 0
  let h = 0
  const dpr = Math.min(window.devicePixelRatio || 1, 2)

  const resize = () => {
    w = window.innerWidth
    h = window.innerHeight
    canvas.width = w * dpr
    canvas.height = h * dpr
    canvas.style.width = `${w}px`
    canvas.style.height = `${h}px`
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  resize()

  // 预渲染一团墨，之后每帧 drawImage 复用，比反复创建径向渐变快得多
  const SPRITE = 64
  const sprite = document.createElement('canvas')
  sprite.width = sprite.height = SPRITE
  const sg = sprite.getContext('2d')
  const grd = sg.createRadialGradient(SPRITE / 2, SPRITE / 2, 0, SPRITE / 2, SPRITE / 2, SPRITE / 2)
  grd.addColorStop(0, 'rgba(42, 39, 36, 1)')
  grd.addColorStop(0.42, 'rgba(42, 39, 36, 0.4)')
  grd.addColorStop(1, 'rgba(42, 39, 36, 0)')
  sg.fillStyle = grd
  sg.fillRect(0, 0, SPRITE, SPRITE)

  const dabs = []
  const MAX_DABS = 700
  const DAB_LIFE = 3600 // 墨点寿命（毫秒）
  let lastX = null
  let lastY = null

  const drop = (x, y) => {
    dabs.push({
      x,
      y,
      r: 18 + Math.random() * 15,
      a: 0.032 + Math.random() * 0.02,
      born: performance.now(),
      life: DAB_LIFE + Math.random() * 900,
    })
    if (dabs.length > MAX_DABS) dabs.shift()
  }

  const onMove = (e) => {
    const x = e.clientX
    const y = e.clientY
    // 沿移动路径补点，快速划过时也不会断成一节一节
    if (lastX !== null) {
      const dist = Math.hypot(x - lastX, y - lastY)
      const steps = Math.min(8, Math.max(1, Math.round(dist / 20)))
      for (let i = 1; i <= steps; i++) {
        const t = i / steps
        drop(lastX + (x - lastX) * t, lastY + (y - lastY) * t)
      }
    } else {
      drop(x, y)
    }
    lastX = x
    lastY = y
  }

  const onLeave = () => {
    lastX = null
    lastY = null
  }

  const render = (now) => {
    ctx.clearRect(0, 0, w, h)
    for (let i = dabs.length - 1; i >= 0; i--) {
      const d = dabs[i]
      const age = (now - d.born) / d.life
      if (age >= 1) {
        dabs.splice(i, 1)
        continue
      }
      // 二次曲线淡出：末段掉得极快，不会在边缘拖出残留
      const fade = (1 - age) * (1 - age)
      const r = d.r * (1 + age * 0.7)
      ctx.globalAlpha = d.a * fade
      ctx.drawImage(sprite, d.x - r, d.y - r, r * 2, r * 2)
    }
    ctx.globalAlpha = 1
    rafTrail = requestAnimationFrame(render)
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerleave', onLeave)
  window.addEventListener('resize', resize)
  rafTrail = requestAnimationFrame(render)

  return () => {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerleave', onLeave)
    window.removeEventListener('resize', resize)
    if (rafTrail) cancelAnimationFrame(rafTrail)
  }
}

// ==========================================
// 水墨背景：鼠标视差
// ==========================================
let rafParallax = null

/**
 * 视差：三层山脊按不同幅度横移
 * @param {HTMLElement | undefined} el 写入 CSS 变量的宿主元素
 */
const initParallax = (el) => {
  if (!el) return null
  let targetX = 0
  let currentX = 0

  const onMove = (e) => {
    targetX = (e.clientX / window.innerWidth) * 2 - 1
  }

  const tick = () => {
    // 缓动跟随，避免鼠标一动山就跳
    currentX += (targetX - currentX) * 0.045
    // 写在组件根元素的行内样式上，优先级高于 CSS 里的默认值，视差照常生效
    el.style.setProperty('--px-far', `${(-currentX * 10).toFixed(2)}px`)
    el.style.setProperty('--px-mid', `${(-currentX * 18).toFixed(2)}px`)
    el.style.setProperty('--px-near', `${(-currentX * 28).toFixed(2)}px`)
    rafParallax = requestAnimationFrame(tick)
  }

  window.addEventListener('pointermove', onMove)
  tick()

  return () => {
    window.removeEventListener('pointermove', onMove)
    if (rafParallax) cancelAnimationFrame(rafParallax)
  }
}

// ===== 生命周期 =====
let detachTrail = null
let detachParallax = null

onMounted(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduceMotion) return

  detachTrail = initInkTrail(trailCanvas.value)
  detachParallax = initParallax(pageEl.value)
})

onBeforeUnmount(() => {
  if (detachTrail) detachTrail()
  if (detachParallax) detachParallax()
  detachTrail = null
  detachParallax = null
})

// ===== 登录逻辑 =====
const handleLogin = async () => {
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    const res = await axios.post(
      'http://127.0.0.1:8002/api/auth/login',
      {
        accounts: loginForm.value.username,
        password: loginForm.value.password,
      },
      {
        headers: { 'Content-Type': 'application/json' },
      },
    )

    // 解构取值：比 res.data.xxx 逐条访问更容易被静态分析识别
    const { access_token: token, user } = res.data
    const username = user.real_name
    const role = user.role
    const user_id = user.id
    const permissions = user.permissions

    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    localStorage.setItem('role', role)
    localStorage.setItem('user_id', user_id)
    localStorage.setItem('permissions', JSON.stringify(permissions))

    localStorage.removeItem(`has_shown_urgent_reminder_${user_id}`)

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
/* ============================================================
   基础
   ============================================================ */
.login-page {
  position: fixed;
  inset: 0;
  overflow: hidden;
  /* 视差用的三个位移量：这里给出静态默认值，
     实际值由 initParallax 以行内样式覆盖 */
  --px-far: 0px;
  --px-mid: 0px;
  --px-near: 0px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: #2a2724;
  /* 背景直接在根容器上：Logo 用 mix-blend-mode 融进纸面时，
     混合的底必须是这层渐变，否则会露出白方块 */
  background:
    radial-gradient(1100px circle at 18% 12%, rgba(226, 214, 192, 0.55), transparent 62%),
    radial-gradient(900px circle at 86% 84%, rgba(214, 202, 182, 0.38), transparent 60%),
    #f6f2e9;
}

.scene {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.svg-defs {
  position: absolute;
}

/* ============================================================
   远日：山后一团淡暖光
   ============================================================ */
.sun {
  position: absolute;
  left: 20%;
  bottom: 28%;
  width: 380px;
  height: 380px;
  z-index: 1;
  pointer-events: none;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(198, 142, 84, 0.17) 0%,
    rgba(198, 142, 84, 0.07) 46%,
    transparent 70%
  );
  filter: blur(18px);
  animation: sun-breathe 28s ease-in-out infinite alternate;
}
@keyframes sun-breathe {
  from { opacity: 0.75; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1.04); }
}

/* ============================================================
   三层山脊
   ============================================================ */
.mountain-layer {
  position: absolute;
  left: -3%;
  bottom: 0;
  width: 106%;
  height: 52%;
  z-index: 1;
  will-change: transform;
}
.mountain-layer svg {
  width: 100%;
  height: 100%;
  display: block;
}
.mountain-far { height: 54%; transform: translate3d(var(--px-far, 0), 0, 0); }
.mountain-mid { height: 44%; transform: translate3d(var(--px-mid, 0), 0, 0); }
.mountain-near { height: 32%; transform: translate3d(var(--px-near, 0), 0, 0); }

.mountain-far path { fill: url(#grad-far); }
.mountain-mid path { fill: url(#grad-mid); }
.mountain-near path { fill: url(#grad-near); }

@keyframes drift-left {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-1.6%, 0, 0); }
}
@keyframes drift-right {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(1.6%, 0, 0); }
}
.mountain-far svg { animation: drift-left 32s ease-in-out infinite alternate; }
.mountain-mid svg { animation: drift-right 24s ease-in-out infinite alternate; }
.mountain-near svg { animation: drift-left 18s ease-in-out infinite alternate; }

/* 墨色呼吸：像墨在纸上还没干透 */
@keyframes ink-breathe {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}
.mountain-far path { animation: ink-breathe 19s ease-in-out infinite; }
.mountain-mid path { animation: ink-breathe 24s ease-in-out infinite reverse; }
.mountain-near path { animation: ink-breathe 31s ease-in-out infinite; }

/* ============================================================
   云雾
   ============================================================ */
.mist {
  position: absolute;
  z-index: 2;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(34px);
  will-change: transform, opacity;
}
.mist-a {
  left: -14%;
  bottom: 26%;
  width: 78%;
  height: 22%;
  background: radial-gradient(ellipse, rgba(255, 253, 248, 0.95), transparent 70%);
  animation: mist-a 26s ease-in-out infinite alternate;
}
.mist-b {
  right: -16%;
  bottom: 15%;
  width: 72%;
  height: 20%;
  background: radial-gradient(ellipse, rgba(255, 253, 248, 0.85), transparent 70%);
  animation: mist-b 33s ease-in-out infinite alternate;
}
.mist-c {
  left: 30%;
  bottom: 38%;
  width: 54%;
  height: 14%;
  background: radial-gradient(ellipse, rgba(255, 253, 248, 0.7), transparent 72%);
  animation: mist-a 39s ease-in-out infinite alternate-reverse;
}
@keyframes mist-a {
  from { transform: translate3d(0, 0, 0) scale(1); opacity: 0.75; }
  to { transform: translate3d(9%, -3%, 0) scale(1.18); opacity: 1; }
}
@keyframes mist-b {
  from { transform: translate3d(0, 0, 0) scale(1.1); opacity: 0.55; }
  to { transform: translate3d(-11%, 2%, 0) scale(0.94); opacity: 0.95; }
}

/* ============================================================
   飞鸟
   ============================================================ */
.birds {
  position: absolute;
  left: 57%;
  top: 15%;
  width: 300px;
  height: 96px;
  z-index: 2;
  pointer-events: none;
  opacity: 0.85;
  animation: birds-drift 38s ease-in-out infinite alternate;
  will-change: transform;
}
.birds path {
  fill: none;
  stroke: rgba(35, 31, 26, 0.62);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
@keyframes birds-drift {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-52px, -16px, 0); }
}

/* ============================================================
   书法艺术字「生元」
   ============================================================ */
.ink-word {
  position: absolute;
  left: 77%;
  top: 5.5%;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  filter: url(#ink-word-bleed);
  /* 微微倾斜，像随手挥毫而不是排版上去的 */
  transform: rotate(-2.5deg);
  animation: mark-breathe 36s ease-in-out infinite alternate;
}
.ink-char {
  width: 132px;
  height: auto;
  display: block;
}
/* 字周围溅出的几点墨 */
.ink-word .splash {
  position: absolute;
  inset: -30px -42px;
  pointer-events: none;
  background-image:
    radial-gradient(circle at 6% 32%, rgba(35, 31, 26, 0.58) 0 2px, transparent 3px),
    radial-gradient(circle at 24% 7%, rgba(35, 31, 26, 0.42) 0 1px, transparent 2px),
    radial-gradient(circle at 93% 44%, rgba(35, 31, 26, 0.52) 0 2px, transparent 3px),
    radial-gradient(circle at 80% 10%, rgba(35, 31, 26, 0.34) 0 1px, transparent 2px),
    radial-gradient(circle at 12% 86%, rgba(35, 31, 26, 0.46) 0 2px, transparent 3px),
    radial-gradient(circle at 90% 80%, rgba(35, 31, 26, 0.38) 0 1px, transparent 2px);
  filter: blur(1px);
}
@keyframes mark-breathe {
  from { opacity: 0.46; }
  to { opacity: 0.68; }
}

/* ============================================================
   鼠标墨迹与纸纹
   ============================================================ */
.trail {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}

.grain {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  opacity: 0.3;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='0.4'/%3E%3C/svg%3E");
}

/* ============================================================
   品牌区
   注意：刻意用 absolute 且不加 transform / z-index。
   fixed 和 transform 都会创建层叠上下文，会把 Logo 的
   mix-blend-mode 隔离掉，白底就融不进纸面了
   ============================================================ */
.brand {
  position: absolute;
  left: clamp(40px, 7vw, 118px);
  top: 30%;
  max-width: 460px;
}

.brand-logo {
  display: block;
  width: clamp(230px, 22vw, 310px);
  height: auto;
  mix-blend-mode: multiply;
}

.brand-rule {
  width: 46px;
  height: 2px;
  margin: 40px 0 26px;
  background: #b3122e;
}

.brand-en {
  font-size: 11px;
  letter-spacing: 0.4em;
  text-indent: 0.4em;
  color: rgba(42, 39, 36, 0.42);
  white-space: nowrap;
}

.seal {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  width: 56px;
  height: 56px;
  margin-top: 44px;
  border: 1px solid rgba(179, 18, 46, 0.78);
  border-radius: 3px;
  color: rgba(179, 18, 46, 0.92);
  font-family: 'Songti SC', 'STSong', 'SimSun', serif;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.1;
}

/* ============================================================
   登录卡片
   ============================================================ */
.card {
  position: absolute;
  left: 64%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  width: min(88vw, 372px);
  padding: 40px 36px 30px;
  border-radius: 5px;
  background: #fffefb;
  box-shadow:
    0 34px 70px -30px rgba(74, 58, 34, 0.4),
    0 2px 8px rgba(74, 58, 34, 0.05);
  animation: card-in 0.95s 0.12s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}
@keyframes card-in {
  from { opacity: 0; transform: translate(-50%, calc(-50% + 18px)); }
  to { opacity: 1; transform: translate(-50%, -50%); }
}

.card h1 {
  font-family: 'Songti SC', 'STSong', 'SimSun', serif;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: #2a2724;
}
.card-sub {
  margin: 9px 0 28px;
  font-size: 12px;
  letter-spacing: 0.04em;
  color: rgba(42, 39, 36, 0.42);
}

.login-form :deep(.el-form-item) {
  margin-bottom: 14px;
}
.login-form :deep(.submit-item) {
  margin-top: 8px;
  margin-bottom: 0;
}

/* 输入框：暖白底 + 浅墨边，聚焦时透出朱砂 */
.login-form :deep(.el-input__wrapper) {
  height: 47px;
  padding: 0 15px;
  border-radius: 5px;
  background-color: #faf7f0;
  box-shadow: 0 0 0 1px #e7e0d2 inset;
  transition: box-shadow 0.25s, background-color 0.25s;
}
.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #d8cfbc inset;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  background-color: #fff;
  box-shadow: 0 0 0 1px rgba(179, 18, 46, 0.45) inset,
    0 0 0 3px rgba(179, 18, 46, 0.07);
}
.login-form :deep(.el-input__inner) {
  color: #2a2724;
  font-size: 14px;
}
.login-form :deep(.el-input__inner::placeholder) {
  color: #b5ab99;
}
.login-form :deep(.el-input__prefix) {
  color: rgba(42, 39, 36, 0.38);
}
.login-form :deep(.el-input__wrapper.is-focus .el-input__prefix) {
  color: #b3122e;
}
.login-form :deep(.el-form-item__error) {
  padding-top: 3px;
  font-size: 11px;
}

.submit-btn {
  width: 100%;
  height: 47px;
  border: 0;
  border-radius: 5px;
  background: #b3122e;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.26em;
  text-indent: 0.26em;
  transition: filter 0.22s, box-shadow 0.3s, transform 0.14s;
}
.submit-btn:hover,
.submit-btn:focus {
  background: #c11734;
  box-shadow: 0 12px 26px -10px rgba(179, 18, 46, 0.55);
}
.submit-btn:active {
  transform: translateY(1px);
}

.copyright {
  margin-top: 26px;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-align: center;
  color: rgba(42, 39, 36, 0.3);
}

/* ============================================================
   页脚
   ============================================================ */
.footer {
  position: absolute;
  left: clamp(40px, 7vw, 118px);
  bottom: 38px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  letter-spacing: 0.22em;
  color: rgba(42, 39, 36, 0.56);
}
.footer i {
  display: block;
  width: 24px;
  height: 1px;
  background: rgba(42, 39, 36, 0.22);
}

/* ============================================================
   响应式
   ============================================================ */
@media (max-width: 960px) {
  .brand {
    top: 11%;
    left: 0;
    right: 0;
    max-width: none;
    padding: 0 32px;
    text-align: center;
  }
  .brand-logo {
    width: 210px;
    margin: 0 auto;
  }
  .brand-rule {
    margin: 22px auto 16px;
  }
  .seal {
    display: none;
  }

  .card {
    left: 50%;
    top: 66%;
    width: min(90vw, 360px);
    padding: 30px 24px 22px;
  }

  .footer {
    display: none;
  }

  .mountain-far { height: 40%; }
  .mountain-mid { height: 32%; }
  .mountain-near { height: 24%; }

  .ink-word {
    left: auto;
    right: 2%;
    top: 3%;
    transform: rotate(-2.5deg) scale(0.62);
    transform-origin: top right;
  }
  .birds {
    left: 40%;
    top: 12%;
    width: 220px;
  }
}

/* 尊重系统的“减少动态效果”设置 */
@media (prefers-reduced-motion: reduce) {
  .mountain-far svg,
  .mountain-mid svg,
  .mountain-near svg,
  .mountain-far path,
  .mountain-mid path,
  .mountain-near path,
  .mist,
  .birds,
  .sun,
  .ink-word,
  .card {
    animation: none !important;
  }
}
</style>
