<template>
  <div class="user-profile-page">
    <el-card class="profile-card" v-loading="loading">
      <div class="profile-basic business-card">
        <div class="card-left">
          <el-avatar :size="72" class="avatar-icon">
            {{ userInfo.real_name ? userInfo.real_name.charAt(0) : 'U' }}
          </el-avatar>
        </div>
        <div class="card-right">
          <div class="name-row">
            <h2 class="user-name">{{ userInfo.real_name || '未设置姓名' }}</h2>
            <el-tag type="primary" effect="light" class="role-tag" round>
              {{ userInfo.role || '未知角色' }}
            </el-tag>
          </div>
          <div class="info-row">
            <span class="info-item">
              <el-icon><User /></el-icon> 账号：{{ userInfo.accounts }}
            </span>
            <span class="info-item">
              <el-icon><Briefcase /></el-icon> 职位：{{ userInfo.position || '暂无职位' }}
            </span>
          </div>
        </div>
      </div>

      <div class="profile-stats">
        <div class="stats-header">
          <h3>案件统计</h3>
          <el-date-picker
            v-model="selectedYear"
            type="year"
            placeholder="选择年份"
            format="YYYY"
            value-format="YYYY"
            :clearable="false"
            @change="fetchStats"
            class="year-picker"
          />
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8" :lg="6" class="stat-col">
            <el-card class="stat-card modern-card" shadow="never">
              <div class="stat-item modern-stat">
                <div class="stat-icon-wrapper blue-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">主办案件数</span>
                  <span class="stat-value blue-text">{{ stats.main_case_count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6" class="stat-col">
            <el-card class="stat-card modern-card" shadow="never">
              <div class="stat-item modern-stat">
                <div class="stat-icon-wrapper green-icon">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">总收费金额 (元)</span>
                  <span class="stat-value green-text">{{ stats.total_income }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6" v-if="isAdmin" class="stat-col">
            <el-card class="stat-card modern-card" shadow="never">
              <div class="stat-item modern-stat">
                <div class="stat-icon-wrapper purple-icon">
                  <el-icon><Select /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">审核业务数</span>
                  <span class="stat-value purple-text">{{ stats.review_case_count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div class="profile-chart">
        <h3>业务类型分布</h3>
        <el-card class="modern-card chart-card" shadow="never">
          <div ref="chartContainer" class="chart-container"></div>
        </el-card>
      </div>

      <div class="change-password">
        <h3>修改密码</h3>
        <el-form
          :model="passwordForm"
          :rules="passwordRules"
          ref="passwordFormRef"
          label-width="auto"
          class="responsive-form"
        >
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input
              v-model="passwordForm.oldPassword"
              type="password"
              placeholder="请输入旧密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
            />
          </el-form-item>
          <el-form-item class="submit-btn-item">
            <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
// 引入 Element Plus 图标
import { User, Briefcase, Document, Money, Select } from '@element-plus/icons-vue'
import request from '@/utils/request'

// 状态管理
const loading = ref(true)
const userInfo = ref({})
// 默认选中当前年份
const selectedYear = ref(new Date().getFullYear().toString())

const stats = ref({
  main_case_count: 0,
  total_income: 0,
  category_stats: {},
  review_case_count: 0,
})
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const passwordFormRef = ref(null)
const chartInstance = ref(null)
const chartContainer = ref(null)
const router = useRouter()

// 当前用户信息
const currentUserRole = ref(localStorage.getItem('role')).value
const isAdmin = computed(() => ['admin', 'owner'].includes(currentUserRole))

// 表单验证规则
const passwordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需为6~20位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 独立获取统计数据的方法
const fetchStats = async () => {
  try {
    const statsRes = await request.get(`/user/profile/case-statistics`, {
      params: {
        year: selectedYear.value,
      },
    })
    stats.value = statsRes.data
    // 数据更新后重新渲染图表
    initChart()
  } catch (err) {
    console.error('获取统计数据失败:', err)
    ElMessage.error('获取统计数据失败')
  }
}

// 初始化数据
const initData = async () => {
  try {
    loading.value = true
    // 获取用户基本信息
    const userRes = await request.get(`/user/profile/info`)
    userInfo.value = userRes.data

    await fetchStats()
  } catch (err) {
    console.error('加载个人信息失败:', err)
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
  }
}

// 图表自适应调整方法
const handleResize = () => {
  if (chartInstance.value) {
    // 窗口尺寸改变时，如果是临界点跨越，建议重新初始化以更新横竖排版
    initChart()
  }
}

// 初始化带顶部数值的柱状图
const initChart = () => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }

  // 使用 ref 获取容器
  chartInstance.value = echarts.init(chartContainer.value)

  // 1. 处理数据：确保案件都显示，无数据则为0
  const caseCategories = [
    '民事案件',
    '银行案件',
    '刑事案件',
    '非诉业务',
    '执行案件',
    '行政案件',
    '劳动仲裁',
    '商事仲裁',
    '法律顾问业务',
    '法律援助(民事)',
    '法律援助(刑事)',
    '法律援助(行政)',
  ]
  const chartData = caseCategories.map((category) => {
    return stats.value.category_stats[category] || 0 // 无数据时默认0
  })

  // 获取当前屏幕宽度，判断是否为移动端
  const isMobile = window.innerWidth <= 768

  // 2. 基础配置：方案B 移动端坐标轴反转 (横向柱状图)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }, // 鼠标悬浮时显示阴影指示器
    },
    grid: {
      left: '3%',
      right: isMobile ? '8%' : '4%', // 移动端右侧留出空间给数值标签
      bottom: '5%',
      top: '8%',
      containLabel: true, // 确保坐标轴标签不被截断
    },
    xAxis: {
      type: isMobile ? 'value' : 'category',
      data: isMobile ? null : caseCategories,
      axisLabel: {
        interval: 0, // 强制显示所有x轴标签
        rotate: isMobile ? 0 : 30, // 移动端无需旋转
      },
      splitLine: {
        show: isMobile, // 移动端时X轴为数值，显示垂直网格线
        lineStyle: { type: 'dashed', color: '#eee' },
      },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: isMobile ? 'category' : 'value',
      data: isMobile ? caseCategories : null,
      inverse: isMobile, // 移动端反转Y轴，让第一个分类排在最上方
      name: isMobile ? '' : '业务数量',
      min: 0,
      axisLabel: {
        interval: 0,
        width: isMobile ? 100 : null, // 移动端限制Y轴文字宽度，防止挤压图表主体
        overflow: 'truncate',
      },
      splitLine: {
        show: !isMobile, // PC端时Y轴为数值，显示水平网格线
        lineStyle: { type: 'dashed', color: '#eee' },
      },
    },
    series: [
      {
        name: '业务数量',
        type: 'bar',
        data: chartData,
        barWidth: isMobile ? '50%' : '30%', // 柱子宽度适配
        itemStyle: {
          // 移动端横向柱状图圆角在右侧，PC端在顶部
          borderRadius: isMobile ? [0, 4, 4, 0] : [4, 4, 0, 0],
          // 移动端渐变方向为从左到右，PC端为从下到上
          color: new echarts.graphic.LinearGradient(
            isMobile ? 0 : 0,
            0,
            isMobile ? 1 : 0,
            isMobile ? 0 : 1,
            [
              { offset: 0, color: '#165DFF' },
              { offset: 1, color: '#4080FF' },
            ],
          ),
        },
        // 4. 标签数值显示位置适配
        label: {
          show: true,
          position: isMobile ? 'right' : 'top', // 横向放在右侧，竖向放在顶部
          fontSize: 14,
          color: '#333',
          fontWeight: 'bold',
        },
        // 鼠标悬浮时高亮
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(
              isMobile ? 0 : 0,
              0,
              isMobile ? 1 : 0,
              isMobile ? 0 : 1,
              [
                { offset: 0, color: '#0E48D8' },
                { offset: 1, color: '#2A6FFF' },
              ],
            ),
          },
        },
      },
    ],
  }

  chartInstance.value.setOption(option)

  // 响应窗口 resize
  window.addEventListener('resize', handleResize)
}

