<template>
  <el-form :model="formData" :rules="formRules" ref="formRef" label-width="140px">
    <el-divider content-position="left">银行案件 - 借贷基础信息</el-divider>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="支行名称" prop="bank_case_details.branch_name">
          <el-input
            v-model="formData.bank_case_details.branch_name"
            placeholder="例如：xx银行xx支行"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="客户经理" prop="bank_case_details.account_manager">
          <el-input v-model="formData.bank_case_details.account_manager" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="借款人证件号" prop="bank_case_details.borrower_id_number">
          <el-input v-model="formData.bank_case_details.borrower_id_number" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="是否普惠金融" prop="bank_case_details.is_inclusive_finance">
          <el-switch v-model="formData.bank_case_details.is_inclusive_finance" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">被告(借款人/担保人)</el-divider>
    <div class="party-section">
      <div class="party-section-header">
        <el-button type="warning" plain size="small" :icon="Plus" @click="addDefendant"
          >添加被告</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_defendants" :key="'def_' + index">
        <div class="party-card defendant-card">
          <div class="party-card-header">
            <span>被告 #{{ index + 1 }}</span>
            <el-button link type="danger" size="small" @click="removeDefendant(index)"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="8"
                ><el-form-item label="姓名"><el-input v-model="item.name" /></el-form-item
              ></el-col>
              <el-col :span="8"
                ><el-form-item label="电话"><el-input v-model="item.phone" /></el-form-item
              ></el-col>
              <el-col :span="8"
                ><el-form-item label="证件号"><el-input v-model="item.id_number" /></el-form-item
              ></el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_defendants.length === 0" class="empty-tip">暂无被告信息</div>
    </div>

    <el-divider content-position="left">金额与期限</el-divider>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="贷款本金" prop="bank_case_details.loan_principal">
          <el-input-number
            v-model="formData.bank_case_details.loan_principal"
            :precision="2"
            :step="10000"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="诉讼标的" prop="bank_case_details.litigation_target_amount">
          <el-input-number
            v-model="formData.bank_case_details.litigation_target_amount"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="信用卡违约金" prop="bank_case_details.credit_card_penalty">
          <el-input-number
            v-model="formData.bank_case_details.credit_card_penalty"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="借款日" prop="bank_case_details.loan_date">
          <el-date-picker
            v-model="formData.bank_case_details.loan_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="到期日" prop="bank_case_details.loan_due_date">
          <el-date-picker
            v-model="formData.bank_case_details.loan_due_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="逾期时间" prop="bank_case_details.overdue_date">
          <el-date-picker
            v-model="formData.bank_case_details.overdue_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="抵/质押物信息" prop="bank_case_details.collateral_info">
      <el-input type="textarea" v-model="formData.bank_case_details.collateral_info" />
    </el-form-item>
    <el-form-item label="抵押物位置" prop="bank_case_details.collateral_location">
      <el-input v-model="formData.bank_case_details.collateral_location" />
    </el-form-item>

    <el-divider content-position="left">管理信息</el-divider>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="主办律师" prop="main_lawyer_id">
          <el-select v-model="formData.main_lawyer_id" filterable style="width: 100%">
            <el-option v-for="l in lawyers" :key="l.id" :label="l.real_name" :value="l.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="委托日期" prop="commission_date">
          <el-date-picker
            v-model="formData.commission_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="form-footer-upload">
      <el-upload
        action="#"
        :auto-upload="false"
        multiple
        v-model:file-list="fileList"
        :on-change="handleFileChange"
      >
        <el-button type="primary" plain>点击上传案件材料</el-button>
      </el-upload>
    </div>

    <div class="form-actions" style="text-align: right; margin-top: 20px">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="submitForm">保存银行案件</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  initialData: { type: Object, default: () => ({}) },
  lawyers: { type: Array, default: () => [] },
  currentUserId: { type: [Number, String] },
})

const emit = defineEmits(['submit', 'cancel'])
const formRef = ref(null)
const fileList = ref([])

// 初始化数据
const formData = reactive({
  case_category: '银行案件',
  main_lawyer_id: null,
  commission_date: null,
  party_defendants: [],
  bank_case_details: {
    branch_name: '',
    loan_principal: 0,
    // ... 其他默认值
  },
})

// 数据回显
watch(
  () => props.initialData,
  (newVal) => {
    if (newVal && Object.keys(newVal).length > 0) {
      Object.assign(formData, JSON.parse(JSON.stringify(newVal)))
      if (!formData.bank_case_details) formData.bank_case_details = {}
      if (!formData.party_defendants) formData.party_defendants = []
    }
  },
  { immediate: true, deep: true },
)

const addDefendant = () => {
  formData.party_defendants.push({ party_type: '被告', name: '' })
}
const removeDefendant = (idx) => {
  formData.party_defendants.splice(idx, 1)
}

const handleFileChange = (file, files) => {
  fileList.value = files
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      const submitData = JSON.parse(JSON.stringify(formData))
      // 传递文件
      const rawFiles = fileList.value.map((f) => f.raw)
      submitData.filesToUpload = rawFiles
      emit('submit', submitData)
    }
  })
}

const formRules = {
  'bank_case_details.branch_name': [{ required: true, message: '请填写支行名称', trigger: 'blur' }],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
}
</script>

<style scoped>
/* 简单的卡片样式 */
.party-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 10px;
  padding: 10px;
}
.party-card-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed #eee;
  padding-bottom: 5px;
  margin-bottom: 10px;
}
</style>
