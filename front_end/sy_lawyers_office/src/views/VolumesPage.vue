<template>
  <div class="volume-dashboard">
    <div class="dashboard-header-card">
      <div class="header-left">
        <div class="title-section">
          <h2>电子卷宗中心</h2>
          <span class="sub-title">全所案件卷宗归档与查阅</span>
        </div>
      </div>

      <div class="stat-group">
        <div class="stat-card">
          <div class="icon-wrapper bg-blue">
            <el-icon class="stat-icon"><Files /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">总卷宗册</div>
            <div class="stat-num">{{ totalVolumes }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="icon-wrapper bg-green">
            <el-icon class="stat-icon"><Box /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">已归档(合并)</div>
            <div class="stat-num success-text">{{ mergedCount }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="content-card">
      <div class="filter-bar">
        <div class="filter-left">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索业务号、当事人、卷宗名或关键词"
            :prefix-icon="Search"
            class="filter-item-input"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />

          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="shortcuts"
            class="filter-item-date"
            @change="handleSearch"
            clearable
          />

          <el-select
            v-model="filters.case_category"
            placeholder="业务类别"
            class="filter-item-select"
            clearable
            @change="handleSearch"
          >
            <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
          </el-select>

          <el-select
            v-if="isAdmin"
            v-model="filters.lawyer_id"
            placeholder="主办律师"
            class="filter-item-select"
            clearable
            filterable
            @change="handleSearch"
          >
            <el-option v-for="l in lawyers" :key="l.id" :label="l.real_name" :value="l.id" />
          </el-select>
        </div>

        <div class="filter-right">
          <el-button type="success" :icon="Plus" @click="openStandaloneDialog"
            >创建独立卷宗</el-button
          >
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="warning" plain icon="Search" @click="globalSearchVisible = true"
            >全文穿透搜索</el-button
          >
        </div>
      </div>

      <div class="table-responsive-wrapper">
        <el-table
          :data="tableData"
          v-loading="loading"
          border
          stripe
          highlight-current-row
          class="custom-table"
          header-cell-class-name="table-header-gray"
          @sort-change="handleSortChange"
        >
          <el-table-column
            label="关联业务号"
            min-width="180"
            align="center"
            :fixed="isMobile ? false : 'left'"
          >
            <template #default="{ row }">
              <el-link
                v-if="row.case"
                type="primary"
                :underline="false"
                class="case-link"
                @click="goToCaseDetail(row.case_id)"
              >
                {{ row.case.case_number }}
              </el-link>
              <el-tag v-else-if="row.is_standalone" type="warning" size="small" effect="plain"
                >独立卷宗</el-tag
              >
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>

          <el-table-column label="卷宗名称" min-width="220">
            <template #default="{ row }">
              <div class="vol-name-cell">
                <el-icon class="folder-icon"><Folder /></el-icon>
                <div class="vol-info">
                  <span class="vol-name" @click="goToManage(row)">{{ row.name }}</span>
                  <el-tag
                    v-if="row.merged_file_path"
                    size="small"
                    type="success"
                    effect="light"
                    class="status-tag"
                    >已归档</el-tag
                  >
                  <el-tag v-else size="small" type="info" effect="plain" class="status-tag"
                    >未归档</el-tag
                  >
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            prop="physical_location"
            label="纸质文件存放位置"
            min-width="160"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <div
                v-if="row.physical_location"
                style="display: flex; align-items: center; gap: 5px; color: #606266"
              >
                <el-icon><Location /></el-icon>
                <span>{{ row.physical_location }}</span>
              </div>
              <span v-else style="color: #ccc; font-size: 12px">未登记</span>
            </template>
          </el-table-column>

          <el-table-column label="业务类别" min-width="130" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{
                row.case?.case_category || row.category || '-'
              }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="主办律师" min-width="120" align="center">
            <template #default="{ row }">
              {{ row.case?.main_lawyer?.real_name || row.main_lawyer_name || '-' }}
            </template>
          </el-table-column>

          <el-table-column label="文件数" min-width="100" align="center">
            <template #default="{ row }">
              <span class="file-count">{{ row.file_count || 0 }}</span> 份
            </template>
          </el-table-column>

          <el-table-column
            prop="updated_at"
            label="最后更新"
            min-width="170"
            align="center"
            sortable="custom"
          >
            <template #default="{ row }">
              <span class="time-text">{{ formatTime(row.updated_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column
            label="操作"
            min-width="120"
            align="center"
            :fixed="isMobile ? false : 'right'"
          >
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="goToManage(row)">
                管理卷宗
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :total="pagination.total"
          :page-sizes="[15, 30, 50, 100]"
          :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
          :pager-count="isMobile ? 5 : 7"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <GlobalFileSearchDialog v-model:visible="globalSearchVisible" />

    <!-- 创建独立卷宗对话框 -->
    <el-dialog
      v-model="standaloneDialogVisible"
      title="创建独立卷宗"
      :width="isMobile ? '95%' : '550px'"
      destroy-on-close
      append-to-body
    >
      <el-form
        :model="standaloneForm"
        :label-width="isMobile ? 'auto' : '100px'"
        :label-position="isMobile ? 'top' : 'right'"
        @submit.prevent
      >
        <el-form-item label="卷宗名称" required>
          <el-input v-model="standaloneForm.name" placeholder="如：XX案一审卷宗" />
        </el-form-item>
        <el-row :gutter="16" v-if="!isMobile">
          <el-col :span="12">
            <el-form-item label="委托人姓名">
              <el-input v-model="standaloneForm.client_name" placeholder="委托人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托人电话">
              <el-input v-model="standaloneForm.client_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <template v-else>
          <el-form-item label="委托人姓名">
            <el-input v-model="standaloneForm.client_name" placeholder="委托人" />
          </el-form-item>
          <el-form-item label="委托人电话">
            <el-input v-model="standaloneForm.client_phone" placeholder="联系电话" />
          </el-form-item>
        </template>
        <el-row :gutter="16" v-if="!isMobile">
          <el-col :span="12">
            <el-form-item label="主办律师">
              <el-input v-model="standaloneForm.main_lawyer_name" placeholder="主办律师姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="案件类别">
              <el-select
                v-model="standaloneForm.category"
                placeholder="选择类别"
                style="width: 100%"
                clearable
              >
                <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <template v-else>
          <el-form-item label="主办律师">
            <el-input v-model="standaloneForm.main_lawyer_name" placeholder="主办律师姓名" />
          </el-form-item>
          <el-form-item label="案件类别">
            <el-select
              v-model="standaloneForm.category"
              placeholder="选择类别"
              style="width: 100%"
              clearable
            >
              <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="简要描述">
          <el-input
            v-model="standaloneForm.case_description"
            type="textarea"
            :rows="2"
            placeholder="案件简要描述"
          />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="standaloneForm.physical_location" placeholder="纸质原件存放位置" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="standaloneDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitStandaloneVolume" :loading="standaloneSubmitting"
          >确认创建</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, Search, Files, Box, Refresh, Location, Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import GlobalFileSearchDialog from '@/components/GlobalFileSearchDialog.vue'

const router = useRouter()
const isAdmin = ref(false)
const loading = ref(false)
const tableData = ref([])
const lawyers = ref([])
const totalVolumes = ref(0)
const mergedCount = ref(0)
const globalSearchVisible = ref(false)

// 独立卷宗创建相关
const standaloneDialogVisible = ref(false)
const standaloneSubmitting = ref(false)
const standaloneForm = ref({
  name: '',
  client_name: '',
  client_phone: '',
  main_lawyer_name: '',
  category: '',
  case_description: '',
  physical_location: '',
})

// 响应式屏幕判断
const screenWidth = ref(window.innerWidth)
const isMobile = computed(() => screenWidth.value < 768)

const handleResize = () => {
  screenWidth.value = window.innerWidth
}

const pagination = reactive({
  page: 1,
  limit: 15,
  total: 0,
})

// 排序状态（默认最新在前）
const sortOrder = ref('desc')

// 标准的排序监听方法
const handleSortChange = ({ order }) => {
  // Element Plus 的 order 值为 'ascending', 'descending', 或者 null
  if (order === 'ascending') {
    sortOrder.value = 'asc'
  } else if (order === 'descending') {
    sortOrder.value = 'desc'
  } else {
    // 如果用户点击到第三下取消了排序（order 为 null），强制设为默认的降序
    sortOrder.value = 'desc'
  }

  handleSearch()
}

const filters = reactive({
  keyword: '',
  dateRange: [],
  case_category: '',
  lawyer_id: null,
  archive_status: '',
})

const caseCategories = [
  '民事案件',
  '银行案件',
  '刑事案件',
  '行政案件',
  '非诉业务',
  '执行案件',
  '劳动仲裁',
  '商事仲裁',
  '法律顾问业务',
  '法律援助(民事)',
  '法律援助(刑事)',
  '法律援助(行政)',
]

const shortcuts = [
  {
    text: '今年',
    value: () => {
      const end = new Date()
      const start = new Date(new Date().getFullYear(), 0, 1)
      return [start, end]
    },
  },
  {
    text: '去年',
    value: () => {
      const date = new Date()
      const start = new Date(date.getFullYear() - 1, 0, 1)
      const end = new Date(date.getFullYear() - 1, 11, 31)
      return [start, end]
    },
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    },
  },
  {
    text: '最近90天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    },
  },
]

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await checkPermission()
  if (isAdmin.value) {
    await fetchLawyers()
  }
  await loadData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const checkPermission = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const res = await request.get(`/user/profile/info?user_id=${userId}`)
    const user = res.data
    isAdmin.value =
      user.role === 'owner' || (user.permissions && user.permissions.volume_manage === true)
  } catch (err) {
    console.error(err)
  }
}

const fetchLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyers.value = res.data
  } catch (e) {
    console.error('加载律师列表失败', e)
    ElMessage.error('加载律师列表失败')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.limit,
      keyword: filters.keyword || null,
      lawyer_id: filters.lawyer_id || null,
      case_category: filters.case_category || null,
      start_date: filters.dateRange && filters.dateRange[0] ? filters.dateRange[0] : null,
      end_date: filters.dateRange && filters.dateRange[1] ? filters.dateRange[1] : null,
      is_archived: filters.archive_status === '' ? null : filters.archive_status,
      sort_by: 'updated_at',
      sort_order: sortOrder.value,
    }

    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] === undefined) {
        params[key] = null
      }
    })

    const res = await request.get('/electronic_volumes/', { params })
    tableData.value = res.data.items
    pagination.total = res.data.total
    totalVolumes.value = res.data.total
    mergedCount.value = res.data.merged_count || 0
  } catch (err) {
    console.error(err)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.dateRange = []
  filters.case_category = ''
  filters.lawyer_id = null
  filters.archive_status = ''
  handleSearch()
}