// 修改密码
const handleChangePassword = async () => {
  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await request.put('/user/profile/change-password', {
        old_password: passwordForm.value.oldPassword,
        new_password: passwordForm.value.newPassword,
      })

      ElMessage.success('密码修改成功，请重新登录')
      // 清空表单
      passwordForm.value = {
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      }
      // 跳转到登录页
      localStorage.clear()
      await router.push('/login')
    } catch (err) {
      console.error('修改密码失败:', err)
      ElMessage.error(err.response?.data?.detail || '修改密码失败')
    }
  })
}

// 页面加载时初始化
onMounted(() => {
  initData()
})

// 组件卸载时移除监听器，防止内存泄漏
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
})
</script>

<style scoped>
.user-profile-page {
  padding: 20px;
  box-sizing: border-box;
  background-color: #f5f7fa; /* 让整个页面有点浅灰底色，凸显卡片质感 */
  min-height: calc(100vh - 60px);
}

.profile-card {
  margin-top: 5px;
  border-radius: 12px; /* 外层大卡片圆角 */
}

.profile-basic,
.profile-stats,
.profile-chart,
.change-password {
  margin-bottom: 35px;
}

h3 {
  margin-bottom: 20px;
  color: #1d2129; /* 加深一点标题颜色，显得更稳重 */
  font-size: 18px;
  font-weight: 600;
  position: relative;
  padding-left: 12px;
}

