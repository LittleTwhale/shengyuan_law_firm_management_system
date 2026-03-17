<template>
  <div class="bank-cases-page">
    <div class="header">
      <h2>银行案件</h2>
      <div class="action-buttons">
        <el-button type="success" @click="handleExportClick">导出表格</el-button>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入业务号或委托银行"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          class="toolbar-item search-input"
        />

        <el-select
          v-if="currentUserRole === 'admin' || currentUserRole === 'owner'"
          v-model="selectedLawyerId"
          placeholder="主办律师筛选"
          clearable
          @change="handleSearch"
          class="toolbar-item filter-select"
        >
          <el-option
            v-for="lawyer in lawyers"
            :key="lawyer.id"
            :label="lawyer.real_name"
            :value="lawyer.id"
          />
        </el-select>

        <el-date-picker
          v-model="selectedYear"
          type="year"
          placeholder="选择年份"
          value-format="YYYY"
          @change="handleSearch"
          clearable
          class="toolbar-item year-picker"
        />
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="cases"
        border
        style="width: 100%"
        v-loading="tableLoading"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="case_number" label="业务号" min-width="200" align="center" />
        <el-table-column prop="client_name" label="委托银行" min-width="220" align="center" />
        <el-table-column prop="case_category" label="案件类别" min-width="120" align="center" />
        <el-table-column
          prop="main_lawyer.real_name"
          label="主办律师"
          min-width="120"
          align="center"
        />
        <el-table-column prop="review_status" label="审核状态" min-width="150" align="center" />
        <el-table-column
          prop="created_at"
          label="创建时间"
          min-width="180"
          align="center"
          sortable="custom"
          :formatter="(row, column, cellValue) => formatDate(cellValue)"
        />
        <el-table-column
          label="操作"
          min-width="400"
          header-align="center"
          align="left"
          :fixed="isMobile ? false : 'right'"
        >
          <template #default="scope">
            <el-button size="small" @click="viewCase(scope.row)">查看</el-button>
            <el-button size="small" type="warning" @click="handleEditClick(scope.row)"
              >编辑</el-button
            >
            <el-button
              size="small"
              type="danger"
              :disabled="currentUserRole === 'user' && scope.row.review_status === '已审核'"
              @click="deleteCase(scope.row.case_id)"
              >删除</el-button
            >

            <el-button size="small" type="primary" plain @click="handleUploadClick(scope.row)">
              <el-icon><Upload /></el-icon>
              上传附件
            </el-button>

            <el-button
              v-if="scope.row.review_status === '已审核'"
              link
              type="primary"
              size="small"
              @click="handleDownloadApproval(scope.row)"
            >
              <el-icon><Document /></el-icon>
              下载审批表
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-pagination
      background
      :layout="isMobile ? 'prev, pager, next' : 'prev, pager, next, jumper, ->, total'"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      @current-change="handlePageChange"
      style="margin-top: 16px; text-align: right; justify-content: flex-end; display: flex"
    />

    <CaseForm
      v-model:visible="showFormDialog"
      :lawyers="lawyers"
      :initial-form-data="formData"
      :mode="formMode"
      :current-user-id="currentUserID"
      :current-user-role="currentUserRole"
      :case-id="currentCaseId"
      :review-status="currentReviewStatus"
      @submit="handleFormSubmit"
    />

    <el-dialog
      title="上传附件"
      v-model="uploadDialogVisible"
      :width="isMobile ? '95%' : '600px'"
      :close-on-click-modal="false"
      destroy-on-close
      @close="resetUploadDialog"
      class="upload-dialog"
    >
      <div class="upload-container">
        <div class="case-info-bar">
          <el-icon><Document /></el-icon>
          <span class="label">当前案件：</span>
          <span class="value">{{ currentUploadCaseNumber }}</span>
        </div>

        <el-upload
          ref="attachmentUploadRef"
          class="upload-demo"
          drag
          action="#"
          :auto-upload="false"
          multiple
          :on-change="handleAttachmentChange"
          :on-remove="handleAttachmentRemove"
          v-model:file-list="attachmentFileList"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              <p>1. 支持多文件同时上传</p>
              <p>2. 单个文件建议不超过 50MB</p>
            </div>
          </template>
        </el-upload>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitAttachments"
            :loading="isUploadingAttachments"
            :disabled="attachmentFileList.length === 0"
          >
            <el-icon v-if="!isUploadingAttachments"><Upload /></el-icon>
            {{ isUploadingAttachments ? '正在上传...' : '开始上传' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      title="导出银行案件数据"
      v-model="showExportDialog"
      :width="isMobile ? '95%' : '550px'"
      :close-on-click-modal="false"
    >
      <el-form
        :model="exportForm"
        :label-width="isMobile ? 'auto' : '110px'"
        :label-position="isMobile ? 'top' : 'right'"
      >
        <el-form-item label="搜索关键词">
          <el-input v-model="exportForm.keyword" placeholder="按业务号/委托银行搜索" clearable />
        </el-form-item>

        <el-form-item
          label="主办律师"
          v-if="currentUserRole === 'admin' || currentUserRole === 'owner'"
        >
          <el-select
            v-model="exportForm.main_lawyer_id"
            placeholder="全部律师"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="lawyer in lawyers"
              :key="lawyer.id"
              :label="lawyer.real_name"
              :value="lawyer.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="委托日期区间">
          <el-date-picker
            v-model="exportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            clearable
          />
          <div class="form-tip text-muted">
            提示：若设置了精确的日期区间，下方的年份筛选将自动失效。
          </div>
        </el-form-item>

        <el-form-item label="指定年份">
          <el-date-picker
            v-model="exportForm.year"
            type="year"
            placeholder="选择年份"
            value-format="YYYY"
            style="width: 100%"
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" :loading="isExporting" @click="submitExport">
            <el-icon v-if="!isExporting"><Download /></el-icon>
            {{ isExporting ? '生成并导出中...' : '确认导出' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import CaseForm from './CaseForm.vue'
import { useRouter } from 'vue-router'
// 导入需要的图标
import { Document, Upload, UploadFilled, Download } from '@element-plus/icons-vue'

// -------------------------- 响应式/移动端适配相关 --------------------------
const isMobile = ref(false)
const checkDeviceType = () => {
  isMobile.value = window.innerWidth <= 768
}

// 当前用户信息
const currentUserID = ref(localStorage.getItem('user_id'))
const currentUserRole = ref(localStorage.getItem('role'))

// 表格与分页数据
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const cases = ref([])
const tableLoading = ref(false)
const searchKeyword = ref('') // 搜索关键词
const selectedLawyerId = ref(null) // 选中的主办律师ID
// 年份变量，默认为当前年份字符串
const selectedYear = ref(new Date().getFullYear().toString())

// 排序相关的响应式变量
const currentSortField = ref('created_at') // 默认按创建时间排序
const currentSortDir = ref('desc') // 默认降序（最新的在前面）

// 弹窗控制
const showFormDialog = ref(false)
const formMode = ref('edit') // 只有编辑模式
const currentCaseId = ref('')
const formData = reactive({})
const lawyers = ref([])

const router = useRouter()

// 初始化加载
onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)

  Promise.all([loadLawyers(), loadBankCases()]).catch((err) => console.error('初始化失败:', err))
})

// 组件销毁前移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})

// 加载律师列表
const loadLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyers.value = res.data || []
  } catch (err) {
    console.error('加载律师列表失败:', err)
    lawyers.value = []
  }
}

