<template>
  <div class="case-review-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件审核</h2>
    </div>

    <!-- 审核表格 -->
    <el-table
      :data="casesList"
      style="width: 100%"
      border
      v-loading="tableLoading"
    >
      <el-table-column prop="case_id" label="案件ID" width="80" />
      <el-table-column prop="case_number" label="案件编号" />
      <el-table-column prop="client_name" label="委托人" />
      <el-table-column prop="case_category" label="案件类别" />
      <el-table-column prop="main_lawyer.real_name" label="主办律师" />
      <el-table-column
        prop="created_at"
        label="创建时间"
        align="center"
        :formatter="(row, column, cellValue) => formatDate(cellValue)"
      />

      <!-- 操作详情列 -->
      <el-table-column label="案件详情">
        <template #default="scope">
          <div
            class="detail-cell"
            @click="navigateToDetail(scope.row.case_id)"
            title="点击查看详情"
          >
            点击查看完整信息
          </div>
        </template>
      </el-table-column>

      <!-- 操作按钮列 -->
      <el-table-column  label="操作">
        <template #default="scope">
          <el-button type="success" size="small" @click="review(scope.row, '已审核')">通过</el-button>
          <el-button type="danger" size="small" @click="review(scope.row, '已拒绝')">拒绝</el-button>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const API_BASE = 'http://127.0.0.1:8001'
const router = useRouter()

// 表格数据
const casesList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const tableLoading = ref(false)

// 当前用户信息
const currentUserRole = ref(sessionStorage.getItem('role'))

// 加载待审核案件
const fetchPendingCases = async () => {
  tableLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/case_review/pending`, {
      params: {
        role: currentUserRole.value,
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value
      }
    })
    casesList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取待审核案件失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取待审核案件失败')
    casesList.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

// 审核操作
const review = async (row, status) => {
  try {
    await axios.put(`${API_BASE}/case_review/${row.case_id}/review`,
      {},
      {
        params: {
          role: currentUserRole.value,
          review_status: status
        }
      }
    )
    ElMessage.success(`案件已${status === '已审核' ? '通过' : '拒绝'}`)
    await fetchPendingCases() // 刷新列表
  } catch (err) {
    console.error('审核操作失败:', err)
    ElMessage.error(err.response?.data?.detail || '审核操作失败')
  }
}

// 跳转到详情页
const navigateToDetail = (caseId) => {
  router.push({
    path: `/main/cases/${caseId}`,
    // 主动添加 meta 信息，记录来源页面
    query: {
      from: '/main/case_review' // 来源是审核页面
    }
  })
}

// 分页切换
const handlePageChange = (p) => {
  page.value = p
  fetchPendingCases()
}

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

// 页面加载时初始化
onMounted(() => {
  // 检查是否为管理员
  if (!['admin', 'owner'].includes(currentUserRole.value)) {
    ElMessage.error('无权限访问审核页面')
    return
  }
  fetchPendingCases()
})
</script>

<style scoped>
.case-review-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.detail-cell {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}
</style>
