<!-- CaseForm.vue -->
<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    width="900px"
    destroy-on-close
    @close="emit('update:visible', false)"
  >
    <el-form
      :model="formData"
      :rules="formRules"
      ref="formRef"
      label-width="150px"
    >
      <!-- 1. 案件基础信息 -->
      <el-form-item label="案件类别" prop="case_category">
        <el-select v-model="formData.case_category" placeholder="请选择案件类别">
          <el-option label="民事案件" value="民事案件"/>
          <el-option label="银行案件" value="银行案件"/>
          <el-option label="刑事案件" value="刑事案件"/>
          <el-option label="行政案件" value="行政案件"/>
          <el-option label="仲裁案件" value="仲裁案件"/>
          <el-option label="非诉案件" value="非诉案件"/>
          <el-option label="法律顾问业务" value="法律顾问业务"/>
          <el-option label="法律援助" value="法律援助"/>
        </el-select>
      </el-form-item>

      <el-form-item label="委托日期" prop="commission_date">
        <el-date-picker v-model="formData.commission_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="委托人" prop="client_name">
        <el-input v-model="formData.client_name" placeholder="请输入委托人姓名"/>
      </el-form-item>

      <el-form-item label="委托人身份证/税号" prop="client_id_number">
        <el-input v-model="formData.client_id_number" placeholder="请输入身份证号或税号"/>
      </el-form-item>

      <el-form-item label="委托人电话" prop="client_phone">
        <el-input v-model="formData.client_phone" placeholder="请输入联系电话"/>
      </el-form-item>

      <!-- 2. 费用相关 -->
      <el-form-item label="案件来源">
        <el-input v-model="formData.case_source" placeholder="请输入案件来源（如客户介绍、线上咨询等）"/>
      </el-form-item>

      <el-form-item label="收费方式">
        <el-input v-model="formData.fee_method" placeholder="请输入收费方式（如固定收费、风险代理等）"/>
      </el-form-item>

      <el-form-item label="风险比例">
        <el-input v-model="formData.risk_ratio" placeholder="请输入风险比例"/>
      </el-form-item>

      <el-form-item label="案件收入" prop="case_income">
        <el-input v-model.number="formData.case_income" type="number" placeholder="请输入金额"/>
      </el-form-item>

      <el-form-item label="付款到期日">
        <el-date-picker v-model="formData.payment_due_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <!-- 3. 案件主体信息 -->
      <el-form-item label="案由" prop="cause">
        <el-input type="textarea" v-model="formData.cause" placeholder="请输入案由"/>
      </el-form-item>

      <el-form-item label="介入阶段">
        <el-input v-model="formData.stage" placeholder="如一审、二审、执行阶段等"/>
      </el-form-item>

      <el-form-item label="原告/申请人/侦察机关/检察院">
        <el-input type="textarea" v-model="formData.plaintiff" placeholder="请输入原告/申请人/侦察机关/检察院信息"/>
      </el-form-item>

      <el-form-item label="上诉人/第三人信息">
        <el-input type="textarea" v-model="formData.appellant_info" placeholder="请输入上诉人或第三人信息"/>
      </el-form-item>

      <el-form-item label="被上诉人">
        <el-input type="textarea" v-model="formData.extra_appellant_info" placeholder="请输入被上诉人信息"/>
      </el-form-item>

      <el-form-item label="被告（人）/被申请人">
        <el-input v-model="formData.defendant" placeholder="请输入被告（人）/被申请人信息"/>
      </el-form-item>

      <!-- 4. 代理与审理信息 -->
      <el-form-item label="代理权限" prop="agency_power">
        <el-select v-model="formData.agency_power" placeholder="请选择">
          <el-option label="特别代理" value="特别代理"/>
          <el-option label="一般代理" value="一般代理"/>
        </el-select>
      </el-form-item>

      <el-form-item label="审理法院">
        <el-input v-model="formData.court" placeholder="请输入审理法院名称"/>
      </el-form-item>

      <el-form-item label="开庭时间">
        <el-date-picker v-model="formData.hearing_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="立案日">
        <el-date-picker v-model="formData.filing_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="结案时间">
        <el-date-picker v-model="formData.closing_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <!-- 5. 律师分配 -->
      <el-form-item label="主办律师" prop="main_lawyer_id">
        <el-select
          v-model="formData.main_lawyer_id"
          placeholder="请选择主办律师"
        >
          <el-option
            v-for="lawyer in props.lawyers"
            :key="lawyer.id"
            :label="lawyer.real_name"
            :value="lawyer.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="助理律师">
        <el-select v-model="formData.assistant_lawyer_id" placeholder="请选择助理律师">
          <el-option v-for="lawyer in lawyers" :key="lawyer.id" :label="lawyer.real_name" :value="lawyer.id"/>
        </el-select>
      </el-form-item>

      <el-form-item label="执行主办律师">
        <el-select v-model="formData.execution_lawyer_id" placeholder="请选择执行主办律师">
          <el-option v-for="lawyer in lawyers" :key="lawyer.id" :label="lawyer.real_name" :value="lawyer.id"/>
        </el-select>
      </el-form-item>

      <el-form-item label="执行助理律师">
        <el-select v-model="formData.execution_assistant_id" placeholder="请选择执行助理律师">
          <el-option v-for="lawyer in lawyers" :key="lawyer.id" :label="lawyer.real_name" :value="lawyer.id"/>
        </el-select>
      </el-form-item>

      <!-- 6. 其他配置 -->
      <el-form-item label="是否重大">
        <el-switch v-model="formData.is_major"/>
      </el-form-item>

      <el-form-item label="是否纸质卷宗">
        <el-switch v-model="formData.has_paper_file"/>
      </el-form-item>

      <el-form-item label="是否解除">
        <el-switch v-model="formData.is_dismissed"/>
      </el-form-item>

      <el-form-item label="是否笔录">
        <el-switch v-model="formData.has_record"/>
      </el-form-item>

      <!-- 7. 保全相关 -->
      <el-form-item label="是否保全">
        <el-switch v-model="formData.has_preservation" @change="handlePreservationChange"/>
      </el-form-item>

      <el-form-item
        label="保全开始日"
        v-if="formData.has_preservation"
      >
        <el-date-picker v-model="formData.preservation_start" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item
        label="保全终止日"
        v-if="formData.has_preservation"
      >
        <el-date-picker v-model="formData.preservation_end" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <!-- 8. 结案与执行 -->
      <el-form-item label="案号">
        <el-input v-model="formData.case_code" placeholder="请输入法院案号"/>
      </el-form-item>

      <el-form-item label="结案状态">
        <el-input v-model="formData.closing_status" placeholder="如已结案、审理中、中止等"/>
      </el-form-item>

      <el-form-item label="结案方式">
        <el-input v-model="formData.closing_method" placeholder="如判决、调解、撤诉等"/>
      </el-form-item>

      <!-- 9. 诉讼费相关 -->
      <el-form-item label="诉讼费缴费时间">
        <el-date-picker v-model="formData.litigation_fee_payment_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="诉讼费缴费金额">
        <el-input v-model.number="formData.litigation_fee_payment_amount" type="number"/>
      </el-form-item>

      <el-form-item label="诉讼费退费时间">
        <el-date-picker v-model="formData.litigation_fee_refund_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="诉讼费退费金额">
        <el-input v-model.number="formData.litigation_fee_refund_amount" type="number"/>
      </el-form-item>

      <!-- 10. 执行相关 -->
      <el-form-item label="申请执行日">
        <el-date-picker v-model="formData.execution_application_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="调解到期日">
        <el-date-picker v-model="formData.mediation_due_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="执行到期日">
        <el-date-picker v-model="formData.execution_due_date" type="date" value-format="YYYY-MM-DD"/>
      </el-form-item>

      <el-form-item label="案件详情">
        <el-input type="textarea" v-model="formData.details" placeholder="请输入案件详细描述"/>
      </el-form-item>

      <!-- 11. 附件上传区域 -->
      <el-form-item label="案件附件">
        <template v-if="props.mode === 'add'">
          <div class="upload-tip">请先新增案件再去编辑界面上传附件</div>
        </template>
        <template v-else>
          <el-upload
            class="upload-demo"
            :action="`http://127.0.0.1:8002/attachments/?case_id=${props.caseId}&uploaded_by=${props.currentUserId}`"
            :on-success="handleAttachmentUpload"
            :on-error="handleAttachmentError"
            :file-list="formData.attachments || []"
            :auto-upload="true"
          >
            <el-button size="small" type="primary">
              <el-icon><Upload /></el-icon> 上传附件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持上传多种格式文件
              </div>
            </template>
          </el-upload>

          <el-table
            v-if="formData.attachments && formData.attachments.length > 0"
            :data="formData.attachments"
            border
            style="width: 100%; margin-top: 10px"
          >
            <el-table-column prop="name" label="文件名" />
            <el-table-column label="操作">
              <template #default="scope">
                <el-button
                  size="small"
                  @click="downloadFormAttachment(scope.row.uid)"
                >
                  下载
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteFormAttachment(scope.row.uid)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </el-form-item>
    </el-form>

    <!-- 底部按钮（通过slot让父组件控制，保持弹窗按钮一致性） -->
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 1. Props：接收父组件传递的数据
const props = defineProps({
  // 接收父组件的弹窗显示状态（v-model 绑定）
  visible: {
    type: Boolean,
    required: true,
    default: false
  },
  // 律师列表（新增/编辑都需要）
  lawyers: {
    type: Array,
    required: true,
    default: () => []
  },
  // 表单初始值（编辑时传入案件数据，新增时为空对象）
  initialFormData: {
    type: Object,
    required: false,
    default: () => ({})
  },
  // 表单模式（新增/编辑，用于差异化逻辑）
  mode: {
    type: String,
    required: true,
    validator: (value) => ['add', 'edit'].includes(value) // 仅允许add/edit两种值
  },
  currentUserId: [String, Number],
  currentUserRole: String,
  caseId: [String, Number]
})
// 使用本地响应式变量替代直接修改 prop
const dialogVisible = computed({
  get() {
    return props.visible
  },
  set(val) {
    emit('update:visible', val)
  }
})

