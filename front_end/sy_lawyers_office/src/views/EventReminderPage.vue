<template>
  <div class="event-reminders-page">
    <div class="header">
      <h2>事项提醒</h2>
      <div class="filter">
        <el-radio-group v-model="daysRange" @change="fetchReminders">
          <el-radio-button :label="3">近3天</el-radio-button>
          <el-radio-button :label="7">近7天</el-radio-button>
          <el-radio-button :label="30">近30天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-table :data="events" border stripe style="width: 100%" v-loading="loading">
      <el-table-column label="状态" width="100" align="center">
        <template #default="scope">
          <el-tag :type="getUrgencyColor(scope.row.days_remaining)" effect="dark">
            剩 {{ scope.row.days_remaining }} 天
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="event_type" label="事项类型" width="120" align="center">
        <template #default="scope">
          <el-tag :type="getEventTypeColor(scope.row.event_type)" effect="plain">
            {{ scope.row.event_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="event_date" label="截止/开庭日期" width="150" align="center" />
      <el-table-column prop="case_number" label="案件号" width="220" />
      <el-table-column prop="client_name" label="委托人" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="scope">
          <el-button size="small" @click="goToCase(scope.row.case_id)">查看案件</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && events.length === 0" description="近期无待办事项" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentUserId = sessionStorage.getItem('user_id')
const events = ref([])
const loading = ref(false)
const daysRange = ref(30) // 默认显示30天

const fetchReminders = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8002/user/profile/reminders', {
      params: {
        user_id: currentUserId,
        days: daysRange.value
      }
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
  return ''
}

const goToCase = (caseId) => {
  router.push(`/main/cases/${caseId}`)
}

onMounted(() => {
  fetchReminders()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}
</style>