/* 标题左侧的一抹蓝色小竖线修饰 */
h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background-color: #165dff;
  border-radius: 2px;
}

/* ================= 优化：名片式头部样式 ================= */
.business-card {
  display: flex;
  align-items: center;
  padding: 24px 30px;
  background: linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #e5e6eb;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.05); /* 极弱的品牌色阴影 */
  gap: 24px;
}

.avatar-icon {
  background-color: #165dff;
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.card-right {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  margin: 0;
  font-size: 24px;
  color: #1d2129;
  font-weight: bold;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 24px;
  color: #4e5969;
  font-size: 14px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ================= 优化：微质感统计卡片样式 ================= */
.stat-col {
  margin-bottom: 20px; /* 确保卡片折叠时有垂直间距 */
}

.modern-card {
  border: none !important;
  border-radius: 12px;
  background-color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important; /* 弥散阴影 */
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.modern-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
}

.modern-stat {
  display: flex;
  flex-direction: row !important; /* 改为左右布局 */
  align-items: center;
  padding: 10px 5px !important;
  gap: 20px;
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.blue-icon {
  background-color: #e8f3ff;
  color: #165dff;
}
.green-icon {
  background-color: #e8ffea;
  color: #00b42a;
}
.purple-icon {
  background-color: #f2e8ff;
  color: #722ed1;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label {
  color: #86909c;
  font-size: 14px;
  font-weight: 500;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  font-family:
    'Din',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    sans-serif;
}

.blue-text {
  color: #165dff;
}
.green-text {
  color: #00b42a;
}
.purple-text {
  color: #722ed1;
}

/* 其他杂项 */
.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-header h3 {
  margin-bottom: 0;
}

.year-picker {
  width: 140px;
}

.chart-container {
  width: 100%;
  height: 500px;
  padding: 10px;
}

.change-password {
  max-width: 500px;
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

/* ================= 移动端适配响应式媒体查询 ================= */
@media screen and (max-width: 768px) {
  .user-profile-page {
    padding: 10px; /* 移动端减小外边距 */
  }

  /* 移动端名片适配 */
  .business-card {
    padding: 20px 15px;
    gap: 15px;
  }

  .avatar-icon {
    width: 60px !important;
    height: 60px !important;
    font-size: 24px;
  }

  .user-name {
    font-size: 20px;
  }

  .info-row {
    flex-direction: column; /* 手机端账号职位竖排 */
    align-items: flex-start;
    gap: 8px;
  }

  /* 统计头部换行适配 */
  .stats-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .year-picker {
    width: 100%; /* 日期选择器占满宽度 */
  }

  /* 针对横向柱状图，增加一定的高度让12个柱子显得不那么拥挤 */
  .chart-container {
    height: 480px;
  }

  /* 移动端表单转为上下布局 (Label在上方) */
  :deep(.responsive-form .el-form-item) {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 18px;
  }

  :deep(.responsive-form .el-form-item__label) {
    width: 100% !important;
    justify-content: flex-start;
    margin-bottom: 8px;
    padding-bottom: 0;
    line-height: 20px;
  }

  :deep(.responsive-form .el-form-item__content) {
    width: 100%;
  }

  /* 提交按钮拉长 */
  .submit-btn-item :deep(.el-button) {
    width: 100%;
  }
}
</style>
