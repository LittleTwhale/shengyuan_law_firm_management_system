<template>
  <div class="bank-case-detail">
    <el-divider content-position="left" class="section-divider">当事人信息</el-divider>
    <el-descriptions
      :column="1"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="委托银行">
        <PartyDetailList :parties="partyClients" :show-badge="false" />
      </el-descriptions-item>

      <el-descriptions-item label="原告/申请人">
        <PartyDetailList :parties="partyPlaintiffs" theme="primary" />
      </el-descriptions-item>

      <el-descriptions-item label="被告/被申请人">
        <PartyDetailList :parties="partyDefendants" theme="warning" />
      </el-descriptions-item>

      <el-descriptions-item label="借款人">
        <PartyDetailList :parties="partyBorrowers" theme="success" />
      </el-descriptions-item>

      <el-descriptions-item label="担保人">
        <PartyDetailList :parties="partyGuarantors" theme="warning" />
      </el-descriptions-item>

      <el-descriptions-item label="第三人" v-if="partyThirdParties.length > 0">
        <PartyDetailList :parties="partyThirdParties" theme="purple" />
      </el-descriptions-item>

      <el-descriptions-item label="其他当事人" v-if="partyOthers.length > 0">
        <PartyDetailList :parties="partyOthers" theme="info" />
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">一、 收案与基础信息</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="业务号">{{ caseData.case_number || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案件来源">{{
        caseData.case_source || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="委托日期">{{
        formatDate(caseData.commission_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="收案日期">{{
        formatDate(details.case_acceptance_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="案件状态">{{ details.case_status || '-' }}</el-descriptions-item>
      <el-descriptions-item label="银行要求案件状态">{{
        details.bank_required_case_status || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="支行名称">{{ details.branch_name || '-' }}</el-descriptions-item>

      <el-descriptions-item label="客户经理">{{
        details.account_manager || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="主办律师">{{
        caseData.main_lawyer?.real_name || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="助理律师">{{
        caseData.assistant_lawyer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="第二助理律师">{{
        caseData.assistant_lawyer_2?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="收费方式">{{ caseData.fee_method || '-' }}</el-descriptions-item>

      <el-descriptions-item label="风险比例">{{ caseData.risk_ratio || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案件收入">{{
        formatCurrency(caseData.case_income)
      }}</el-descriptions-item>

      <el-descriptions-item label="付款到期日">{{
        formatDate(caseData.payment_due_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="案卷标记" :span="2">
        <el-space wrap>
          <el-tag :type="caseData.is_major ? 'danger' : 'info'">{{
            caseData.is_major ? '重大案件' : '非重大案件'
          }}</el-tag>
          <el-tag :type="caseData.has_paper_file ? 'success' : 'info'">{{
            caseData.has_paper_file ? '含纸质卷宗' : '无纸质卷宗'
          }}</el-tag>
          <el-tag :type="caseData.has_record ? 'primary' : 'info'">{{
            caseData.has_record ? '含笔录' : '无笔录'
          }}</el-tag>
          <el-tag :type="caseData.is_dismissed ? 'warning' : 'info'">{{
            caseData.is_dismissed ? '已解除' : '未解除'
          }}</el-tag>
        </el-space>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">二、 借贷基础信息</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="贷款类型">{{ details.loan_type || '-' }}</el-descriptions-item>
      <el-descriptions-item label="贷款账号">{{
        details.loan_account || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="贷款本金">{{
        formatCurrency(details.loan_principal)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼标的(含利息)">{{
        formatCurrency(details.litigation_target_amount)
      }}</el-descriptions-item>

      <el-descriptions-item label="信用卡违约金">{{
        formatCurrency(details.credit_card_penalty)
      }}</el-descriptions-item>
      <el-descriptions-item label="借款日">{{
        formatDate(details.loan_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="到期日">{{
        formatDate(details.loan_due_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼时效">{{
        formatDate(details.statute_of_limitations)
      }}</el-descriptions-item>

      <el-descriptions-item label="抵/质押物信息" :span="2">
        <div class="case-detail-content">{{ details.collateral_info || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="抵押物位置" :span="2">
        <div class="case-detail-content">{{ details.collateral_location || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="诉前催收情况" :span="2">
        <div class="case-detail-content">{{ details.pre_litigation_collection || '-' }}</div>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">三、 诉讼与立案阶段</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="介入阶段">{{ caseData.stage || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案由">{{ caseData.cause || '-' }}</el-descriptions-item>

      <el-descriptions-item label="代理权限">{{
        caseData.agency_power || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="审理法院">{{ caseData.court || '-' }}</el-descriptions-item>

      <el-descriptions-item label="承办法官">{{
        details.handling_judge || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="法院案号">{{ caseData.case_code || '-' }}</el-descriptions-item>

      <el-descriptions-item label="取材料人">{{
        details.material_fetcher || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="缺少具体材料">{{
        details.missing_specific_materials || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="盖章日">{{
        formatDate(details.seal_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="材料提交法院日">{{
        formatDate(details.material_submission_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="立案日">{{
        formatDate(caseData.filing_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="开庭时间">{{
        formatDate(caseData.hearing_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼费缴费金额">{{
        formatCurrency(caseData.litigation_fee_payment_amount)
      }}</el-descriptions-item>

      <el-descriptions-item label="诉讼费缴费时间">{{
        formatDate(caseData.litigation_fee_payment_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼费退费金额">{{
        formatCurrency(caseData.litigation_fee_refund_amount)
      }}</el-descriptions-item>

      <el-descriptions-item label="诉讼费退费时间" :span="2">{{
        formatDate(caseData.litigation_fee_refund_date)
      }}</el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">四、 财产保全阶段</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="是否保全" :span="caseData.has_preservation ? 1 : 2">
        <el-tag :type="caseData.has_preservation ? 'success' : 'info'">{{
          caseData.has_preservation ? '是' : '否'
        }}</el-tag>
      </el-descriptions-item>

      <template v-if="caseData.has_preservation">
        <el-descriptions-item label="保全开始日">{{
          formatDate(caseData.preservation_start)
        }}</el-descriptions-item>
        <el-descriptions-item label="保全终止日">{{
          formatDate(caseData.preservation_end)
        }}</el-descriptions-item>
        <el-descriptions-item label="查封冻结时间">{{
          formatDate(details.seizure_freeze_date)
        }}</el-descriptions-item>
      </template>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">五、 裁判与诉讼结案</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="裁判时间">{{
        formatDate(details.judgment_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="裁判方式">{{
        details.judgment_method || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="二审/再审">
        <el-tag :type="details.has_second_instance_or_retrial ? 'warning' : 'info'">
          {{ details.has_second_instance_or_retrial ? '有' : '无' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="支持律师费金额">{{
        formatCurrency(details.lawyer_fee_supported)
      }}</el-descriptions-item>

      <el-descriptions-item label="被告支付律师费">{{
        formatCurrency(details.defendant_paid_lawyer_fee)
      }}</el-descriptions-item>
      <el-descriptions-item label="结案时间">{{
        formatDate(caseData.closing_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="结案状态">{{
        caseData.closing_status || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="结案方式">{{
        caseData.closing_method || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="是否还清" :span="details.is_settled ? 1 : 2">
        <el-tag :type="details.is_settled ? 'success' : 'info'">{{
          details.is_settled ? '是' : '否'
        }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="还清时间" v-if="details.is_settled">
        {{ formatDate(details.payoff_date) }}
      </el-descriptions-item>

      <el-descriptions-item label="裁判摘要" :span="2">
        <div class="case-detail-content">{{ details.judgment_summary || '-' }}</div>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider execution"
      >六、 执行阶段启动</el-divider
    >
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="执行主办律师">{{
        caseData.execution_lawyer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="执行助理律师">{{
        caseData.execution_assistant?.real_name || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="执行案号">{{
        details.execution_case_number || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="执行法官">{{
        details.execution_judge || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="申请执行日">{{
        formatDate(caseData.execution_application_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="收取材料时间">{{
        formatDate(details.execution_material_receipt_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="材料提交法院时间">{{
        formatDate(details.execution_material_submission_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="执行立案时间">{{
        formatDate(details.execution_filing_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="执行到期日">{{
        formatDate(caseData.execution_due_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="恢复执行">
        <el-tag :type="details.is_execution_recovery ? 'warning' : 'info'">
          {{ details.is_execution_recovery ? '是' : '否' }}
        </el-tag>
      </el-descriptions-item>

      <el-descriptions-item label="执行本金金额">{{
        formatCurrency(details.execution_principal)
      }}</el-descriptions-item>
      <el-descriptions-item label="执行律师费金额">{{
        formatCurrency(details.execution_lawyer_fee)
      }}</el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider execution"
      >七、 执行查控与财产处置</el-divider
    >
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="拍卖程序">{{
        details.auction_status || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="拍卖变卖成交价">{{
        formatCurrency(details.auction_deal_price)
      }}</el-descriptions-item>

      <el-descriptions-item label="财产调查情况" :span="2">
        <div class="case-detail-content">{{ details.property_investigation || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="网络查控财产情况" :span="2">
        <div class="case-detail-content">{{ details.network_control_status || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="承办人执行方案" :span="2">
        <div class="case-detail-content">{{ details.execution_plan || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="法院执行措施" :span="2">
        <div class="case-detail-content">{{ details.court_execution_measures || '-' }}</div>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider execution"
      >八、 执行结案与回款</el-divider
    >
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="调解到期日">{{
        formatDate(caseData.mediation_due_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="调解跟踪情况">{{
        details.mediation_tracking || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="终本时间">{{
        formatDate(details.procedure_termination_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="终本原因">{{
        details.termination_reason || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="恢复执行时间">{{
        formatDate(details.execution_recovery_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="终结执行时间">{{
        formatDate(details.execution_conclusion_date)
      }}</el-descriptions-item>

      <el-descriptions-item label="执行回款总金额">{{
        formatCurrency(details.execution_collection_amount)
      }}</el-descriptions-item>
      <el-descriptions-item label="执行回款来源">{{
        details.collection_source || '-'
      }}</el-descriptions-item>

      <el-descriptions-item label="执行和解内容" :span="2">
        <div class="case-detail-content">{{ details.execution_settlement_content || '-' }}</div>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left" class="section-divider">九、 补充详情</el-divider>
    <el-descriptions
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
      class="unified-descriptions"
    >
      <el-descriptions-item label="审核状态">
        <el-tag
          :type="
            caseData.review_status === '已通过'
              ? 'success'
              : caseData.review_status === '已驳回'
                ? 'danger'
                : 'warning'
          "
        >
          {{ caseData.review_status || '待审核' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="审核人">{{
        caseData.reviewer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="案件地点">{{ caseData.location || '-' }}</el-descriptions-item>
      <el-descriptions-item label="借款人工作单位">{{
        details.borrower_work_unit || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="案件详情" :span="2">
        <div class="case-detail-content">{{ caseData.details || '-' }}</div>
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import PartyDetailList from './PartyDetailList.vue'

// 获取移动端状态，默认 false
const isMobile = inject('isMobile', false)
const props = defineProps({
  caseData: {
    type: Object,
    required: true,
    default: () => ({}),
  },
})

const details = computed(() => props.caseData.bank_case_details || {})

// =================== 当事人数组分组计算 ===================
const partyClients = computed(() => {
  return props.caseData.parties?.filter((p) => p.party_type === '委托人') || []
})

const partyPlaintiffs = computed(() => {
  return (
    props.caseData.parties?.filter((p) => ['原告', '申请人', '上诉人'].includes(p.party_type)) || []
  )
})

const partyDefendants = computed(() => {
  return (
    props.caseData.parties?.filter((p) =>
      ['被告', '被告人', '被申请人', '被上诉人'].includes(p.party_type),
    ) || []
  )
})

const partyBorrowers = computed(() => {
  return props.caseData.parties?.filter((p) => p.party_type === '借款人') || []
})

const partyGuarantors = computed(() => {
  return props.caseData.parties?.filter((p) => p.party_type === '担保人') || []
})

const partyThirdParties = computed(() => {
  return props.caseData.parties?.filter((p) => p.party_type === '第三人') || []
})

const partyOthers = computed(() => {
  const knownTypes = [
    '委托人',
    '原告',
    '申请人',
    '上诉人',
    '被告',
    '被告人',
    '被申请人',
    '被上诉人',
    '借款人',
    '担保人',
    '第三人',
  ]
  return props.caseData.parties?.filter((p) => !knownTypes.includes(p.party_type)) || []
})

// =================== 格式化辅助函数 ===================
const formatDate = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const formatCurrency = (amount) => {
  if (amount === null || amount === undefined || amount === '') return '-'
  return Number(amount).toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' })
}
</script>

<style scoped>
.section-divider {
  margin-top: 35px;
  margin-bottom: 25px;
}
.section-divider :deep(.el-divider__text) {
  font-size: 15px;
  font-weight: bold;
  color: #303133;
}
.section-divider.execution :deep(.el-divider__text) {
  color: #c0392b;
}

/* 统一所有的 Descriptions Label 宽度，保证无论两列还是一列都能完美纵向对齐 */
.unified-descriptions :deep(.el-descriptions__label) {
  width: 150px;
}

.case-detail-content {
  white-space: pre-line;
  line-height: 1.8;
  color: #444;
  padding: 5px 0;
}
/* 移动端适配 CSS */
@media screen and (max-width: 768px) {
  /* 调整卡片内边距 */
  .unified-descriptions :deep(.el-descriptions__content) {
    word-break: break-all;
  }
}
</style>
