<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    width="1000px"
    destroy-on-close
    @close="handleCancel"
    top="5vh"
    class="custom-dialog"
  >
    <el-form :model="formData" :rules="formRules" ref="formRef" label-width="160px">
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
          <el-option label="仲裁案件" value="仲裁案件" />
          <el-option label="非诉业务" value="非诉业务" />
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
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit"> 确定 </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, provide } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

// 引入拆分后的子组件
import GeneralCaseForm from '@/views/GeneralCaseForm.vue'
import BankCaseForm from './BankCaseForm.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  caseId: { type: [Number, String], default: null },
  currentUserId: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const dialogTitle = computed(() => (props.caseId ? '编辑业务' : '新增业务'))
const loading = ref(false)
const formRef = ref(null)
const rawFiles = ref([])
const lawyerOptions = ref([])

// 定义银行案件初始详情数据
const initialBankDetails = {
  branch_name: null,
  is_inclusive_finance: false,
  account_manager: null,
  loan_principal: 0,
  litigation_target_amount: 0,
  credit_card_penalty: 0,
  loan_date: null,
  loan_due_date: null,
  overdue_date: null,
  statute_of_limitations: null,
  material_fetcher: null,
  pre_litigation_collection: null,
  seal_date: null,
  material_submission_date: null,
  judgment_summary: null,
  lawyer_fee_supported: 0,
  defendant_paid_lawyer_fee: 0,
  is_settled: false,
  execution_case_number: null,
  execution_filing_date: null,
  execution_judge: null,
  borrower_work_unit: null,
  is_execution_recovery: false,
  execution_principal: 0,
  execution_lawyer_fee: 0,
  property_investigation: null,
  network_control_status: null,
  execution_plan: null,
  court_execution_measures: null,
  seizure_freeze_info: null,
  auction_status: null,
  auction_deal_price: 0,
  execution_settlement_content: null,
  procedure_termination_date: null,
  termination_reason: null,
  execution_conclusion_date: null,
  execution_recovery_date: null,
  payoff_date: null,
  execution_collection_amount: 0,
  collection_source: null,
  mediation_tracking: null,
  // 注意：原有的 guarantor, borrower_id_number 等单行字段已废弃，改用 party_bank_borrowers 等数组
}

// 统一的大表单数据对象
const formData = reactive({
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

  // 旧字段保留（用于兼容，提交时填充）
  client_name: null,
  client_id_number: null,
  client_phone: null,

  case_source: null,
  stage: null,
  cause: null,

  // 律师
  main_lawyer_id: null,
  assistant_lawyer_id: null,
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

provide('caseFormData', formData)

const formRules = computed(() => {
  const isBankCase = formData.case_category === '银行案件'

  return {
    case_category: [{ required: true, message: '请选择业务类别', trigger: 'change' }],
    commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
    main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
    //  银行案件是非必填，其他案件必填
    cause: [{ required: !isBankCase, message: '请填写案由', trigger: 'blur' }],
    fee_method: [{ required: !isBankCase, message: '请填写收费方式', trigger: 'blur' }],
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
  }
}

// 加载律师列表
const fetchLawyers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8002/cases/users/lawyers')
    lawyerOptions.value = res.data
  } catch (e) {
    console.error('加载律师列表失败', e)
  }
}

// 获取详情并填充表单
const fetchCaseDetail = async () => {
  if (!props.caseId) return
  try {
    const res = await axios.get(`http://127.0.0.1:8002/cases/${props.caseId}`)
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
        formData[key] = data[key]
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
      if (data.client_name) {
        // 尝试拆分旧的逗号分隔字符串
        const clients = data.client_name.split(/[,，、]/).filter((s) => s)
        clients.forEach((c, idx) => {
          formData.party_clients.push({
            party_type: '委托人',
            name: c,
            phone: idx === 0 ? data.client_phone : '', // 仅第一个填充电话
            id_number: idx === 0 ? data.client_id_number : '',
            address: '',
          })
        })
      }
      if (data.plaintiff) {
        const plaintiffs = data.plaintiff.split(/[,，、]/).filter((s) => s)
        plaintiffs.forEach((p) => {
          formData.party_plaintiffs.push({ party_type: '原告', name: p })
        })
      }
      if (data.defendant) {
        const defendants = data.defendant.split(/[,，、]/).filter((s) => s)
        defendants.forEach((d) => {
          formData.party_defendants.push({ party_type: '被告', name: d })
        })
      }
      if (data.third_party) {
        const thirdParties = data.third_party.split(/[,，、]/).filter((s) => s)
        thirdParties.forEach((t) => {
          formData.party_third_parties.push({ party_type: '第三人', name: t })
        })
      }
    }

    // 律师映射
    if (data.main_lawyer && data.main_lawyer.id) formData.main_lawyer_id = data.main_lawyer.id
    if (data.assistant_lawyer && data.assistant_lawyer.id)
      formData.assistant_lawyer_id = data.assistant_lawyer.id
    if (data.execution_lawyer && data.execution_lawyer.id)
      formData.execution_lawyer_id = data.execution_lawyer.id
    if (data.execution_assistant && data.execution_assistant.id)
      formData.execution_assistant_id = data.execution_assistant.id

    // 填充银行案件数据
    if (data.case_category === '银行案件' && data.bank_case_details) {
      formData.bank_case_details = { ...initialBankDetails, ...data.bank_case_details }
    } else {
      formData.bank_case_details = JSON.parse(JSON.stringify(initialBankDetails))
    }

    await loadFormAttachments(props.caseId)
  } catch (err) {
    console.error(err)
    ElMessage.error('加载业务数据失败')
  }
}

