<template>
  <div class="case-detail">
    <el-page-header @back="goBack" title="返回" />

    <h2 class="page-title">业务详情与卷宗</h2>

    <el-tabs v-model="activeTab" type="border-card" class="detail-tabs">
      <el-tab-pane label="业务详情" name="detail">
        <el-card
          class="detail-card"
          v-loading="loading"
          shadow="never"
          style="border: none; margin-top: 0"
        >
          <el-descriptions title="业务基本信息" :column="2" border>
            <el-descriptions-item label="业务号">{{
              caseData.case_number || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="业务类别">{{
              caseData.case_category || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="委托日期">{{
              formatDate(caseData.commission_date)
            }}</el-descriptions-item>
            <el-descriptions-item label="业务来源">{{
              caseData.case_source || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="介入阶段">{{
              caseData.stage || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="案由">{{ caseData.cause || '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-descriptions title="当事人信息" :column="1" border>
            <el-descriptions-item :label="clientLabel">
              <div v-if="partyClients.length > 0">
                <div v-for="(p, index) in partyClients" :key="p.id" class="party-item">
                  <span class="party-index">{{ index + 1 }}.</span>
                  <span class="party-name">{{ p.name }}</span>
                  <span class="party-tag" v-if="p.phone">
                    <el-icon><Phone /></el-icon> {{ p.phone }}
                  </span>
                  <span class="party-tag" v-if="p.id_number">
                    <el-icon><Postcard /></el-icon> {{ p.id_number }}
                  </span>
                  <span class="party-address" v-if="p.address"> (地址: {{ p.address }}) </span>
                  <span class="party-address" v-if="p.legal_representative">
                    [法人: {{ p.legal_representative }}]
                  </span>
                </div>
              </div>
              <span v-else>-</span>
            </el-descriptions-item>

            <el-descriptions-item
              :label="plaintiffLabel"
              v-if="caseData.case_category !== '刑事案件'"
            >
              <div v-if="partyPlaintiffs.length > 0">
                <div v-for="(p, index) in partyPlaintiffs" :key="p.id" class="party-item">
                  <span class="party-index">{{ index + 1 }}.</span>
                  <span class="party-role-badge">{{ p.party_type }}</span>
                  <span class="party-name">{{ p.name }}</span>
                  <span class="party-tag" v-if="p.phone">
                    <el-icon><Phone /></el-icon> {{ p.phone }}
                  </span>
                  <span class="party-tag" v-if="p.id_number">
                    <el-icon><Postcard /></el-icon> {{ p.id_number }}
                  </span>
                  <span class="party-address" v-if="p.address"> (地址: {{ p.address }}) </span>
                  <span class="party-address" v-if="p.legal_representative">
                    [法人: {{ p.legal_representative }}]
                  </span>
                </div>
              </div>
              <span v-else>-</span>
            </el-descriptions-item>

            <template v-if="caseData.case_category === '刑事案件'">
              <el-descriptions-item label="侦查机关">
                {{ caseData.investigative_agency || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="检察院">
                {{ caseData.procuratorate || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="二审检察机关">
                {{ caseData.second_instance_procuratorate || '-' }}
              </el-descriptions-item>
            </template>

            <el-descriptions-item :label="defendantLabel">
              <div v-if="partyDefendants.length > 0">
                <div v-for="(p, index) in partyDefendants" :key="p.id" class="party-item">
                  <span class="party-index">{{ index + 1 }}.</span>
                  <span class="party-role-badge warning">{{ p.party_type }}</span>
                  <span class="party-name">{{ p.name }}</span>
                  <span class="party-tag" v-if="p.phone">
                    <el-icon><Phone /></el-icon> {{ p.phone }}
                  </span>
                  <span class="party-tag" v-if="p.id_number">
                    <el-icon><Postcard /></el-icon> {{ p.id_number }}
                  </span>
                  <span class="party-address" v-if="p.address"> (地址: {{ p.address }}) </span>
                  <span class="party-address" v-if="p.legal_representative">
                    [法人: {{ p.legal_representative }}]
                  </span>
                </div>
              </div>
              <span v-else>-</span>
            </el-descriptions-item>

            <el-descriptions-item label="第三人" v-if="caseData.case_category !== '刑事案件'">
              <div v-if="partyThirdParties.length > 0">
                <div v-for="(p, index) in partyThirdParties" :key="p.id" class="party-item">
                  <span class="party-index">{{ index + 1 }}.</span>
                  <el-tag
                    size="small"
                    color="#ebdcfc"
                    style="color: #6d14d7; border-color: #6d14d7; margin-right: 5px"
                  >
                    第三人
                  </el-tag>
                  <span class="party-name">{{ p.name }}</span>
                  <span class="party-tag" v-if="p.phone">
                    <el-icon><Phone /></el-icon> {{ p.phone }}
                  </span>
                  <span class="party-tag" v-if="p.id_number">
                    <el-icon><Postcard /></el-icon> {{ p.id_number }}
                  </span>
                  <span class="party-address" v-if="p.address"> (地址: {{ p.address }}) </span>
                  <span class="party-address" v-if="p.legal_representative">
                    [法人: {{ p.legal_representative }}]
                  </span>
                </div>
              </div>
              <span v-else>
                {{ caseData.third_party || '-' }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <template v-if="caseData.case_category === '银行案件' && caseData.bank_case_details">
            <el-divider />

            <el-descriptions title="银行案件 - 借贷基础信息" :column="2" border>
              <el-descriptions-item label="支行名称">{{
                caseData.bank_case_details.branch_name || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="客户经理">{{
                caseData.bank_case_details.account_manager || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="借款人身份证号码/统信代码">{{
                caseData.bank_case_details.borrower_id_number || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="借款人工作单位">{{
                caseData.bank_case_details.borrower_work_unit || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="担保人">{{
                caseData.bank_case_details.guarantor || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="是否普惠金融">
                <el-tag
                  :type="caseData.bank_case_details.is_inclusive_finance ? 'success' : 'info'"
                >
                  {{ caseData.bank_case_details.is_inclusive_finance ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="借款日">{{
                formatDate(caseData.bank_case_details.loan_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="到期日">{{
                formatDate(caseData.bank_case_details.loan_due_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="逾期时间">{{
                formatDate(caseData.bank_case_details.overdue_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="诉讼时效">{{
                caseData.bank_case_details.statute_of_limitations || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="抵/质押物信息" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.collateral_info || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="抵押物位置" :span="2">{{
                caseData.bank_case_details.collateral_location || '-'
              }}</el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <el-descriptions title="银行案件 - 金额与流程" :column="2" border>
              <el-descriptions-item label="贷款本金">
                {{ formatCurrency(caseData.bank_case_details.loan_principal) }}
              </el-descriptions-item>
              <el-descriptions-item label="诉讼标的金额(含利息)">
                {{ formatCurrency(caseData.bank_case_details.litigation_target_amount) }}
              </el-descriptions-item>
              <el-descriptions-item label="信用卡违约金">
                {{ formatCurrency(caseData.bank_case_details.credit_card_penalty) }}
              </el-descriptions-item>
              <el-descriptions-item label="取材料人">{{
                caseData.bank_case_details.material_fetcher || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="诉前催收情况" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.pre_litigation_collection || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="盖章日">{{
                formatDate(caseData.bank_case_details.seal_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="材料提交法院日">{{
                formatDate(caseData.bank_case_details.material_submission_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="裁判摘要" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.judgment_summary || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="支持律师费金额">
                {{ formatCurrency(caseData.bank_case_details.lawyer_fee_supported) }}
              </el-descriptions-item>
              <el-descriptions-item label="被告支付律师费金额">
                {{ formatCurrency(caseData.bank_case_details.defendant_paid_lawyer_fee) }}
              </el-descriptions-item>
              <el-descriptions-item label="是否还清">
                <el-tag :type="caseData.bank_case_details.is_settled ? 'success' : 'info'">
                  {{ caseData.bank_case_details.is_settled ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <el-descriptions title="银行案件 - 执行与查控" :column="2" border>
              <el-descriptions-item label="执行案号">{{
                caseData.bank_case_details.execution_case_number || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="执行法官">{{
                caseData.bank_case_details.execution_judge || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="执行立案时间">{{
                formatDate(caseData.bank_case_details.execution_filing_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="是否为恢复执行">
                <el-tag
                  :type="caseData.bank_case_details.is_execution_recovery ? 'success' : 'info'"
                >
                  {{ caseData.bank_case_details.is_execution_recovery ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="执行本金金额">
                {{ formatCurrency(caseData.bank_case_details.execution_principal) }}
              </el-descriptions-item>
              <el-descriptions-item label="执行律师费金额">
                {{ formatCurrency(caseData.bank_case_details.execution_lawyer_fee) }}
              </el-descriptions-item>
              <el-descriptions-item label="财产调查情况" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.property_investigation || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="网络查控财产情况" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.network_control_status || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="承办人执行方案" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.execution_plan || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="法院执行措施" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.court_execution_measures || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="查封冻结标的及时间" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.seizure_freeze_info || '-' }}
                </div>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <el-descriptions title="银行案件 - 拍卖、结案与回款" :column="2" border>
              <el-descriptions-item label="拍卖程序">{{
                caseData.bank_case_details.auction_status || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="拍卖变卖成交价">
                {{ formatCurrency(caseData.bank_case_details.auction_deal_price) }}
              </el-descriptions-item>
              <el-descriptions-item label="执行和解内容" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.execution_settlement_content || '-' }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="终本时间">{{
                formatDate(caseData.bank_case_details.procedure_termination_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="终本原因">{{
                caseData.bank_case_details.termination_reason || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="终结执行时间">{{
                formatDate(caseData.bank_case_details.execution_conclusion_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="恢复执行时间">{{
                formatDate(caseData.bank_case_details.execution_recovery_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="还清时间">{{
                formatDate(caseData.bank_case_details.payoff_date)
              }}</el-descriptions-item>
              <el-descriptions-item label="执行回款总金额">
                {{ formatCurrency(caseData.bank_case_details.execution_collection_amount) }}
              </el-descriptions-item>
              <el-descriptions-item label="执行回款来源">{{
                caseData.bank_case_details.collection_source || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="调解案件履行跟踪情况" :span="2">
                <div class="case-detail-content">
                  {{ caseData.bank_case_details.mediation_tracking || '-' }}
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </template>

          <el-divider />

          <el-descriptions title="费用信息" :column="2" border>
            <el-descriptions-item label="收费方式">{{
              caseData.fee_method || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="业务收入">
              {{ caseData.case_income ? `${caseData.case_income} 元` : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="风险比例">{{
              caseData.risk_ratio || '-'
            }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-descriptions title="律师信息" :column="2" border>
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

          <el-descriptions title="审理与管辖信息" :column="2" border>
            <el-descriptions-item label="上诉人">{{
              caseData.appellant_info || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="被上诉人">{{
              caseData.extra_appellant_info || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="代理权限">{{
              caseData.agency_power || '-'
            }}</el-descriptions-item>
            <el-descriptions-item :label="courtLabel">
              {{ caseData.court || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="案号">
              {{ caseData.case_code || '-' }}
            </el-descriptions-item>
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
            <el-descriptions-item label="案件地点">{{
              caseData.location || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="案件详情">
              <div class="case-detail-content" v-text="caseData.details || '-'"></div>
            </el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-descriptions title="系统信息" :column="2" border>
            <el-descriptions-item label="创建时间">{{
              formatDateTime(caseData.created_at)
            }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{
              formatDateTime(caseData.updated_at)
            }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-descriptions title="业务状态" :column="2" border>
            <el-descriptions-item label="审核状态">{{
              caseData.review_status
            }}</el-descriptions-item>
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

          <el-descriptions title="执行信息" :column="2" border>
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
          </el-descriptions>

          <el-divider />

          <el-descriptions title="业务附件" border>
            <el-descriptions-item label="附件列表" :column="1">
              <div class="attachment-list">
                <div v-if="attachments.length === 0 && !loadingAttachments" class="no-attachments">
                  暂无附件
                </div>

                <el-table
                  v-if="attachments.length > 0"
                  :data="attachments"
                  border
                  style="width: 100%; margin-top: 10px"
                >
                  <el-table-column prop="file_name" label="文件名" />
                  <el-table-column
                    prop="uploader"
                    label="上传人"
                    :formatter="(row) => row.uploader?.real_name || '-'"
                  />
                  <el-table-column prop="file_size" label="文件大小" :formatter="formatFileSize" />
                  <el-table-column
                    prop="uploaded_at"
                    label="上传时间"
                    :formatter="(row, column, cellValue) => formatDateTime(cellValue)"
                  />
                  <el-table-column label="操作">
                    <template #default="scope">
                      <el-button size="small" @click="previewAttachment(scope.row)">
                        预览
                      </el-button>
                      <el-button size="small" @click="downloadAttachment(scope.row.attachment_id)">
                        下载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="电子卷宗" name="volume" :lazy="true">
        <CaseVolumePanel v-if="caseId" :case-id="caseId" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="showFilePreview"
      :title="previewTitle"
      width="90%"
      height="90vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="preview-container">
        <img
          v-if="previewType === 'image'"
          :src="previewUrl"
          class="image-preview"
          alt="预览图片"
        />

        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="pdf-iframe" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Phone, Postcard } from '@element-plus/icons-vue' // 引入图标

import CaseVolumePanel from '@/views/CaseVolumePanel.vue'

const route = useRoute()
const router = useRouter()

// >>>  Tab 控制变量 <<<
const activeTab = ref('detail') // 默认显示详情

const caseData = ref({})
const loading = ref(false)
const caseId = route.params.id

// 附件相关变量
const attachments = ref([])
const attachmentFileList = ref([])
const loadingAttachments = ref(false)

onMounted(() => {
  loadCaseDetail()

  // 如果 URL 参数中有 tab=volume，自动切换到卷宗 Tab
  if (route.query.tab === 'volume') {
    activeTab.value = 'volume'
  }
})

const goBack = () => {
  // 从路由状态中获取来源页面路径，默认返回案件管理页面
  const fromPath = route.query.from || '/main/cases'
  router.push(fromPath)
}

const loadCaseDetail = async () => {
  loading.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:8002/cases/${caseId}`)
    caseData.value = res.data || {}

    // 权限判断逻辑
    const role = localStorage.getItem('role')
    const currentUserId = localStorage.getItem('user_id')
    const mainLawyerId = caseData.value.main_lawyer?.id
    const assistantLawyerId = caseData.value.assistant_lawyer?.id

    if (
      role === 'user' &&
      String(mainLawyerId) !== String(currentUserId) &&
      String(assistantLawyerId) !== String(currentUserId)
    ) {
      ElMessage.error('您没有权限查看此业务')
      await router.push('/main/cases')
    } else {
      // 加载业务附件
      await loadAttachments()
    }
  } catch (err) {
    console.error('加载业务详情失败:', err)
    ElMessage.error('加载业务详情失败')
    await router.push('/main/cases')
  } finally {
    loading.value = false
  }
}

// 1️⃣ 当事人标题动态化
const plaintiffLabel = computed(() => {
  // 修正：移除了刑事案件的判断，因为刑事案件不再显示此字段
  if (caseData.value.case_category?.includes('仲裁')) return '申请人'
  return '原告/申请人'
})

const defendantLabel = computed(() => {
  if (caseData.value.case_category?.includes('刑')) return '被告人'
  if (caseData.value.case_category?.includes('仲裁')) return '被申请人'
  return '被告'
})

// 2️⃣ 委托人标题动态化
const clientLabel = computed(() => {
  if (caseData.value.case_category?.includes('银行')) return '委托银行'
  return '委托人'
})

// 3️⃣ 审理机构标题动态化
const courtLabel = computed(() => {
  if (caseData.value.case_category?.includes('仲裁')) return '仲裁委员会'
  if (caseData.value.case_category?.includes('刑')) return '审理机构'
  return '审理法院'
})

// 修改点4：当事人分组计算属性
const partyClients = computed(() => {
  if (!caseData.value.parties) return []
  return caseData.value.parties.filter((p) => p.party_type === '委托人')
})

const partyPlaintiffs = computed(() => {
  if (!caseData.value.parties) return []
  return caseData.value.parties.filter((p) => ['原告', '申请人', '上诉人'].includes(p.party_type))
})

const partyDefendants = computed(() => {
  if (!caseData.value.parties) return []
  return caseData.value.parties.filter((p) =>
    ['被告', '被告人', '被申请人', '被上诉人'].includes(p.party_type),
  )
})

const partyThirdParties = computed(() => {
  if (!caseData.value.parties) return []
  return caseData.value.parties.filter((p) => p.party_type === '第三人')
})

// 加载案件附件
const loadAttachments = async () => {
  if (!caseId) return

  loadingAttachments.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:8002/attachments/case/${caseId}`)
    attachments.value = res.data
    // 转换为上传组件需要的格式
    attachmentFileList.value = res.data.map((item) => ({
      name: item.file_name,
      url: `/attachments/${item.attachment_id}/download`,
      uid: item.attachment_id,
    }))
  } catch (err) {
    console.error('加载附件失败:', err)
    ElMessage.error('加载附件失败')
  } finally {
    loadingAttachments.value = false
  }
}

// 文件大小转换方法
const formatFileSize = (row) => {
  // 假设file_size单位是字节，转换为KB或MB并保留两位小数
  if (!row.file_size) return '0 KB'
  if (row.file_size < 1024 * 1024) {
    return (row.file_size / 1024).toFixed(2) + ' KB'
  }
  const mbSize = row.file_size / (1024 * 1024)
  return mbSize.toFixed(2) + ' MB'
}

// 下载附件
const downloadAttachment = (attachmentId) => {
  window.open(`http://127.0.0.1:8002/attachments/${attachmentId}/download`, '_blank')
}

// 新增预览相关变量
const showFilePreview = ref(false)
const previewUrl = ref('')
const previewType = ref('') // 'image' 或 'pdf'
const previewTitle = ref('文件预览')

// 预览附件
const previewAttachment = (attachment) => {
  // 根据文件类型决定预览方式
  const fileType = attachment.file_type || ''
  const previewUrlTemp = `http://127.0.0.1:8002/attachments/${attachment.attachment_id}/preview`

  // 图片类型处理
  if (fileType.startsWith('image/')) {
    previewType.value = 'image'
    previewUrl.value = previewUrlTemp
    previewTitle.value = `图片预览：${attachment.file_name}`
    showFilePreview.value = true
    return
  }

  // PDF类型处理
  const previewableTypes = [
    'application/pdf',
    'application/msword', // .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  ]
  if (previewableTypes.includes(fileType)) {
    previewType.value = 'pdf'
    previewUrl.value = previewUrlTemp
    previewTitle.value = `PDF预览：${attachment.file_name}`
    showFilePreview.value = true
    return
  }

  // 对于Office文档，可以提示无法直接预览或使用第三方服务
  ElMessage.info('该文件类型不支持直接预览，建议下载查看')
}

onMounted(() => {
  loadCaseDetail()
})

const formatDate = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 金额格式化辅助函数
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined || amount === '') return '-'
  return Number(amount).toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' })
}

const formatDateTime = (dateVal) => {
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
/* 附件列表样式 */
.attachment-list {
  margin-top: 10px;
}
.no-attachments {
  color: #999;
  padding: 10px;
  text-align: center;
}

.preview-container {
  width: 100%;
  height: calc(90vh - 100px); /* 减去弹窗标题栏高度 */
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
}

.image-preview {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain; /* 保持图片比例，避免拉伸 */
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #ffffff;
  border-radius: 4px;
}

/* 新增当事人列表样式 */
.party-item {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #eee;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.party-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}
.party-index {
  color: #999;
  font-weight: bold;
}
.party-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
}
.party-tag {
  font-size: 13px;
  color: #666;
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.party-role-badge {
  font-size: 12px;
  background-color: #ecf5ff;
  color: #409eff;
  border: 1px solid #d9ecff;
  padding: 0 5px;
  border-radius: 4px;
}
.party-role-badge.warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border-color: #faecd8;
}
.party-address {
  font-size: 12px;
  color: #999;
}
</style>
