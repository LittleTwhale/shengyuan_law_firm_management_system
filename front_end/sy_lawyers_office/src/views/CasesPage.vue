<template>
  <div class="cases-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件管理</h2>
      <el-button type="primary" @click="handleAddClick">新增案件</el-button>
    </div>

    <!-- 案件表格 -->
    <el-table :data="cases" border style="width: 100%" v-loading="tableLoading">
      <el-table-column prop="case_number" label="案件号" width="180" align="center"/>
      <el-table-column prop="client_name" label="委托人" align="center"/>
      <el-table-column prop="case_category" label="案件类别" align="center"/>
      <el-table-column prop="main_lawyer.real_name" label="主办律师" align="center"/>
      <el-table-column
        prop="created_at"
        label="创建时间"
        align="center"
        :formatter="formatDate"
      />
      <el-table-column label="操作" width="220" align="center">
        <template #default="scope">
          <el-button size="small" @click="viewCase(scope.row)">查看</el-button>
          <el-button size="small" type="warning" @click="handleEditClick(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteCase(scope.row.case_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页组件 -->
    <el-pagination
      background
      layout="prev, pager, next, jumper, ->, total"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      @current-change="handlePageChange"
      style="margin-top: 16px; text-align: right"
    />

    <!-- 1. 新增/编辑案件：复用 CaseForm 组件 -->
    <CaseForm
      v-model:visible="showFormDialog"
      :lawyers="lawyers"
      :initial-form-data="formData"
      :mode="formMode"
      @submit="handleFormSubmit"
    />

    <!-- 2. 查看案件 Dialog -->
    <el-dialog
      title="案件详情"
      v-model:visible="showViewDialog"
      width="900px"
      destroy-on-close
    >
      <el-descriptions :column="1" border size="default">
        <!-- 基础信息 -->
        <el-descriptions-item label="案件号">{{ viewData.case_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件类别">{{ viewData.case_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托日期">{{ formatDate(viewData.commission_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托人">{{ viewData.client_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托人身份证/税号">{{ viewData.client_id_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托人电话">{{ viewData.client_phone || '-' }}</el-descriptions-item>

        <!-- 费用信息 -->
        <el-descriptions-item label="是否银行案件">{{ viewData.is_bank_case ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="案件来源">{{ viewData.case_source || '-' }}</el-descriptions-item>
        <el-descriptions-item label="收费方式">{{ viewData.fee_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="风险比例">{{ viewData.risk_ratio || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件收入">{{ viewData.case_income ? `${viewData.case_income} 元` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="付款到期日">{{ formatDate(viewData.payment_due_date) || '-' }}</el-descriptions-item>

        <!-- 案件主体信息 -->
        <el-descriptions-item label="案由">{{ viewData.cause || '-' }}</el-descriptions-item>
        <el-descriptions-item label="介入阶段">{{ viewData.stage || '-' }}</el-descriptions-item>
        <el-descriptions-item label="原告/申请人">{{ viewData.plaintiff || '-' }}</el-descriptions-item>
        <el-descriptions-item label="上诉人/第三人信息">{{ viewData.appellant_info || '-' }}</el-descriptions-item>
        <el-descriptions-item label="补充上诉人/补告">{{ viewData.extra_appellant_info || '-' }}</el-descriptions-item>
        <el-descriptions-item label="被告">{{ viewData.defendant || '-' }}</el-descriptions-item>

        <!-- 代理与审理 -->
        <el-descriptions-item label="代理权限">{{ viewData.agency_power || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审理法院">{{ viewData.court || '-' }}</el-descriptions-item>
        <el-descriptions-item label="开庭时间">{{ formatDate(viewData.hearing_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="立案日">{{ formatDate(viewData.filing_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结案时间">{{ formatDate(viewData.closing_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件地点">{{ viewData.location || '-' }}</el-descriptions-item>

        <!-- 律师分配 -->
        <el-descriptions-item label="主办律师">{{ viewData.main_lawyer?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="助理律师">{{ getLawyerName(viewData.assistant_lawyer_id) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行主办律师">{{ getLawyerName(viewData.execution_lawyer_id) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行助理律师">{{ getLawyerName(viewData.execution_assistant_id) || '-' }}</el-descriptions-item>

        <!-- 其他配置 -->
        <el-descriptions-item label="是否重大">{{ viewData.is_major ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否纸质卷宗">{{ viewData.has_paper_file ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否解除">{{ viewData.is_dismissed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否笔录">{{ viewData.has_record ? '是' : '否' }}</el-descriptions-item>

        <!-- 保全信息 -->
        <el-descriptions-item label="是否保全">{{ viewData.has_preservation ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item v-if="viewData.has_preservation" label="保全开始日">{{ formatDate(viewData.preservation_start) || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="viewData.has_preservation" label="保全终止日">{{ formatDate(viewData.preservation_end) || '-' }}</el-descriptions-item>

        <!-- 结案与执行 -->
        <el-descriptions-item label="案号">{{ viewData.case_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结案状态">{{ viewData.closing_status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结案方式">{{ viewData.closing_method || '-' }}</el-descriptions-item>

        <!-- 诉讼费 -->
        <el-descriptions-item label="诉讼费缴费时间">{{ formatDate(viewData.litigation_fee_payment_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费缴费金额">{{ viewData.litigation_fee_payment_amount ? `${viewData.litigation_fee_payment_amount} 元` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费退费时间">{{ formatDate(viewData.litigation_fee_refund_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费退费金额">{{ viewData.litigation_fee_refund_amount ? `${viewData.litigation_fee_refund_amount} 元` : '-' }}</el-descriptions-item>

        <!-- 执行相关 -->
        <el-descriptions-item label="申请执行日">{{ formatDate(viewData.execution_application_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="调解到期日">{{ formatDate(viewData.mediation_due_date) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行到期日">{{ formatDate(viewData.execution_due_date) || '-' }}</el-descriptions-item>

        <!-- 案件详情 -->
        <el-descriptions-item label="案件详情" :span="1">
          <pre style="white-space: pre-wrap; word-break: break-all; margin: 0">{{ viewData.details || '-' }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import CaseForm from './CaseForm.vue' // 引入抽离的CaseForm组件

// -------------------------- 表格与分页相关 --------------------------
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const cases = ref([])
const tableLoading = ref(false) // 表格加载状态

// -------------------------- 弹窗控制相关 --------------------------
const showViewDialog = ref(false) // 查看弹窗显示状态
// 明确指定formMode的类型为'add'或'edit'
const formMode = ref('add') // 表单模式：'add'（新增）/'edit'（编辑）
const currentCaseId = ref('') // 当前编辑的案件ID（编辑时用）


// -------------------------- 数据存储相关 --------------------------
const lawyers = ref([]) // 律师列表
const formData = reactive({}) // 传递给CaseForm的表单数据
const viewData = reactive({}) // 查看弹窗的数据

// -------------------------- 初始化加载 --------------------------
onMounted(() => {
  Promise.all([loadLawyers(), loadCases()]) // 并行加载律师和案件列表
    .catch(err => console.error('初始化加载失败:', err))
})

// -------------------------- 律师列表加载 --------------------------
const loadLawyers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8001/cases/users/lawyers')
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
    const res = await axios.get('http://127.0.0.1:8001/cases', {
      params: {
        user_id: 1,
        role: 'admin',
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value
      }
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

// -------------------------- 分页切换 --------------------------
const handlePageChange = (p) => {
  page.value = p
  loadCases()
}

// -------------------------- 新增案件相关 --------------------------
const showFormDialog = ref(false)
const handleAddClick = () => {
  formMode.value = 'add' // 切换为新增模式
  // 清空表单数据（避免残留编辑数据）
  Object.assign(formData, JSON.parse(JSON.stringify({})))
  showFormDialog.value = true
}

// -------------------------- 编辑案件相关 --------------------------
const handleEditClick = (row) => {
  formMode.value = 'edit' // 切换为编辑模式
  currentCaseId.value = row.case_id // 记录当前编辑的案件ID
  // 深拷贝案件数据到表单（避免修改子组件数据影响父组件）
  Object.assign(formData, JSON.parse(JSON.stringify(row)))
  showFormDialog.value = true
}

// -------------------------- CaseForm 组件事件回调 --------------------------
// 表单提交（新增/编辑通用）
const handleFormSubmit = async (submittedData) => {
  try {
    if (formMode.value === 'add') {
      // 新增案件请求
      await axios.post('http://127.0.0.1:8001/cases/operations', {
        user_id: 1,
        operation_type: '新增',
        pending_data: submittedData
      })
      ElMessage.success('新增案件成功')
    } else {
      // 编辑案件请求（携带案件ID）
      await axios.post('http://127.0.0.1:8001/cases/operations', {
        user_id: 1,
        operation_type: '修改',
        case_id: currentCaseId.value,
        pending_data: submittedData
      })
      ElMessage.success('编辑案件成功')
    }
    // 提交成功后刷新列表并重置状态
    await loadCases()
  } catch (err) {
    console.error(`${formMode.value === 'add' ? '新增' : '编辑'}案件失败:`, err)
    ElMessage.error(`${formMode.value === 'add' ? '新增' : '编辑'}案件失败，请重试`)
  }
}

// -------------------------- 查看案件相关 --------------------------
const viewCase = (row) => {
  // 深拷贝案件数据到查看弹窗
  Object.assign(viewData, JSON.parse(JSON.stringify(row)))
  showViewDialog.value = true
}

// -------------------------- 删除案件相关 --------------------------
const deleteCase = async (caseId) => {
  if (!confirm('确定要删除该案件吗？删除后不可恢复！')) return

  try {
    await axios.post('http://127.0.0.1:8001/cases/operations', {
      user_id: 1,
      operation_type: '删除',
      case_id: caseId,
      pending_data: {}
    })
    ElMessage.success('删除案件成功')
    await loadCases() // 刷新列表
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 辅助工具函数 --------------------------
// 日期格式化（将时间戳/ISO字符串转为本地日期）
const formatDate = (dateVal) => {
  if (!dateVal) return ''
  const date = new Date(dateVal)
  return date.toLocaleDateString()
}

// 根据律师ID获取律师姓名（查看弹窗用）
const getLawyerName = computed(() => (lawyerId) => {
  if (!lawyerId) return ''
  const lawyer = lawyers.value.find(item => item.id === lawyerId)
  return lawyer ? lawyer.real_name : '未知律师'
})
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
</style>
