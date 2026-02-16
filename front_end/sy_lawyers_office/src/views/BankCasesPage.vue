<template>
  <div class="bank-cases-page">
    <div class="header">
      <h2>银行案件</h2>
      <div class="action-buttons">
        <el-button type="success" @click="handleExportClick">导出表格</el-button>
      </div>
    </div>

    <!-- 搜索区 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入业务号或委托银行"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 250px; margin-right: 15px"
        />

        <!-- 管理员专属：主办律师筛选 -->
        <el-select
          v-if="currentUserRole === 'admin' || currentUserRole === 'owner'"
          v-model="selectedLawyerId"
          placeholder="主办律师筛选"
          clearable
          @change="handleSearch"
          style="width: 200px"
        >
          <el-option
            v-for="lawyer in lawyers"
            :key="lawyer.id"
            :label="lawyer.real_name"
            :value="lawyer.id"
          />
        </el-select>
      </div>
    </div>

    <!-- 案件表格：委托人列改为委托银行 -->
    <el-table :data="cases" border style="width: 100%" v-loading="tableLoading">
      <el-table-column prop="case_number" label="业务号" width="220" align="center" />
      <el-table-column prop="client_name" label="委托银行" align="center" />
      <!-- 修改此处label -->
      <el-table-column prop="case_category" label="案件类别" align="center" />
      <el-table-column prop="main_lawyer.real_name" label="主办律师" align="center" />
      <el-table-column prop="review_status" label="审核状态" align="center" />
      <el-table-column
        prop="created_at"
        label="创建时间"
        align="center"
        :formatter="(row, column, cellValue) => formatDate(cellValue)"
      />
      <el-table-column label="操作" width="220" align="center">
        <template #default="scope">
          <el-button size="small" @click="viewCase(scope.row)">查看</el-button>
          <el-button size="small" type="warning" @click="handleEditClick(scope.row)"
            >编辑</el-button
          >
          <el-button size="small" type="danger" @click="deleteCase(scope.row.case_id)"
            >删除</el-button
          >
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

    <!-- 编辑案件弹窗（复用现有CaseForm组件） -->
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
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import CaseForm from './CaseForm.vue'
import { useRouter } from 'vue-router'

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

// 弹窗控制
const showFormDialog = ref(false)
const formMode = ref('edit') // 只有编辑模式
const currentCaseId = ref('')
const formData = reactive({})
const lawyers = ref([])

const router = useRouter()

// 初始化加载
onMounted(() => {
  Promise.all([loadLawyers(), loadBankCases()]).catch((err) => console.error('初始化失败:', err))
})

// 加载律师列表（复用现有接口）
const loadLawyers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8002/cases/users/lawyers')
    lawyers.value = res.data || []
  } catch (err) {
    console.error('加载律师列表失败:', err)
    lawyers.value = []
  }
}

// 核心：加载银行案件列表（调用新增的bank_cases接口）
const loadBankCases = async () => {
  tableLoading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8002/cases/bank_cases', {
      params: {
        user_id: currentUserID.value,
        role: currentUserRole.value,
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
        keyword: searchKeyword.value, // 传递搜索关键词
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
      from: '/main/cases/bank_cases', // 来源是银行案件页面
    },
  })
  window.open(routeData.href, '_blank')
}

// 编辑案件
const handleEditClick = async (row) => {
  formMode.value = 'edit'
  currentCaseId.value = row.case_id
  try {
    const res = await axios.get(`http://127.0.0.1:8002/cases/${row.case_id}`)
    Object.assign(formData, JSON.parse(JSON.stringify(res.data)))
    showFormDialog.value = true
  } catch (err) {
    console.error('加载案件详情失败:', err)
    ElMessage.error('加载案件详情失败')
  }
}

// 提交编辑表单
const handleFormSubmit = async (submittedData) => {
  try {
    await axios.put(`http://127.0.0.1:8002/cases/case_update/${currentCaseId.value}`, submittedData)
    ElMessage.success('编辑案件成功')
    showFormDialog.value = false
    await loadBankCases()
  } catch (err) {
    console.error('编辑案件失败:', err)
    ElMessage.error('编辑案件失败')
  }
}

// 删除案件
const deleteCase = async (caseId) => {
  if (!confirm('确定要删除该案件吗？')) return

  try {
    await axios.delete(`http://127.0.0.1:8002/cases/case_delete/${caseId}`)
    ElMessage.success('删除案件成功')
    await loadBankCases() // 刷新列表
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 导出Excel表格 --------------------------
const handleExportClick = async () => {
  try {
    // 1️⃣ 发起请求到后端接口
    const response = await axios.get('http://127.0.0.1:8002/cases/export/bank_cases', {
      params: {
        user_id: currentUserID.value,
        role: currentUserRole.value,
      },
      responseType: 'blob', // 告诉 axios 返回文件流
    })

    // 2️⃣ 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl

    // 3️⃣ 动态生成文件名（使用当前时间）
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

    // 4️⃣ 触发下载
    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElMessage.success('Excel 文件导出成功 ✅')
  } catch (error) {
    console.error('导出Excel失败：', error)
    ElMessage.error('导出失败，请稍后重试 ❌')
  }
}

// 日期格式化（复用现有函数）
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
