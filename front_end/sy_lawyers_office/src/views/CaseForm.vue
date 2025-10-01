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
          <el-option label="刑事案件" value="刑事案件"/>
          <el-option label="行政案件" value="行政案件"/>
          <el-option label="仲裁案件" value="仲裁案件"/>
          <el-option label="非诉案件" value="非诉案件"/>
          <el-option label="法律顾问业务" value="法律顾问业务"/>
        </el-select>
      </el-form-item>

      <el-form-item label="委托日期" prop="commission_date">
        <el-date-picker v-model="formData.commission_date" type="date" placeholder="选择日期"/>
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
      <el-form-item label="是否银行案件">
        <el-switch v-model="formData.is_bank_case"/>
      </el-form-item>

      <el-form-item label="案件来源">
        <el-input v-model="formData.case_source" placeholder="请输入案件来源（如客户介绍、线上咨询等）"/>
      </el-form-item>

      <el-form-item label="收费方式">
        <el-input v-model="formData.fee_method" placeholder="请输入收费方式（如固定收费、风险代理等）"/>
      </el-form-item>

      <el-form-item label="风险比例">
        <el-input v-model="formData.risk_ratio" placeholder="如10%"/>
      </el-form-item>

      <el-form-item label="案件收入" prop="case_income">
        <el-input v-model.number="formData.case_income" type="number" placeholder="请输入金额"/>
      </el-form-item>

      <el-form-item label="付款到期日">
        <el-date-picker v-model="formData.payment_due_date" type="date"/>
      </el-form-item>

      <!-- 3. 案件主体信息 -->
      <el-form-item label="案由" prop="cause">
        <el-input type="textarea" v-model="formData.cause" placeholder="请输入案由"/>
      </el-form-item>

      <el-form-item label="介入阶段">
        <el-input v-model="formData.stage" placeholder="如一审、二审、执行阶段等"/>
      </el-form-item>

      <el-form-item label="原告/申请人">
        <el-input v-model="formData.plaintiff" placeholder="请输入原告或申请人信息"/>
      </el-form-item>

      <el-form-item label="上诉人/第三人信息">
        <el-input type="textarea" v-model="formData.appellant_info" placeholder="请输入上诉人或第三人信息"/>
      </el-form-item>

      <el-form-item label="补充上诉人/补告">
        <el-input type="textarea" v-model="formData.extra_appellant_info" placeholder="请输入补充上诉人信息"/>
      </el-form-item>

      <el-form-item label="被告">
        <el-input v-model="formData.defendant" placeholder="请输入被告信息"/>
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
        <el-date-picker v-model="formData.hearing_date" type="date"/>
      </el-form-item>

      <el-form-item label="立案日">
        <el-date-picker v-model="formData.filing_date" type="date"/>
      </el-form-item>

      <el-form-item label="结案时间">
        <el-date-picker v-model="formData.closing_date" type="date"/>
      </el-form-item>

      <!-- 5. 律师分配 -->
      <el-form-item label="主办律师" prop="main_lawyer_id">
        <el-select v-model="formData.main_lawyer_id" placeholder="请选择主办律师">
          <el-option v-for="lawyer in lawyers" :key="lawyer.id" :label="lawyer.real_name" :value="lawyer.id"/>
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
        <el-date-picker v-model="formData.preservation_start" type="date"/>
      </el-form-item>

      <el-form-item
        label="保全终止日"
        v-if="formData.has_preservation"
      >
        <el-date-picker v-model="formData.preservation_end" type="date"/>
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
        <el-date-picker v-model="formData.litigation_fee_payment_date" type="date"/>
      </el-form-item>

      <el-form-item label="诉讼费缴费金额">
        <el-input v-model.number="formData.litigation_fee_payment_amount" type="number"/>
      </el-form-item>

      <el-form-item label="诉讼费退费时间">
        <el-date-picker v-model="formData.litigation_fee_refund_date" type="date"/>
      </el-form-item>

      <el-form-item label="诉讼费退费金额">
        <el-input v-model.number="formData.litigation_fee_refund_amount" type="number"/>
      </el-form-item>

      <!-- 10. 执行相关 -->
      <el-form-item label="申请执行日">
        <el-date-picker v-model="formData.execution_application_date" type="date"/>
      </el-form-item>

      <el-form-item label="调解到期日">
        <el-date-picker v-model="formData.mediation_due_date" type="date"/>
      </el-form-item>

      <el-form-item label="执行到期日">
        <el-date-picker v-model="formData.execution_due_date" type="date"/>
      </el-form-item>

      <el-form-item label="案件详情">
        <el-input type="textarea" v-model="formData.details" placeholder="请输入案件详细描述"/>
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
  }
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

// 表单数据
const formData = reactive({
  // 初始化默认值（避免undefined）
  case_category: '',
  commission_date: '',
  client_name: '',
  client_id_number: '',
  client_phone: '',
  is_bank_case: false,
  case_source: '',
  fee_method: '',
  risk_ratio: '',
  case_income: 0,
  payment_due_date: '',
  cause: '',
  stage: '',
  plaintiff: '',
  appellant_info: '',
  extra_appellant_info: '',
  defendant: '',
  agency_power: '',
  court: '',
  hearing_date: '',
  filing_date: '',
  closing_date: '',
  main_lawyer_id: '',
  assistant_lawyer_id: '',
  execution_lawyer_id: '',
  execution_assistant_id: '',
  is_major: false,
  has_paper_file: false,
  is_dismissed: false,
  has_record: false,
  has_preservation: false,
  preservation_start: '',
  preservation_end: '',
  case_code: '',
  closing_status: '',
  closing_method: '',
  litigation_fee_payment_date: '',
  litigation_fee_payment_amount: 0,
  litigation_fee_refund_date: '',
  litigation_fee_refund_amount: 0,
  execution_application_date: '',
  mediation_due_date: '',
  execution_due_date: '',
  details: ''
})
// 保全状态切换时的处理逻辑
const handlePreservationChange = (val) => {
  if (!val) {
    // 如果关闭保全，清空日期
    formData.preservation_start = ''
    formData.preservation_end = ''
  }
}

// 3. 表单验证规则（确保数据合法性）
const formRules = reactive({
  case_category: [{ required: true, message: '请选择案件类别', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入委托人姓名', trigger: 'blur' }],
  client_id_number: [{ required: true, message: '请输入委托人身份证/税号', trigger: 'blur' }],
  client_phone: [
    { required: true, message: '请输入委托人电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  case_income: [{ required: true, message: '请输入案件收入', trigger: 'blur' }],
  cause: [{ required: true, message: '请输入案由', trigger: 'blur' }],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
  agency_power: [{ required: true, message: '请选择代理权限', trigger: 'change' }]
})

// 4. 监听initialFormData变化（编辑时加载案件数据）

watch(
  () => props.initialFormData,
  (newVal) => {
    if (newVal && props.mode === 'edit') {
      Object.assign(formData, JSON.parse(JSON.stringify(newVal)))
    }
  },
  { immediate: true, deep: true }
)


// 5. 事件：向父组件传递操作结果
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
    // 传递表单数据给父组件（深拷贝，避免引用问题）
    emit('submit', JSON.parse(JSON.stringify(formData)))
    emit('update:visible', false) // 提交成功后关闭弹窗
  }
}

</script>
