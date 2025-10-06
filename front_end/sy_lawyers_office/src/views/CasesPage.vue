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
      <el-table-column prop="review_status" label="审核状态" align="center"/>
      <el-table-column
        prop="created_at"
        label="创建时间"
        align="center"
        :formatter="(row, column, cellValue) => formatDate(cellValue)"
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
      :current-user-id="currentUserID"
      :current-user-role="currentUserRole"
      @submit="handleFormSubmit"
    />


  </div>
</template>

<script setup>
import { ref, reactive, onMounted} from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import CaseForm from './CaseForm.vue' // 引入抽离的CaseForm组件
import { useRouter } from 'vue-router'

// -------------------------- 当前用户数据 ----------------------------
const currentUserID = ref(sessionStorage.getItem('user_id'))
const currentUserRole = ref(sessionStorage.getItem('role'))

// -------------------------- 表格与分页相关 --------------------------
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const cases = ref([])
const tableLoading = ref(false) // 表格加载状态

// -------------------------- 弹窗控制相关 --------------------------
// 明确指定formMode的类型为'add'或'edit'
const formMode = ref('add') // 表单模式：'add'（新增）/'edit'（编辑）
const currentCaseId = ref('') // 当前编辑的案件ID（编辑时用）


// -------------------------- 数据存储相关 --------------------------
const lawyers = ref([]) // 律师列表
const formData = reactive({}) // 传递给CaseForm的表单数据

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
        user_id: currentUserID.value ,
        role: currentUserRole.value ,
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
const handleEditClick = async (row) => {
  formMode.value = 'edit'
  currentCaseId.value = row.case_id

  try {
    // 调接口获取完整案件详情（CaseOut）
    const res = await axios.get(`http://127.0.0.1:8001/cases/${row.case_id}`)
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

// -------------------------- CaseForm 组件事件回调 --------------------------
// 表单提交（新增/编辑通用）
const handleFormSubmit = async (submittedData) => {
  try {
    if (formMode.value === 'add') {
      // 新增案件请求
      await axios.post('http://127.0.0.1:8001/cases/operations', {
        user_id: currentUserID.value,
        operation_type: '新增',
        pending_data: submittedData
      })
      ElMessage.success('新增案件成功,等待管理员审核')
    } else {
      // 编辑案件请求（携带案件ID）
      await axios.post('http://127.0.0.1:8001/cases/operations', {
        user_id: currentUserID.value,
        operation_type: '修改',
        case_id: currentCaseId.value,
        pending_data: submittedData
      })
      ElMessage.success('编辑案件成功,等待管理员审核')
    }
    // 提交成功后刷新列表并重置状态
    await loadCases()
  } catch (err) {
    console.error(`${formMode.value === 'add' ? '新增' : '编辑'}案件失败:`, err)
    ElMessage.error(`${formMode.value === 'add' ? '新增' : '编辑'}案件失败，请重试`)
  }
}

// -------------------------- 查看案件相关 --------------------------
const router = useRouter()
const viewCase = (row) => {
  router.push(`/main/cases/${row.case_id}`)
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
    ElMessage.success('删除案件成功,等待管理员审核')
    await loadCases() // 刷新列表
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 辅助工具函数 --------------------------
// 日期格式化（将时间戳/ISO字符串转为本地日期）
const formatDate = (dateVal) => {
  if (!dateVal) return '';

  let timestamp;

  // 处理时间戳（数字类型）
  if (typeof dateVal === 'number') {
    // 处理秒级时间戳（如果是10位数字）
    if (dateVal.toString().length === 10) {
      dateVal *= 1000;
    }
    timestamp = dateVal;
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
      dateVal
    ];

    // 尝试各种格式，找到能正确解析的
    for (const fmt of formats) {
      const tempDate = new Date(fmt);
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime();
        break;
      }
    }
  }
  // 处理Date对象
  else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime();
  }

  // 验证时间戳是否有效
  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal);
    return '无效日期';
  }

  const date = new Date(timestamp);

  // 使用toLocaleString()同时显示日期和时间
  // 可以通过参数自定义格式，例如：
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false // 24小时制
  });
};

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
