<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    :width="isMobile ? '95%' : '1000px'"
    destroy-on-close
    @close="handleCancel"
    top="5vh"
    class="custom-dialog"
  >
    <el-form
      :model="formData"
      :rules="formRules"
      ref="formRef"
      :label-width="isMobile ? 'auto' : '160px'"
      :label-position="isMobile ? 'top' : 'right'"
    >
      <el-form-item label="业务类别" prop="case_category">
        <el-select
          v-model="formData.case_category"
          placeholder="请选择业务类别"
          style="width: 100%"
          @change="handleCategoryChange"
        >
          <el-option label="民事案件" value="民事案件" />
          <el-option label="银行案件" value="银行案件" />
          <el-option label="刑事案件" value="刑事案件" />
          <el-option label="行政案件" value="行政案件" />
          <el-option label="劳动仲裁" value="劳动仲裁" />
          <el-option label="商事仲裁" value="商事仲裁" />
          <el-option label="非诉业务" value="非诉业务" />
          <el-option label="执行案件" value="执行案件" />
          <el-option label="法律顾问业务" value="法律顾问业务" />
          <el-option label="法律援助(民事)" value="法律援助(民事)" />
          <el-option label="法律援助(刑事)" value="法律援助(刑事)" />
          <el-option label="法律援助(行政)" value="法律援助(行政)" />
        </el-select>
      </el-form-item>

      <BankCaseForm
        v-if="formData.case_category === '银行案件'"
        :lawyer-options="lawyerOptions"
        :current-user-id="currentUserId"
      />

      <GeneralCaseForm v-else :lawyer-options="lawyerOptions" />

      <el-divider content-position="left">附件上传</el-divider>
      <el-upload
        class="upload-demo"
        drag
        action="#"
        :auto-upload="false"
        multiple
        v-model:file-list="rawFiles"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">选择文件后，点击底部的“确定”按钮保存业务时会自动上传。</div>
        </template>
      </el-upload>

      <div v-if="formData.attachments && formData.attachments.length > 0" style="margin-top: 20px">
        <p style="font-weight: bold; margin-bottom: 10px">已上传附件:</p>
        <el-table :data="formData.attachments" border style="width: 100%" size="small">
          <el-table-column prop="name" label="文件名" />
          <el-table-column label="操作" width="160" align="center">
            <template #default="scope">
              <el-button
                link
                type="primary"
                size="small"
                @click="downloadFormAttachment(scope.row.uid)"
              >
                下载
              </el-button>
              <el-button
                link
                type="danger"
                size="small"
                @click="deleteFormAttachment(scope.row.uid)"
                :disabled="isRestricted"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <span v-if="validationErrorCount > 0" class="error-badge" @click="scrollToFirstError">
          <el-icon><WarningFilled /></el-icon>
          还有 {{ validationErrorCount }} 项必填未完成，点击定位
        </span>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit"> 确定 </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, provide, onUnmounted, onMounted, nextTick } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, WarningFilled } from '@element-plus/icons-vue'

// 引入拆分后的子组件
import GeneralCaseForm from '@/views/GeneralCaseForm.vue'
import BankCaseForm from './BankCaseForm.vue'

// -------------------------- 响应式/移动端适配相关 --------------------------
const isMobile = ref(false)
const checkDeviceType = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})

// 向下层子组件提供移动端状态，以备子组件需要做深层 JS 逻辑适配
provide('isMobile', isMobile)
// ---------------------------------------------------------------------------

const props = defineProps({
  visible: { type: Boolean, default: false },
  caseId: { type: [Number, String], default: null },
  cloneId: { type: [Number, String], default: null }, // 接收克隆的源业务ID
  currentUserId: { type: [Number, String], default: null },
  currentUserRole: { type: String, default: '' },
  reviewStatus: { type: String, default: '' },
})

// 计算是否为受限状态：是普通用户 且 案件已审核
const isRestricted = computed(() => {
  return props.currentUserRole === 'user' && props.reviewStatus === '已审核'
})

// 专门控制当事人区域的受限状态
const isPartyRestricted = computed(() => {
  // 如果是银行案件，当事人信息不受限（即使已审核也允许普通用户修改）
  if (formData.case_category === '银行案件') {
    return false
  }
  return isRestricted.value
})

// 将受限状态下发给子组件
provide('isRestricted', isRestricted)
provide('isPartyRestricted', isPartyRestricted)

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

