<template>
  <div class="event-reminders-page">
    <div class="main-content">
      <div class="header-section">
        <div class="header-top">
          <div class="header-title-group">
            <h2>事项与日程</h2>
            <el-radio-group v-model="viewMode" size="small" class="view-switch">
              <el-radio-button label="table">
                <el-icon><List /></el-icon> 列表视图
              </el-radio-button>
              <el-radio-button label="calendar" class="hide-on-mobile">
                <el-icon><Calendar /></el-icon> 日历视图
              </el-radio-button>
            </el-radio-group>
          </div>
          <el-button type="primary" class="add-btn" :icon="Plus" @click="openDrawer()">
            新建日程
          </el-button>
        </div>

        <div class="filter-bar">
          <el-select
            v-model="mainLawyerId"
            placeholder="筛选主办律师"
            clearable
            filterable
            @change="handleFilterChange"
            class="lawyer-select"
          >
            <el-option
              v-for="lawyer in lawyerList"
              :key="lawyer.id"
              :label="lawyer.real_name"
              :value="lawyer.id"
            />
          </el-select>

          <el-radio-group
            v-show="viewMode === 'table'"
            v-model="relationFilter"
            @change="handleFilterChange"
            class="responsive-radio"
          >
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="mine">我的业务</el-radio-button>
            <el-radio-button label="others">他人业务</el-radio-button>
          </el-radio-group>

          <el-radio-group
            v-show="viewMode === 'table'"
            v-model="daysRange"
            @change="handleFilterChange"
            class="responsive-radio"
          >
            <el-radio-button :label="3">近3天</el-radio-button>
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
            <el-radio-button :label="0">全部</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div v-if="viewMode === 'table'" class="table-container">
        <el-table :data="events" border stripe style="width: 100%" v-loading="loading">
          <el-table-column label="状态" width="110" align="center">
            <template #default="scope">
              <el-tag :type="getUrgencyColor(scope.row.days_remaining)" effect="dark">
                剩 {{ scope.row.days_remaining }} 天
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="来源" width="100" align="center">
            <template #default="scope">
              <template v-if="scope.row.source === 'case'">
                <el-tag
                  :type="scope.row.is_mine ? 'primary' : 'info'"
                  size="small"
                  :effect="scope.row.is_mine ? 'light' : 'plain'"
                >
                  {{ scope.row.is_mine ? '我的业务' : '他人业务' }}
                </el-tag>
              </template>
              <el-tag v-else type="success" size="small" effect="light"> 自定义 </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="event_type" label="事项/标题" min-width="140" align="center">
            <template #default="scope">
              <el-tag :type="getEventTypeColor(scope.row.event_type)" effect="plain">
                {{ scope.row.event_type }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="event_date" label="提醒日期" width="110" align="center" />

          <el-table-column label="关联业务号" min-width="160" show-overflow-tooltip>
            <template #default="scope">
              {{ getDisplayCaseNumber(scope.row) }}
            </template>
          </el-table-column>

          <el-table-column label="委托人" min-width="110" show-overflow-tooltip>
            <template #default="scope">
              {{ getDisplayClientName(scope.row) }}
            </template>
          </el-table-column>

          <el-table-column label="详细备注" min-width="150" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.description" class="note-text">
                <el-icon class="note-icon"><Document /></el-icon>
                {{ scope.row.description }}
              </span>
              <span v-else style="color: #c0c4cc">--</span>
            </template>
          </el-table-column>

          <el-table-column
            label="操作"
            :width="isMobile ? 120 : 240"
            align="center"
            :fixed="isMobile ? false : 'right'"
          >
            <template #default="scope">
              <div class="action-buttons" :class="{ 'is-mobile-actions': isMobile }">
                <el-button
                  v-if="getCaseId(scope.row)"
                  size="small"
                  type="primary"
                  plain
                  :icon="View"
                  @click="goToCase(getCaseId(scope.row))"
                >
                  业务
                </el-button>

                <template v-if="scope.row.source === 'custom'">
                  <el-button
                    size="small"
                    type="warning"
                    plain
                    :icon="Edit"
                    @click="openDrawer(scope.row)"
                  >
                    编辑
                  </el-button>
                  <el-popconfirm
                    title="确定删除该日程吗？"
                    @confirm="handleDelete(scope.row.schedule_id)"
                  >
                    <template #reference>
                      <el-button size="small" type="danger" plain :icon="Delete">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && events.length === 0" description="近期无待办事项" />

        <div class="pagination-wrapper" v-if="totalEvents > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalEvents"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
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
                  :key="e.id || e.schedule_id"
                  class="event-badge"
                  :class="e.source"
                  :title="e.description ? `${e.event_type}\n备注: ${e.description}` : e.event_type"
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
            <h4>
              {{ activity.event_type }}
              <el-tag
                size="small"
                type="info"
                v-if="activity.source === 'case' && !activity.is_mine"
                style="margin-left: 6px; font-weight: normal"
              >
                他人业务
              </el-tag>
            </h4>
            <p v-if="getDisplayCaseNumber(activity) !== '--'" class="timeline-desc text-primary">
              <el-icon><Briefcase /></el-icon> {{ getDisplayCaseNumber(activity) }} ({{
                getDisplayClientName(activity)
              }})
            </p>
            <p v-if="activity.description" class="timeline-desc note-box">
              <el-icon><Document /></el-icon> {{ activity.description }}
            </p>
            <div class="timeline-footer">
              <span :class="'text-' + getUrgencyColor(activity.days_remaining)">
                <el-icon><Timer /></el-icon> 剩 {{ activity.days_remaining }} 天
              </span>
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
          <el-input v-model="form.title" placeholder="如：约见客户、提交材料" />
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
            :rows="5"
            placeholder="记录更详细的备忘信息，将直接显示在列表中..."
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue' // 引入 watch
import request from '@/utils/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  View,
  Document,
  Calendar,
  List,
  Briefcase,
  Timer,
} from '@element-plus/icons-vue'

