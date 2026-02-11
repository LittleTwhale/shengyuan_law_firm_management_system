<template>
  <el-form :model="formData" :rules="formRules" ref="formRef" label-width="160px">
    <el-form-item label="业务类别" prop="case_category" v-if="false">
      <el-input v-model="formData.case_category" disabled />
    </el-form-item>

    <el-divider content-position="left">当事人信息</el-divider>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">委托人</span>
        <el-button type="primary" plain size="small" :icon="Plus" @click="addClient"
          >添加委托人</el-button
        >
      </div>

      <template v-for="(item, index) in formData.party_clients" :key="'client_' + index">
        <div class="party-card client-card">
          <div class="party-card-header">
            <span class="party-index-label">
              <el-icon><User /></el-icon> 委托人 #{{ index + 1 }}
            </span>
            <el-button link type="danger" :icon="Delete" size="small" @click="removeClient(index)">
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  :prop="'party_clients.' + index + '.name'"
                  :rules="{ required: true, message: '请输入委托人姓名', trigger: 'blur' }"
                  label-width="90px"
                >
                  <el-input v-model="item.name" placeholder="请输入姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="电话"
                  :prop="'party_clients.' + index + '.phone'"
                  :rules="{ required: true, message: '请输入联系电话', trigger: 'blur' }"
                  label-width="60px"
                >
                  <el-input v-model="item.phone" placeholder="联系电话" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="证件号"
                  :prop="'party_clients.' + index + '.id_number'"
                  :rules="{ required: true, message: '请输入身份证/税号', trigger: 'blur' }"
                  label-width="70px"
                >
                  <el-input v-model="item.id_number" placeholder="身份证号/税号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="50px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_clients.length === 0" class="empty-tip">
        <el-icon><Warning /></el-icon> 暂无委托人信息，请添加。
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">原告/申请人/上诉人</span>
        <el-button type="success" plain size="small" :icon="Plus" @click="addPlaintiff"
          >添加原告/申请人/上诉人</el-button
        >
      </div>

      <template v-for="(item, index) in formData.party_plaintiffs" :key="'plaintiff_' + index">
        <div class="party-card plaintiff-card">
          <div class="party-card-header">
            <span class="party-index-label"> 原告/申请人/上诉人 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removePlaintiff(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="5">
                <el-form-item
                  label="类型"
                  label-width="50px"
                  :prop="'party_plaintiffs.' + index + '.party_type'"
                  :rules="{ required: true, message: '必选', trigger: 'change' }"
                >
                  <el-select v-model="item.party_type">
                    <el-option label="原告" value="原告" />
                    <el-option label="申请人" value="申请人" />
                    <el-option label="上诉人" value="上诉人" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="50px"
                  :prop="'party_plaintiffs.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.name" placeholder="姓名/名称" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="50px">
                  <el-input v-model="item.phone" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="7">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="50px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_plaintiffs.length === 0" class="empty-tip-simple">
        暂无原告/申请人/上诉人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">被告/被告人/被申请人/被上诉人</span>
        <el-button type="warning" plain size="small" :icon="Plus" @click="addDefendant"
          >添加被告/被告人/被申请人/被上诉人</el-button
        >
      </div>

      <template v-for="(item, index) in formData.party_defendants" :key="'defendant_' + index">
        <div class="party-card defendant-card">
          <div class="party-card-header">
            <span class="party-index-label"> 被告/被告人/被申请人/被上诉人 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeDefendant(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="5">
                <el-form-item
                  label="类型"
                  label-width="50px"
                  :prop="'party_defendants.' + index + '.party_type'"
                  :rules="{ required: true, message: '必选', trigger: 'change' }"
                >
                  <el-select v-model="item.party_type">
                    <el-option label="被告" value="被告" />
                    <el-option label="被告人" value="被告人" />
                    <el-option label="被申请人" value="被申请人" />
                    <el-option label="被上诉人" value="被上诉人" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="50px"
                  :prop="'party_defendants.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.name" placeholder="姓名/名称" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="50px">
                  <el-input v-model="item.phone" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="7">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="50px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_defendants.length === 0" class="empty-tip-simple">
        暂无被告/被申请人/被上诉人信息
      </div>
    </div>

    <div class="party-section" v-if="formData.case_category !== '刑事案件'">
      <div class="party-section-header">
        <span class="section-title">第三人</span>
        <el-button color="#6d14d7" plain size="small" :icon="Plus" @click="addThirdParty">
          添加第三人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_third_parties" :key="'third_' + index">
        <div class="party-card third-party-card">
          <div class="party-card-header">
            <span class="party-index-label"> 第三人 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeThirdParty(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="5">
                <el-form-item label="类型" label-width="50px">
                  <el-input v-model="item.party_type" disabled />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="50px"
                  :prop="'party_third_parties.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.name" placeholder="姓名/名称" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="50px">
                  <el-input v-model="item.phone" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="7">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="50px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_third_parties.length === 0" class="empty-tip-simple">
        暂无第三人信息
      </div>
    </div>

    <el-divider content-position="left">通用信息</el-divider>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="委托日期" prop="commission_date">
          <el-date-picker
            v-model="formData.commission_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="业务来源" prop="case_source">
          <el-input v-model="formData.case_source" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="介入阶段" prop="stage">
          <el-input v-model="formData.stage" placeholder="如一审、二审、执行阶段等" />
        </el-form-item>
      </el-col>
      <el-col :span="24">
        <el-form-item label="案由" prop="cause">
          <el-input v-model="formData.cause" type="textarea" />
        </el-form-item>
      </el-col>

      <template v-if="formData.case_category === '刑事案件'">
        <el-col :span="12">
          <el-form-item label="侦查机关" prop="investigative_agency">
            <el-input v-model="formData.investigative_agency" placeholder="公安局/侦查部门" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="检察院" prop="procuratorate">
            <el-input v-model="formData.procuratorate" placeholder="提起公诉的检察院" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="二审检察机关" prop="second_instance_procuratorate">
            <el-input v-model="formData.second_instance_procuratorate" placeholder="二审检察机关" />
          </el-form-item>
        </el-col>
      </template>

      <el-col :span="12">
        <el-form-item label="案号" prop="case_code">
          <el-input v-model="formData.case_code" placeholder="请输入案号" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item :label="courtLabel" prop="court">
          <el-input v-model="formData.court" :placeholder="'请输入' + courtLabel" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="代理权限" prop="agency_power">
          <el-select v-model="formData.agency_power">
            <el-option label="特别代理" value="特别代理" />
            <el-option label="一般代理" value="一般代理" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="开庭时间" prop="hearing_date">
          <el-date-picker
            v-model="formData.hearing_date"
            type="date"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="立案日" prop="filing_date">
          <el-date-picker
            v-model="formData.filing_date"
            type="date"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="结案时间" prop="closing_date">
          <el-date-picker
            v-model="formData.closing_date"
            type="date"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="业务地点" prop="location">
          <el-input v-model="formData.location" />
        </el-form-item>
      </el-col>
      <el-col :span="24">
        <el-form-item label="案件详情" prop="details">
          <el-input v-model="formData.details" type="textarea" :rows="3" />
        </el-form-item>
      </el-col>

      <el-divider content-position="left">律师分配</el-divider>
      <el-col :span="12">
        <el-form-item label="主办律师" prop="main_lawyer_id">
          <el-select
            v-model="formData.main_lawyer_id"
            filterable
            placeholder="请选择"
            style="width: 100%"
          >
            <el-option
              v-for="item in lawyerOptions"
              :key="item.id"
              :label="item.real_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="助理律师" prop="assistant_lawyer_id">
          <el-select
            v-model="formData.assistant_lawyer_id"
            filterable
            placeholder="请选择"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in lawyerOptions"
              :key="item.id"
              :label="item.real_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="执行主办律师" prop="execution_lawyer_id">
          <el-select
            v-model="formData.execution_lawyer_id"
            filterable
            placeholder="请选择"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in lawyerOptions"
              :key="item.id"
              :label="item.real_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="执行助理律师" prop="execution_assistant_id">
          <el-select
            v-model="formData.execution_assistant_id"
            filterable
            placeholder="请选择"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in lawyerOptions"
              :key="item.id"
              :label="item.real_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-col>

      <el-divider content-position="left">费用与标记</el-divider>
      <el-col :span="8">
        <el-form-item label="收费方式" prop="fee_method">
          <el-input v-model="formData.fee_method" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="风险比例" prop="risk_ratio">
          <el-input v-model="formData.risk_ratio" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="业务收入" prop="case_income">
          <el-input-number v-model="formData.case_income" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="付款到期日" prop="payment_due_date">
          <el-date-picker
            v-model="formData.payment_due_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="16">
        <el-form-item label="标记">
          <el-checkbox v-model="formData.is_major">是否重大</el-checkbox>
          <el-checkbox v-model="formData.has_paper_file">是否纸质卷宗</el-checkbox>
          <el-checkbox v-model="formData.has_record">是否笔录</el-checkbox>
          <el-checkbox v-model="formData.has_preservation">是否保全</el-checkbox>
          <el-checkbox v-model="formData.is_dismissed">是否解除</el-checkbox>
        </el-form-item>
      </el-col>

      <el-col :span="12" v-if="formData.has_preservation">
        <el-form-item label="保全开始日" prop="preservation_start">
          <el-date-picker
            v-model="formData.preservation_start"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12" v-if="formData.has_preservation">
        <el-form-item label="保全终止日" prop="preservation_end">
          <el-date-picker
            v-model="formData.preservation_end"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>

      <el-divider content-position="left">诉讼费情况</el-divider>
      <el-col :span="12">
        <el-form-item label="诉讼费缴费时间" prop="litigation_fee_payment_date">
          <el-date-picker
            v-model="formData.litigation_fee_payment_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="诉讼费缴费金额" prop="litigation_fee_payment_amount">
          <el-input-number
            v-model="formData.litigation_fee_payment_amount"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="诉讼费退费时间" prop="litigation_fee_refund_date">
          <el-date-picker
            v-model="formData.litigation_fee_refund_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="诉讼费退费金额" prop="litigation_fee_refund_amount">
          <el-input-number
            v-model="formData.litigation_fee_refund_amount"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>

      <el-divider content-position="left">结案与执行</el-divider>
      <el-col :span="8">
        <el-form-item label="结案状态" prop="closing_status">
          <el-input v-model="formData.closing_status" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="结案方式" prop="closing_method">
          <el-input v-model="formData.closing_method" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="申请执行日" prop="execution_application_date">
          <el-date-picker
            v-model="formData.execution_application_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="调解到期日" prop="mediation_due_date">
          <el-date-picker
            v-model="formData.mediation_due_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="执行到期日" prop="execution_due_date">
          <el-date-picker
            v-model="formData.execution_due_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">附件上传</el-divider>
    <el-upload
      class="upload-demo"
      drag
      action="#"
      :auto-upload="false"
      multiple
      v-model:file-list="rawFiles"
      :on-change="handleFileChange"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
      <template #tip>
        <div class="el-upload__tip">选择文件后，点击底部的“确定”按钮保存业务时会自动上传。</div>
      </template>
    </el-upload>

    <div v-if="formData.attachments && formData.attachments.length > 0" style="margin-top: 20px">
      <p style="font-weight: bold; margin-bottom: 10px">已归档附件:</p>
      <el-table :data="formData.attachments" border style="width: 100%" size="small">
        <el-table-column prop="name" label="文件名" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="scope">
            <el-button
              link
              type="primary"
              size="small"
              @click="$emit('download-attachment', scope.row.uid)"
            >
              下载
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="$emit('delete-attachment', scope.row.uid)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="form-actions" style="text-align: right; margin-top: 20px">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="submitForm">确定</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { UploadFilled, Delete, Plus, User, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  initialData: { type: Object, default: () => ({}) },
  lawyers: { type: Array, default: () => [] },
  currentUserId: { type: [Number, String] },
})

const emit = defineEmits(['submit', 'cancel', 'download-attachment', 'delete-attachment'])

const formRef = ref(null)
const rawFiles = ref([])

// 律师列表选项
const lawyerOptions = computed(() => props.lawyers)

// 表单数据
const formData = reactive({
  case_category: '民事案件',
  party_clients: [],
  party_plaintiffs: [],
  party_defendants: [],
  party_third_parties: [],
  attachments: [],
  // ...其他字段初始化...
})

// 表单验证规则 (保留原规则)
const formRules = {
  case_category: [{ required: true, message: '请选择业务类别', trigger: 'change' }],
  commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
}

// 审理机构动态Label
const courtLabel = computed(() => {
  if (formData.case_category === '仲裁案件') {
    return '仲裁委员会'
  } else if (formData.case_category === '刑事案件') {
    return '审理机构'
  }
  return '审理法院'
})

// 监听初始数据变化 (回显)
watch(
  () => props.initialData,
  (newVal) => {
    if (newVal && Object.keys(newVal).length > 0) {
      Object.assign(formData, JSON.parse(JSON.stringify(newVal)))

      // 初始化当事人数组
      if (!formData.party_clients) formData.party_clients = []
      if (!formData.party_plaintiffs) formData.party_plaintiffs = []
      if (!formData.party_defendants) formData.party_defendants = []
      if (!formData.party_third_parties) formData.party_third_parties = []

      // 如果没有任何委托人，默认添加一行方便输入
      if (formData.party_clients.length === 0) {
        addClient()
      }
    }
  },
  { immediate: true, deep: true },
)

// 文件变更处理
const handleFileChange = (file, files) => {
  rawFiles.value = files
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      if (formData.party_clients.length === 0) {
        ElMessage.error('请至少添加一位委托人')
        return
      }

      // 深拷贝数据
      const submitData = JSON.parse(JSON.stringify(formData))

      // 传递文件列表 (raw objects)
      const filesToUpload = rawFiles.value.map((f) => f.raw)
      submitData.filesToUpload = filesToUpload

      // 触发父组件提交
      emit('submit', submitData)
    }
  })
}