const goToCaseDetail = (caseId) => {
  if (!caseId) return
  const routeUrl = router.resolve({
    path: `/main/cases/${caseId}`,
  })
  window.open(routeUrl.href, '_blank')
}

const goToManage = (row) => {
  if (row.is_standalone) {
    // 独立卷宗跳转到独立管理页
    const routeUrl = router.resolve({
      path: `/main/standalone-volume/${row.id}`,
    })
    window.open(routeUrl.href, '_blank')
  } else {
    const routeUrl = router.resolve({
      path: `/main/cases/${row.case_id}`,
      query: { tab: 'volume' },
    })
    window.open(routeUrl.href, '_blank')
  }
}

const openStandaloneDialog = () => {
  standaloneForm.value = {
    name: '',
    client_name: '',
    client_phone: '',
    main_lawyer_name: '',
    category: '',
    case_description: '',
    physical_location: '',
  }
  standaloneDialogVisible.value = true
}

const submitStandaloneVolume = async () => {
  if (!standaloneForm.value.name.trim()) {
    ElMessage.warning('请输入卷宗名称')
    return
  }
  standaloneSubmitting.value = true
  try {
    await request.post('/electronic_volumes/', {
      name: standaloneForm.value.name,
      client_name: standaloneForm.value.client_name || undefined,
      client_phone: standaloneForm.value.client_phone || undefined,
      main_lawyer_name: standaloneForm.value.main_lawyer_name || undefined,
      category: standaloneForm.value.category || undefined,
      case_description: standaloneForm.value.case_description || undefined,
      physical_location: standaloneForm.value.physical_location || undefined,
    })
    ElMessage.success('独立卷宗创建成功')
    standaloneDialogVisible.value = false
    await loadData()
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    standaloneSubmitting.value = false
  }
}

