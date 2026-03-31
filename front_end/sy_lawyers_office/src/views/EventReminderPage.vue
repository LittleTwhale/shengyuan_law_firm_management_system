<template>
  <div class="event-reminders-page">
    <div class="main-content">
      <div class="header">
        <div class="header-left">
          <h2>事项与日程</h2>
          <el-radio-group v-model="viewMode" size="small" class="view-switch">
            <el-radio-button label="table">列表视图</el-radio-button>
            <el-radio-button label="calendar" class="hide-on-mobile">日历视图</el-radio-button>
          </el-radio-group>
        </div>

        <div class="filter">
          <el-radio-group
            v-show="viewMode === 'table'"
            v-model="daysRange"
            @change="fetchReminders"
            class="responsive-radio"
          >
            <el-radio-button :label="3">近3天</el-radio-button>
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
            <el-radio-button :label="0">全部</el-radio-button>
          </el-radio-group>
          <el-button type="primary" class="add-btn" @click="openDrawer()"> 新建日程 </el-button>
        </div>
      </div>

      <div v-if="viewMode === 'table'" class="table-container">
        <el-table :data="events" border stripe style="width: 100%" v-loading="loading">
          <el-table-column label="状态" width="120" align="center">
            <template #default="scope">
              <el-tag :type="getUrgencyColor(scope.row.days_remaining)" effect="dark">
                剩 {{ scope.row.days_remaining }} 天
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="来源" width="90" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.source === 'case' ? 'info' : 'success'" size="small">
                {{ scope.row.source === 'case' ? '系统业务' : '自定义' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="event_type" label="事项/标题" min-width="120" align="center">
            <template #default="scope">
              <el-tag :type="getEventTypeColor(scope.row.event_type)" effect="plain">
                {{ scope.row.event_type }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="event_date" label="截止/提醒日期" width="130" align="center" />

          <el-table-column
            prop="case_number"
            label="关联业务号"
            min-width="180"
            show-overflow-tooltip
          >
            <template #default="scope">
              {{ scope.row.case_number || '--' }}
            </template>
          </el-table-column>

          <el-table-column prop="client_name" label="委托人" min-width="120" show-overflow-tooltip>
            <template #default="scope">
              {{ scope.row.client_name || '--' }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="250" align="center" fixed="right">
            <template #default="scope">
              <el-button
                v-if="scope.row.case_id"
                size="small"
                type="primary"
                plain
                @click="goToCase(scope.row.case_id)"
              >
                业务详情
              </el-button>

              <template v-if="scope.row.source === 'custom'">
                <el-button size="small" type="warning" plain @click="openDrawer(scope.row)">
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定删除该日程吗？"
                  @confirm="handleDelete(scope.row.schedule_id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger" plain>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && events.length === 0" description="近期无待办事项" />
      </div>

      <div v-else class="calendar-container" v-loading="loading">
        <el-calendar v-model="calendarDate">
          <template #header="{ date }">
            <div class="custom-calendar-header">
              <span class="calendar-title">{{ date }}</span>
              <div class="calendar-actions">
                <el-date-picker
                  v-model="calendarDate"
                  type="month"
                  placeholder="快速跳转年月"
                  :clearable="false"
                  size="small"
                  style="width: 140px; margin-right: 12px"
                />
                <el-button-group>
                  <el-button size="small" @click="shiftDate('prev')">上一月</el-button>
                  <el-button size="small" @click="shiftDate('today')">今天</el-button>
                  <el-button size="small" @click="shiftDate('next')">下一月</el-button>
                </el-button-group>
              </div>
            </div>
          </template>

          <template #date-cell="{ data }">
            <div class="calendar-cell">
              <span :class="{ 'is-today': data.isToday }">{{ data.day.split('-').pop() }}</span>
              <div class="calendar-events">
                <div
                  v-for="e in getEventsByDate(data.day)"
                  :key="e.id"
                  class="event-badge"
                  :class="e.source"
                  :title="e.event_type"
                  @click.stop="viewEventDetail(e)"
                >
                  {{ e.event_type }}
                </div>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>
    </div>

    <div class="side-panel">
      <div class="side-header">
        <h3>🚀 紧迫待办 (TOP 5)</h3>
      </div>
      <el-timeline v-if="urgentEvents.length > 0">
        <el-timeline-item
          v-for="(activity, index) in urgentEvents"
          :key="index"
          :type="getUrgencyColor(activity.days_remaining)"
          :hollow="true"
          :timestamp="activity.event_date"
          placement="top"
        >
          <el-card class="timeline-card" shadow="hover">
            <h4>{{ activity.event_type }}</h4>
            <p v-if="activity.case_number" class="timeline-desc">{{ activity.case_number }}</p>
            <p v-if="activity.description" class="timeline-desc">{{ activity.description }}</p>
            <div class="timeline-footer">
              <span :class="'text-' + getUrgencyColor(activity.days_remaining)"
                >剩 {{ activity.days_remaining }} 天</span
              >
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无紧迫任务" :image-size="80" />
    </div>

    <el-drawer
      v-model="drawerVisible"
      :title="isEditing ? '编辑自定义日程' : '新建自定义日程'"
      size="400px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" label-position="top">
        <el-form-item label="事项标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>

        <el-form-item label="提醒日期" prop="event_date">
          <el-date-picker
            v-model="form.event_date"
            type="date"
            placeholder="选择截止/提醒日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="关联业务 (可选)" prop="related_case_id">
          <el-select
            v-model="form.related_case_id"
            placeholder="请选择或搜索关联的业务"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in myCases"
              :key="item.case_id"
              :label="`${item.case_number || '无案号'} - ${item.client_name || '无委托人'}`"
              :value="item.case_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="详细备注" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="记录更详细的备忘信息..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="submitForm">
            保存日程
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 数据状态
const events = ref([])
const loading = ref(false)
const daysRange = ref(30) // 默认显示30天
const viewMode = ref('table') // 视图切换
const calendarDate = ref(new Date())
const myCases = ref([]) // 我的业务

// 抽屉状态
const drawerVisible = ref(false)
const isEditing = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)

const form = reactive({
  schedule_id: null,
  title: '',
  event_date: '',
  related_case_id: null,
  description: '',
})

const rules = {
  title: [{ required: true, message: '请输入事项标题', trigger: 'blur' }],
  event_date: [{ required: true, message: '请选择提醒日期', trigger: 'change' }],
}

// 计算属性：紧迫事项 (用于右侧Timeline展示前5个)
const urgentEvents = computed(() => {
  return events.value.slice(0, 5)
})

// 日历视图：获取指定日期的事项
const getEventsByDate = (dateStr) => {
  return events.value.filter((e) => e.event_date === dateStr)
}

// --- API 交互 ---

// 获取用户的业务下拉列表
const fetchMyCases = async () => {
  try {
    const res = await request.get('/user/profile/my-cases/simple')
    myCases.value = res.data
  } catch (error) {
    console.error('获取关联业务列表失败', error)
  }
}

// 获取提醒列表
const fetchReminders = async () => {
  loading.value = true
  try {
    const res = await request.get('/user/profile/reminders', {
      params: { days: daysRange.value },
    })
    // 假设后端返回的数据结构如设计：[{source: 'case'|'custom', days_remaining, event_type...}]
    events.value = res.data
  } catch (error) {
    console.error('获取提醒失败', error)
    ElMessage.error('获取事项提醒失败')
  } finally {
    loading.value = false
  }
}

// 提交表单 (新增 / 修改)
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const payload = {
          title: form.title,
          event_date: form.event_date,
          description: form.description,
          related_case_id: form.related_case_id || null,
        }

        if (isEditing.value) {
          await request.put(`/user/profile/reminders/custom/${form.schedule_id}`, payload)
          ElMessage.success('修改成功')
        } else {
          await request.post('/user/profile/reminders/custom', payload)
          ElMessage.success('创建成功')
        }
        drawerVisible.value = false
        fetchReminders() // 刷新列表
      } catch (error) {
        console.error(error)
        ElMessage.error('保存失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 删除自定义日程
const handleDelete = async (scheduleId) => {
  try {
    await request.delete(`/user/profile/reminders/custom/${scheduleId}`)
    ElMessage.success('删除成功')
    fetchReminders()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除失败')
  }
}

// --- 交互与工具函数 ---

// 打开抽屉
const openDrawer = (row = null) => {
  if (formRef.value) formRef.value.resetFields()
  if (row) {
    isEditing.value = true
    form.schedule_id = row.schedule_id
    form.title = row.event_type
    form.event_date = row.event_date
    form.related_case_id = row.case_id || null
    form.description = row.description || ''
  } else {
    isEditing.value = false
    form.schedule_id = null
    form.title = ''
    form.event_date = ''
    form.related_case_id = null
    form.description = ''
  }
  drawerVisible.value = true
}

// 日历卡片点击详情
const viewEventDetail = (eventData) => {
  if (eventData.source === 'custom') {
    openDrawer(eventData)
  } else if (eventData.case_id) {
    goToCase(eventData.case_id)
  }
}

const getUrgencyColor = (days) => {
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}

const getEventTypeColor = (type) => {
  if (['开庭', '诉讼时效到期'].includes(type)) return 'danger'
  if (['保全到期', '付款到期'].includes(type)) return 'warning'
  return 'primary' // 自定义或其他默认蓝色
}

const goToCase = (caseId) => {
  router.push(`/main/cases/${caseId}`)
}

// 日历月份快速切换函数
const shiftDate = (type) => {
  const current = new Date(calendarDate.value)
  if (type === 'prev') {
    current.setMonth(current.getMonth() - 1)
  } else if (type === 'next') {
    current.setMonth(current.getMonth() + 1)
  } else if (type === 'today') {
    calendarDate.value = new Date()
    return
  }
  calendarDate.value = current
}

onMounted(() => {
  fetchReminders()
  fetchMyCases() // 组件挂载时获取案件下拉数据
})
</script>

<style scoped>
/* 统一卡片式UI风格，增加左右布局 */
.event-reminders-page {
  display: flex;
  flex-direction: row;
  height: calc(100vh - 40px);
  margin: 20px;
  gap: 20px;
  box-sizing: border-box;
}

/* 左侧主内容区 */
.main-content {
  flex: 3;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 右侧侧边栏 (时间轴) */
.side-panel {
  flex: 1;
  min-width: 280px;
  background-color: #ffffff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow-y: auto;
}

.side-header h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 16px;
  color: #303133;
  border-bottom: 2px solid #ebeef5;
  padding-bottom: 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.filter {
  display: flex;
  align-items: center;
  gap: 15px;
}

.table-container,
.calendar-container {
  flex: 1;
  overflow-y: auto; /* 防止外层越界，滚动条限制在内部 */
}

/* --- 新增：自定义日历头部样式 --- */
.custom-calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.calendar-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}
.calendar-actions {
  display: flex;
  align-items: center;
}

/* --- 日历样式定制 --- */
.calendar-cell {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 4px;
  box-sizing: border-box;
}
.is-today {
  color: var(--el-color-primary);
  font-weight: bold;
}

/* --- 修改：日历单元格防溢出 --- */
.calendar-events {
  margin-top: 4px;
  flex: 1;
  overflow-y: auto;
  max-height: 85px; /* 限制最大高度，防止撑破单元格 */
}

/* 美化单元格内的微型滚动条 */
.calendar-events::-webkit-scrollbar {
  width: 4px;
}
.calendar-events::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 4px;
}

.event-badge {
  font-size: 11px;
  padding: 2px 6px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 系统业务颜色 */
.event-badge.case {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
  border: 1px solid var(--el-color-info-light-7);
}
/* 自定义日程颜色 */
.event-badge.custom {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-7);
}
.event-badge:hover {
  opacity: 0.8;
}

/* --- Timeline 卡片样式 --- */
.timeline-card {
  margin-bottom: 8px;
}
.timeline-card h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #303133;
}
.timeline-desc {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #909399;
}
.timeline-footer {
  font-size: 12px;
  font-weight: bold;
}
.text-danger {
  color: var(--el-color-danger);
}
.text-warning {
  color: var(--el-color-warning);
}
.text-success {
  color: var(--el-color-success);
}

/* 修复文本溢出 */
:deep(.el-table .cell) {
  white-space: nowrap;
}

/* --- 移动端响应式适配 (视口宽度 <= 992px) --- */
@media (max-width: 992px) {
  .event-reminders-page {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .side-panel {
    min-height: 300px;
  }
}

/* --- 移动端响应式适配 (视口宽度 <= 768px) --- */
@media (max-width: 768px) {
  .event-reminders-page {
    margin: 10px;
    gap: 10px;
  }

  .main-content,
  .side-panel {
    padding: 16px;
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
    justify-content: space-between;
  }

  /* 移动端隐藏日历视图切换按钮 */
  .hide-on-mobile {
    display: none !important;
  }

  /* 调整按钮大小以节省空间 */
  :deep(.el-table .el-button--small) {
    padding: 5px 12px;
  }
}
</style>
