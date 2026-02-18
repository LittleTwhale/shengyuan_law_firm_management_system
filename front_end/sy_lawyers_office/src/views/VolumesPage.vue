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
          <el-icon class="stat-icon bg-blue"><Files /></el-icon>
          <div class="stat-info">
            <div class="stat-label">总卷宗册</div>
            <div class="stat-num">{{ totalVolumes }}</div>
          </div>
        </div>
        <div class="stat-card">
          <el-icon class="stat-icon bg-green"><Box /></el-icon>
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
            placeholder="搜索案号、卷宗名或当事人"
            prefix-icon="Search"
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
            placeholder="案件类别"
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
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </div>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        highlight-current-row
        class="custom-table"
        header-cell-class-name="table-header-gray"
      >
        <el-table-column label="关联业务号" width="220" align="center" fixed>
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
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <el-table-column label="卷宗名称" min-width="200">
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

        <el-table-column prop="case.case_category" label="案件类别" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.case?.case_category || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="case.main_lawyer.real_name"
          label="主办律师"
          width="120"
          align="center"
        />

        <el-table-column label="文件数" width="100" align="center">
          <template #default="{ row }">
            <span class="file-count">{{ row.files ? row.files.length : 0 }}</span> 份
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="最后更新" width="170" align="center">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="goToManage(row)"
              >管理卷宗</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :total="pagination.total"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, Search, Files, Box, Refresh, Location } from '@element-plus/icons-vue' // 新增 Location 图标
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const isAdmin = ref(false)
const loading = ref(false)
const tableData = ref([])
const lawyers = ref([])
const totalVolumes = ref(0)
const mergedCount = ref(0)

const pagination = reactive({
  page: 1,
  limit: 15,
  total: 0,
})

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
  await checkPermission()
  if (isAdmin.value) {
    await fetchLawyers()
  }
  await loadData()
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
  const routeUrl = router.resolve({
    path: `/main/cases/${row.case_id}`,
    query: { tab: 'volume' },
  })
  window.open(routeUrl.href, '_blank')
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

.stat-group {
  display: flex;
  gap: 24px;
}

.stat-card {
  background: #fcfcfc;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 180px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  font-size: 24px;
  padding: 10px;
  border-radius: 8px;
  color: #fff;
}
.bg-blue {
  background-color: #409eff;
}
.bg-green {
  background-color: #67c23a;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.stat-num.success-text {
  color: #67c23a;
}
.stat-label {
  font-size: 13px;
  color: #909399;
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
  width: 240px;
}
.filter-item-date {
  width: 260px !important;
  flex-grow: 0;
}
.filter-item-select {
  width: 150px;
}

.custom-table {
  width: 100%;
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

@media (max-width: 768px) {
  .dashboard-header-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  .stat-group {
    width: 100%;
    justify-content: space-between;
  }
  .stat-card {
    flex: 1;
    min-width: auto;
  }
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-left {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-item-input,
  .filter-item-date,
  .filter-item-select {
    width: 100% !important;
  }
}
</style>
