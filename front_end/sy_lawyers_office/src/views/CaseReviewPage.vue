<template>
  <div class="case-review-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>案件审核</h2>
      <el-button type="primary" @click="toggleHistory">
        {{ showHistory ? '返回待审核' : '查看历史记录' }}
      </el-button>
    </div>

    <!-- 审核表格 -->
    <el-table :data="casesList" style="width: 100%">
      <el-table-column prop="operation_id" label="编号" width="80" />
      <el-table-column prop="case_id" label="案件编号" />
      <el-table-column prop="operation_type" label="操作类型" />
      <el-table-column prop="user_name" label="提交人" />

      <!-- 操作详情列（单行显示 + 点击弹窗） -->
      <el-table-column label="操作详情">
        <template #default="scope">
          <div
            class="detail-cell"
            @click="showDetailDialog(scope.row)"
            title="点击查看完整内容"
          >
            <!-- 仅显示第一条变化信息作为预览 -->
            <template v-if="scope.row.details && scope.row.details.length > 0">
              <span>
                {{ scope.row.details[0].field }}：
                <span v-if="scope.row.details[0].old_value !== null">
                  原值：{{ scope.row.details[0].old_value }}
                </span>
                <span v-if="scope.row.details[0].new_value !== null">
                  → 新值：{{ scope.row.details[0].new_value }}
                </span>
              </span>
              <span v-if="scope.row.details.length > 1">（共 {{ scope.row.details.length }} 项变更）</span>
            </template>
            <span v-else>无变更</span>
          </div>
        </template>
      </el-table-column>

      <!-- 操作按钮列 -->
      <el-table-column v-if="!showHistory" label="操作">
        <template #default="scope">
          <el-button type="success" size="small" @click="review(scope.row, true)">通过</el-button>
          <el-button type="danger" size="small" @click="review(scope.row, false)">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 弹窗：显示完整操作详情 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="操作详情"
      width="600px"
      center
    >
      <div v-if="selectedDetails.length > 0">
        <el-descriptions :column="1" border>
          <el-descriptions-item
            v-for="(item, index) in selectedDetails"
            :key="index"
            :label="convertFieldToChinese(item.field)"
          >
            <div>
              <span v-if="item.old_value !== null">原值：{{ item.old_value }}</span>
              <span v-if="item.new_value !== null"> → 新值：{{ item.new_value }}</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8001'

const casesList = ref([])
const showHistory = ref(false)
const detailDialogVisible = ref(false)
const selectedDetails = ref([])

const currentUserId = sessionStorage.getItem('user_id')
const currentUserRole = sessionStorage.getItem('role')

// 加载待审核案件
const fetchPendingCases = async () => {
  try {
    const res = await axios.get(`${API_BASE}/case_review/pending`, {
      params: { role: currentUserRole }
    })
    casesList.value = res.data
  } catch (err) {
    console.error(err)
    ElMessage.error('获取待审核案件失败')
  }
}

// 加载历史记录
const fetchAllOperations = async () => {
  try {
    const res = await axios.get(`${API_BASE}/case_review/all`, {
      params: { role: currentUserRole }
    })
    casesList.value = res.data
  } catch (err) {
    console.error(err)
    ElMessage.error('获取历史记录失败')
  }
}

// 切换模式（待审核 <-> 历史记录）
const toggleHistory = () => {
  showHistory.value = !showHistory.value
  if (showHistory.value) {
    fetchAllOperations()
  } else {
    fetchPendingCases()
  }
}

// 审核通过/拒绝
const review = async (row, approved) => {
  try {
    await axios.put(`${API_BASE}/case_review/${row.operation_id}/review`, {
      review_status: approved ? '已通过' : '已拒绝',
      review_user_id: currentUserId
    }, {
      params: { role: currentUserRole }
    })
    ElMessage.success('操作成功')
    await fetchPendingCases()
  } catch (err) {
    console.error(err)
    ElMessage.error('操作失败')
  }
}

// 显示详情弹窗
const showDetailDialog = (row) => {
  selectedDetails.value = row.details || []
  detailDialogVisible.value = true
}

// 属性名转换（英转中）
const convertFieldToChinese = (field) => {
  const mapping = {
    // 案件基本信息
    cause: '案由',
    court: '承办法院',
    stage: '介入阶段',
    details: '案件详情',
    is_major: '是否重大案件',
    case_code: '案件编号',
    defendant: '被告',
    plaintiff: '原告',
    fee_method: '收费方式',
    has_record: '是否有笔录',
    risk_ratio: '风险比例',
    case_income: '案件收入',
    case_source: '案件来源',
    client_name: '委托人',
    filing_date: '立案日期',
    agency_power: '代理权限',
    client_phone: '联系电话',
    closing_date: '结案日期',
    hearing_date: '开庭日期',
    is_bank_case: '是否银行案件',
    is_dismissed: '是否已撤诉',
    case_category: '案件类别',
    appellant_info: '上诉人信息',
    closing_method: '结案方式',
    closing_status: '结案状态',
    has_paper_file: '是否有纸质档案',
    main_lawyer_id: '主办律师ID',
    commission_date: '委托日期',
    client_id_number: '身份证号 / 税号',
    has_preservation: '是否保全',
    payment_due_date: '付款截止日期',
    preservation_end: '保全结束时间',
    execution_due_date: '执行截止日期',
    mediation_due_date: '调解截止日期',
    preservation_start: '保全开始时间',
    assistant_lawyer_id: '协办律师ID',
    execution_lawyer_id: '执行律师ID',
    extra_appellant_info: '其他上诉人信息',
    execution_assistant_id: '执行助理ID',
    execution_application_date: '申请执行日期',
    litigation_fee_refund_date: '诉讼费退费日期',
    litigation_fee_payment_date: '诉讼费缴费日期',
    litigation_fee_refund_amount: '诉讼费退费金额',
    litigation_fee_payment_amount: '诉讼费缴费金额',
    // 其他
    operation_type: '操作类型',
    user_name: '提交人',
    review_status: '审核状态',
    created_at: '创建时间',
    updated_at: '更新时间',
    default: '未知字段'
  }

  return mapping[field] || field
}

onMounted(() => {
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
  margin-bottom: 10px;
}
.detail-cell {
  white-space: nowrap;        /* 单行显示 */
  overflow: hidden;           /* 超出隐藏 */
  text-overflow: ellipsis;    /* 显示省略号 */
  cursor: pointer;            /* 鼠标变为点击手势 */
  color: #409eff;
}
.detail-cell:hover {
  text-decoration: underline;
}
</style>
