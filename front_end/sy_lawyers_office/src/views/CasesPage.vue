<template>
  <div class="cases-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件管理</h2>
      <div class="action-buttons">
        <el-button type="primary" @click="handleAddClick">新增案件</el-button>
        <el-button type="success" @click="handleExportClick">导出表格</el-button>
      </div>
    </div>

    <!-- 搜索与筛选区 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入案件号或委托人"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 250px; margin-right: 15px"
        />
        <el-select
          v-model="selectedCategory"
          placeholder="案件类别筛选"
          clearable
          @change="handleSearch"
          style="width: 200px"
        >
          <el-option
            v-for="category in caseCategories"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>
      </div>
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
      :case-id="formMode === 'edit' ? currentCaseId : null"
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

// -------------------------- 搜索与筛选相关 --------------------------
const searchKeyword = ref('')
const selectedCategory = ref('')
// 案件类别选项
const caseCategories = ref([
  { label: '民事案件', value: '民事案件' },
  { label: '刑事案件', value: '刑事案件' },
  { label: '行政案件', value: '行政案件' },
  { label: '非诉案件', value: '非诉案件' },
  { label: '仲裁案件', value: '仲裁案件' },
  { label: '法律顾问业务', value: '法律顾问业务' }
])

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
    const res = await axios.get('http://127.0.0.1:8002/cases/users/lawyers')
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
    const res = await axios.get('http://127.0.0.1:8002/cases/', {
      params: {
        user_id: currentUserID.value ,
        role: currentUserRole.value ,
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
        keyword: searchKeyword.value,  // 搜索关键词
        category: selectedCategory.value  // 类别筛选
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

// -------------------------- 搜索功能 --------------------------
const handleSearch = () => {
  page.value = 1  // 重置为第一页
  loadCases()
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
    const res = await axios.get(`http://127.0.0.1:8002/cases/${row.case_id}`)
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
      // 调用 /cases/case_create
      await axios.post('http://127.0.0.1:8002/cases/case_create', submittedData)
      ElMessage.success('新增案件成功')
    } else {
      // 调用 /cases/case_update/{case_id}
      await axios.put(`http://127.0.0.1:8002/cases/case_update/${currentCaseId.value}`, submittedData)
      ElMessage.success('编辑案件成功')
    }
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
    await axios.delete(`http://127.0.0.1:8002/cases/case_delete/${caseId}`)
    ElMessage.success('删除案件成功')
    await loadCases() // 刷新列表
  } catch (err) {
    console.error('删除案件失败:', err)
    ElMessage.error('删除案件失败，请重试')
  }
}

// -------------------------- 导出Excel表格 --------------------------
const handleExportClick = async () => {
  try {
    // 1️⃣ 发起请求到后端接口
    const response = await axios.get('http://127.0.0.1:8002/cases/export/all', {
      params: {
        user_id: currentUserID.value,
        role: currentUserRole.value
      },
      responseType: 'blob' // 告诉 axios 返回文件流
    });

    // 2️⃣ 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });

    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;

    // 3️⃣ 动态生成文件名（使用当前时间）
    const timestamp = new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\D/g, '');
    link.download = `案件数据_${timestamp}.xlsx`;

    // 4️⃣ 触发下载
    link.click();
    window.URL.revokeObjectURL(downloadUrl);

    ElMessage.success('Excel 文件导出成功 ✅');
  } catch (error) {
    console.error('导出Excel失败：', error);
    ElMessage.error('导出失败，请稍后重试 ❌');
  }
};

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