const downloadFormAttachment = (attachmentId) => {
  window.open(`http://127.0.0.1:8002/attachments/${attachmentId}/download`, '_blank')
}

const deleteFormAttachment = async (attachmentId) => {
  try {
    await ElMessageBox.confirm('确定要永久删除该附件吗？', '提示', {
      type: 'warning',
    })
    await axios.delete(`http://127.0.0.1:8002/attachments/${attachmentId}`)
    ElMessage.success('附件删除成功')
    formData.attachments = formData.attachments.filter((item) => item.uid !== attachmentId)
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除附件失败')
  }
}

const loadFormAttachments = async (caseId) => {
  try {
    const res = await axios.get(`http://127.0.0.1:8002/attachments/case/${caseId}`)
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

watch(
  () => props.visible,
  (val) => {
    if (val) {
      fetchLawyers()
      if (props.caseId) {
        fetchCaseDetail()
      } else {
        if (formRef.value) formRef.value.resetFields()
        // 重置所有状态
        Object.assign(formData, {
          case_category: '民事案件',
          case_code: null,
          commission_date: null,
          main_lawyer_id: null,
          assistant_lawyer_id: null,
          execution_lawyer_id: null,
          execution_assistant_id: null,
          bank_case_details: JSON.parse(JSON.stringify(initialBankDetails)),
          attachments: [],
          party_clients: [],
          party_plaintiffs: [],
          party_defendants: [],
          party_third_parties: [],
          party_bank_borrowers: [],
          party_bank_guarantors: [],
          party_others: [],
        })

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
  formRef.value?.resetFields()
  rawFiles.value = []
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (formData.party_clients.length === 0) {
        ElMessage.error('请至少添加一位委托人')
        return
      }

      loading.value = true
      try {
        const submitData = JSON.parse(JSON.stringify(formData))

        // 兼容旧字段 logic
        if (submitData.party_clients && submitData.party_clients.length > 0) {
          const firstClient = submitData.party_clients[0]
          submitData.client_name = firstClient.name || ''
          submitData.client_phone = firstClient.phone || ''
          submitData.client_id_number = firstClient.id_number || ''
        } else {
          submitData.client_name = ''
        }

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
          const conflictRes = await axios.post(
            'http://127.0.0.1:8002/cases/check_conflict',
            submitData,
          )

          if (conflictRes.data.has_conflict) {
            const detailsHtml = conflictRes.data.details
              .map(
                (item, index) => `
              <div style="margin-bottom: 10px; padding: 8px; background-color: #fef0f0; border-radius: 4px; border: 1px solid #fde2e2;">
                <div style="font-weight: bold; color: #f56c6c;">${index + 1}. ${item.conflict_type}</div>
                <div style="font-size: 13px; margin: 4px 0;">${item.message}</div>
                <div style="font-size: 12px; color: #909399;">
                  冲突案件: ${item.case_number} | 承办律师: ${item.other_lawyer_name}
                </div>
              </div>
            `,
              )
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
        if (props.caseId) {
          res = await axios.put(
            `http://127.0.0.1:8002/cases/case_update/${props.caseId}`,
            submitData,
          )
          targetCaseId = props.caseId
          ElMessage.success('更新成功')
        } else {
          res = await axios.post('http://127.0.0.1:8002/cases/case_create', submitData)
          targetCaseId = res.data.case_id
          ElMessage.success('创建成功')
        }

        // ================== 附件上传 ==================
        if (rawFiles.value.length > 0 && targetCaseId) {
          const uploadPromises = rawFiles.value.map((fileItem) => {
            const fd = new FormData()
            const file = fileItem.raw || fileItem
            fd.append('file', file)
            fd.append('case_id', targetCaseId)
            fd.append('uploaded_by', props.currentUserId || 1)

            return axios.post('http://127.0.0.1:8002/attachments/', fd, {
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
</style>
