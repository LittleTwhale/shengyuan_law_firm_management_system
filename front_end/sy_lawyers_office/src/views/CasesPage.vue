<template>
  <div class="cases-page">
    <div class="header">
      <div class="page-title">
        <h2>业务管理</h2>
        <p class="page-subtitle">统一管理业务数据、附件上传、批量导入与导出</p>
      </div>

      <div class="action-buttons">
        <el-button type="primary" @click="handleAddClick">新增业务</el-button>
        <el-button type="warning" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button
          type="success"
          plain
          :disabled="selectedCases.length === 0"
          :loading="isExportingSelected"
          @click="handleExportSelected"
        >
          导出选中
        </el-button>
        <el-button type="success" @click="handleExportClick">导出表格</el-button>
        <el-button type="danger" :disabled="selectedCases.length === 0" @click="handleBatchDelete">
          批量删除
        </el-button>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入业务号或当事人"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          class="toolbar-item search-input"
        />
        <el-select
          v-model="selectedCategory"
          placeholder="业务类别筛选"
          clearable
          filterable
          @change="handleSearch"
          class="toolbar-item filter-select"
        >
          <el-option
            v-for="category in caseCategories"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>

        <el-select
          v-model="selectedLawyerId"
          placeholder="主办律师筛选"
          clearable
          filterable
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

        <el-select
          v-model="selectedExecutionLawyerId"
          placeholder="执行主办律师筛选"
          clearable
          filterable
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

        <el-select
          v-model="selectedReviewStatus"
          placeholder="审核状态筛选"
          clearable
          @change="handleSearch"
          class="toolbar-item filter-select"
        >
          <el-option label="待审核" value="待审核" />
          <el-option label="已审核" value="已审核" />
          <el-option label="已拒绝" value="已拒绝" />
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

        <el-select
          v-model="selectedMonth"
          placeholder="选择月份(按委托日期)"
          clearable
          @change="handleSearch"
          class="toolbar-item month-select"
        >
          <el-option v-for="m in monthOptions" :key="m" :label="`${m}月`" :value="m" />
        </el-select>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="cases"
        border
        style="width: 100%"
        v-loading="tableLoading"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        class="cases-table"
      >
        <el-table-column type="selection" width="55" align="center" />

        <el-table-column prop="case_number" label="业务号" min-width="200" align="center" />
        <el-table-column label="委托人" min-width="220" align="center">
          <template #default="{ row }">
            {{ getClientNames(row.parties) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="case_category" label="业务类别" min-width="150" align="center" />
        <el-table-column
          prop="main_lawyer.real_name"
          label="主办律师"
          min-width="120"
          align="center"
        />

        <el-table-column label="审核状态" min-width="140" align="center">
          <template #default="scope">
            <el-tooltip
              v-if="scope.row.review_status === '已拒绝' && scope.row.review_comment"
              :content="scope.row.review_comment"
              placement="top"
              :show-after="300"
              effect="light"
            >
              <div class="review-status-with-badge">
                <el-tag :type="getReviewStatusType(scope.row.review_status)" effect="dark" size="small">
                  {{ scope.row.review_status }}
                </el-tag>
                <el-icon class="comment-indicator" :size="14"><Warning /></el-icon>
              </div>
            </el-tooltip>
            <el-tag v-else :type="getReviewStatusType(scope.row.review_status)" effect="dark" size="small">
              {{ scope.row.review_status || '未知' }}
            </el-tag>
          </template>
        </el-table-column>

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
          min-width="290"
          header-align="center"
          align="left"
          :fixed="isMobile ? false : 'right'"
        >
          <template #default="scope">
            <div class="row-actions">
              <el-dropdown
                split-button
                size="small"
                @click="viewCase(scope.row, 'current')"
                @command="(cmd) => viewCase(scope.row, cmd)"
              >
                查看
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="blank">新标签页打开</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-button size="small" type="warning" @click="handleEditClick(scope.row)">
                编辑
              </el-button>

              <el-button
                size="small"
                type="danger"
                :disabled="isDeleteDisabled(scope.row)"
                @click="deleteCase(scope.row.case_id)"
              >
                删除
              </el-button>

              <el-dropdown trigger="click" @command="(cmd) => handleMoreAction(cmd, scope.row)">
                <el-button size="small" plain>
                  更多 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="clone">
                      <el-icon><CopyDocument /></el-icon> 复用此业务
                    </el-dropdown-item>

                    <el-dropdown-item command="upload">
                      <el-icon><Upload /></el-icon> 上传附件
                    </el-dropdown-item>

                    <el-dropdown-item
                      v-if="scope.row.review_status === '已审核'"
                      command="download"
                    >
                      <el-icon><Download /></el-icon>
                      下载审批表
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-pagination
      background
      :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
      :page-sizes="[10, 15, 30, 50, 100]"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
      :pager-count="isMobile ? 4 : 7"
      class="page-pagination"
    />

    <CaseForm
      v-model:visible="showFormDialog"
      :lawyers="lawyers"
      :initial-form-data="formData"
      :mode="formMode"
      :current-user-id="currentUserID"
      :current-user-role="currentUserRole"
      :case-id="formMode === 'edit' ? currentCaseId : null"
      :clone-id="currentCloneId"
      :review-status="currentReviewStatus"
      @submit="handleFormSubmit"
    />

    <el-dialog
      title="批量导入案件"
      v-model="showImportDialog"
      :width="isMobile ? '95%' : '600px'"
      :close-on-click-modal="false"
      class="styled-dialog import-dialog"
    >
      <div class="import-container">
        <p class="import-tip">
          支持.xlsx/.xls格式，模板下载：<el-link @click="downloadTemplate">案件导入模板</el-link>
        </p>

        <el-upload
          class="upload-area"
          drag
          ref="uploadRef"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          :accept="'.xlsx,.xls'"
          :limit="1"
          :on-exceed="handleExceed"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">将 Excel 文件拖到此处，或 <em>点击选择</em></div>

          <template #tip>
            <div class="el-upload__tip text-danger upload-tip-note">
              请确保Excel表头包含：业务号、业务类别
            </div>
          </template>
        </el-upload>

        <el-progress
          v-if="showProgress"
          :percentage="progress"
          stroke-width="4"
          class="upload-progress"
        ></el-progress>
      </div>

      <template #footer>
        <el-button @click="showImportDialog = false" :disabled="isUploading">取消</el-button>
        <el-button type="primary" @click="handleImport" :disabled="!canUpload || isUploading">
          <el-icon v-if="!isUploading"><Check /></el-icon>
          <el-icon v-if="isUploading"><Loading /></el-icon>
          {{ isUploading ? '导入中...' : '开始导入' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      title="导入结果"
      v-model="showResultDialog"
      :width="isMobile ? '95%' : '700px'"
      :close-on-click-modal="false"
      class="styled-dialog result-dialog"
    >
      <div class="result-stats">
        <div class="stat-item">
          <span>总条数：</span>
          <span class="total">{{ result.total_cases || 0 }}</span>
        </div>
        <div class="stat-item">
          <span>成功条数：</span>
          <span class="success">{{ result.imported_cases || 0 }}</span>
        </div>
        <div class="stat-item">
          <span>失败条数：</span>
          <span class="failed">{{ result.failed_cases?.length || 0 }}</span>
        </div>
      </div>

      <div class="result-table-wrap">
        <el-table
          v-if="result.failed_cases && result.failed_cases.length"
          :data="result.failed_cases"
          border
          style="width: 100%; min-width: 400px"
        >
          <el-table-column prop="case_number" label="业务号/行号" width="150"></el-table-column>
          <el-table-column prop="reason" label="失败原因"></el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showResultDialog = false">关闭</el-button>
        <el-button
          type="primary"
          @click="handleDownloadErrorLog"
          :disabled="!result.failed_cases || !result.failed_cases.length"
        >
          下载错误日志
        </el-button>
      </template>
    </el-dialog>


    <el-dialog
      title="上传附件"
      v-model="uploadDialogVisible"
      :width="isMobile ? '95%' : '600px'"
      :close-on-click-modal="false"
      destroy-on-close
      @close="resetUploadDialog"
      class="styled-dialog upload-dialog"
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
            <div class="el-upload__tip attachment-tip">
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
      title="导出业务数据"
      v-model="showExportDialog"
      :width="isMobile ? '95%' : '550px'"
      :close-on-click-modal="false"
      class="styled-dialog export-dialog"
    >
      <el-form
        :model="exportForm"
        :label-width="isMobile ? 'auto' : '110px'"
        :label-position="isMobile ? 'top' : 'right'"
        class="export-form"
      >
        <el-form-item label="搜索关键词">
          <el-input v-model="exportForm.keyword" placeholder="按业务号/委托人搜索" clearable />
        </el-form-item>

        <el-form-item label="业务类别">
          <el-select
            v-model="exportForm.case_category"
            placeholder="全部类别"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="category in caseCategories"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="主办律师"
          v-if="currentUserRole === 'admin' || currentUserRole === 'owner'"
        >
          <el-select
            v-model="exportForm.main_lawyer_id"
            placeholder="全部律师"
            clearable
            filterable
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

        <el-form-item
          label="执行主办律师"
          v-if="currentUserRole === 'admin' || currentUserRole === 'owner'"
        >
          <el-select
            v-model="exportForm.execution_lawyer_id"
            placeholder="全部执行律师"
            clearable
            filterable
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

        <el-form-item label="指定月份">
          <el-select
            v-model="exportForm.month"
            placeholder="选择月份(按委托日期)"
            clearable
            style="width: 100%"
          >
            <el-option v-for="m in monthOptions" :key="m" :label="`${m}月`" :value="m" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" :loading="isExporting" @click="submitExport">
            <el-icon v-if="!isExporting"><Download /></el-icon>
            {{
              isExporting
                ? exportProgress > 0 && exportProgress < 100
                  ? `下载中 ${exportProgress}%`
                  : '生成并导出中...'
                : '确认导出'
            }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue' // 新增了 onUnmounted
import request from '@/utils/request'
import { uploadToCOS } from '@/utils/cosUpload'
import { ElMessage, ElNotification } from 'element-plus'
import CaseForm from './CaseForm.vue' // 引入抽离的CaseForm组件
import { useRouter } from 'vue-router'
import { handleErrorAnalysis } from '@/utils/errorAnalysisNotify'
import {
  Check,
  Document,
  Loading,
  Upload,
  UploadFilled,
  Download,
  ArrowDown,
  CopyDocument,
  Warning,
} from '@element-plus/icons-vue'

// 辅助函数：从 parties 中提取委托人名称
const getClientNames = (parties) => {
  if (!parties || !parties.length) return ''
  return parties
    .filter(p => p.party_type && p.party_type.includes('委托'))
    .map(p => p.name)
    .join('、')
}

// -------------------------- 响应式/移动端适配相关 --------------------------
const isMobile = ref(false)
const checkDeviceType = () => {
  isMobile.value = window.innerWidth <= 768
}

// -------------------------- 当前用户数据 ----------------------------
const currentUserID = ref(localStorage.getItem('user_id'))
const currentUserRole = ref(localStorage.getItem('role'))

// >>>>>>>>> 删除权限综合判断逻辑 >>>>>>>>>
// 允许删除银行案件的特定用户 ID 白名单
const allowedDeleteUserIds = ['1', '2', '3']

// 计算属性，判断当前登录用户是否在白名单内
const hasDeletePermission = computed(() => {
  return allowedDeleteUserIds.includes(currentUserID.value)
})

// 判断某一行数据是否禁用删除功能
const isDeleteDisabled = (row) => {
  // 如果案件未审核或已拒绝，任何人均不禁用（均可删除）
  if (row.review_status !== '已审核') return false

  // 如果是“已审核”的案件，按业务分类区分逻辑：
  if (row.case_category === '银行案件') {
    // 银行案件：不在白名单内的用户禁用
    return !hasDeletePermission.value
  } else {
    // 其他案件：普通 user 禁用
    return currentUserRole.value === 'user'
  }
}

// -------------------------- 表格与分页相关 --------------------------
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const cases = ref([])
const tableLoading = ref(false) // 表格加载状态

// -------------------------- 搜索与筛选相关 --------------------------
const searchKeyword = ref('')
const selectedCategory = ref('')
// 案件类别选项
const caseCategories = ref([
  { label: '民事案件', value: '民事案件' },
  { label: '银行案件', value: '银行案件' },
  { label: '刑事案件', value: '刑事案件' },
  { label: '行政案件', value: '行政案件' },
  { label: '非诉业务', value: '非诉业务' },
  { label: '执行案件', value: '执行案件' },
  { label: '劳动仲裁', value: '劳动仲裁' },
  { label: '商事仲裁', value: '商事仲裁' },
  { label: '法律顾问业务', value: '法律顾问业务' },
  { label: '法律援助(民事)', value: '法律援助(民事)' },
  { label: '法律援助(刑事)', value: '法律援助(刑事)' },
  { label: '法律援助(行政)', value: '法律援助(行政)' },
])

// 根据审核状态返回 Tag 颜色类型
const getReviewStatusType = (status) => {
  if (status === '已审核') return 'success'
  if (status === '待审核' || status === '未审核') return 'warning'
  if (status === '已拒绝') return 'danger' // 修改为已拒绝
  return 'info'
}

const selectedLawyerId = ref(null) // 选中的主办律师ID
const selectedExecutionLawyerId = ref(null) // 选中的执行主办律师ID
const selectedReviewStatus = ref('') // 选中的审核状态筛选
// 年份变量，默认为当前年份字符串
const selectedYear = ref(new Date().getFullYear().toString())
// 月份变量（按委托日期筛选，与年份独立叠加），默认为空
const selectedMonth = ref(null)
// 月份下拉选项：1-12 月
const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1)
// 排序相关的响应式变量
const currentSortField = ref('created_at') // 默认按创建时间排序
const currentSortDir = ref('desc') // 默认降序（最新的在前面）

// -------------------------- 弹窗控制相关 --------------------------
// 明确指定formMode的类型为'add'或'edit'
const formMode = ref('add') // 表单模式：'add'（新增）/'edit'（编辑）
const currentCaseId = ref('') // 当前编辑的案件ID（编辑时用）
const currentCloneId = ref(null) // 用于记录正在被复用的业务ID

// -------------------------- 数据存储相关 --------------------------
const lawyers = ref([]) // 律师列表
const formData = reactive({}) // 传递给CaseForm的表单数据

// -------------------------- 初始化加载 --------------------------
onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)

  Promise.all([loadLawyers(), loadCases()]) // 并行加载律师和案件列表
    .catch((err) => console.error('初始化加载失败:', err))
})

// 组件销毁前移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})

// -------------------------- 律师列表加载 --------------------------
const loadLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyers.value = res.data || []
  } catch (err) {
    console.error('加载律师列表失败:', err)
    lawyers.value = []
  }
}