// 加载银行案件列表
const loadBankCases = async () => {
  tableLoading.value = true
  try {
    const res = await request.get('/cases/bank_cases', {
      params: {
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
        keyword: searchKeyword.value,
        year: selectedYear.value || '', // 年份筛选
        sort_field: currentSortField.value, // 排序字段
        sort_dir: currentSortDir.value, // 排序方向
        ...(currentUserRole.value === 'admin' || currentUserRole.value === 'owner'
          ? { main_lawyer_id: selectedLawyerId.value }
          : {}),
      },
    })
    cases.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('加载银行案件失败:', err)
    cases.value = []
    total.value = 0
    ElMessage.error('获取银行案件列表失败')
  } finally {
    tableLoading.value = false
  }
}

// -------------------------- 处理表格排序事件 --------------------------
const handleSortChange = ({ prop, order }) => {
  if (prop === 'created_at') {
    if (order === 'ascending') {
      currentSortDir.value = 'asc'
    } else if (order === 'descending') {
      currentSortDir.value = 'desc'
    } else {
      // 如果用户取消排序，通常恢复默认排序（降序）
      currentSortDir.value = 'desc'
    }

    currentSortField.value = 'created_at'

    // 重置到第一页并重新加载数据
    page.value = 1
    loadBankCases()
  }
}

