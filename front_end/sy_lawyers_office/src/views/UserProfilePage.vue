<template>
  <div class="user-profile-page">
    <el-page-header @back="goBack" title="个人信息" />

    <el-card class="profile-card" v-loading="loading">
      <!-- 基本信息 -->
      <div class="profile-basic">
        <h3>基本信息</h3>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="账号">{{ userInfo.accounts }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ userInfo.real_name }}</el-descriptions-item>
          <el-descriptions-item label="职位">{{ userInfo.position }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ userInfo.role }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 统计信息 -->
      <div class="profile-stats">
        <h3>案件统计</h3>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-item">
                <span class="stat-label">主办案件数</span>
                <span class="stat-value">{{ stats.main_case_count }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-item">
                <span class="stat-label">总收费金额</span>
                <span class="stat-value">{{ stats.total_income }} 元</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6" v-if="isAdmin">
            <el-card class="stat-card">
              <div class="stat-item">
                <span class="stat-label">审核案件数</span>
                <span class="stat-value">{{ stats.review_case_count }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 案件类型统计图表 -->
      <div class="profile-chart">
        <h3>案件类型分布</h3>
        <el-card>
          <div ref="chartContainer" class="chart-container"></div>
        </el-card>
      </div>

      <!-- 修改密码 -->
      <div class="change-password">
        <h3>修改密码</h3>
        <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="120px">
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input v-model="passwordForm.oldPassword" type="password" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

// 状态管理
const loading = ref(true)
const userInfo = ref({})
const stats = ref({
  main_case_count: 0,
  total_income: 0,
  category_stats: {},
  review_case_count: 0
})
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordFormRef = ref(null)
const chartInstance = ref(null)
const chartContainer = ref(null)
const router = useRouter()

// 当前用户信息
const currentUserId = ref(sessionStorage.getItem('user_id')).value
const currentUserRole = ref(sessionStorage.getItem('role')).value
const isAdmin = computed(() => ['admin', 'owner'].includes(currentUserRole))

// 表单验证规则
const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需为6~20位', trigger: 'blur' }
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
      trigger: 'blur'
    }
  ]
}

// 初始化数据
const initData = async () => {
  try {
    loading.value = true
    // 获取用户基本信息
    const userRes = await axios.get(`http://127.0.0.1:8002/user/profile/info?user_id=${currentUserId}`)
    userInfo.value = userRes.data

    // 获取案件统计数据
    const statsRes = await axios.get(`http://127.0.0.1:8002/user/profile/case-statistics?user_id=${currentUserId}`)
    stats.value = statsRes.data

    // 初始化图表
    initChart()
  } catch (err) {
    console.error('加载个人信息失败:', err)
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
  }
}

// 初始化带顶部数值的柱状图（替换原 initChart 函数）
const initChart = () => {
  if (chartInstance.value) {
    chartInstance.value.dispose();
  }

  // 使用 ref 获取容器（原代码用 querySelector，改用 ref 更符合 Vue 规范）
  chartInstance.value = echarts.init(chartContainer.value);

  // 1. 处理数据：确保6类案件都显示，无数据则为0
  const caseCategories = [
    "民事案件",
    "刑事案件",
    "非诉案件",
    "行政案件",
    "仲裁案件",
    "法律顾问业务",
  ];
  const chartData = caseCategories.map((category) => {
    return stats.value.category_stats[category] || 0; // 无数据时默认0
  });

  // 2. 基础柱状图配置（重点：添加 label 实现顶部数值显示）
  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" }, // 鼠标悬浮时显示阴影指示器
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true, // 确保坐标轴标签不被截断
    },
    xAxis: {
      type: "category",
      data: caseCategories,
      axisLabel: {
        interval: 0, // 强制显示所有x轴标签
        rotate: 30, // 标签旋转30度，避免文字重叠
      },
    },
    yAxis: {
      type: "value",
      name: "案件数量",
      min: 0, // y轴最小值设为0，避免数据偏差
    },
    series: [
      {
        name: "案件数量",
        type: "bar", // 基础柱状图类型（无需3D依赖）
        data: chartData,
        barWidth: "50%", // 柱子宽度，避免过宽或过窄
        // 3. 柱子样式：渐变色（保留原视觉效果）
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#165DFF" },
            { offset: 1, color: "#4080FF" },
          ]),
        },
        // 4. 顶部显示数值（核心需求）
        label: {
          show: true, // 启用标签
          position: "top", // 数值在柱子顶部
          fontSize: 14,
          color: "#333", // 数值颜色
          fontWeight: "bold",
        },
        // 鼠标悬浮时高亮
        emphasis: {
          focus: "series",
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "#0E48D8" },
              { offset: 1, color: "#2A6FFF" },
            ]),
          },
        },
      },
    ],
  };

  chartInstance.value.setOption(option);

  // 响应窗口 resize
  window.addEventListener("resize", () => {
    chartInstance.value.resize();
  });
};

// 修改密码
const handleChangePassword = async () => {
  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await axios.put('http://127.0.0.1:8002/user/profile/change-password', {
        user_id: currentUserId,
        old_password: passwordForm.value.oldPassword,
        new_password: passwordForm.value.newPassword
      })

      ElMessage.success('密码修改成功，请重新登录')
      // 清空表单
      passwordForm.value = {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      // 跳转到登录页
      sessionStorage.clear()
      await router.push('/login')
    } catch (err) {
      console.error('修改密码失败:', err)
      ElMessage.error(err.response?.data?.detail || '修改密码失败')
    }
  })
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 页面加载时初始化
onMounted(() => {
  initData()
})
</script>

<style scoped>
.user-profile-page {
  padding: 20px;
}

.profile-card {
  margin-top: 15px;
}

.profile-basic, .profile-stats, .profile-chart, .change-password {
  margin-bottom: 30px;
}

h3 {
  margin-bottom: 15px;
  color: #1e88e5;
  font-size: 16px;
  font-weight: bold;
}

.stat-card {
  height: 100%;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px 0;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-value {
  color: #165DFF;
  font-size: 24px;
  font-weight: bold;
}

.chart-container {
  width: 100%;
  height: 500px; /* 增加高度以更好地展示3D效果 */
}

.change-password {
  max-width: 600px;
}
</style>