// 2. 表单核心数据
const formRef = ref(null) // 表单引用，用于验证
// 计算属性：根据模式确定弹窗标题
const dialogTitle = computed(() => {
  return props.mode === 'add' ? '新增案件' : '编辑案件'
})
// 工具函数：获取当前日期（Date对象，时分秒设为0，适配el-date-picker的date类型）
const getCurrentDate = () => {
  const now = new Date()
  // 获取本地时区的年、月、日
  const year = now.getFullYear()
  // 月份从0开始，需要+1并补零
  const month = String(now.getMonth() + 1).padStart(2, '0')
  // 日期补零
  const day = String(now.getDate()).padStart(2, '0')

  // 返回YYYY-MM-DD格式的字符串
  return `${year}-${month}-${day}`
}
// 表单数据
const defaultFormData = {
  // 初始化默认值（避免undefined）
  case_category: "",
  commission_date: getCurrentDate(),
  client_name: "",
  client_id_number: "",
  client_phone: "",
  case_source: "",
  fee_method: "",
  risk_ratio: "",
  case_income: 0,
  payment_due_date: null,
  cause: "",
  stage: "",
  plaintiff: "",
  appellant_info: "",
  extra_appellant_info: "",
  defendant: "",
  agency_power: "",
  court: "",
  hearing_date: null,
  filing_date: null,
  closing_date: null,
  main_lawyer_id: Number(props.currentUserId),
  assistant_lawyer_id: null,
  execution_lawyer_id: null,
  execution_assistant_id: null,
  is_major: false,
  has_paper_file: false,
  is_dismissed: false,
  has_record: false,
  has_preservation: false,
  preservation_start: null,
  preservation_end: null,
  case_code: "",
  closing_status: "",
  closing_method: "",
  litigation_fee_payment_date: null,
  litigation_fee_payment_amount: 0,
  litigation_fee_refund_date: null,
  litigation_fee_refund_amount: 0,
  execution_application_date: null,
  mediation_due_date: null,
  execution_due_date: null,
  details: "",
  attachments: [] // 新增附件数组
}
const formData = reactive(defaultFormData)
// 保全状态切换时的处理逻辑
const handlePreservationChange = (val) => {
  if (!val) {
    // 如果关闭保全，清空日期
    formData.preservation_start = null
    formData.preservation_end = null
  }
}