// -------------------------- 案件列表加载 --------------------------
const loadCases = async () => {
  tableLoading.value = true
  try {
    const res = await request.get('/cases/', {
      params: {
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
        keyword: searchKeyword.value, // 搜索关键词
        category: selectedCategory.value, // 类别筛选
        year: selectedYear.value || '', // 年份筛选
        month: selectedMonth.value, // 月份筛选（按委托日期）
        sort_field: currentSortField.value,
        sort_dir: currentSortDir.value,
        main_lawyer_id: selectedLawyerId.value, // 主办律师筛选
        execution_lawyer_id: selectedExecutionLawyerId.value, // 执行主办律师筛选
        review_status: selectedReviewStatus.value || '', // 审核状态筛选
      },
    })
    cases.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('加载案件列表失败:', err)
    cases.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

// -------------------------- 处理表格排序事件 --------------------------
const handleSortChange = ({ prop, order }) => {
  // prop 是列的属性名（如 'created_at'）
  // order 是排序方式：'ascending'（升序）, 'descending'（降序）, null（取消排序）

  if (prop === 'created_at') {
    // 映射 Element Plus 的排序状态到后端 API 需要的格式 ('asc' / 'desc')
    if (order === 'ascending') {
      currentSortDir.value = 'asc'
    } else if (order === 'descending') {
      currentSortDir.value = 'desc'
    } else {
      // 如果用户取消排序（即 order 为 null），通常恢复默认排序（降序）
      currentSortDir.value = 'desc'
    }

    // 更新排序字段（虽然这里只有创建时间，但为了扩展性可以写上）
    currentSortField.value = 'created_at'

    // 重置到第一页并重新加载数据
    page.value = 1
    loadCases()
  }
}

// -------------------------- 搜索功能 --------------------------
const handleSearch = () => {
  page.value = 1 // 重置为第一页
  loadCases()
}

// -------------------------- 分页切换 --------------------------
const handlePageChange = (p) => {
  page.value = p
  loadCases()
}

// 切换每页条数
const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1 // 切换每页条数后，务必重置回第一页
  loadCases()
}

// -------------------------- 批量删除相关 --------------------------
const selectedCases = ref([]) // 存储当前选中的行数据

// 表格选中项变化时的回调
const handleSelectionChange = (val) => {
  selectedCases.value = val
}

// 执行批量删除
const handleBatchDelete = async () => {
  if (selectedCases.value.length === 0) return

  // 1. 权限过滤：根据不同业务类型，检查是否有无权删除的案件
  const validCases = selectedCases.value.filter((row) => !isDeleteDisabled(row))

  if (validCases.length === 0) {
    ElMessage.warning('选中的案件已审核，您无权删除')
    return
  }

  // 2. 弹窗确认提示
  let confirmMsg = `确定要删除选中的 ${validCases.length} 个案件吗？`
  if (validCases.length < selectedCases.value.length) {
    confirmMsg = `其中 ${selectedCases.value.length - validCases.length} 个案件已审核无法删除，是否继续删除剩余的 ${validCases.length} 个案件？`
  }

  if (!confirm(confirmMsg)) return

  try {
    // 3. 执行删除操作: 利用 Promise.all 并发请求
    const deletePromises = validCases.map((row) =>
      request.delete(`/cases/case_delete/${row.case_id}`),
    )
    await Promise.all(deletePromises)

    ElMessage.success('批量删除成功')

    // 4. 重置状态并刷新列表
    selectedCases.value = [] // 清空选中状态
    await loadCases()
  } catch (err) {
    console.error('批量删除失败:', err)
    ElMessage.error('部分或全部删除失败，请重试')
    await loadCases() // 失败也最好刷新一下，避免数据不同步
  }
}

// -------------------------- 新增案件相关 --------------------------
const showFormDialog = ref(false)
const handleAddClick = () => {
  formMode.value = 'add'
  currentCaseId.value = null // 确保编辑 ID 清空
  currentCloneId.value = null // 重置克隆ID
  currentReviewStatus.value = '' // 重置审核状态
  // 清空表单数据（避免残留）
  Object.assign(formData, JSON.parse(JSON.stringify({})))
  showFormDialog.value = true
}

// -------------------------- 编辑案件相关 --------------------------
// 记录当前操作案件的审核状态
const currentReviewStatus = ref('')
const handleEditClick = async (row) => {
  formMode.value = 'edit'
  currentCaseId.value = row.case_id
  currentReviewStatus.value = row.review_status
  try {
    // 调接口获取完整案件详情（CaseOut）
    const res = await request.get(`/cases/${row.case_id}`)
    const fullCaseData = res.data

    // 深拷贝 CaseOut 数据到表单
    Object.assign(formData, JSON.parse(JSON.stringify(fullCaseData)))

    // 打开弹窗
    showFormDialog.value = true
  } catch (err) {
    console.error('加载案件详情失败:', err)
    ElMessage.error('加载案件详情失败，请稍后重试')
  }
}

// -------------------------- 复用案件相关 --------------------------
const handleCloneClick = (row) => {
  formMode.value = 'add' // 模式依然是新增
  currentCaseId.value = null // 不是编辑，所以置空
  currentCloneId.value = row.case_id // 记录要复用的源ID
  currentReviewStatus.value = ''
  showFormDialog.value = true
}

// 更多下拉菜单处理函数
const handleMoreAction = (command, row) => {
  if (command === 'clone') {
    handleCloneClick(row) // 调用我们之前写的复用函数
  } else if (command === 'upload') {
    handleUploadClick(row) // 原有的上传附件函数
  } else if (command === 'download') {
    handleDownloadApproval(row) // 原有的下载审批表函数
  }
}

// -------------------------- CaseForm 组件事件回调 --------------------------
// 表单提交（新增/编辑通用）
const handleFormSubmit = () => {
  // CaseForm 组件内部已经处理完了所有提交和附件上传逻辑
  // 外层页面只需要负责重新拉取数据，刷新表格即可
  loadCases()
}

// -------------------------- 查看案件相关 --------------------------
const router = useRouter()
const viewCase = (row, mode = 'current') => {
  const routeLocation = {
    path: `/main/cases/${row.case_id}`,
    query: {
      from: '/main/cases', // 明确传入来源路由，方便详情页返回
    },
  }

  if (mode === 'blank') {
    // 方案 A：新标签页打开
    const routeData = router.resolve(routeLocation)
    // routeData.href 就是解析出来的完整链接
    window.open(routeData.href, '_blank')
  } else {
    // 方案 B：当前标签页直接跳转
    router.push(routeLocation)
  }
}

// -------------------------- 删除案件相关 --------------------------
const deleteCase = async (caseId) => {
  if (!confirm('确定要删除该案件吗？')) return

  try {
    await request.delete(`/cases/case_delete/${caseId}`)
    ElMessage.success('删除案件成功')
    await loadCases() // 刷新列表
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 导出Excel表格相关 --------------------------
const showExportDialog = ref(false)
const isExporting = ref(false)

// 导出表单数据
const exportForm = reactive({
  keyword: '',
  case_category: '',
  main_lawyer_id: null,
  execution_lawyer_id: null,
  year: '',
  month: null, // 指定月份（按委托日期）
  dateRange: [],
})

// 新增：精准导出选中的 loading 状态
const isExportingSelected = ref(false)

// 执行导出选中的案件
const handleExportSelected = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先勾选需要导出的案件')
    return
  }

  try {
    isExportingSelected.value = true

    // 提取所有选中的 case_id
    const selectedIds = selectedCases.value.map((row) => row.case_id)

    // 构建 payload，总表不需要锁定 category，仅传入选中 ID 即可
    const payload = {
      case_ids: selectedIds,
    }

    // 调用导出接口
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

    // 文件名加以区分
    link.download = `业务数据(选中导出)_${timestamp}.xlsx`

    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElMessage.success(`成功导出 ${selectedIds.length} 条案件数据 ✅`)
  } catch (error) {
    console.error('精准导出Excel失败：', error)
    ElMessage.error('导出失败，请检查网络或稍后重试 ❌')
  } finally {
    isExportingSelected.value = false
  }
}

// 点击列表页的导出按钮 -> 打开弹窗，并默认带入当前列表的筛选条件
const handleExportClick = () => {
  exportForm.keyword = searchKeyword.value || ''
  exportForm.case_category = selectedCategory.value || ''
  exportForm.main_lawyer_id = selectedLawyerId.value || null
  exportForm.execution_lawyer_id = selectedExecutionLawyerId.value || null
  exportForm.year = selectedYear.value || ''
  exportForm.month = selectedMonth.value || null // 带入当前月份筛选
  exportForm.dateRange = [] // 默认不设置具体日期区间

  showExportDialog.value = true
}

// 下载进度变量
const exportProgress = ref(0)
// 确认并提交导出
const submitExport = async () => {
  try {
    isExporting.value = true
    exportProgress.value = 0 // 每次导出前重置进度

    // 1️⃣ 构建请求 Payload (严格匹配后端的 CaseExportQuery 模型)
    const payload = {
      keyword: exportForm.keyword || null,
      case_category: exportForm.case_category || null,
      main_lawyer_id: exportForm.main_lawyer_id || null,
      execution_lawyer_id: exportForm.execution_lawyer_id || null,
      year: exportForm.year || null,
      month: exportForm.month || null, // 指定月份（按委托日期）
      start_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[0] : null,
      end_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[1] : null,
    }

    // 2️⃣ 发起 POST 请求，加入进度监听
    const response = await request.post('/cases/export', payload, {
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        // 当后端返回了 Content-Length 时，total 才有值
        if (progressEvent.total) {
          exportProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      },
    })

    // 3️⃣ 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl

    // 4️⃣ 动态生成文件名
    const timestamp = new Date()
      .toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
      .replace(/\D/g, '')
    link.download = `业务明细数据_${timestamp}.xlsx`

    // 5️⃣ 触发下载并清理
    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElMessage.success('Excel 文件导出成功 ✅')
    showExportDialog.value = false // 导出成功后关闭弹窗
  } catch (error) {
    console.error('导出Excel失败：', error)
    ElMessage.error('导出失败，请检查网络或稍后重试 ❌')
  } finally {
    isExporting.value = false
    exportProgress.value = 0 // 结束清空
  }
}

// -------------------------- 独立上传附件逻辑 --------------------------
const uploadDialogVisible = ref(false)
const isUploadingAttachments = ref(false)
const attachmentFileList = ref([])
const currentUploadCaseId = ref(null)
const currentUploadCaseNumber = ref('')

// 1. 点击列表中的“上传附件”按钮
const handleUploadClick = (row) => {
  currentUploadCaseId.value = row.case_id
  currentUploadCaseNumber.value = row.case_number
  attachmentFileList.value = [] // 清空旧文件列表
  uploadDialogVisible.value = true
}

// 2. 监听文件选择变化
const handleAttachmentChange = (file, fileList) => {
  attachmentFileList.value = fileList
}

// 3. 监听文件移除
const handleAttachmentRemove = (file, fileList) => {
  attachmentFileList.value = fileList
}

// 4. 重置弹窗状态
const resetUploadDialog = () => {
  attachmentFileList.value = []
  isUploadingAttachments.value = false
}

// 5. 提交上传
const submitAttachments = async () => {
  if (attachmentFileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  isUploadingAttachments.value = true

  try {
    // 并行上传所有选中的文件
    const uploadPromises = attachmentFileList.value.map(async (file) => {
      const formData = new FormData()
      formData.append('case_id', currentUploadCaseId.value)
      formData.append('file', file.raw)

      const res = await request.post('/attachments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      // COS 模式 + 非 Word 文件：后端返回 STS 临时凭证，需前端直传 COS
      if (res.data?.type === 'COS') {
        const result = await uploadToCOS(file.raw, res.data)
        if (!result.success) {
          throw new Error(result.error || 'COS 上传失败')
        }
        // 回写文件大小（字节），静默失败不影响主流程
        request.patch(`/attachments/${res.data.attachment_id}/size`, null, {
          params: { file_size: result.file_size }
        }).catch(() => {})
      }
      return res
    })

    // 等待所有上传完成
    await Promise.all(uploadPromises)

    ElMessage.success(`成功上传 ${attachmentFileList.value.length} 个附件`)
    uploadDialogVisible.value = false

    // 可选：如果需要在当前页面显示附件数量变化，这里可以刷新列表
    // await loadCases()
  } catch (error) {
    console.error('附件上传失败:', error)
    ElMessage.error('部分或全部附件上传失败，请重试')
  } finally {
    isUploadingAttachments.value = false
  }
}

// -------------------------- 辅助工具函数 --------------------------
// 日期格式化（将时间戳/ISO字符串转为本地日期）
const formatDate = (dateVal) => {
  if (!dateVal) return ''

  let timestamp

  // 处理时间戳（数字类型）
  if (typeof dateVal === 'number') {
    // 处理秒级时间戳（如果是10位数字）
    if (dateVal.toString().length === 10) {
      dateVal *= 1000
    }
    timestamp = dateVal
  }
  // 处理字符串类型
  else if (typeof dateVal === 'string') {
    // 尝试多种常见格式转换
    const formats = [
      // 尝试不添加Z的情况（本地时间）
      dateVal.replace(' ', 'T'),
      // 尝试添加Z的情况（UTC时间）
      dateVal.replace(' ', 'T') + 'Z',
      // 尝试直接解析原始字符串
      dateVal,
    ]

    // 尝试各种格式，找到能正确解析的
    for (const fmt of formats) {
      const tempDate = new Date(fmt)
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime()
        break
      }
    }
  }
  // 处理Date对象
  else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime()
  }

  // 验证时间戳是否有效
  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal)
    return '无效日期'
  }

  const date = new Date(timestamp)

  // 使用toLocaleString()同时显示日期和时间
  // 可以通过参数自定义格式，例如：
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false, // 24小时制
  })
}
// ---------------------------- 批量导入 --------------------------
// 批量导入相关状态
const showImportDialog = ref(false)
const showResultDialog = ref(false)
const uploadRef = ref(null)
const fileList = ref([])
const isUploading = ref(false)
const progress = ref(0)
const showProgress = ref(false)
const result = ref({})
const canUpload = computed(() => fileList.value.length > 0)

