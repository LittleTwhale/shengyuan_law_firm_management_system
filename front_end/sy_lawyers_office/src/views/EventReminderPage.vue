<template>
  <div class="event-reminders-page">
    <div class="header">
      <h2>事项提醒</h2>
      <div class="filter">
        <el-radio-group v-model="daysRange" @change="fetchReminders" class="responsive-radio">
          <el-radio-button :label="3">近3天</el-radio-button>
          <el-radio-button :label="7">近7天</el-radio-button>
          <el-radio-button :label="30">近30天</el-radio-button>
          <el-radio-button :label="0">全部</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="events" border stripe style="width: 100%" v-loading="loading">
        <el-table-column label="状态" min-width="90" align="center">
          <template #default="scope">
            <el-tag :type="getUrgencyColor(scope.row.days_remaining)" effect="dark">
              剩 {{ scope.row.days_remaining }} 天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="event_type" label="事项类型" min-width="100" align="center">
          <template #default="scope">
            <el-tag :type="getEventTypeColor(scope.row.event_type)" effect="plain">
              {{ scope.row.event_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="event_date" label="截止/开庭日期" min-width="130" align="center" />
        <el-table-column prop="case_number" label="业务号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="client_name" label="委托人" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" plain @click="goToCase(scope.row.case_id)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-if="!loading && events.length === 0" description="近期无待办事项" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentUserId = localStorage.getItem('user_id')
const events = ref([])
const loading = ref(false)
const daysRange = ref(30) // 默认显示30天

const fetchReminders = async () => {
  loading.value = true
  try {
    const res = await request.get('/user/profile/reminders', {
      params: {
        user_id: currentUserId,
        days: daysRange.value,
      },
    })
    events.value = res.data
  } catch (error) {
    console.error('获取提醒失败', error)
  } finally {
    loading.value = false
  }
}

const getUrgencyColor = (days) => {
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}

const getEventTypeColor = (type) => {
  if (type === '开庭') return 'danger'
  if (type === '保全到期') return 'warning'
  return 'primary'
}

const goToCase = (caseId) => {
  router.push(`/main/cases/${caseId}`)
}

onMounted(() => {
  fetchReminders()
})
</script>

<style scoped>
/* 统一卡片式UI风格 */
.event-reminders-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
  margin: 20px;
  padding: 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.table-container {
  flex: 1;
  overflow: hidden; /* 防止外层越界，滚动条限制在表格内部 */
}

/* 修复文本溢出 */
:deep(.el-table .cell) {
  white-space: nowrap;
}

/* --- 移动端响应式适配 (视口宽度 <= 768px) --- */
@media (max-width: 768px) {
  .event-reminders-page {
    margin: 10px;
    padding: 16px;
    height: calc(100vh - 20px);
  }

  /* 顶部从左右分布改为上下分布 */
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .filter {
    width: 100%;
    overflow-x: auto; /* 单选按钮组太长时允许滑动 */
    padding-bottom: 5px;
  }

  /* 调整按钮大小以节省空间 */
  :deep(.el-table .el-button--small) {
    padding: 5px 12px;
  }
}
</style>