// 3. 表单验证规则（确保数据合法性）
const formRules = reactive({
  case_category: [{ required: true, message: '请选择案件类别', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入委托人姓名', trigger: 'blur' }],
  client_id_number: [
    {
      required: false,  // 改为非必填
      message: '请输入委托人身份证号或税号',
      trigger: 'blur'
    },
    {
      // 自定义校验：非空时必须为18位字符
      validator: (rule, value, callback) => {
        // 1. 若未填写（value为空），直接通过校验
        if (!value) {
          return callback();
        }
        // 2. 若填写了，校验是否为18位字符（数字/字母均可，若需纯数字可加正则）
        const length = value.trim().length; // 去除空格后计算长度
        if (length === 18) {
          callback(); // 长度正确，通过校验
        } else {
          callback(new Error('身份证号/税号需为18位字符')); // 长度错误，抛出提示
        }
      },
      trigger: 'blur' // 失去焦点时触发校验
    }
  ],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
  commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
  plaintiff: [{ required: true, message: '请输入原告/申请人信息', trigger: 'blur' }]
})

// 4. 附件相关变量和方法
const formMode = ref(props.mode) // 表单模式

// 处理附件上传成功
const handleAttachmentUpload = async (response) => {
  ElMessage.success('附件上传成功')

  // 将上传的附件添加到表单列表
  formData.attachments.push({
    name: response.file_name,
    uid: response.attachment_id,
    url: `/attachments/${response.attachment_id}/download`
  })
}

// 处理附件上传失败
const handleAttachmentError = (err) => {
  console.error('附件上传失败:', err)
  ElMessage.error('附件上传失败')
}

// 下载表单中的附件
const downloadFormAttachment = (attachmentId) => {
  window.open(`http://127.0.0.1:8002/attachments/${attachmentId}/download`, '_blank')
}

// 删除表单中的附件
const deleteFormAttachment = async (attachmentId) => {
  if (!confirm('确定要删除该附件吗？')) return

  try {
    await axios.delete(`http://127.0.0.1:8002/attachments/${attachmentId}`)
    ElMessage.success('附件删除成功')

    // 从表单列表中移除
    formData.attachments = formData.attachments.filter(
      item => item.uid !== attachmentId
    )
  } catch (err) {
    console.error('删除附件失败:', err)
    ElMessage.error('删除附件失败')
  }
}

// 5. 监听initialFormData变化（编辑时加载案件数据）
watch(
  () => props.initialFormData,
  (newVal) => {
    if (newVal && props.mode === 'edit') {
      const copy = JSON.parse(JSON.stringify(newVal))
      // 将对象型字段转换为 ID
      copy.main_lawyer_id = copy.main_lawyer?.id || null
      copy.assistant_lawyer_id = copy.assistant_lawyer?.id || null
      copy.execution_lawyer_id = copy.execution_lawyer?.id || null
      copy.execution_assistant_id = copy.execution_assistant?.id || null

      Object.assign(formData, copy)

      // 加载该案件的附件
      if (copy.case_id) {
        loadFormAttachments(copy.case_id)
      }
    }
  },
  { immediate: true, deep: true }
)
watch(
  () => props.mode,
  (newMode) => {
    formMode.value = newMode
    if (newMode === 'add') {
      // 清空所有字段
      Object.keys(formData).forEach(key => (formData[key] = ""))
      // 重置布尔字段为 false
      const boolKeys = [
        'is_major',
        'has_record',
        'has_paper_file',
        'is_dismissed',
        'has_preservation',
      ]
      boolKeys.forEach(key => (formData[key] = false))

      formData.case_income = 0
      formData.litigation_fee_payment_amount = 0
      formData.litigation_fee_refund_amount = 0
      formData.commission_date = getCurrentDate()
      formData.attachments = [] // 清空附件列表

      // 主办律师默认为当前用户
      if (props.currentUserRole === 'user' || props.currentUserRole === 'admin') {
        formData.main_lawyer_id = Number(props.currentUserId)
      }
      // 重置其他律师ID和各日期为null
      const resetLawyerKeys = [
        'assistant_lawyer_id',
        'execution_lawyer_id',
        'execution_assistant_id'
      ]
      resetLawyerKeys.forEach(key => (formData[key] = null))

      const resetDateKeys = [
        'preservation_start',
        'preservation_end',
        'litigation_fee_payment_date',
        'litigation_fee_refund_date',
        'execution_application_date',
        'mediation_due_date',
        'execution_due_date',
        'closing_date',
        'filing_date',
        'hearing_date',
        'payment_due_date'
      ]
      resetDateKeys.forEach(key => (formData[key] = null))
    }
  }
)

// 加载表单中的附件列表
const loadFormAttachments = async (caseId) => {
  try {
    const res = await axios.get(`http://127.0.0.1:8002/attachments/case/${caseId}`)
    formData.attachments = res.data.map(item => ({
      name: item.file_name,
      uid: item.attachment_id,
      url: `/attachments/${item.attachment_id}/download`
    }))
  } catch (err) {
    console.error('加载附件失败:', err)
    ElMessage.error('加载附件失败')
  }
}

// 6. 事件：向父组件传递操作结果
const emit = defineEmits(['submit', 'update:visible'])

// 取消操作：通知父组件关闭弹窗
const handleCancel = () => {
  emit('update:visible', false)
  // 重置表单（避免下次打开有残留数据）
  formRef.value?.resetFields()
}

// 提交操作：先验证，再通知父组件
const handleSubmit = async () => {
  // 表单验证
  const valid = await formRef.value.validate()
  if (valid) {
    // 深拷贝避免引用问题
    const submitData = JSON.parse(JSON.stringify(formData));

    // 移除附件信息，因为附件是通过单独API上传的
    delete submitData.attachments;

    emit('submit', submitData);
    emit('update:visible', false); // 提交成功后关闭弹窗
  }
}

</script>
