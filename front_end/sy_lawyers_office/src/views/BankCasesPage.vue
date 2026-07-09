<template>
  <div class="bank-cases-page">
    <div class="header">
      <div class="page-title">
        <h2>银行案件</h2>
        <p class="page-subtitle">统一管理银行案件数据、附件上传与批量导出</p>
      </div>
      <div class="action-buttons">
        <el-button type="primary" plain @click="handleSyncClick">
          <el-icon><Refresh /></el-icon>
          批量同步(更新)
        </el-button>
        <el-button
          v-if="hasDeletePermission"
          type="danger"
          :disabled="selectedCases.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
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
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入业务号、法院案号或当事人"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          class="toolbar-item search-input"
        />

        <el-select
          v-model="selectedBank"
          placeholder="委托银行筛选"
          clearable
          filterable
          allow-create
          default-first-option
          @change="handleSearch"
          class="toolbar-item filter-select"
        >
          <el-option v-for="bank in bankOptions" :key="bank" :label="bank" :value="bank" />
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
          v-model="selectedCaseStatus"
          placeholder="案件状态筛选"
          clearable
          filterable
          @change="handleSearch"
          class="toolbar-item filter-select"
        >
          <el-option
            v-for="status in caseStatusOptions"
            :key="status"
            :label="status"
            :value="status"
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
        @selection-change="handleSelectionChange"
        class="cases-table"
      >
        <el-table-column type="selection" width="55" align="center" />

        <el-table-column prop="case_number" label="业务号" min-width="200" align="center" />
        <el-table-column prop="case_code" label="法院案号" min-width="180" align="center">
          <template #default="scope">
            {{ scope.row.case_code || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="委托银行" min-width="150" align="center">
          <template #default="{ row }">
            {{ getClientNames(row.parties) || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="案件状态" min-width="160" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.case_status)" effect="light" round>
              {{ scope.row.case_status || '未知状态' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="borrower_name" label="借款人" min-width="150" align="center" />
        <el-table-column
          prop="main_lawyer.real_name"
          label="主办律师"
          min-width="120"
          align="center"
        />

        <el-table-column label="执行主办律师" min-width="120" align="center">
          <template #default="scope">
            {{ scope.row.execution_lawyer?.real_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="诉讼费缴费金额" min-width="130" align="center">
          <template #default="scope">
            {{ scope.row.litigation_fee_payment_amount ?? '-' }}
          </template>
        </el-table-column>

        <el-table-column label="诉讼费退费金额" min-width="130" align="center">
          <template #default="scope">
            {{ scope.row.litigation_fee_refund_amount ?? '-' }}
          </template>
        </el-table-column>

        <el-table-column label="审核状态" min-width="100" align="center">
          <template #default="scope">
            <el-tag :type="getReviewStatusType(scope.row.review_status)" effect="dark" size="small">
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
          min-width="400"
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
              <el-button size="small" type="warning" @click="handleEditClick(scope.row)"
                >编辑</el-button
              >
              <el-button
                size="small"
                type="danger"
                :disabled="!hasDeletePermission && scope.row.review_status === '已审核'"
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
      title="导出银行案件数据"
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
          <el-input v-model="exportForm.keyword" placeholder="按业务号/当事人搜索" clearable />
        </el-form-item>

        <el-form-item label="委托银行">
          <el-select
            v-model="exportForm.client_name"
            placeholder="全部银行"
            clearable
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option v-for="bank in bankOptions" :key="bank" :label="bank" :value="bank" />
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

        <el-form-item label="案件状态">
          <el-select
            v-model="exportForm.case_status"
            placeholder="全部状态"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="status in caseStatusOptions"
              :key="status"
              :label="status"
              :value="status"
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

    <el-dialog
      title="批量同步/覆盖更新案件"
      v-model="showSyncDialog"
      :width="isMobile ? '95%' : '650px'"
      :close-on-click-modal="false"
      class="styled-dialog sync-dialog"
    >
      <div class="sync-guide">
        <div class="guide-step">
          <div class="step-num">1</div>
          <div class="step-content">
            <h4>导出当前数据</h4>
            <p>点击本页面的“导出表格”按钮，下载最新的 Excel 原始数据。</p>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-num">2</div>
          <div class="step-content">
            <h4>线下修改信息</h4>
            <p>
              在 Excel 中批量修改案件字段。<strong>注意：请勿修改“业务ID”列</strong>，系统依赖该 ID
              识别现有案件。如需同步当事人信息，请在<strong>「当事人明细」</strong>工作表中编辑。
            </p>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-num">3</div>
          <div class="step-content">
            <h4>上传并同步</h4>
            <p>上传修改后的 Excel，系统将根据业务 ID 自动覆盖数据库中的现有案件内容。</p>
          </div>
        </div>
      </div>

      <div class="warning-alert">
        <el-alert title="重要提醒" type="warning" :closable="false" show-icon>
          <ul class="warning-list">
            <li>该操作具有<strong>覆盖性</strong>，请务必核实数据后再上传。</li>
            <li><strong>严禁修改业务ID</strong>，否则将导致同步失败或创建重复案件。</li>
            <li>当前版本基于「当事人明细」Sheet 支持<strong>当事人全量同步</strong>（先删除后重新插入）。</li>
            <li>若“业务ID”为空，系统将基于“业务号”尝试新建案件。</li>
          </ul>
        </el-alert>
      </div>

      <div class="sync-upload-area">
        <el-upload
          class="sync-uploader"
          drag
          action="#"
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleSyncFileChange"
          v-model:file-list="syncFileList"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">将修改后的 Excel 拖到此处，或 <em>点击上传</em></div>
        </el-upload>
      </div>

      <div v-if="syncErrors.length > 0" class="sync-errors-container">
        <div class="error-header">同步失败详情：</div>
        <el-scrollbar max-height="150px">
          <ul class="error-list">
            <li v-for="(err, idx) in syncErrors" :key="idx">{{ err }}</li>
          </ul>
        </el-scrollbar>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSyncDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="isSyncing"
            @click="submitSync"
            :disabled="syncFileList.length === 0"
          >
            {{ isSyncing ? '正在同步数据...' : '开始批量同步' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import request from '@/utils/request'
import { uploadToCOS } from '@/utils/cosUpload'
import { ElMessage, ElMessageBox } from 'element-plus'
import { handleErrorAnalysis } from '@/utils/errorAnalysisNotify'
import CaseForm from './CaseForm.vue'
import { useRouter } from 'vue-router'
// 导入需要的图标
import { Document, Upload, UploadFilled, Download, Refresh } from '@element-plus/icons-vue'

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

// 当前用户信息
const currentUserID = ref(localStorage.getItem('user_id'))
const currentUserRole = ref(localStorage.getItem('role'))

// 允许删除的特定用户 ID 白名单
const allowedDeleteUserIds = ['1', '2', '3']

// 计算属性，判断当前登录用户是否有删除权限
const hasDeletePermission = computed(() => {
  return allowedDeleteUserIds.includes(currentUserID.value)
})

// 表格与分页数据
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const cases = ref([])
const tableLoading = ref(false)
const searchKeyword = ref('') // 搜索关键词
const selectedLawyerId = ref(null) // 选中的主办律师ID
const selectedExecutionLawyerId = ref(null) // 选中的执行主办律师ID
// 年份变量，默认为当前年份字符串
const selectedYear = ref(new Date().getFullYear().toString())
// 委托银行相关响应式变量
const selectedBank = ref(null)
const bankOptions = [
  '建设银行',
  '邮政银行',
  '农村商业银行',
  '工商银行',
  '交通银行',
  '住房公积金',
  '长沙村镇银行',
  '中国银行',
]
const selectedCaseStatus = ref(null) // 选中的案件状态
const caseStatusOptions = [
  '写诉讼状中',
  '资料不足',
  '退回案件',
  '移交法院排队立案',
  '诉讼立案',
  '已开庭',
  '已裁判',
  '债务履行完毕结案',
  '银行要求撤诉',
  '终结执行',
  '跟进调解履行情况',
  '写执行申请资料',
  '移交法院执行手续',
  '执行排队立案中',
  '执行和解',
  '网络查控资产情况',
  '扣划工资工积金处置抵押物',
  '询价查看不动产情况',
  '拍卖抵押物',
  '终本',
  '恢复执行中',
  '银行要求不起诉',
  '银行要求暂不起诉',
  '银行未交诉讼费撤诉',
  '被告已还清不起诉',
  '被告已还清撤诉',
  '执行盖章中',
  '诉讼盖章中',
]

// 根据案件状态返回 Tag 颜色类型
const getStatusType = (status) => {
  if (!status) return 'info'
  const dangerKeywords = ['撤诉', '资料不足', '暂不起诉', '银行要求不起诉', '退回案件']
  const successKeywords = ['已裁判', '结案', '已还清', '和解']
  const warningKeywords = ['跟进', '查控', '扣划', '询价', '拍卖']
  const infoKeywords = ['终结', '终本']

  if (dangerKeywords.some((kw) => status.includes(kw))) return 'danger'
  if (successKeywords.some((kw) => status.includes(kw))) return 'success'
  if (warningKeywords.some((kw) => status.includes(kw))) return 'warning'
  if (infoKeywords.some((kw) => status.includes(kw))) return 'info'
  return 'primary' // 默认如“立案、开庭、写资料等”为蓝色
}

// 根据审核状态返回 Tag 颜色类型
const getReviewStatusType = (status) => {
  if (status === '已审核') return 'success'
  if (status === '待审核' || status === '未审核') return 'warning'
  if (status === '已拒绝') return 'danger' // 修改为已拒绝
  return 'info'
}

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
        case_status: selectedCaseStatus.value, // 案件状态筛选
        sort_field: currentSortField.value, // 排序字段
        sort_dir: currentSortDir.value, // 排序方向
        main_lawyer_id: selectedLawyerId.value, // 主办律师筛选
        execution_lawyer_id: selectedExecutionLawyerId.value, // 执行主办律师筛选
        client_name: selectedBank.value, // 委托银行筛选
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

// 切换每页条数
const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1 // 切换每页条数后，务必重置回第一页
  loadBankCases()
}

// 搜索功能
const handleSearch = () => {
  page.value = 1 // 重置到第一页
  loadBankCases()
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

  // 1. 权限过滤：检查是否有普通用户无权删除的“已审核”案件
  const validCases = selectedCases.value.filter(
    (row) => !(currentUserRole.value === 'user' && row.review_status === '已审核'),
  )

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
    await loadBankCases()
  } catch (err) {
    console.error('批量删除失败:', err)
    ElMessage.error('部分或全部删除失败，请重试')
    await loadBankCases() // 失败也最好刷新一下，避免数据不同步
  }
}

// 查看案件详情
const viewCase = (row, mode = 'current') => {
  const routeLocation = {
    path: `/main/cases/${row.case_id}`,
    query: {
      from: '/main/cases/bank_cases', // 明确传入来源为银行案件列表
    },
  }

  if (mode === 'blank') {
    const routeData = router.resolve(routeLocation)
    window.open(routeData.href, '_blank')
  } else {
    router.push(routeLocation)
  }
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
const exportProgress = ref(0) // 导出进度

// 导出表单数据
const exportForm = reactive({
  keyword: '',
  client_name: null,
  main_lawyer_id: null,
  execution_lawyer_id: null,
  year: '',
  dateRange: [],
  case_status: null,
})

// 精准导出选中的 loading 状态
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

    // 构建 payload，锁定分类并传入 case_ids
    const payload = {
      case_category: '银行案件',
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
    link.download = `银行案件数据(选中导出)_${timestamp}.xlsx`

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

// 打开导出弹窗，同步当前的筛选状态
const handleExportClick = () => {
  exportForm.keyword = searchKeyword.value || ''
  exportForm.client_name = selectedBank.value || null
  exportForm.main_lawyer_id = selectedLawyerId.value || null
  exportForm.execution_lawyer_id = selectedExecutionLawyerId.value || null
  exportForm.case_status = selectedCaseStatus.value || null
  exportForm.year = selectedYear.value || ''
  exportForm.dateRange = []
  showExportDialog.value = true
}

// 确认导出
const submitExport = async () => {
  try {
    isExporting.value = true
    exportProgress.value = 0

    // 构建符合后端的 CaseExportQuery 的 payload
    // 注意这里强制锁定 case_category: '银行案件'
    const payload = {
      keyword: exportForm.keyword || null,
      case_category: '银行案件',
      main_lawyer_id: exportForm.main_lawyer_id || null,
      execution_lawyer_id: exportForm.execution_lawyer_id || null,
      client_name: exportForm.client_name || null,
      year: exportForm.year || null,
      case_status: exportForm.case_status || null,
      start_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[0] : null,
      end_date:
        exportForm.dateRange && exportForm.dateRange.length === 2 ? exportForm.dateRange[1] : null,
    }

    // 调用与总库一样的 export 接口，加入进度监听
    const response = await request.post('/cases/export', payload, {
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          exportProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      },
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
    exportProgress.value = 0
  }
}

// -------------------------- 批量同步(更新) 逻辑 --------------------------
const showSyncDialog = ref(false)
const isSyncing = ref(false)
const syncFileList = ref([])
const syncErrors = ref([])

// 打开同步弹窗
const handleSyncClick = () => {
  syncFileList.value = []
  syncErrors.value = []
  showSyncDialog.value = true
}

// 文件变化
const handleSyncFileChange = (file) => {
  syncFileList.value = [file]
}

// 提交同步
const submitSync = async () => {
  if (syncFileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  try {
    await ElMessageBox.confirm('系统将基于业务ID覆盖现有案件数据，确定继续吗？', '操作确认', {
      confirmButtonText: '确定同步',
      cancelButtonText: '取消',
      type: 'warning',
    })

    isSyncing.value = true
    syncErrors.value = []

    const formData = new FormData()
    formData.append('file', syncFileList.value[0].raw)

    const res = await request.post('/cases/batch_sync_excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // 成功提示
    ElMessage({
      message: res.data.summary || '批量同步任务完成',
      type: res.data.errors?.length > 0 ? 'warning' : 'success',
      duration: 5000,
    })

    // 记录错误
    if (res.data.errors && res.data.errors.length > 0) {
      syncErrors.value = res.data.errors
      // 🚀 自动触发 AI 错误诊断
      setTimeout(() => triggerSyncDiagnosis(res.data.errors), 1000)
    } else {
      showSyncDialog.value = false
      await loadBankCases()
    }
  } catch (err) {
    if (err !== 'cancel') {
      console.error('同步失败:', err)
      ElMessage.error(err.response?.data?.detail || '批量同步接口调用失败')
    }
  } finally {
    isSyncing.value = false
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

// 🚀 自动触发 AI 诊断（异步模式——后台分析，前端轮询，全局弹窗）
// 即使切换到其他页面，轮询和弹窗也不受影响
async function triggerSyncDiagnosis(errors) {
  try {
    const formData = new FormData()
    formData.append('errors', JSON.stringify(errors))
    formData.append('source', 'sync')

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

</script>

<style scoped>
/* 同步最新的整体渐变背景体系 */
.bank-cases-page {
  min-height: 100%;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(79, 70, 229, 0.08), transparent 34%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #f4f7fb 100%);
}

/* 头部样式（毛玻璃） */
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
  flex-wrap: wrap;
  gap: 14px;
}
.toolbar-item {
  flex-shrink: 0;
}
.search-input {
  width: 280px;
}
.filter-select {
  width: 220px;
}
.year-picker {
  width: 140px;
}

/* 输入框高级化处理 */
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

/* 行操作按钮排列 */
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

/* 分页器样式 */
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

:deep(.upload-demo .el-upload-list__item) {
  border-radius: 12px;
  transition: background 0.2s ease;
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

/* 批量同步弹窗特定样式 */
.sync-guide {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 24px;
}

.guide-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.step-num {
  width: 28px;
  height: 28px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 10px;
}

.step-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #1e293b;
}

.step-content p {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.warning-alert {
  margin-bottom: 20px;
}

.warning-list {
  padding-left: 18px;
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
}

.sync-errors-container {
  margin-top: 15px;
  padding: 12px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
  border-radius: 12px;
}

.error-header {
  font-weight: bold;
  color: #be123c;
  font-size: 13px;
  margin-bottom: 8px;
}

.error-list {
  margin: 0;
  padding-left: 18px;
  color: #e11d48;
  font-size: 12px;
  line-height: 1.8;
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
   移动端响应式适配 CSS
   ======================================= */
@media screen and (max-width: 768px) {
  .bank-cases-page {
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
  .year-picker {
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

  .sync-guide {
    flex-direction: column;
    gap: 20px;
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

/* ── 诊断结果 Markdown 样式 ── */
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