// 分页切换
const handlePageChange = (p) => {
  page.value = p
  loadBankCases()
}

// 搜索功能
const handleSearch = () => {
  page.value = 1 // 重置到第一页
  loadBankCases()
}

// 查看案件详情
const viewCase = (row) => {
  const routeData = router.resolve({
    path: `/main/cases/${row.case_id}`,
    query: {
      from: '/main/cases/bank_cases',
    },
  })
  window.open(routeData.href, '_blank')
}

// 记录当前操作案件的审核状态
const currentReviewStatus = ref('')
// 编辑案件
const handleEditClick = async (row) => {
  formMode.value = 'edit'
  currentCaseId.value = row.case_id
  currentReviewStatus.value = row.review_status
  try {
    const res = await request.get(`/cases/${row.case_id}`)
    Object.assign(formData, JSON.parse(JSON.stringify(res.data)))
    showFormDialog.value = true
  } catch (err) {
    console.error('加载案件详情失败:', err)
    ElMessage.error('加载案件详情失败')
  }
}

// 提交编辑表单
const handleFormSubmit = () => {
  // CaseForm 组件内部已经处理了真实的保存 API 调用和关闭弹窗
  // 这里只需要重新加载列表数据
  loadBankCases()
}

// 删除案件
const deleteCase = async (caseId) => {
  if (!confirm('确定要删除该案件吗？')) return

  try {
    await request.delete(`/cases/case_delete/${caseId}`)
    ElMessage.success('删除案件成功')
    await loadBankCases()
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 下载审批表 --------------------------
const handleDownloadApproval = async (row) => {
  try {
    ElMessage.info('正在生成审批表，请稍候...')

    const response = await request.get(`/case_review/${row.case_id}/approval_form`, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })

    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `业务审批表_${row.case_number}.docx`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)

    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载审批表失败:', error)
    ElMessage.error('下载审批表失败，请稍后重试')
  }
}

// -------------------------- 独立上传附件逻辑 --------------------------
const uploadDialogVisible = ref(false)
const isUploadingAttachments = ref(false)
const attachmentFileList = ref([])
const currentUploadCaseId = ref(null)
const currentUploadCaseNumber = ref('')

// 点击列表中的“上传附件”按钮
const handleUploadClick = (row) => {
  currentUploadCaseId.value = row.case_id
  currentUploadCaseNumber.value = row.case_number
  attachmentFileList.value = [] // 清空旧文件列表
  uploadDialogVisible.value = true
}

// 监听文件选择变化
const handleAttachmentChange = (file, fileList) => {
  attachmentFileList.value = fileList
}

// 监听文件移除
const handleAttachmentRemove = (file, fileList) => {
  attachmentFileList.value = fileList
}

// 重置弹窗状态
const resetUploadDialog = () => {
  attachmentFileList.value = []
  isUploadingAttachments.value = false
}