// 文件选择变化
const handleFileChange = (file, newFileList) => {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    newFileList.pop()
    return
  }

  // 限制只保留一个文件
  if (newFileList.length > 1) {
    newFileList.splice(0, newFileList.length - 1)
  }

  // ✅ 关键：更新响应式 fileList
  fileList.value = [...newFileList]
}

// 超出文件数量限制
const handleExceed = () => {
  ElMessage.warning('每次只能上传一个Excel文件')
}

// 下载导入模板
const downloadTemplate = async () => {
  const fileName = 'case_import_template.xlsx'
  try {
    // 请求文件流
    const response = await request.get(`/template/download`, {
      params: { filename: fileName },
      responseType: 'blob', // 告诉 axios 返回二进制流
    })

    // 创建 Blob 对象
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    // 创建一个临时下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.click()

    // 清理对象URL
    window.URL.revokeObjectURL(downloadUrl)

    ElNotification({
      title: '提示',
      message: '模板下载成功，请查收',
      type: 'success',
    })
  } catch (error) {
    console.error('模板下载失败:', error)
    ElNotification({
      title: '错误',
      message: '模板下载失败，请稍后重试',
      type: 'error',
    })
  }
}

// 开始导入
const handleImport = async () => {
  if (!fileList.value.length) return

  const formData = new FormData()
  formData.append('file', fileList.value[0].raw)

  try {
    isUploading.value = true
    showProgress.value = true
    progress.value = 0

    // ✅ 使用 axios 提供的 onUploadProgress 获取真实进度
    const response = await request.post('/cases/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total > 0) {
          progress.value = Math.round((event.loaded / event.total) * 100)
        }
      },
    })

    // ✅ 上传完成（确保100%）
    progress.value = 100

    // 显示结果
    result.value = response.data
    showImportDialog.value = false
    showResultDialog.value = true
    await loadCases()

    ElNotification({
      title: '导入完成',
      message: `成功导入 ${response.data.imported_cases} 条，失败 ${response.data.failed_cases?.length || 0} 条`,
      type: response.data.failed_cases?.length ? 'warning' : 'success',
    })

    // 🚀 自动触发 AI 错误诊断（如果有失败记录）
    if (response.data.failed_cases && response.data.failed_cases.length > 0) {
      // 延迟片刻，避免与导入完成通知重叠
      setTimeout(() => triggerImportDiagnosis(response.data.failed_cases), 1000)
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error({
      message: error.response?.data?.detail || '导入失败，请检查文件格式后重试',
      duration: 5000,
    })
  } finally {
    isUploading.value = false
    // 3秒后重置进度条
    setTimeout(() => {
      showProgress.value = false
      progress.value = 0
      fileList.value = []
    }, 3000)
  }
}