const formatTime = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleString()
}
</script>

<style scoped>
.volume-dashboard {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 80px);
}

.dashboard-header-card {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.title-section h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1f2d3d;
}

.sub-title {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
  display: block;
}

/* --- 统计卡片优化样式 --- */
.stat-group {
  display: flex;
  gap: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 12px; /* 圆角改大一点更现代 */
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 200px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.02); /* 默认微弱阴影 */
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); /* 悬浮时阴影加深 */
}

/* 外层容器控制背景和形状，避免挤压图标 */
.icon-wrapper {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

/* 控制图标的真实大小 */
.stat-icon {
  font-size: 26px;
  color: #ffffff;
}

/* 颜色与发光效果 */
.bg-blue {
  background-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3); /* 同色系发光阴影 */
}

.bg-green {
  background-color: #67c23a;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px; /* 调整标题和数字的间距 */
}

.stat-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.stat-num {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', sans-serif; /* 让数字字体更好看 */
}

.stat-num.success-text {
  color: #67c23a;
}

.content-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.filter-left {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter-item-input {
  width: 300px;
}
.filter-item-date {
  width: 240px !important;
  flex-grow: 0;
}
.filter-item-select {
  width: 150px;
}

.filter-right {
  display: flex;
  gap: 10px;
}

.custom-table {
  width: 100%;
}
.table-responsive-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
:deep(.table-header-gray) {
  background-color: #f5f7fa !important;
  color: #606266;
  font-weight: 600;
}

.vol-name-cell {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.vol-info {
  display: flex;
  flex-direction: column;
}
.folder-icon {
  color: #e6a23c;
  font-size: 18px;
  margin-top: 2px;
}
.vol-name {
  color: #303133;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}
.vol-name:hover {
  color: #409eff;
  text-decoration: underline;
}
.status-tag {
  margin-top: 4px;
  width: fit-content;
}

.case-link {
  font-family: monospace;
  font-weight: 600;
}
.file-count {
  font-weight: bold;
  color: #409eff;
}
.time-text {
  font-size: 13px;
  color: #909399;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式样式适配 */
@media (max-width: 768px) {
  /* 1. 基础容器适配，防止被内部元素撑开 */
  .volume-dashboard {
    padding: 8px;
    box-sizing: border-box;
    width: 100%;
    overflow-x: hidden;
  }
  .dashboard-header-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 14px;
    box-sizing: border-box;
    width: 100%;
  }
  .content-card {
    padding: 12px;
    box-sizing: border-box;
    width: 100%;
  }

  /* 标题缩小 */
  .title-section h2 {
    font-size: 18px;
  }
  .sub-title {
    font-size: 12px;
  }

  /* 2. 统计卡片适配 */
  .stat-group {
    width: 100%;
    justify-content: space-between;
    gap: 10px;
    box-sizing: border-box;
  }
  .stat-card {
    flex: 1;
    min-width: 0;
    padding: 10px 12px;
    gap: 10px;
  }
  .icon-wrapper {
    width: 40px;
    height: 40px;
    border-radius: 10px;
  }
  .stat-icon {
    font-size: 20px;
  }
  .stat-num {
    font-size: 18px;
  }
  .stat-label {
    font-size: 12px;
  }

  /* 3. 搜索和筛选栏适配 */
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
    box-sizing: border-box;
    gap: 12px;
    margin-bottom: 12px;
    padding-bottom: 12px;
  }
  .filter-left {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
    box-sizing: border-box;
    gap: 8px;
  }

  /* 强制所有输入框宽度 100% 且包含 padding */
  .filter-item-input,
  .filter-item-date,
  .filter-item-select {
    width: 100% !important;
    max-width: 100%;
    box-sizing: border-box;
  }

  /* 4. 核心修复：深度重置 el-date-picker 的内部强制宽度 */
  :deep(.el-date-editor.el-input__wrapper) {
    min-width: 0 !important;
    width: 100%;
    box-sizing: border-box;
    padding: 0 10px;
  }

  :deep(.el-range-input) {
    min-width: 0 !important;
    width: 100%;
    font-size: 13px;
  }

  :deep(.el-range-separator) {
    flex-shrink: 0;
    padding: 0 5px;
  }

  /* 5. 按钮区域适配 */
  .filter-right {
    width: 100%;
    justify-content: stretch;
  }
  .filter-right .el-button {
    flex: 1;
    margin: 0;
  }
  .filter-right .el-button + .el-button {
    margin-left: 8px;
  }

  /* 表格移动端优化 */
  .table-responsive-wrapper {
    margin-left: -12px;
    margin-right: -12px;
    width: calc(100% + 24px);
    padding: 0 4px;
    box-sizing: border-box;
  }

  /* 表格内字号缩小 */
  :deep(.custom-table .cell) {
    font-size: 12px;
    padding: 6px 4px;
  }

  .pagination-wrapper {
    justify-content: center;
    margin-top: 16px;
  }
}
</style>