const router = useRouter()

// 数据状态
const events = ref([])
const loading = ref(false)
const daysRange = ref(30) // 默认显示30天
const relationFilter = ref('all') // 关联筛选 'all', 'mine', 'others'
const viewMode = ref('table') // 视图切换
const calendarDate = ref(new Date())
const myCases = ref([]) // 我的业务

// 过滤与分页状态
const mainLawyerId = ref(null) // 主办律师筛选
const lawyerList = ref([]) // 律师下拉列表数据
const currentPage = ref(1) // 当前页码
const pageSize = ref(10) // 每页条数
const totalEvents = ref(0) // 总条数

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

// 响应式变量和监听函数判断是否为移动端
const isMobile = ref(window.innerWidth <= 768)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

// 计算属性：紧迫事项 (用于右侧Timeline展示前5个)
const urgentEvents = computed(() => {
  return events.value.slice(0, 5)
})

// 日历视图：获取指定日期的事项
const getEventsByDate = (dateStr) => {
  return events.value.filter((e) => e.event_date === dateStr)
}

// --- 数据映射辅助函数 (解决委托人/案号为空的问题) ---

// 安全获取case_id (兼容不同的后端返回字段)
const getCaseId = (row) => row.case_id || row.related_case_id || null

// 根据映射获取委托人姓名
const getDisplayClientName = (row) => {
  if (row.client_name) return row.client_name
  const cid = getCaseId(row)
  if (cid && myCases.value.length) {
    const matched = myCases.value.find((c) => c.case_id === cid)
    if (matched) return matched.client_name || '--'
  }
  return '--'
}

// 根据映射获取案号
const getDisplayCaseNumber = (row) => {
  if (row.case_number) return row.case_number
  const cid = getCaseId(row)
  if (cid && myCases.value.length) {
    const matched = myCases.value.find((c) => c.case_id === cid)
    if (matched) return matched.case_number || '--'
  }
  return '--'
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

// 获取律师列表供下拉筛选使用
const fetchLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyerList.value = res.data
  } catch (error) {
    console.error('获取律师列表失败', error)
  }
}

// 获取提醒列表 (适配了后端的各项优化)
const fetchReminders = async (resetPage = false) => {
  if (resetPage) currentPage.value = 1
  loading.value = true
  try {
    // 逻辑优化：如果是日历视图，为了渲染完整的月份，向后端请求非常大的 limit 取消分页限制
    const currentLimit = viewMode.value === 'calendar' ? 1000 : pageSize.value
    const currentSkip = viewMode.value === 'calendar' ? 0 : (currentPage.value - 1) * pageSize.value

    const res = await request.get('/user/profile/reminders', {
      params: {
        days: daysRange.value,
        main_lawyer_id: mainLawyerId.value || null,
        relation: relationFilter.value, // 传给后端的关系参数
        skip: currentSkip,
        limit: currentLimit,
      },
    })

    // 适配后端新的返回结构： { items: [...], total: ... }
    if (res.data && res.data.items !== undefined) {
      events.value = res.data.items
      totalEvents.value = res.data.total
    } else {
      // 兼容旧接口（若后端尚未完全更新）
      events.value = res.data || []
      totalEvents.value = events.value.length
    }
  } catch (error) {
    console.error('获取提醒失败', error)
    ElMessage.error('获取事项提醒失败')
  } finally {
    loading.value = false
  }
}