// 🚀 自动触发 AI 错误诊断（异步模式——后台分析，前端轮询，全局弹窗）
// 即使此时切换到其他页面，轮询和弹窗也不受影响
async function triggerImportDiagnosis(errors) {
  try {
    const formData = new FormData()
    formData.append('errors', JSON.stringify(errors))
    formData.append('source', 'import')

    const res = await request.post('/ai/diagnose_excel_errors', formData, {
      timeout: 30000,
    })

    // 交给 handleErrorAnalysis 处理：
    // ElMessage 提示 → 轮询 GET /error-analyses/{id} → 完成后全局 ElMessageBox.alert 弹窗
    handleErrorAnalysis(res.data)
  } catch (error) {
    console.error('AI 错误诊断失败:', error)
    // 诊断失败不弹对话框（静默失败）
  }
}

// 下载错误日志
const handleDownloadErrorLog = () => {
  if (!result.value.failed_cases?.length) return

  const logContent = [
    `案件导入错误日志 - ${new Date().toLocaleString()}`,
    `总条数: ${result.value.total_cases}`,
    `成功条数: ${result.value.imported_cases}`,
    `失败条数: ${result.value.failed_cases.length}`,
    '\n失败详情:',
    ...result.value.failed_cases.map(
      (item, index) => `${index + 1}. 业务号/行号: ${item.case_number} - 原因: ${item.reason}`,
    ),
  ].join('\n')

  const blob = new Blob([logContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `案件导入错误日志_${new Date().getTime()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleDownloadApproval = async (row) => {
  try {
    ElMessage.info('正在生成审批表，请稍候...')

    // 发起请求
    const response = await request.get(`/case_review/${row.case_id}/approval_form`, {
      responseType: 'blob', // 关键设置：告诉 axios 响应是一个二进制文件流
    })

    // 创建 Blob 对象
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })

    // 创建下载链接
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)

    // 设置文件名：优先使用后端 header 中的 filename，如果没有则手动拼接
    // 也可以直接用: `案件审批表_${row.case_number}.docx`
    link.download = `业务审批表_${row.case_number}.docx`

    // 触发下载
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)

    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载审批表失败:', error)
    ElMessage.error('下载审批表失败，请稍后重试')
  }
}
</script>

<style scoped>
.cases-page {
  min-height: 100%;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(79, 70, 229, 0.08), transparent 34%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #f4f7fb 100%);
}

/* 原有基础布局样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  padding: 22px 24px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.page-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.5px;
}

.page-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.action-buttons .el-button {
  margin-left: 0 !important;
  height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.2px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    opacity 0.2s ease;
}

.action-buttons .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.12);
}

/* 顶部搜索/筛选栏基础样式 */
.toolbar {
  margin-bottom: 16px;
  padding: 18px 20px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 14px 40px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(14px);
}

.toolbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* 允许换行 */
  gap: 14px; /* 使用 gap 代替原先复杂的 margin 控制 */
}

.toolbar-item {
  flex-shrink: 0;
}

/* 提取原有的内联宽度到 class 中，方便媒体查询覆盖 */
.search-input {
  width: 280px;
}
.filter-select {
  width: 220px;
}
.year-picker {
  width: 140px;
}
.month-select {
  width: 180px;
}

/* 对 Element Plus 输入框做统一高级化处理 */
:deep(.toolbar-item .el-input__wrapper),
:deep(.toolbar-item .el-select__wrapper),
:deep(.toolbar-item .el-date-editor.el-input__wrapper) {
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18);
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

:deep(.toolbar-item .el-input__wrapper:hover),
:deep(.toolbar-item .el-select__wrapper:hover),
:deep(.toolbar-item .el-date-editor.el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.25);
}

:deep(.toolbar-item .el-input__wrapper.is-focus),
:deep(.toolbar-item .el-select__wrapper.is-focused),
:deep(.toolbar-item .el-date-editor.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px rgba(59, 130, 246, 0.35),
    0 0 0 4px rgba(59, 130, 246, 0.08);
}

/* 表格容器 */
.table-container {
  border: 1px solid rgba(255, 255, 255, 0.76);
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
}

/* 表格整体气质优化 */
:deep(.cases-table) {
  --el-table-border-color: rgba(226, 232, 240, 0.95);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: #f8fbff;
}

/* 优化 Element Plus 表格内部滚动到底部时的滚动链传递 */
:deep(.el-table__body-wrapper .el-scrollbar__wrap) {
  overscroll-behavior-y: auto !important; /* 确保垂直滚动能顺畅传递给父级/页面 */
}
:deep(.el-table__inner-wrapper) {
  overflow-y: visible !important;
}
:deep(.el-table__body-wrapper) {
  overflow-y: visible !important;
}

:deep(.cases-table .el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #fbfdff 0%, #f3f7ff 100%);
  color: #334155;
  font-weight: 700;
  letter-spacing: 0.2px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

:deep(.cases-table .el-table__header-wrapper th.el-table__cell .cell) {
  padding: 14px 10px;
}

:deep(.cases-table .el-table__row td.el-table__cell) {
  transition: background 0.18s ease;
}

:deep(.cases-table .el-table__row:hover > td.el-table__cell) {
  background: #f8fbff !important;
}

:deep(.cases-table .el-table__body tr td.el-table__cell) {
  color: #334155;
}

:deep(.cases-table .el-table__body tr:last-child td.el-table__cell) {
  border-bottom: none;
}

:deep(.cases-table .el-table__fixed-right),
:deep(.cases-table .el-table__fixed) {
  box-shadow: 0 0 22px rgba(15, 23, 42, 0.08);
}

:deep(.cases-table .el-button) {
  border-radius: 10px;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  justify-content: flex-start;
  padding: 4px 0;
}

.row-actions .el-button {
  margin-left: 0 !important;
}

.page-pagination {
  margin-top: 16px;
  padding: 14px 18px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 10px 32px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(14px);
}

/* 批量导入相关样式 */
.import-container {
  padding: 6px 2px 2px;
}

.import-tip {
  margin: 0 0 16px 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.upload-tip-note {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.upload-progress {
  margin-top: 18px;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid #e5e7eb;
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #fbfdff 0%, #f8fbff 100%);
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
}

.stat-item span:first-child {
  color: #64748b;
  font-size: 13px;
}

.stat-item .total {
  font-weight: 800;
  color: #0f172a;
  font-size: 18px;
}
.stat-item .success {
  font-weight: 800;
  color: #10b981;
  font-size: 18px;
}
.stat-item .failed {
  font-weight: 800;
  color: #ef4444;
  font-size: 18px;
}
.text-danger {
  color: #f56c6c;
}

.result-table-wrap {
  overflow-x: auto;
  border-radius: 14px;
}

/* 上传弹窗样式优化 */
.upload-container {
  padding: 0 6px;
}

.case-info-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
  border: 1px solid #bbf7d0;
  padding: 14px 16px;
  border-radius: 16px;
  margin-bottom: 18px;
  color: #16a34a;
  box-shadow: 0 8px 18px rgba(16, 185, 129, 0.08);
}

.case-info-bar .el-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.case-info-bar .label {
  font-weight: 700;
  margin-right: 2px;
}
.case-info-bar .value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  word-break: break-all;
}

.upload-demo {
  text-align: center;
}

:deep(.upload-demo .el-upload-dragger) {
  width: 100%;
  border-radius: 18px;
  border: 1.5px dashed #cbd5e1;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

:deep(.upload-demo .el-upload-dragger:hover) {
  border-color: #60a5fa;
  box-shadow: 0 14px 28px rgba(59, 130, 246, 0.08);
  transform: translateY(-1px);
}

:deep(.upload-area .el-upload-dragger) {
  border-radius: 18px;
}

:deep(.upload-area .el-upload-list__item),
:deep(.upload-demo .el-upload-list__item) {
  border-radius: 12px;
  transition: background 0.2s ease;
}

.review-status-with-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.comment-indicator {
  color: #f56c6c;
  animation: pulse-warn 2s ease-in-out infinite;
}

@keyframes pulse-warn {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.el-upload__tip {
  margin-top: 10px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 10px 12px;
  border-radius: 12px;
}

.el-upload__tip p {
  margin: 0;
}

.attachment-tip {
  line-height: 1.7;
}

.form-tip.text-muted {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin-top: 6px;
}

/* 弹窗统一美化 */
.styled-dialog :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.18);
}

.styled-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #eef2f7;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.styled-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.styled-dialog :deep(.el-dialog__body) {
  padding: 20px;
  background: #ffffff;
}

.styled-dialog :deep(.el-dialog__footer) {
  padding: 14px 20px 20px;
  border-top: 1px solid #eef2f7;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.dialog-footer {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

/* export form */
.export-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.export-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

/* 1. 强制关闭表格内部的纵向滚动，保留横向滚动 */
:deep(.el-table__body-wrapper),
:deep(.el-table__body-wrapper .el-scrollbar__wrap) {
  overflow-y: hidden !important;
}

/* 2. 隐藏 Element Plus 自动生成的虚拟纵向滚动条 */
:deep(.el-scrollbar__bar.is-vertical) {
  display: none !important;
}

/* 3. 确保纵向滚动时，固定列不会出现错位断层 */
:deep(.el-table__fixed-right),
:deep(.el-table__fixed) {
  height: 100% !important;
}

/* =======================================
   新增：移动端响应式适配 CSS
   ======================================= */
@media screen and (max-width: 768px) {
  .cases-page {
    padding: 12px;
    border-radius: 18px;
  }

  /* 头部标题和按钮堆叠排列 */
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding: 16px;
    border-radius: 18px;
  }

  .page-title h2 {
    font-size: 20px;
  }

  .page-subtitle {
    font-size: 12px;
  }

  .action-buttons {
    width: 100%;
    justify-content: flex-start;
  }

  .action-buttons .el-button {
    height: 38px;
    padding: 0 14px;
  }

  /* 搜索框和筛选条件垂直平铺 */
  .toolbar {
    padding: 14px;
    border-radius: 18px;
  }

  .toolbar-left {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  /* 所有筛选控件在移动端占满 100% 宽度 */
  .toolbar-item {
    width: 100% !important;
  }

  .search-input,
  .filter-select,
  .year-picker,
  .month-select {
    width: 100%;
  }

  .table-container {
    border-radius: 18px;
  }

  .row-actions {
    justify-content: center;
  }

  .page-pagination {
    justify-content: center;
    padding: 12px 10px;
    border-radius: 16px;
  }

  .result-stats {
    grid-template-columns: 1fr;
  }

  /* 调整弹窗内部文字排版 */
  .case-info-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .styled-dialog :deep(.el-dialog__body) {
    padding: 16px;
  }

  .styled-dialog :deep(.el-dialog__header),
  .styled-dialog :deep(.el-dialog__footer) {
    padding-left: 16px;
    padding-right: 16px;
  }
}

/* ── AI 错误诊断对话框 ── */
.diagnosis-dialog :deep(.el-dialog__body) {
  max-height: 65vh;
  overflow-y: auto;
}

.diagnosis-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: #165dff;
}

.diagnosis-loading .is-loading {
  animation: diagnosis-spin 1.4s ease-in-out infinite;
}

@keyframes diagnosis-spin {
  0%, 100% { opacity: 1; transform: rotate(0deg); }
  50% { opacity: 0.5; transform: rotate(180deg); }
}

.diagnosis-loading p {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.diagnosis-error {
  padding: 20px;
}

.diagnosis-content {
  padding: 4px 0;
}

.diagnosis-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.diagnosis-source {
  font-size: 12px;
  color: #909399;
}

/* ── 诊断结果 Markdown 样式（复用 ErrorAnalysisPage 风格） ── */
.analysis-result {
  background: linear-gradient(135deg, #f5f9ff 0%, #fafcff 100%);
  border: 1px solid #d6e4f0;
  border-radius: 10px;
  padding: 20px 24px;
  line-height: 1.9;
  font-size: 14px;
  color: #2b3a4a;
}
.analysis-result :deep(h1),
.analysis-result :deep(h2),
.analysis-result :deep(h3),
.analysis-result :deep(h4) {
  margin-top: 18px;
  margin-bottom: 10px;
  color: #165dff;
  font-weight: 600;
}
.analysis-result :deep(h1) { font-size: 19px; }
.analysis-result :deep(h2) {
  font-size: 17px;
  border-bottom: 1px solid #e5edf5;
  padding-bottom: 6px;
}
.analysis-result :deep(h3) { font-size: 15px; }
.analysis-result :deep(p) { margin: 10px 0; }
.analysis-result :deep(ul),
.analysis-result :deep(ol) {
  padding-left: 22px;
  margin: 10px 0;
}
.analysis-result :deep(li) { margin: 6px 0; }
.analysis-result :deep(li::marker) { color: #165dff; }
.analysis-result :deep(code) {
  background: #e8f0fe;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #165dff;
}
.analysis-result :deep(pre) {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 16px 18px;
  overflow-x: auto;
  margin: 14px 0;
}
.analysis-result :deep(pre code) {
  background: transparent;
  color: #cdd6f4;
  padding: 0;
  font-size: 13px;
}
.analysis-result :deep(blockquote) {
  border-left: 4px solid #165dff;
  background: #f0f5ff;
  padding: 10px 14px;
  margin: 14px 0;
  color: #4e5969;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
}
.analysis-result :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-size: 13px;
}
.analysis-result :deep(th),
.analysis-result :deep(td) {
  border: 1px solid #d9e1ec;
  padding: 10px 14px;
  text-align: left;
}
.analysis-result :deep(th) {
  background: #eaf2fa;
  font-weight: 600;
  color: #1d2129;
}
.analysis-result :deep(strong) {
  color: #1d2129;
  font-weight: 600;
}
</style>