// 根据不同状态动态计算弹窗标题
const dialogTitle = computed(() => {
  if (props.caseId) return '编辑业务'
  if (props.cloneId) return '复用业务'
  return '新增业务'
})

const loading = ref(false)
const formRef = ref(null)
const rawFiles = ref([])
const lawyerOptions = ref([])
const validationErrorCount = ref(0)

/** 滚动到第一个校验失败的字段 */
const scrollToFirstError = () => {
  nextTick(() => {
    const firstError = formRef.value?.$el?.querySelector('.is-error')
    if (firstError) {
      firstError.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

// 定义银行案件初始详情数据
const initialBankDetails = {
  // --- 收案与基础信息 ---
  branch_name: null,
  case_status: null,
  bank_required_case_status: null,
  account_manager: null,
  material_fetcher: null,
  missing_specific_materials: null,
  case_acceptance_date: null,

  // --- 借贷基础信息 ---
  loan_type: null,
  loan_account: null,
  loan_principal: null,
  litigation_target_amount: null,
  credit_card_penalty: 0,
  loan_date: null,
  loan_due_date: null,
  statute_of_limitations: null,
  guarantee_due_date: null,
  collateral_info: null,
  collateral_location: null,
  pre_litigation_collection: null,

  // --- 诉讼与立案阶段 ---
  handling_judge: null,
  seal_date: null,
  material_submission_date: null,

  // --- 财产保全阶段 ---
  seizure_freeze_date: null,

  // --- 裁判与诉讼结案 ---
  judgment_date: null,
  judgment_method: null,
  has_second_instance_or_retrial: false,
  judgment_summary: null,
  lawyer_fee_supported: 0,
  defendant_paid_lawyer_fee: 0,
  is_settled: false,
  payoff_date: null,

  // --- 执行阶段启动 ---
  execution_case_number: null,
  execution_judge: null,
  borrower_work_unit: null,
  is_execution_recovery: false,
  execution_material_receipt_date: null,
  execution_material_submission_date: null,
  execution_filing_date: null,
  execution_principal: 0,
  execution_lawyer_fee: 0,

  // --- 执行查控与财产处置 ---
  property_investigation: null,
  network_control_status: null,
  execution_plan: null,
  court_execution_measures: null,
  auction_status: null,
  auction_deal_price: 0,

  // --- 执行结案与回款 ---
  execution_settlement_content: null,
  execution_settlement_due_date: null,
  execution_settlement_tracking: null,
  mediation_tracking: null,
  procedure_termination_date: null,
  termination_reason: null,
  execution_conclusion_date: null,
  execution_recovery_date: null,
  execution_collection_amount: 0,
  collection_source: null,
}

// 提取全量字段工厂函数，用于干净彻底地重置表单
const getInitialFormData = () => ({
  case_category: '民事案件',
  case_code: null,
  commission_date: null,

  // ============ 通用当事人列表 ============
  party_clients: [], // 委托人 (银行案件中为委托银行)
  party_plaintiffs: [], // 原告/申请人
  party_defendants: [], // 被告/被申请人
  party_third_parties: [], // 第三人
  party_others: [],

  // ============ 银行案件专属当事人列表  ============
  party_bank_borrowers: [], // 借款人 (BankCaseForm中使用)
  party_bank_guarantors: [], // 担保人 (BankCaseForm中使用)

  // 旧字段已废弃 — 当事人信息统一通过 case_parties 表管理

  case_source: null,
  stage: null,
  cause: null,

  // 律师
  main_lawyer_id: null,
  assistant_lawyer_id: null,
  assistant_lawyer_2_id: null,
  execution_lawyer_id: null,
  execution_assistant_id: null,

  // 诉讼主体(刑事)
  investigative_agency: null,
  procuratorate: null,
  second_instance_procuratorate: null,

  // 审理信息
  agency_power: null,
  court: null,
  hearing_date: null,
  filing_date: null,
  closing_date: null,
  location: null,
  details: null,

  // 费用
  fee_method: null,
  risk_ratio: null,
  case_income: 0,
  payment_due_date: null,

  // 标记
  is_major: false,
  has_paper_file: false,
  has_record: false,
  has_preservation: false,
  is_dismissed: false,
  preservation_start: null,
  preservation_end: null,

  // 结案与执行
  closing_status: null,
  closing_method: null,
  execution_application_date: null,
  mediation_due_date: null,
  execution_due_date: null,
  advisory_due_date: null,

  // 诉讼费
  litigation_fee_payment_date: null,
  litigation_fee_payment_amount: 0,
  litigation_fee_refund_date: null,
  litigation_fee_refund_amount: 0,

  // 银行案件详情对象
  bank_case_details: JSON.parse(JSON.stringify(initialBankDetails)),

  // 附件列表
  attachments: [],
})

// 统一的大表单数据对象 (使用工厂函数初始化)
const formData = reactive(getInitialFormData())

provide('caseFormData', formData)

const formRules = computed(() => {
  const isBankCase = formData.case_category === '银行案件'

  return {
    case_category: [{ required: true, message: '请选择业务类别', trigger: 'change' }],
    commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
    main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
    //  银行案件是非必填，其他案件必填
    cause: [{ required: !isBankCase, message: '请填写案由', trigger: 'blur' }],
    fee_method: [{ required: !isBankCase, message: '请选择收费方式', trigger: 'change' }],
    stage: [{ required: true, message: '请填写介入阶段', trigger: 'blur' }],

    // 银行案件专属必填校验
    'bank_case_details.branch_name': [{ required: isBankCase, message: '必填', trigger: 'change' }],
    'bank_case_details.loan_type': [{ required: isBankCase, message: '必填', trigger: 'blur' }],
    'bank_case_details.loan_principal': [
      { required: isBankCase, message: '必填', trigger: 'blur' },
    ],
    'bank_case_details.collateral_info': [
      { required: isBankCase, message: '必填(若无请填"无")', trigger: 'blur' },
    ],
    'bank_case_details.case_acceptance_date': [
      { required: isBankCase, message: '必填', trigger: 'change' },
    ],
    'bank_case_details.litigation_target_amount': [
      { required: isBankCase, message: '必填', trigger: 'blur' },
    ],
    'bank_case_details.case_status': [{ required: isBankCase, message: '必填', trigger: 'change' }],
    'bank_case_details.loan_date': [{ required: isBankCase, message: '必填', trigger: 'change' }],
    'bank_case_details.loan_due_date': [
      { required: isBankCase, message: '必填', trigger: 'change' },
    ],
  }
})

// 切换业务类别时，重置部分数据
const handleCategoryChange = (val) => {
  // 可以在这里做一些清空特定字段的操作，防止切来切去数据污染
  // 但为了保留用户误操作的数据，暂时不做硬性清空，提交时会过滤
  if (val === '银行案件') {
    // 确保银行详情对象存在
    if (!formData.bank_case_details) {
      formData.bank_case_details = JSON.parse(JSON.stringify(initialBankDetails))
    }
    // 自动为必填的三项各添加一条空数据（如果原本为空）
    if (formData.party_plaintiffs.length === 0) addEmptyParty(formData.party_plaintiffs, '原告')
    if (formData.party_defendants.length === 0) addEmptyParty(formData.party_defendants, '被告')
    if (formData.party_bank_borrowers.length === 0)
      addEmptyParty(formData.party_bank_borrowers, '借款人')
  }
}

// 加载律师列表
const fetchLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyerOptions.value = res.data
  } catch (e) {
    console.error('加载律师列表失败', e)
  }
}

// 获取详情并填充表单 (修改为接收动态目标ID)
const fetchCaseDetail = async (targetId) => {
  if (!targetId) return
  try {
    const res = await request.get(`/cases/${targetId}`)
    const data = res.data

    // 填充基础数据
    Object.keys(formData).forEach((key) => {
      // 跳过复杂对象和数组
      if (
        [
          'bank_case_details',
          'attachments',
          'party_clients',
          'party_plaintiffs',
          'party_defendants',
          'party_third_parties',
          'party_bank_borrowers',
          'party_bank_guarantors',
        ].includes(key)
      )
        return
      if (data[key] !== undefined) {
        // 如果 formData 中初始定义该字段是数字类型，且后端返回了字符串，则将其转换为数字
        if (
          typeof formData[key] === 'number' &&
          typeof data[key] === 'string' &&
          !isNaN(Number(data[key]))
        ) {
          formData[key] = Number(data[key])
        } else {
          formData[key] = data[key]
        }
      }
    })

    // 重置数组
    formData.party_clients = []
    formData.party_plaintiffs = []
    formData.party_defendants = []
    formData.party_third_parties = []
    formData.party_bank_borrowers = []
    formData.party_bank_guarantors = []
    formData.party_others = []

    // 填充当事人
    if (data.parties && data.parties.length > 0) {
      data.parties.forEach((p) => {
        // 通用类型映射
        if (p.party_type === '委托人') {
          formData.party_clients.push(p)
        } else if (['原告', '申请人', '上诉人'].includes(p.party_type)) {
          formData.party_plaintiffs.push(p)
        } else if (['被告', '被告人', '被申请人', '被上诉人'].includes(p.party_type)) {
          formData.party_defendants.push(p)
        } else if (p.party_type === '第三人') {
          formData.party_third_parties.push(p)
        }
        // 银行专属类型映射 (假设后端存储的类型为 "借款人" 和 "担保人")
        else if (p.party_type === '借款人') {
          formData.party_bank_borrowers.push(p)
        } else if (p.party_type === '担保人') {
          formData.party_bank_guarantors.push(p)
        } else {
          // 其他类型都归为 "其他"
          formData.party_others.push(p)
        }
      })
    } else {
      // 旧字段已废弃，数据已全部迁移至 case_parties 表，data.parties 始终存在
    }

    // 律师映射
    if (data.main_lawyer && data.main_lawyer.id) formData.main_lawyer_id = data.main_lawyer.id
    if (data.assistant_lawyer && data.assistant_lawyer.id)
      formData.assistant_lawyer_id = data.assistant_lawyer.id
    if (data.assistant_lawyer_2 && data.assistant_lawyer_2.id)
      formData.assistant_lawyer_2_id = data.assistant_lawyer_2.id
    if (data.execution_lawyer && data.execution_lawyer.id)
      formData.execution_lawyer_id = data.execution_lawyer.id
    if (data.execution_assistant && data.execution_assistant.id)
      formData.execution_assistant_id = data.execution_assistant.id

    // 填充银行案件数据
    if (data.case_category === '银行案件' && data.bank_case_details) {
      const backendDetails = data.bank_case_details
      Object.keys(initialBankDetails).forEach((key) => {
        const val = backendDetails[key]
        if (val !== undefined && val !== null) {
          // 如果模板定义这是个数字，而后端给了字符串，强转成 Number
          if (
            typeof initialBankDetails[key] === 'number' &&
            typeof val === 'string' &&
            !isNaN(Number(val))
          ) {
            formData.bank_case_details[key] = Number(val)
          } else {
            formData.bank_case_details[key] = val
          }
        } else {
          formData.bank_case_details[key] = initialBankDetails[key] // 后端没传则用默认值
        }
      })
    } else {
      formData.bank_case_details = JSON.parse(JSON.stringify(initialBankDetails))
    }

    // 如果是复用模式，剥离不该复制的信息
    if (props.cloneId && !props.caseId) {
      formData.attachments = [] // 不带旧附件过来
      formData.case_code = null // 法院案号不能重复
      // 可按需在这里把想要置空的内容重置：例如 closing_status = null 等
    } else {
      // 只有正常编辑，才去拉取旧附件
      await loadFormAttachments(targetId)
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('加载业务数据失败')
  }
}

const downloadFormAttachment = async (attachmentId) => {
  try {
    ElMessage.info('正在获取文件...')
    // 使用带有 Token 的 request 去请求文件流
    const res = await request.get(`/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    })

    // 从 headers 中尝试提取文件名 (如果后端设置了 Content-Disposition)
    // 也可以直接在前端找对应附件列表里的名字
    const attachmentInfo = formData.attachments.find((item) => item.uid === attachmentId)
    const fileName = attachmentInfo ? attachmentInfo.name : '附件下载'

    // 创建 blob 下载链接
    const blob = new Blob([res.data]) // 注意 mimetype 根据实际情况可能需要补充
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName // 设定下载的文件名
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (err) {
    console.error('下载失败', err)
    ElMessage.error('附件下载失败')
  }
}

const deleteFormAttachment = async (attachmentId) => {
  try {
    await ElMessageBox.confirm('确定要永久删除该附件吗？', '提示', {
      type: 'warning',
    })
    await request.delete(`/attachments/${attachmentId}`)
    ElMessage.success('附件删除成功')
    formData.attachments = formData.attachments.filter((item) => item.uid !== attachmentId)
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除附件失败')
  }
}

const loadFormAttachments = async (caseId) => {
  try {
    const res = await request.get(`/attachments/case/${caseId}`)
    formData.attachments = res.data.map((item) => ({
      name: item.file_name,
      uid: item.attachment_id,
      url: `/attachments/${item.attachment_id}/download`,
    }))
  } catch (err) {
    console.error('加载附件失败:', err)
  }
}

// 辅助函数：添加空当事人
const addEmptyParty = (arr, type) => {
  arr.push({
    party_type: type,
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}

// 优化侦听器，覆盖 cloneId 分支
watch(
  () => props.visible,
  (val) => {
    if (val) {
      validationErrorCount.value = 0
      fetchLawyers()
      if (props.caseId) {
        // 编辑模式
        fetchCaseDetail(props.caseId)
      } else if (props.cloneId) {
        // 复用模式
        if (formRef.value) formRef.value.clearValidate()
        rawFiles.value = [] // 清除旧的待上传文件
        fetchCaseDetail(props.cloneId)
      } else {
        // 纯新增模式
        // 清除表单校验错误提示
        if (formRef.value) formRef.value.clearValidate()

        // 重置所有状态，使用完整的初始数据对象覆盖
        Object.assign(formData, getInitialFormData())

        // 新增时默认添加一位委托人
        addEmptyParty(formData.party_clients, '委托人')

        if (props.currentUserId) {
          formData.main_lawyer_id = Number(props.currentUserId)
        }
        rawFiles.value = []
      }
    }
  },
)

const handleCancel = () => {
  emit('update:visible', false)
  formRef.value?.clearValidate()
  rawFiles.value = []
  validationErrorCount.value = 0
}

const handleSubmit = async () => {
  if (!formRef.value) return
  // 点击提交时先清空上次的错误计数，等待新一次校验结果
  validationErrorCount.value = 0
  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (formData.party_clients.length === 0) {
        ElMessage.error('请至少添加一位委托人')
        return
      }
      if (formData.case_category === '银行案件') {
        // 校验原告
        if (formData.party_plaintiffs.length === 0) {
          ElMessage.error('请至少添加一位原告/申请人')
          loading.value = false
          return
        }
        // 校验被告
        if (formData.party_defendants.length === 0) {
          ElMessage.error('请至少添加一位被告/被申请人')
          loading.value = false
          return
        }
        // 校验借款人
        if (formData.party_bank_borrowers.length === 0) {
          ElMessage.error('请至少添加一位借款人')
          loading.value = false
          return
        }
      }

      loading.value = true
      try {
        const submitData = JSON.parse(JSON.stringify(formData))

        // 清理非本业务类型的数据
        if (submitData.case_category !== '银行案件') {
          submitData.bank_case_details = null
          // 如果是非银行案件，确保不提交借款人/担保人数组(虽然合并逻辑在下面，但清理一下是个好习惯)
          submitData.party_bank_borrowers = []
          submitData.party_bank_guarantors = []
        }

        // ================== 合并当事人数据 ==================
        let finalParties = [
          ...formData.party_clients,
          ...formData.party_third_parties,
          ...formData.party_others,
        ]

        if (formData.case_category === '银行案件') {
          // 银行案件：合并 原告 + 被告 + 借款人 + 担保人 到 parties 数组
          finalParties = [
            ...finalParties,
            ...formData.party_plaintiffs,
            ...formData.party_defendants,
            ...formData.party_bank_borrowers,
            ...formData.party_bank_guarantors,
          ]
        } else {
          // 通用案件：合并 原告 + 被告
          finalParties = [
            ...finalParties,
            ...formData.party_plaintiffs,
            ...formData.party_defendants,
          ]
        }

        submitData.parties = finalParties

        // 移除前端临时数组和附件字段
        delete submitData.party_clients
        delete submitData.party_plaintiffs
        delete submitData.party_defendants
        delete submitData.party_third_parties
        delete submitData.party_others
        delete submitData.party_bank_borrowers
        delete submitData.party_bank_guarantors
        delete submitData.attachments

        // ================== 利益冲突检测 ==================
        try {
          const conflictRes = await request.post('/cases/check_conflict', submitData)

          if (conflictRes.data.has_conflict) {
            const detailsHtml = conflictRes.data.details
              .map((item, index) => {
                // 判断是否为模糊匹配
                const isFuzzy = item.match_level === 'fuzzy'
                // 模糊匹配用橙黄色(Warning)，确切匹配用红色(Danger)
                const themeColor = isFuzzy ? '#E6A23C' : '#f56c6c'
                const bgColor = isFuzzy ? '#fdf6ec' : '#fef0f0'
                const borderColor = isFuzzy ? '#faecd8' : '#fde2e2'
                const tagText = isFuzzy ? '疑似冲突' : '匹配冲突'

                return `
                <div style="margin-bottom: 10px; padding: 10px; background-color: ${bgColor}; border-radius: 4px; border: 1px solid ${borderColor};">
                  <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: ${themeColor};">${index + 1}. ${item.conflict_type}</span>
                    <span style="font-size: 12px; color: ${themeColor}; border: 1px solid ${themeColor}; padding: 1px 6px; border-radius: 10px; background-color: #ffffff;">
                      ${tagText}
                    </span>
                  </div>
                  <div style="font-size: 13px; margin-bottom: 6px; color: #303133; line-height: 1.4;">${item.message}</div>
                  <div style="font-size: 12px; color: #909399;">
                    冲突案件: <span style="color: #606266; font-weight: bold;">${item.case_number}</span> | 承办律师: ${item.other_lawyer_name}
                  </div>
                </div>
              `
              })
              .join('')

            const warningHtml = `
              <div style="text-align: left;">
                <p style="font-size: 14px; margin-bottom: 10px;">
                  系统检测到 <strong>${conflictRes.data.details.length}</strong> 项潜在的利益冲突风险：
                </p>
                <div style="max-height: 300px; overflow-y: auto;">
                  ${detailsHtml}
                </div>
                <p style="margin-top: 10px; color: #E6A23C;">是否确认忽略风险并强制提交？</p>
              </div>
            `

            await ElMessageBox.confirm(warningHtml, '可能存在利益冲突', {
              dangerouslyUseHTMLString: true,
              confirmButtonText: '强制提交',
              cancelButtonText: '取消提交',
              confirmButtonClass: 'el-button--danger',
              type: 'warning',
              closeOnClickModal: false,
              width: '600px',
            })
          }
        } catch (conflictErr) {
          if (conflictErr === 'cancel') {
            loading.value = false
            return
          }
          console.error('利益冲突检测服务异常', conflictErr)
        }

        // ================== 提交保存 ==================
        let res
        let targetCaseId
        // ✅ 只有明确传了 caseId 才是更新，复用由于 caseId 为空会走新建逻辑
        if (props.caseId) {
          res = await request.put(`/cases/case_update/${props.caseId}`, submitData)
          targetCaseId = props.caseId
          ElMessage.success('更新成功')
        } else {
          res = await request.post('/cases/case_create', submitData)
          targetCaseId = res.data.case_id
          ElMessage.success(props.cloneId ? '复用创建成功' : '创建成功') // 顺手优化下提示文案
        }

        // ================== 附件上传 ==================
        if (rawFiles.value.length > 0 && targetCaseId) {
          const uploadPromises = rawFiles.value.map((fileItem) => {
            const fd = new FormData()
            const file = fileItem.raw || fileItem
            fd.append('file', file)
            fd.append('case_id', targetCaseId) // ✅ 如果是复用生成的，这里会把暂存区的附件挂载到新业务下

            return request.post('/attachments/', fd, {
              headers: { 'Content-Type': 'multipart/form-data' },
            })
          })

          try {
            await Promise.all(uploadPromises)
            ElMessage.success(`成功上传 ${rawFiles.value.length} 个附件`)
          } catch (uploadErr) {
            console.error('部分附件上传失败', uploadErr)
            ElMessage.warning('业务已保存，但部分附件上传失败，请检查')
          }
        }

        emit('submit')
        handleCancel()
      } catch (err) {
        console.error(err)
        ElMessage.error('提交失败: ' + (err.response?.data?.detail || err.message))
      } finally {
        loading.value = false
      }
    } else {
      // 校验失败：统计错误项并滚动到第一个错误字段
      nextTick(() => {
        const errorEls = formRef.value?.$el?.querySelectorAll('.is-error')
        validationErrorCount.value = errorEls.length
        if (errorEls.length > 0) {
          errorEls[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      })
    }
  })
}
</script>

<style scoped>
/* 继承原有的样式 */
:deep(.el-divider__text) {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
}

/* 校验错误提示徽章 */
.error-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #f56c6c;
  font-size: 13px;
  font-weight: 500;
  margin-right: 16px;
  cursor: pointer;
  user-select: none;
}
.error-badge .el-icon {
  font-size: 15px;
}

/* 添加针对移动端弹窗的兜底样式 */
@media screen and (max-width: 768px) {
  .custom-dialog {
    margin: 0 auto !important;
  }
  .error-badge {
    margin-right: 0;
    margin-bottom: 8px;
    width: 100%;
    justify-content: center;
  }
}
</style>