// 筛选条件改变触发
const handleFilterChange = () => {
  fetchReminders(true)
}

// 分页大小改变触发
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchReminders(true)
}

// 页码改变触发
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchReminders(false)
}

// 监听视图模式切换，切换时重新获取对应数据格式（分页 vs 全量）
watch(viewMode, () => {
  fetchReminders(true)
})

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
        fetchReminders(true) // 刷新列表并重置分页
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

    // 如果当前页只有一条数据，删除后页码前移
    if (events.value.length === 1 && currentPage.value > 1) {
      currentPage.value--
    }
    fetchReminders(false)
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
    form.related_case_id = getCaseId(row)
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
  } else {
    const cid = getCaseId(eventData)
    if (cid) goToCase(cid)
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
  window.addEventListener('resize', handleResize) // 监听窗口大小变化
  fetchLawyers() // 挂载时拉取律师列表
  fetchReminders(true)
  fetchMyCases() // 组件挂载时获取案件下拉数据，用于名称映射
})

// 组件销毁时移除监听，防止内存泄漏
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
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

/* ================= 头部与筛选栏重构样式 ================= */

.header-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 16px;
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title-group h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

/* 新增的独立灰色筛选卡片层 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background-color: #f8f9fb;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

/* 律师筛选下拉框样式 */
.lawyer-select {
  width: 140px;
}

/* ======================================================== */

.table-container,
.calendar-container {
  flex: 1;
  overflow-y: auto; /* 防止外层越界，滚动条限制在内部 */
  display: flex;
  flex-direction: column;
}

/* 分页组件外层包装器样式 */
.pagination-wrapper {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  padding-bottom: 10px;
}

/* --- 表格样式定制美化 --- */
:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa !important;
  color: #606266;
  font-weight: 600;
}
.note-text {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
}
.note-icon {
  color: #909399;
}

/* --- 自定义日历头部样式 --- */
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

/* --- 日历单元格防溢出 --- */
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

/* --- Timeline 卡片样式美化 --- */
.timeline-card {
  margin-bottom: 8px;
}
.timeline-card h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
  display: flex;
  align-items: center;
}
.timeline-desc {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
.note-box {
  background: #f4f4f5;
  padding: 6px;
  border-radius: 4px;
  color: #606266;
  align-items: flex-start;
}
.text-primary {
  color: var(--el-color-primary);
}
.timeline-footer {
  margin-top: 10px;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  align-items: center;
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

/* 操作列按钮组通用样式 */
.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

/* 覆盖 Element Plus 默认的兄弟按钮边距，全权由外层 gap 控制 */
.action-buttons .el-button {
  margin-left: 0 !important;
}

/* --- 平板端响应式适配 (视口宽度 <= 992px) --- */
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

/* --- 移动端响应式极致适配 (视口宽度 <= 768px) --- */
@media (max-width: 768px) {
  .event-reminders-page {
    margin: 10px;
    gap: 10px;
  }

  .main-content,
  .side-panel {
    padding: 16px;
  }

  /* 顶部重新排版：垂直居左 */
  .header-top {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding-bottom: 12px;
  }

  .header-title-group {
    justify-content: space-between; /* 标题和切换按钮分布两端 */
  }

  /* 筛选栏全部垂直化 */
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
    gap: 12px;
  }

  .lawyer-select {
    width: 100%;
  }

  /* 单选按钮组在手机上撑满等宽 */
  :deep(.responsive-radio) {
    display: flex;
    width: 100%;
  }
  :deep(.responsive-radio .el-radio-button) {
    flex: 1;
  }
  :deep(.responsive-radio .el-radio-button__inner) {
    width: 100%;
    padding: 8px 0;
    font-size: 13px; /* 字体略微缩小防折行 */
  }

  /* 移动端隐藏日历视图切换按钮 */
  .hide-on-mobile {
    display: none !important;
  }

  /* 调整按钮大小以节省空间 */
  :deep(.el-table .el-button--small) {
    padding: 5px 12px;
  }

  /* 移动端操作列纵向折叠适配 */
  .is-mobile-actions {
    flex-direction: column;
    gap: 6px;
  }

  /* 移动端让按钮宽度充满这一列，点击热区更大 */
  .is-mobile-actions .el-button {
    width: 100%;
  }
}
</style>
