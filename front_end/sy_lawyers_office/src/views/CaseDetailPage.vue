<template>
  <div class="case-detail">
    <!-- 顶部返回栏 -->
    <el-page-header @back="goBack" title="返回" />

    <!-- 居中标题 -->
    <h2 class="page-title">案件详情</h2>

    <el-card class="detail-card" v-loading="loading">
      <!-- 案件基本信息 -->
      <el-descriptions title="案件基本信息" :column="2" border>
        <el-descriptions-item label="案件号">{{ caseData.case_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件类别">{{ caseData.case_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托日期">{{ formatDate(caseData.commission_date) }}</el-descriptions-item>
        <el-descriptions-item label="委托人">{{ caseData.client_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="身份证号/单位税号">{{ caseData.client_id_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ caseData.client_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否银行案件">{{ caseData.is_bank_case ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="案件来源">{{ caseData.case_source || '-' }}</el-descriptions-item>
        <el-descriptions-item label="介入阶段">{{ caseData.stage || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案由">{{ caseData.cause || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 收费信息 -->
      <el-descriptions title="费用信息" :column="2" border>
        <el-descriptions-item label="收费方式">{{ caseData.fee_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件收入">
          {{ caseData.case_income ? `${caseData.case_income} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="风险比例">{{ caseData.risk_ratio || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 律师信息 -->
      <el-descriptions title="律师信息" :column="2" border>
        <el-descriptions-item label="主办律师">{{ caseData.main_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="助理律师">{{ caseData.assistant_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行律师">{{ caseData.execution_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行助理">{{ caseData.execution_assistant?.real_name || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 系统信息 -->
      <el-descriptions title="系统信息" :column="2" border>
        <el-descriptions-item label="创建时间">{{ formatDateTime(caseData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(caseData.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 诉讼信息 -->
      <el-descriptions title="诉讼信息" :column="2" border>
        <el-descriptions-item label="原告">{{ caseData.plaintiff || '-' }}</el-descriptions-item>
        <el-descriptions-item label="被告">{{ caseData.defendant || '-' }}</el-descriptions-item>
        <el-descriptions-item label="代理权限">{{ caseData.agency_power || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审理法院">{{ caseData.court || '-' }}</el-descriptions-item>
        <el-descriptions-item label="立案日">{{ formatDate(caseData.filing_date) }}</el-descriptions-item>
        <el-descriptions-item label="开庭时间">{{ formatDate(caseData.hearing_date) }}</el-descriptions-item>
        <el-descriptions-item label="结案时间">{{ formatDate(caseData.closing_date) }}</el-descriptions-item>
        <el-descriptions-item label="结案状态">{{ caseData.closing_status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结案方式">{{ caseData.closing_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件地点">{{ caseData.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件详情">
          <div class="case-detail-content" v-text="caseData.details || '-'"></div>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 保全与状态 -->
      <el-descriptions title="案件状态" :column="2" border>
        <el-descriptions-item label="审核状态">{{ caseData.review_status }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ caseData.reviewer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否重大">{{ caseData.is_major ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否解除">{{ caseData.is_dismissed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否纸质卷宗">{{ caseData.has_paper_file ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否笔录">{{ caseData.has_record ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否保全">{{ caseData.has_preservation ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="保全开始日">{{ formatDate(caseData.preservation_start) }}</el-descriptions-item>
        <el-descriptions-item label="保全终止日">{{ formatDate(caseData.preservation_end) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 费用与执行 -->
      <el-descriptions title="费用与执行信息" :column="2" border>
        <el-descriptions-item label="诉讼费缴费时间">{{ formatDate(caseData.litigation_fee_payment_date) }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费缴费金额">
          {{ caseData.litigation_fee_payment_amount ? `${caseData.litigation_fee_payment_amount} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="诉讼费退费时间">{{ formatDate(caseData.litigation_fee_refund_date) }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费退费金额">
          {{ caseData.litigation_fee_refund_amount ? `${caseData.litigation_fee_refund_amount} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="申请执行日">{{ formatDate(caseData.execution_application_date) }}</el-descriptions-item>
        <el-descriptions-item label="调解到期日">{{ formatDate(caseData.mediation_due_date) }}</el-descriptions-item>
        <el-descriptions-item label="执行到期日">{{ formatDate(caseData.execution_due_date) }}</el-descriptions-item>
      </el-descriptions>

    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const caseData = ref({})
const loading = ref(false)
const caseId = route.params.id

const goBack = () => {
  // 从路由状态中获取来源页面路径，默认返回案件管理页面
  const fromPath = route.query.from || '/main/cases'
  console.log('fromPath:', fromPath)
  router.push(fromPath)
}

const loadCaseDetail = async () => {
  loading.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:8002/cases/${caseId}`)
    caseData.value = res.data || {}

    // 权限判断逻辑
    const role = sessionStorage.getItem('role')
    const currentUserId = sessionStorage.getItem('user_id')
    const mainLawyerId = caseData.value.main_lawyer?.id

    if (role === 'user' && mainLawyerId && String(mainLawyerId) !== String(currentUserId)) {
      ElMessage.error('您没有权限查看此案件')
      await router.push('/main/cases')
    }
  } catch (err) {
    console.error('加载案件详情失败:', err)
    ElMessage.error('加载案件详情失败')
    await router.push('/main/cases')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCaseDetail()
})

const formatDate = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const formatDateTime = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.case-detail {
  padding: 20px;
}
.detail-card {
  margin-top: 10px;
}
/* 居中标题样式 */
.page-title {
  text-align: center;
  font-size: 22px;
  font-weight: bold;
  color: #333;
  margin: 15px 0 25px 0;
}
.detail-card {
  margin-top: 10px;
  line-height: 1.6;
}
/* 案件详情文本换行样式 */
.case-detail-content {
white-space: pre-line; /* 保留换行符，自动处理空格和宽度 */
line-height: 1.8; /* 增加行高，提升长文本可读性 */
color: #444; /* 可选：调整文本颜色，区分于标签 */
padding: 5px 0; /* 可选：增加上下内边距，避免与其他内容拥挤 */
}
</style>
