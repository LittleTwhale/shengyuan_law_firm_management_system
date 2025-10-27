<template>
  <div class="case-review-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件审核</h2>
      <div class="bulk-actions">
        <el-button
          type="primary"
          size="small"
          @click="toggleSelectAll"
          :disabled="!casesList.length"
        >
          {{ isAllSelected ? '取消全选' : '全选当前页' }}
        </el-button>

        <el-button
          type="success"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已审核')"
        >批量通过</el-button>

        <el-button
          type="danger"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已拒绝')"
        >批量拒绝</el-button>
      </div>
    </div>

    <!-- 审核表格 -->
    <el-table
      ref="caseTableRef"
      :data="casesList"
      style="width: 100%"
      border
      v-loading="tableLoading"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
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
      <el-table-column label="操作">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const API_BASE = 'http://127.0.0.1:8002'
const router = useRouter()

// 表格数据
const casesList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const tableLoading = ref(false)
const caseTableRef = ref(null)

// 当前用户信息
const currentUserId = ref(sessionStorage.getItem('user_id'))
const currentUserRole = ref(sessionStorage.getItem('role'))

// 多选状态
const selectedCases = ref([])
const isAllSelected = ref(false)

// 监听勾选变化
const handleSelectionChange = (val) => {
  selectedCases.value = val
  isAllSelected.value = val.length === casesList.value.length && val.length > 0
}

// 切换全选/取消全选
const toggleSelectAll = () => {
  if (!caseTableRef.value) return
  if (isAllSelected.value) {
    caseTableRef.value.clearSelection()
  } else {
    casesList.value.forEach(row => {
      caseTableRef.value.toggleRowSelection(row, true)
    })
  }
  isAllSelected.value = !isAllSelected.value
}

// 利益冲突确认对话框
const showConflictDialog = (conflicts, caseId, caseNumber) => {
  return new Promise((resolve) => {
    // 构建冲突详情HTML
    let conflictHtml = `<div style="max-height: 300px; overflow-y: auto;">
      <p style="color: #e6a23c; margin-bottom: 15px;">
        <i class="el-icon-warning"></i>
        案件 <strong>${caseNumber}</strong> 可能存在利益冲突，是否继续审核？
      </p>
      <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #606266;">冲突详情：</h4>
        <ul style="margin: 0; padding-left: 20px;">
          ${conflicts.map(conflict =>
          `<li style="margin-bottom: 8px;">
              <div>
                <strong>冲突案件：</strong>
                <a href="javascript:void(0)"
                   onclick="window.open('/main/cases/${conflict.case_id}', '_blank')"
                   style="color: #409eff; text-decoration: none;">
                  ${conflict.case_number}
                </a>
              </div>
              <div><strong>对方律师：</strong>${conflict.other_lawyer_name}</div>
              <div><strong>冲突角色：</strong>
                ${conflict.conflict_type === '常规利益冲突'
            ? `委托人在${conflict.case_number}中担任${conflict.role}`
            : '该案件被告为法律顾问单位'}
              </div>
              <div><strong>案件类别：</strong>${conflict.conflict_case_category}</div>
            </li>`
        ).join('')}
        </ul>
      </div>
    </div>`

    ElMessageBox.confirm(conflictHtml, '利益冲突警告', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '继续通过',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'conflict-dialog'
    }).then(() => {
      resolve(true) // 用户选择继续
    }).catch(() => {
      resolve(false) // 用户选择取消
    })
  })
}

// 审核操作
const review = async (row, status) => {
  try {
    // 如果是审核通过，先检查利益冲突
    if (status === '已审核') {
      try {
        // 直接发送审核请求，后端会返回冲突信息
        await axios.put(`${API_BASE}/case_review/${row.case_id}/review`,
          {},
          {
            params: {
              reviewer_id: currentUserId.value,
              role: currentUserRole.value,
              review_status: status
            }
          }
        )
      } catch (err) {
        // 如果是冲突错误（409），显示冲突对话框
        if (err.response?.status === 409 && err.response?.data?.detail?.conflicts) {
          const conflictData = err.response.data.detail
          const userContinue = await showConflictDialog(
            conflictData.conflicts,
            row.case_id,
            row.case_number
          )

          if (userContinue) {
            // 用户确认继续，强制通过审核（忽略冲突）
            await forceReview(row.case_id, status)
          } else {
            return // 用户取消，不执行任何操作
          }
        } else {
          // 其他错误正常抛出
          throw err
        }
      }
    } else {
      // 拒绝审核不需要检查冲突
      await axios.put(`${API_BASE}/case_review/${row.case_id}/review`,
        {},
        {
          params: {
            reviewer_id: currentUserId.value,
            role: currentUserRole.value,
            review_status: status
          }
        }
      )
    }

    ElMessage.success(`案件已${status === '已审核' ? '通过' : '拒绝'}`)
    await fetchPendingCases()
  } catch (err) {
    if (err.response?.status !== 409) { // 排除冲突错误，因为已经处理过了
      console.error('审核操作失败:', err)
      ElMessage.error(err.response?.data?.detail?.message || err.response?.data?.detail || '审核操作失败')
    }
  }
}

// 强制通过审核（忽略冲突）
const forceReview = async (caseId, status) => {
  await axios.put(`${API_BASE}/case_review/${caseId}/force_review`,
    {},
    {
      params: {
        reviewer_id: currentUserId.value,
        role: currentUserRole.value,
        review_status: status,
      }
    }
  )
}

// 批量审核
const batchReview = async (status) => {
  if (!selectedCases.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedCases.value.length} 个案件标记为「${status}」吗？`,
      '批量审核确认',
      { type: status === '已审核' ? 'success' : 'warning' }
    )

    await Promise.all(
      selectedCases.value.map(item =>
        axios.put(`${API_BASE}/case_review/${item.case_id}/review`, {}, {
          params: {
            reviewer_id: currentUserId.value,
            role: currentUserRole.value,
            review_status: status
          }
        })
      )
    )

    ElMessage.success(`已成功批量${status === '已审核' ? '通过' : '拒绝'} ${selectedCases.value.length} 个案件`)
    selectedCases.value = []
    isAllSelected.value = false
    await fetchPendingCases()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量审核失败:', err)
      ElMessage.error(err.response?.data?.detail || '批量审核失败')
    }
  }
}

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

// 跳转到详情页
const navigateToDetail = (caseId) => {
  router.push({
    path: `/main/cases/${caseId}`,
    query: {
      from: '/main/case_review'
    }
  })
}

// 分页切换
const handlePageChange = (p) => {
  page.value = p
  fetchPendingCases()
}

// 日期格式化
const formatDate = (dateVal) => {
  if (!dateVal) return '';

  let timestamp;
  if (typeof dateVal === 'number') {
    if (dateVal.toString().length === 10) {
      dateVal *= 1000;
    }
    timestamp = dateVal;
  } else if (typeof dateVal === 'string') {
    const formats = [
      dateVal.replace(' ', 'T'),
      dateVal.replace(' ', 'T') + 'Z',
      dateVal
    ];

    for (const fmt of formats) {
      const tempDate = new Date(fmt);
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime();
        break;
      }
    }
  } else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime();
  }

  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal);
    return '无效日期';
  }

  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};

// 页面加载时初始化
onMounted(() => {
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

/* 冲突对话框样式 */
:deep(.conflict-dialog) {
  max-width: 600px;
}
:deep(.conflict-dialog .el-message-box__content) {
  max-height: 400px;
  overflow-y: auto;
}
</style>
