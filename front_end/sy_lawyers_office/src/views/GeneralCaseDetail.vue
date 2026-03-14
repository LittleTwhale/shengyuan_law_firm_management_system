<template>
  <div class="general-case-detail">
    <el-descriptions
      title="业务基本信息"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="业务号">{{ caseData.case_number || '-' }}</el-descriptions-item>
      <el-descriptions-item label="业务类别">{{
        caseData.case_category || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="委托日期">{{
        formatDate(caseData.commission_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="业务来源">{{
        caseData.case_source || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="介入阶段">{{ caseData.stage || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案由">{{ caseData.cause || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="当事人信息"
      :column="1"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item :label="clientLabel">
        <PartyDetailList :parties="partyClients" :show-badge="false" />
      </el-descriptions-item>

      <el-descriptions-item :label="plaintiffLabel" v-if="caseData.case_category !== '刑事案件'">
        <PartyDetailList :parties="partyPlaintiffs" theme="primary" />
      </el-descriptions-item>

      <template v-if="caseData.case_category === '刑事案件'">
        <el-descriptions-item label="侦查机关">{{
          caseData.investigative_agency || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="检察院">{{
          caseData.procuratorate || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="二审检察机关">{{
          caseData.second_instance_procuratorate || '-'
        }}</el-descriptions-item>
      </template>

      <el-descriptions-item :label="defendantLabel">
        <PartyDetailList :parties="partyDefendants" theme="warning" />
      </el-descriptions-item>

      <el-descriptions-item label="第三人" v-if="caseData.case_category !== '刑事案件'">
        <PartyDetailList
          :parties="partyThirdParties"
          theme="purple"
          :empty-text="caseData.third_party || '-'"
        />
      </el-descriptions-item>

      <el-descriptions-item label="其他当事人" v-if="partyOthers.length > 0">
        <PartyDetailList :parties="partyOthers" theme="info" />
      </el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="费用信息"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="收费方式">{{ caseData.fee_method || '-' }}</el-descriptions-item>
      <el-descriptions-item label="业务收入">{{
        caseData.case_income ? `${caseData.case_income} 元` : '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="风险比例">{{ caseData.risk_ratio || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="律师信息"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="主办律师">{{
        caseData.main_lawyer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="助理律师">{{
        caseData.assistant_lawyer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="执行律师">{{
        caseData.execution_lawyer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="执行助理">{{
        caseData.execution_assistant?.real_name || '-'
      }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="审理与管辖信息"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="上诉人">{{
        caseData.appellant_info || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="被上诉人">{{
        caseData.extra_appellant_info || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="代理权限">{{
        caseData.agency_power || '-'
      }}</el-descriptions-item>
      <el-descriptions-item :label="courtLabel">{{ caseData.court || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案号">{{ caseData.case_code || '-' }}</el-descriptions-item>
      <el-descriptions-item label="立案日">{{
        formatDate(caseData.filing_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="开庭时间">{{
        formatDate(caseData.hearing_date)
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
      <el-descriptions-item label="案件地点">{{ caseData.location || '-' }}</el-descriptions-item>
      <el-descriptions-item label="案件详情">
        <div class="case-detail-content" v-text="caseData.details || '-'"></div>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="业务状态"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="审核状态">{{ caseData.review_status }}</el-descriptions-item>
      <el-descriptions-item label="审核人">{{
        caseData.reviewer?.real_name || '-'
      }}</el-descriptions-item>
      <el-descriptions-item label="是否重大">{{
        caseData.is_major ? '是' : '否'
      }}</el-descriptions-item>
      <el-descriptions-item label="是否解除">{{
        caseData.is_dismissed ? '是' : '否'
      }}</el-descriptions-item>
      <el-descriptions-item label="是否纸质卷宗">{{
        caseData.has_paper_file ? '是' : '否'
      }}</el-descriptions-item>
      <el-descriptions-item label="是否笔录">{{
        caseData.has_record ? '是' : '否'
      }}</el-descriptions-item>
      <el-descriptions-item label="是否保全">{{
        caseData.has_preservation ? '是' : '否'
      }}</el-descriptions-item>
      <el-descriptions-item label="保全开始日">{{
        formatDate(caseData.preservation_start)
      }}</el-descriptions-item>
      <el-descriptions-item label="保全终止日">{{
        formatDate(caseData.preservation_end)
      }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <el-descriptions
      title="执行信息"
      :column="isMobile ? 1 : 2"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      border
    >
      <el-descriptions-item label="诉讼费缴费时间">{{
        formatDate(caseData.litigation_fee_payment_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼费缴费金额">
        {{
          caseData.litigation_fee_payment_amount
            ? `${caseData.litigation_fee_payment_amount} 元`
            : '-'
        }}
      </el-descriptions-item>
      <el-descriptions-item label="诉讼费退费时间">{{
        formatDate(caseData.litigation_fee_refund_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="诉讼费退费金额">
        {{
          caseData.litigation_fee_refund_amount
            ? `${caseData.litigation_fee_refund_amount} 元`
            : '-'
        }}
      </el-descriptions-item>
      <el-descriptions-item label="申请执行日">{{
        formatDate(caseData.execution_application_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="调解到期日">{{
        formatDate(caseData.mediation_due_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="执行到期日">{{
        formatDate(caseData.execution_due_date)
      }}</el-descriptions-item>
      <el-descriptions-item label="顾问到期日" v-if="caseData.case_category === '法律顾问业务'">{{
        formatDate(caseData.advisory_due_date)
      }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import PartyDetailList from './PartyDetailList.vue' // 引入当事人列表组件

// 获取移动端状态
const isMobile = inject('isMobile', false)

const props = defineProps({
  caseData: {
    type: Object,
    required: true,
    default: () => ({}),
  },
})

// 1️⃣ 当事人标题动态化
const plaintiffLabel = computed(() => {
  // 修正：移除了刑事案件的判断，因为刑事案件不再显示此字段
  if (props.caseData.case_category?.includes('仲裁')) return '申请人'
  return '原告/申请人'
})

const defendantLabel = computed(() => {
  if (props.caseData.case_category?.includes('刑')) return '被告人'
  if (props.caseData.case_category?.includes('仲裁')) return '被申请人'
  return '被告'
})

// 2️⃣ 委托人标题动态化
const clientLabel = computed(() => {
  if (props.caseData.case_category?.includes('银行')) return '委托银行'
  return '委托人'
})

// 3️⃣ 审理机构标题动态化
const courtLabel = computed(() => {
  if (props.caseData.case_category?.includes('仲裁')) return '仲裁委员会'
  if (props.caseData.case_category?.includes('刑')) return '审理机构'
  return '审理法院'
})

// 修改点4：当事人分组计算属性 (通过 parties 数组过滤)
const partyClients = computed(() => {
  if (!props.caseData.parties) return []
  return props.caseData.parties.filter((p) => p.party_type === '委托人')
})

const partyPlaintiffs = computed(() => {
  if (!props.caseData.parties) return []
  return props.caseData.parties.filter((p) => ['原告', '申请人', '上诉人'].includes(p.party_type))
})

const partyDefendants = computed(() => {
  if (!props.caseData.parties) return []
  return props.caseData.parties.filter((p) =>
    ['被告', '被告人', '被申请人', '被上诉人'].includes(p.party_type),
  )
})

const partyThirdParties = computed(() => {
  if (!props.caseData.parties) return []
  return props.caseData.parties.filter((p) => p.party_type === '第三人')
})

const partyOthers = computed(() => {
  if (!props.caseData.parties) return []
  // 过滤出不属于通用类型的其他当事人
  const knownTypes = [
    '委托人',
    '原告',
    '申请人',
    '上诉人',
    '被告',
    '被告人',
    '被申请人',
    '被上诉人',
    '第三人',
  ]
  return props.caseData.parties.filter((p) => !knownTypes.includes(p.party_type))
})

// 日期格式化辅助函数
const formatDate = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
/* 案件详情文本换行样式 */
.case-detail-content {
  white-space: pre-line; /* 保留换行符，自动处理空格和宽度 */
  line-height: 1.8; /* 增加行高，提升长文本可读性 */
  color: #444; /* 可选：调整文本颜色，区分于标签 */
  padding: 5px 0; /* 可选：增加上下内边距，避免与其他内容拥挤 */
}
/* 移动端适配 CSS */
@media screen and (max-width: 768px) {
  :deep(.el-descriptions__content) {
    word-break: break-all;
  }
}
</style>
