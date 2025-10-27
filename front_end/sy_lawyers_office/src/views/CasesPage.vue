<template>
  <div class="cases-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件管理</h2>
      <div class="action-buttons">
        <el-button type="primary" @click="handleAddClick">新增案件</el-button>
        <!-- 新增批量导入按钮 -->
        <el-button type="warning" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
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
          style="width: 200px; margin-right: 15px"
        >
          <el-option
            v-for="category in caseCategories"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>

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

    <!-- 案件表格 -->
    <el-table :data="cases" border style="width: 100%" v-loading="tableLoading">
      <el-table-column prop="case_number" label="案件号" width="220" align="center"/>
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

    <!-- 批量导入弹窗 -->
    <el-dialog
      title="批量导入案件"
      v-model="showImportDialog"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-container">
        <p class="import-tip">支持.xlsx/.xls格式，模板下载：<el-link @click="downloadTemplate">案件导入模板</el-link></p>

        <!-- 上传区域 -->
        <el-upload
          class="upload-area"
          ref="uploadRef"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          :accept="'.xlsx,.xls'"
          :limit="1"
          :on-exceed="handleExceed"
        >
          <el-button type="primary" :loading="isUploading">
            <el-icon><Upload /></el-icon> 选择Excel文件
          </el-button>
          <template #tip>
            <div class="el-upload__tip text-danger">
              请确保Excel表头包含：案件号、委托日期、委托人、案件类别、主办律师
            </div>
          </template>
        </el-upload>

        <!-- 进度条 -->
        <el-progress
          v-if="showProgress"
          :percentage="progress"
          stroke-width="4"
          style="margin-top: 20px;"
        ></el-progress>
      </div>

      <template #footer>
        <el-button @click="showImportDialog = false" :disabled="isUploading">取消</el-button>
        <el-button
          type="primary"
          @click="handleImport"
          :disabled="!canUpload || isUploading"
        >
          <el-icon v-if="!isUploading"><Check /></el-icon>
          <el-icon v-if="isUploading"><Loading /></el-icon>
          {{ isUploading ? '导入中...' : '开始导入' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入结果弹窗 -->
    <el-dialog
      title="导入结果"
      v-model="showResultDialog"
      width="700px"
      :close-on-click-modal="false"
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

      <!-- 失败详情表格 -->
      <el-table
        v-if="result.failed_cases && result.failed_cases.length"
        :data="result.failed_cases"
        border
        style="width: 100%; margin-top: 15px;"
      >
        <el-table-column prop="case_number" label="案件号/行号" width="150"></el-table-column>
        <el-table-column prop="reason" label="失败原因"></el-table-column>
      </el-table>

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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import CaseForm from './CaseForm.vue' // 引入抽离的CaseForm组件
import { useRouter } from 'vue-router'
import { Upload,Check,Loading } from '@element-plus/icons-vue'

// -------------------------- 当前用户数据 ----------------------------
const currentUserID = ref(sessionStorage.getItem('user_id'))
const currentUserRole = ref(sessionStorage.getItem('role'))

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
  { label: '非诉案件', value: '非诉案件' },
  { label: '仲裁案件', value: '仲裁案件' },
  { label: '法律顾问业务', value: '法律顾问业务' },
  { label: '法律援助(民事)', value: '法律援助(民事)' },
  { label: '法律援助(刑事)', value: '法律援助(刑事)' },
])
const selectedLawyerId = ref(null) // 选中的主办律师ID

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
        category: selectedCategory.value,  // 类别筛选
        ...(currentUserRole.value === 'admin' || currentUserRole.value === 'owner'
          ? { main_lawyer_id: selectedLawyerId.value }
          : {})
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
      // 新增案件：先检测利益冲突
      const conflictRes = await axios.post(
        'http://127.0.0.1:8002/cases/check_conflict',
        submittedData,
        {
          params: {
          }
        }
      );

      if (conflictRes.data.has_conflict) {
        try {
          // 构建冲突提示文本
          let message = '';
          // 检查是否有顾问单位类型的冲突
          const hasConsultantConflict = conflictRes.data.details.some(c =>
            c.conflict_type === '顾问单位作为被告'
          );

          if (hasConsultantConflict) {
            // 顾问单位冲突提示
            message = `检测到可能存在利益冲突：该案件的被告为法律顾问单位，是否继续创建？\n`;
          } else {
            // 常规利益冲突提示（使用第一个冲突的角色）
            message = `检测到可能存在利益冲突：该委托人在以下案件中担任${conflictRes.data.details[0].role}，是否继续创建？\n`;
          }

          // 拼接所有冲突案件信息
          message += conflictRes.data.details.map(c =>
            `案件号：${c.case_number}（主办律师：${c.other_lawyer_name || c.other_lawyer_id}）`
          ).join('\n');

          // 弹出确认框
          await ElMessageBox.confirm(
            message,
            '利益冲突警告',
            {
              confirmButtonText: '继续创建',
              cancelButtonText: '取消',
              type: 'warning'
            }
          )
        } catch {
          // 用户点了“取消”，直接返回，不创建案件
          ElMessage.info('已取消创建')
          return
        }
      }

      // 无冲突或用户确认继续，则提交创建
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
  if (!confirm('确定要删除该案件吗？')) return

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
    const response = await axios.get(`http://127.0.0.1:8002/template/download`, {
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
    const response = await axios.post(
      'http://127.0.0.1:8002/cases/import',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total > 0) {
            progress.value = Math.round((event.loaded / event.total) * 100)
          }
        }
      }
    )

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
      type: response.data.failed_cases?.length ? 'warning' : 'success'
    })
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error({
      message: error.response?.data?.detail || '导入失败，请检查文件格式后重试',
      duration: 5000
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

// 下载错误日志
const handleDownloadErrorLog = () => {
  if (!result.value.failed_cases?.length) return

  const logContent = [
    `案件导入错误日志 - ${new Date().toLocaleString()}`,
    `总条数: ${result.value.total_cases}`,
    `成功条数: ${result.value.imported_cases}`,
    `失败条数: ${result.value.failed_cases.length}`,
    '\n失败详情:',
    ...result.value.failed_cases.map((item, index) =>
      `${index + 1}. 案件号/行号: ${item.case_number} - 原因: ${item.reason}`
    )
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
/* 批量导入相关样式 */
.import-container {
  padding: 10px 0;
}

.import-tip {
  margin: 0 0 15px 0;
  color: #666;
  font-size: 14px;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
}

.result-stats {
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-item .total {
  font-weight: bold;
  color: #333;
}

.stat-item .success {
  font-weight: bold;
  color: #10b981;
}

.stat-item .failed {
  font-weight: bold;
  color: #ef4444;
}

.text-danger {
  color: #f56c6c;
}
</style>