// ================= 当事人操作方法 (保留原逻辑) =================
const addClient = () => {
  formData.party_clients.push({
    party_type: '委托人',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeClient = (index) => {
  formData.party_clients.splice(index, 1)
}

const addPlaintiff = () => {
  let defaultType = '原告'
  if (formData.case_category === '仲裁案件') {
    defaultType = '申请人'
  }
  formData.party_plaintiffs.push({
    party_type: defaultType,
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removePlaintiff = (index) => {
  formData.party_plaintiffs.splice(index, 1)
}

const addDefendant = () => {
  let defaultType = '被告'
  if (formData.case_category === '刑事案件') {
    defaultType = '被告人'
  } else if (formData.case_category === '仲裁案件') {
    defaultType = '被申请人'
  }
  formData.party_defendants.push({
    party_type: defaultType,
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeDefendant = (index) => {
  formData.party_defendants.splice(index, 1)
}
const addThirdParty = () => {
  formData.party_third_parties.push({
    party_type: '第三人',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeThirdParty = (index) => {
  formData.party_third_parties.splice(index, 1)
}
</script>

<style scoped>
/* 样式保留原 CaseForm.vue 的样式 */
.file-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.file-list li {
  padding: 4px 0;
  color: #606266;
  font-size: 14px;
}

/* 当事人部分通用样式 */
.party-section {
  margin-bottom: 24px;
}

.party-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-weight: bold;
  font-size: 14px;
  color: #606266;
}

.party-card {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 12px;
  background-color: #fff;
  transition: all 0.3s;
}

.party-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.party-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  background-color: #f5f7fa;
  border-radius: 4px 4px 0 0;
}

.party-index-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}

.party-card-body {
  padding: 16px 12px 4px 12px; /* Bottom padding slightly reduced */
}

/* 委托人特有样式 */
.client-card .party-card-header {
  background-color: #ecf5ff; /* Light Blue */
}
.client-card .party-index-label {
  color: #409eff;
}
.client-card {
  border-left: 3px solid #409eff;
}

/* 原告特有样式 */
.plaintiff-card .party-card-header {
  background-color: #f0f9eb; /* Light Green */
}
.plaintiff-card .party-index-label {
  color: #67c23a;
}
.plaintiff-card {
  border-left: 3px solid #67c23a;
}

/* 被告特有样式 */
.defendant-card .party-card-header {
  background-color: #fdf6ec; /* Light Orange */
}
.defendant-card .party-index-label {
  color: #e6a23c;
}
.defendant-card {
  border-left: 3px solid #e6a23c;
}

/* 第三人特有样式 */
.third-party-card .party-card-header {
  background-color: #ebdcfc;
}
.third-party-card .party-index-label {
  color: #6d14d7;
}
.third-party-card {
  border-left: 3px solid #6d14d7;
}

/* 空状态样式 */
.empty-tip {
  color: #f56c6c;
  font-size: 13px;
  margin-left: 4px;
  background-color: #fef0f0;
  padding: 8px 12px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.empty-tip-simple {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px dashed #dcdfe6;
}
</style>