// 提交上传
const submitAttachments = async () => {
  if (attachmentFileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  isUploadingAttachments.value = true

  try {
    const uploadPromises = attachmentFileList.value.map((file) => {
      const formData = new FormData()
      formData.append('case_id', currentUploadCaseId.value)
      formData.append('file', file.raw)

      return request.post('/attachments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    })

    await Promise.all(uploadPromises)

    ElMessage.success(`成功上传 ${attachmentFileList.value.length} 个附件`)
    uploadDialogVisible.value = false
  } catch (error) {
    console.error('附件上传失败:', error)
    ElMessage.error('部分或全部附件上传失败，请重试')
  } finally {
    isUploadingAttachments.value = false
  }
}

// -------------------------- 导出Excel表格 (弹窗模式) --------------------------
const showExportDialog = ref(false)
const isExporting = ref(false)

// 导出表单数据
const exportForm = reactive({
  keyword: '',
  main_lawyer_id: null,
  year: '',
  dateRange: [],
})

// 打开导出弹窗，同步当前的筛选状态
const handleExportClick = () => {
  exportForm.keyword = searchKeyword.value || ''
  exportForm.main_lawyer_id = selectedLawyerId.value || null
  exportForm.year = selectedYear.value || ''
  exportForm.dateRange = []
  showExportDialog.value = true
}

// 确认导出
const submitExport = async () => {
  try {
    isExporting.value = true

    // 构建符合后端的 CaseExportQuery 的 payload
    // 注意这里强制锁定 case_category: '银行案件'
    const payload = {
      keyword: exportForm.keyword || null,
      case_category: '银行案件',
      main_lawyer_id: exportForm.main_lawyer_id || null,
      year: exportForm.year || null,
      start_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[0] : null,
      end_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[1] : null,
    }

    // 调用与总库一样的 export 接口
    const response = await request.post('/cases/export', payload, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl

    const timestamp = new Date()
      .toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
      .replace(/\D/g, '')
    link.download = `银行案件数据_${timestamp}.xlsx`

    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElMessage.success('Excel 文件导出成功 ✅')
    showExportDialog.value = false
  } catch (error) {
    console.error('导出Excel失败：', error)
    ElMessage.error('导出失败，请检查网络或稍后重试 ❌')
  } finally {
    isExporting.value = false
  }
}

// 日期格式化
const formatDate = (dateVal) => {
  if (!dateVal) return ''

  let timestamp

  if (typeof dateVal === 'number') {
    if (dateVal.toString().length === 10) {
      dateVal *= 1000
    }
    timestamp = dateVal
  } else if (typeof dateVal === 'string') {
    const formats = [dateVal.replace(' ', 'T'), dateVal.replace(' ', 'T') + 'Z', dateVal]

    for (const fmt of formats) {
      const tempDate = new Date(fmt)
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime()
        break
      }
    }
  } else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime()
  }

  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal)
    return '无效日期'
  }

  const date = new Date(timestamp)

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

/* 顶部搜索/筛选栏基础样式 */
.toolbar {
  margin-bottom: 15px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* 允许换行 */
  gap: 15px; /* 使用 gap 代替原先复杂的 margin 控制 */
}
/* 提取原有的内联宽度到 class 中，方便媒体查询覆盖 */
.search-input {
  width: 250px;
}
.filter-select {
  width: 200px;
}
.year-picker {
  width: 120px;
}

/* 上传弹窗样式优化 */
.upload-container {
  padding: 0 10px;
}

.case-info-bar {
  display: flex;
  align-items: center;
  background-color: #f0f9eb;
  border: 1px solid #e1f3d8;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #67c23a;
}

.case-info-bar .el-icon {
  font-size: 18px;
  margin-right: 8px;
}

.case-info-bar .label {
  font-weight: bold;
  margin-right: 8px;
}

.case-info-bar .value {
  font-family: monospace;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.upload-demo {
  text-align: center;
}

.el-upload__tip {
  margin-top: 10px;
  color: #909399;
  font-size: 12px;
  line-height: 1.6;
  text-align: left;
  background-color: #f4f4f5;
  padding: 8px 12px;
  border-radius: 4px;
}

.el-upload__tip p {
  margin: 0;
}

/* 表单辅助提示文字 */
.form-tip.text-muted {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}

/* =======================================
   移动端响应式适配 CSS
   ======================================= */
@media screen and (max-width: 768px) {
  /* 头部标题和按钮堆叠排列 */
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .action-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  /* 移除 Element 按钮自带的 margin-left，统一用 flex gap 管理间距 */
  .action-buttons .el-button {
    margin-left: 0 !important;
  }

  /* 搜索框和筛选条件垂直平铺 */
  .toolbar-left {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  /* 所有筛选控件在移动端占满 100% 宽度 */
  .toolbar-item {
    width: 100% !important;
  }

  /* 调整弹窗内部文字排版 */
  .case-info-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style>
