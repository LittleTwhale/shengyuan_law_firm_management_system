<template>
  <div class="bank-case-form">
    <el-divider content-position="left">当事人信息</el-divider>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">委托银行</span>
        <el-button
          type="primary"
          plain
          size="small"
          :icon="Plus"
          @click="addClient"
          :disabled="isPartyRestricted"
        >
          添加委托银行
        </el-button>
      </div>
      <template v-for="(item, index) in formData.party_clients" :key="'client_' + index">
        <div class="party-card client-card">
          <div class="party-card-header">
            <span class="party-index-label">
              <el-icon><OfficeBuilding /></el-icon> 委托银行 #{{ index + 1 }}
            </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeClient(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item
                  label="银行名称"
                  :prop="'party_clients.' + index + '.name'"
                  :rules="{ required: true, message: '请输入银行名称', trigger: 'blur' }"
                  label-width="90px"
                >
                  <el-select
                    v-model="item.name"
                    placeholder="请选择或输入银行名称"
                    filterable
                    allow-create
                    default-first-option
                    style="width: 100%"
                    :disabled="isPartyRestricted"
                  >
                    <el-option
                      v-for="bank in bankOptions"
                      :key="bank"
                      :label="bank"
                      :value="bank"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="联系电话"
                  :prop="'party_clients.' + index + '.phone'"
                  label-width="90px"
                >
                  <el-input
                    v-model="item.phone"
                    placeholder="联系电话"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="统信代码"
                  :prop="'party_clients.' + index + '.id_number'"
                  label-width="90px"
                  :rules="{ validator: validateIdNumber, trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.id_number"
                    placeholder="统一社会信用代码"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="90px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="负责人" label-width="90px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="负责人/法定代表人"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_clients.length === 0" class="empty-tip">
        <el-icon><Warning /></el-icon> 暂无委托银行信息，请添加。
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">原告/申请人/上诉人</span>
        <el-button
          type="success"
          plain
          size="small"
          :icon="Plus"
          @click="addPlaintiff"
          :disabled="isPartyRestricted"
          >添加原告/申请人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_plaintiffs" :key="'plaintiff_' + index">
        <div class="party-card plaintiff-card">
          <div class="party-card-header">
            <span class="party-index-label">原告/申请人 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removePlaintiff(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="70px"
                  :prop="'party_plaintiffs.' + index + '.party_type'"
                >
                  <el-select
                    v-model="item.party_type"
                    style="width: 100%"
                    :disabled="isPartyRestricted"
                  >
                    <el-option label="原告" value="原告" />
                    <el-option label="申请人" value="申请人" />
                    <el-option label="上诉人" value="上诉人" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="60px"
                  :prop="'party_plaintiffs.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="姓名/名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="证件号" label-width="70px" :prop="'party_plaintiffs.' + index + '.id_number'" :rules="{ validator: validateIdNumber, trigger: 'blur' }">
                  <el-input
                    v-model="item.id_number"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="70px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_plaintiffs.length === 0" class="empty-tip-simple">
        暂无原告/申请人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">被告/被申请人/被上诉人</span>
        <el-button
          type="warning"
          plain
          size="small"
          :icon="Plus"
          @click="addDefendant"
          :disabled="isPartyRestricted"
          >添加被告/被申请人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_defendants" :key="'defendant_' + index">
        <div class="party-card defendant-card">
          <div class="party-card-header">
            <span class="party-index-label">被告/被申请人 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeDefendant(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="70px"
                  :prop="'party_defendants.' + index + '.party_type'"
                >
                  <el-select
                    v-model="item.party_type"
                    style="width: 100%"
                    :disabled="isPartyRestricted"
                  >
                    <el-option label="被告" value="被告" />
                    <el-option label="被申请人" value="被申请人" />
                    <el-option label="被上诉人" value="被上诉人" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="60px"
                  :prop="'party_defendants.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="姓名/名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="证件号" label-width="70px" :prop="'party_defendants.' + index + '.id_number'" :rules="{ validator: validateIdNumber, trigger: 'blur' }">
                  <el-input
                    v-model="item.id_number"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="70px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_defendants.length === 0" class="empty-tip-simple">
        暂无被告/被申请人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">借款人</span>
        <el-button
          color="#13c2c2"
          plain
          size="small"
          :icon="Plus"
          @click="addBorrower"
          :disabled="isPartyRestricted"
          >添加借款人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_bank_borrowers" :key="'borrower_' + index">
        <div class="party-card borrower-card">
          <div class="party-card-header">
            <span class="party-index-label">借款人 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeBorrower(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  label-width="90px"
                  :prop="'party_bank_borrowers.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="借款人姓名或公司名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="证件号"
                  label-width="70px"
                  :prop="'party_bank_borrowers.' + index + '.id_number'"
                  :rules="[
                    { required: true, message: '证件号必填', trigger: 'blur' },
                    { validator: validateIdNumber, trigger: 'blur' },
                  ]"
                >
                  <el-input
                    v-model="item.id_number"
                    placeholder="身份证/统信代码必填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="90px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_bank_borrowers.length === 0" class="empty-tip-simple">
        暂无借款人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">担保人</span>
        <el-button
          color="#d4b106"
          plain
          size="small"
          :icon="Plus"
          @click="addGuarantor"
          :disabled="isPartyRestricted"
          >添加担保人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_bank_guarantors" :key="'guarantor_' + index">
        <div class="party-card guarantor-card">
          <div class="party-card-header">
            <span class="party-index-label">担保人 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeGuarantor(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  label-width="90px"
                  :prop="'party_bank_guarantors.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="担保人姓名或公司名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="证件号" label-width="70px" :prop="'party_bank_guarantors.' + index + '.id_number'" :rules="{ validator: validateIdNumber, trigger: 'blur' }">
                  <el-input
                    v-model="item.id_number"
                    placeholder="身份证/统信代码"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="90px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_bank_guarantors.length === 0" class="empty-tip-simple">
        暂无担保人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">第三人</span>
        <el-button
          color="#6d14d7"
          plain
          size="small"
          :icon="Plus"
          @click="addThirdParty"
          :disabled="isPartyRestricted"
          >添加第三人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_third_parties" :key="'third_' + index">
        <div class="party-card third-party-card">
          <div class="party-card-header">
            <span class="party-index-label">第三人 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeThirdParty(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  label-width="90px"
                  :prop="'party_third_parties.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="姓名/名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="证件号" label-width="70px" :prop="'party_third_parties.' + index + '.id_number'" :rules="{ validator: validateIdNumber, trigger: 'blur' }">
                  <el-input
                    v-model="item.id_number"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="90px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
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

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">其他当事人</span>
        <el-button
          color="#909399"
          plain
          size="small"
          :icon="Plus"
          @click="addOtherParty"
          :disabled="isPartyRestricted"
          >添加其他当事人</el-button
        >
      </div>
      <template v-for="(item, index) in formData.party_others" :key="'other_' + index">
        <div class="party-card other-party-card">
          <div class="party-card-header">
            <span class="party-index-label">其他 #{{ index + 1 }}</span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeOtherParty(index)"
              :disabled="isPartyRestricted"
              >删除</el-button
            >
          </div>
          <div class="party-card-body">
            <el-row :gutter="24">
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="70px"
                  :prop="'party_others.' + index + '.party_type'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.party_type"
                    placeholder="如: 见证人"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="60px"
                  :prop="'party_others.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input
                    v-model="item.name"
                    placeholder="姓名/名称"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" :disabled="isPartyRestricted" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="证件号" label-width="70px" :prop="'party_others.' + index + '.id_number'" :rules="{ validator: validateIdNumber, trigger: 'blur' }">
                  <el-input
                    v-model="item.id_number"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="70px">
                  <el-input
                    v-model="item.address"
                    placeholder="选填"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法定代表人" label-width="100px">
                  <el-input
                    v-model="item.legal_representative"
                    placeholder="法定代表人 (选填)"
                    :disabled="isPartyRestricted"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </template>
      <div v-if="formData.party_others.length === 0" class="empty-tip-simple">
        暂无其他当事人信息
      </div>
    </div>

    <template v-if="formData.bank_case_details">
      <el-divider content-position="left" class="workflow-divider">一、 收案与基础信息</el-divider>
      <el-row :gutter="24">
        <el-col :span="8">
          <el-form-item label="委托日期" prop="commission_date" label-width="120px">
            <el-date-picker
              v-model="formData.commission_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              :disabled="isRestricted"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="收案日期"
            prop="bank_case_details.case_acceptance_date"
            label-width="120px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.case_acceptance_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="案件来源" prop="case_source" label-width="120px">
            <el-input v-model="formData.case_source" placeholder="案件业务来源" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="案件状态" prop="bank_case_details.case_status" label-width="120px">
            <el-select
              v-model="formData.bank_case_details.case_status"
              placeholder="请选择案件状态"
              filterable
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="status in caseStatusOptions"
                :key="status"
                :label="status"
                :value="status"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item prop="bank_case_details.bank_required_case_status" label-width="120px">
            <template #label>
              <span>银行要求状态</span>
              <el-tooltip content="银行要求的案件状态" placement="top">
                <el-icon style="margin-left: 4px; vertical-align: middle"
                  ><QuestionFilled
                /></el-icon>
              </el-tooltip>
            </template>
            <el-select
              v-model="formData.bank_case_details.bank_required_case_status"
              placeholder="请选择"
              filterable
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="status in bankRequiredCaseStatusOptions"
                :key="status"
                :label="status"
                :value="status"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="支行名称" prop="bank_case_details.branch_name" label-width="120px">
            <el-select
              v-model="formData.bank_case_details.branch_name"
              placeholder="请选择或输入支行名称"
              filterable
              allow-create
              default-first-option
              style="width: 100%"
            >
              <el-option
                v-for="branch in branchOptions"
                :key="branch"
                :label="branch"
                :value="branch"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="客户经理"
            prop="bank_case_details.account_manager"
            label-width="120px"
          >
            <el-input v-model="formData.bank_case_details.account_manager" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="主办律师" prop="main_lawyer_id" label-width="120px">
            <el-select
              v-model="formData.main_lawyer_id"
              filterable
              placeholder="请选择"
              style="width: 100%"
              :disabled="isRestricted"
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
          <el-form-item label="助理律师" prop="assistant_lawyer_id" label-width="120px">
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
          <el-form-item label="第二助理律师" prop="assistant_lawyer_2_id" label-width="120px">
            <el-select
              v-model="formData.assistant_lawyer_2_id"
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

        <el-col :span="8">
          <el-form-item label="收费方式" prop="fee_method" label-width="120px">
            <el-select v-model="formData.fee_method" placeholder="请选择收费方式" style="width: 100%">
              <el-option label="固定收费" value="固定收费" />
              <el-option label="风险收费" value="风险收费" />
              <el-option label="免费（顾问单位）" value="免费（顾问单位）" />
              <el-option label="免费（法律援助）" value="免费（法律援助）" />
              <el-option label="免费（亲戚）" value="免费（亲戚）" />
              <el-option label="免费（原阶段已包含）" value="免费（原阶段已包含）" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="风险比例" prop="risk_ratio" label-width="120px">
            <el-input v-model="formData.risk_ratio" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="案件收入" prop="case_income" label-width="120px">
            <el-input-number
              v-model="formData.case_income"
              :precision="2"
              style="width: 100%"
              :disabled="isRestricted"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="付款到期日" prop="payment_due_date" label-width="120px">
            <el-date-picker
              v-model="formData.payment_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="案卷标记" label-width="120px">
            <el-checkbox v-model="formData.is_major">重大案件</el-checkbox>
            <el-checkbox v-model="formData.has_paper_file">含纸质卷宗</el-checkbox>
            <el-checkbox v-model="formData.has_record">含笔录</el-checkbox>
            <el-checkbox v-model="formData.is_dismissed">是否解除</el-checkbox>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider">二、 借贷基础信息</el-divider>
      <el-row :gutter="24">
        <el-col :span="8">
          <el-form-item label="贷款类型" prop="bank_case_details.loan_type" label-width="150px">
            <el-select
              v-model="formData.bank_case_details.loan_type"
              placeholder="请选择贷款类型"
              style="width: 100%"
            >
              <el-option label="个贷" value="个贷" />
              <el-option label="房贷" value="房贷" />
              <el-option label="信用卡" value="信用卡" />
              <el-option label="普惠" value="普惠" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="贷款种类" prop="bank_case_details.loan_category" label-width="150px">
            <el-input
              v-model="formData.bank_case_details.loan_category"
              placeholder="请输入贷款种类"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="贷款账号" prop="bank_case_details.loan_account" label-width="150px">
            <el-input
              v-model="formData.bank_case_details.loan_account"
              placeholder="请输入贷款账号"
            />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item
            label="贷款本金"
            prop="bank_case_details.loan_principal"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.loan_principal"
              :precision="2"
              :step="1000"
              style="width: 100%"
              placeholder="必填"
          /></el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="诉讼标的金额(含利息)"
            prop="bank_case_details.litigation_target_amount"
            label-width="160px"
          >
            <el-input-number
              v-model="formData.bank_case_details.litigation_target_amount"
              :precision="2"
              :step="1000"
              style="width: 100%"
              placeholder="必填"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="信用卡违约金"
            prop="bank_case_details.credit_card_penalty"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.credit_card_penalty"
              :precision="2"
              :step="100"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="借款日" prop="bank_case_details.loan_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.loan_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              placeholder="必填"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="到期日" prop="bank_case_details.loan_due_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.loan_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              placeholder="必填"
              @change="handleLoanDueDateChange"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="诉讼时效"
            prop="bank_case_details.statute_of_limitations"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.statute_of_limitations"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              placeholder="默认到期日三年后"
            />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item
            label="保证到期日"
            prop="bank_case_details.guarantee_due_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.guarantee_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              placeholder="默认到期日两年后"
            />
          </el-form-item>
        </el-col>

        <el-col :span="16">
          <el-form-item
            label="抵/质押物信息"
            prop="bank_case_details.collateral_info"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              placeholder="必填，如无请填“无”"
              v-model="formData.bank_case_details.collateral_info"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="抵押物位置"
            prop="bank_case_details.collateral_location"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.collateral_location"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item
            label="诉前催收情况"
            prop="bank_case_details.pre_litigation_collection"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.pre_litigation_collection"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider">三、 诉讼与立案阶段</el-divider>
      <el-row :gutter="24">
        <el-col :span="8">
          <el-form-item label="介入阶段" prop="stage" label-width="150px">
            <el-input
              v-model="formData.stage"
              placeholder="一审、二审等"
              :disabled="isRestricted"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="案由" prop="cause" label-width="150px">
            <el-input v-model="formData.cause" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="代理权限" prop="agency_power" label-width="150px">
            <el-select v-model="formData.agency_power" style="width: 100%">
              <el-option label="特别代理" value="特别代理" />
              <el-option label="一般代理" value="一般代理" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="审理法院" prop="court" label-width="150px">
            <el-input v-model="formData.court" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="承办法官"
            prop="bank_case_details.handling_judge"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.handling_judge" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="法院案号" prop="case_code" label-width="150px">
            <el-input v-model="formData.case_code" />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item
            label="取材料人"
            prop="bank_case_details.material_fetcher"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.material_fetcher" />
          </el-form-item>
        </el-col>
        <el-col :span="16">
          <el-form-item
            label="缺少具体材料"
            prop="bank_case_details.missing_specific_materials"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="1"
              v-model="formData.bank_case_details.missing_specific_materials"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="盖章日" prop="bank_case_details.seal_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.seal_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="材料提交法院日"
            prop="bank_case_details.material_submission_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.material_submission_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="立案日" prop="filing_date" label-width="150px">
            <el-date-picker
              v-model="formData.filing_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="开庭时间" prop="hearing_date" label-width="150px">
            <el-date-picker
              v-model="formData.hearing_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="诉讼费缴费金额"
            prop="litigation_fee_payment_amount"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.litigation_fee_payment_amount"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="诉讼费缴费时间"
            prop="litigation_fee_payment_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.litigation_fee_payment_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="诉讼费退费金额"
            prop="litigation_fee_refund_amount"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.litigation_fee_refund_amount"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="诉讼费退费时间"
            prop="litigation_fee_refund_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.litigation_fee_refund_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider">四、 财产保全阶段</el-divider>
      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="是否保全" prop="has_preservation" label-width="150px">
            <el-switch v-model="formData.has_preservation" />
          </el-form-item>
        </el-col>

        <template v-if="formData.has_preservation">
          <el-col :span="8">
            <el-form-item label="保全开始日" prop="preservation_start" label-width="150px">
              <el-date-picker
                v-model="formData.preservation_start"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="保全终止日" prop="preservation_end" label-width="150px">
              <el-date-picker
                v-model="formData.preservation_end"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item
              label="查封冻结时间"
              prop="bank_case_details.seizure_freeze_date"
              label-width="150px"
            >
              <el-date-picker
                v-model="formData.bank_case_details.seizure_freeze_date"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                placeholder="财产实际查封日"
              />
            </el-form-item>
          </el-col>
        </template>
      </el-row>

      <el-divider content-position="left" class="workflow-divider">五、 裁判与诉讼结案</el-divider>
      <el-row :gutter="24">
        <el-col :span="8">
          <el-form-item label="裁判时间" prop="bank_case_details.judgment_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.judgment_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="裁判方式"
            prop="bank_case_details.judgment_method"
            label-width="150px"
          >
            <el-select
              v-model="formData.bank_case_details.judgment_method"
              style="width: 100%"
              clearable
              placeholder="请选择裁判方式"
            >
              <el-option label="判决" value="判决" />
              <el-option label="裁定" value="裁定" />
              <el-option label="调解" value="调解" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="是否有二审、再审"
            prop="bank_case_details.has_second_instance_or_retrial"
            label-width="150px"
          >
            <el-switch
              v-model="formData.bank_case_details.has_second_instance_or_retrial"
              active-text="有"
              inactive-text="无"
            />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item
            label="裁判摘要"
            prop="bank_case_details.judgment_summary"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.judgment_summary"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="支持律师费金额"
            prop="bank_case_details.lawyer_fee_supported"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.lawyer_fee_supported"
              :precision="2"
              style="width: 100%"
              placeholder="判决支持金额"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="被告支付律师费金额"
            prop="bank_case_details.defendant_paid_lawyer_fee"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.defendant_paid_lawyer_fee"
              :precision="2"
              style="width: 100%"
              placeholder="实际支付金额"
            />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="结案时间" prop="closing_date" label-width="150px">
            <el-date-picker
              v-model="formData.closing_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="结案状态" prop="closing_status" label-width="150px">
            <el-input v-model="formData.closing_status" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="结案方式" prop="closing_method" label-width="150px">
            <el-input v-model="formData.closing_method" />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="是否还清" prop="bank_case_details.is_settled" label-width="150px">
            <el-switch v-model="formData.bank_case_details.is_settled" />
          </el-form-item>
        </el-col>
        <el-col :span="16">
          <el-form-item
            label="还清时间"
            prop="bank_case_details.payoff_date"
            v-if="formData.bank_case_details.is_settled"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.payoff_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="调解到期日" prop="mediation_due_date" label-width="150px">
            <el-date-picker
              v-model="formData.mediation_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="调解案件履行跟踪情况"
            prop="bank_case_details.mediation_tracking"
            label-width="160px"
          >
            <el-input v-model="formData.bank_case_details.mediation_tracking" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider execution-zone"
        >六、 执行阶段启动</el-divider
      >
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="执行主办律师" prop="execution_lawyer_id" label-width="150px">
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
          <el-form-item label="执行助理律师" prop="execution_assistant_id" label-width="150px">
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

        <el-col :span="12">
          <el-form-item
            label="执行案号"
            prop="bank_case_details.execution_case_number"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.execution_case_number" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="执行法官"
            prop="bank_case_details.execution_judge"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.execution_judge" />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item label="申请执行日" prop="execution_application_date" label-width="150px">
            <el-date-picker
              v-model="formData.execution_application_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="收取执行材料时间"
            prop="bank_case_details.execution_material_receipt_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_material_receipt_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="执行材料提交法院时间"
            prop="bank_case_details.execution_material_submission_date"
            label-width="160px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_material_submission_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="8">
          <el-form-item
            label="执行立案时间"
            prop="bank_case_details.execution_filing_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_filing_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="执行到期日" prop="execution_due_date" label-width="150px">
            <el-date-picker
              v-model="formData.execution_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="是否为恢复执行"
            prop="bank_case_details.is_execution_recovery"
            label-width="150px"
          >
            <el-switch
              v-model="formData.bank_case_details.is_execution_recovery"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="执行本金金额"
            prop="bank_case_details.execution_principal"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.execution_principal"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="执行律师费金额"
            prop="bank_case_details.execution_lawyer_fee"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.execution_lawyer_fee"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider execution-zone"
        >七、 执行查控与财产处置</el-divider
      >
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item
            label="财产调查情况"
            prop="bank_case_details.property_investigation"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="3"
              v-model="formData.bank_case_details.property_investigation"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="网络查控财产情况"
            prop="bank_case_details.network_control_status"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="3"
              v-model="formData.bank_case_details.network_control_status"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="承办人执行方案"
            prop="bank_case_details.execution_plan"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.execution_plan"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="法院执行措施"
            prop="bank_case_details.court_execution_measures"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.court_execution_measures"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="冻结开始日期" prop="bank_case_details.freeze_start_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.freeze_start_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="冻结截止日期" prop="bank_case_details.freeze_end_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.freeze_end_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="查封开始日期" prop="bank_case_details.seizure_start_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.seizure_start_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="查封截止日期" prop="bank_case_details.seizure_end_date" label-width="150px">
            <el-date-picker
              v-model="formData.bank_case_details.seizure_end_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="拍卖程序"
            prop="bank_case_details.auction_status"
            label-width="150px"
          >
            <el-input
              v-model="formData.bank_case_details.auction_status"
              placeholder="拍卖状态与进度"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="拍卖变卖成交价"
            prop="bank_case_details.auction_deal_price"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.auction_deal_price"
              :precision="2"
              style="width: 100%"
              placeholder="成交价格"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider execution-zone"
        >八、 执行结案与回款</el-divider
      >
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item
            label="执行和解到期日"
            prop="bank_case_details.execution_settlement_due_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_settlement_due_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="执行和解跟踪情况"
            prop="bank_case_details.execution_settlement_tracking"
            label-width="160px"
          >
            <el-input v-model="formData.bank_case_details.execution_settlement_tracking" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="终本时间"
            prop="bank_case_details.procedure_termination_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.procedure_termination_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="终本原因"
            prop="bank_case_details.termination_reason"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.termination_reason" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="恢复执行时间"
            prop="bank_case_details.execution_recovery_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_recovery_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="终结执行时间"
            prop="bank_case_details.execution_conclusion_date"
            label-width="150px"
          >
            <el-date-picker
              v-model="formData.bank_case_details.execution_conclusion_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="执行回款总金额"
            prop="bank_case_details.execution_collection_amount"
            label-width="150px"
          >
            <el-input-number
              v-model="formData.bank_case_details.execution_collection_amount"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="执行回款来源"
            prop="bank_case_details.collection_source"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.collection_source" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item
            label="执行和解内容"
            prop="bank_case_details.execution_settlement_content"
            label-width="150px"
          >
            <el-input
              type="textarea"
              :rows="2"
              v-model="formData.bank_case_details.execution_settlement_content"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left" class="workflow-divider">九、 补充详情</el-divider>
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="案件地点" prop="location" label-width="150px">
            <el-input v-model="formData.location" placeholder="输入相关地点" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="借款人工作单位"
            prop="bank_case_details.borrower_work_unit"
            label-width="150px"
          >
            <el-input v-model="formData.bank_case_details.borrower_work_unit" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="案件详情" prop="details" label-width="150px">
            <el-input
              v-model="formData.details"
              type="textarea"
              :rows="4"
              placeholder="其他补充详情或备注信息"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { Plus, Delete, OfficeBuilding, Warning, QuestionFilled } from '@element-plus/icons-vue'

// 证件号验证器：选填时为空则通过，否则必须18位
const validateIdNumber = (_rule, value, callback) => {
  if (!value || value.trim() === '') {
    callback()
  } else if (value.trim().length !== 18) {
    callback(new Error('证件号必须为18位'))
  } else {
    callback()
  }
}

defineProps({
  lawyerOptions: {
    type: Array,
    default: () => [],
  },
  currentUserId: {
    type: [Number, String],
    default: null,
  },
})

const formData = inject('caseFormData')
// 获取表单其余部分的受限状态
const isRestricted = inject('isRestricted', false)
// 获取当事人区域的受限状态
const isPartyRestricted = inject('isPartyRestricted', false)

const bankOptions = [
  '建设银行',
  '邮政银行',
  '农村商业银行',
  '工商银行',
  '交通银行',
  '住房公积金',
  '长沙村镇银行',
  '中国银行',
]

const branchOptions = [
  '保靖支行',
  '凤凰支行',
  '古丈支行',
  '花垣支行',
  '吉大支行',
  '吉首支行',
  '经开区支行',
  '龙山支行',
  '泸溪支行',
  '文艺路支行',
  '乾城支行',
  '乾州支行',
  '人民路支行',
  '营业部',
  '永顺支行',
  '矮寨支行',
  '城东支行',
  '城南支行',
  '丹青支行',
  '河溪支行',
  '马颈坳支行',
  '排吼支行',
  '社塘坡支行',
  '太平支行',
  '雅溪支行',
  '寒阳支行',
  '峒河支行',
  '团结西路支行',
  '湘西州分行',
]

// 案件状态选项数组
const caseStatusOptions = [
  '写诉讼状中',
  '资料不足',
  '退回案件',
  '移交法院排队立案',
  '诉讼立案',
  '已开庭',
  '已裁判',
  '债务履行完毕结案',
  '银行要求撤诉',
  '终结执行',
  '跟进调解履行情况',
  '写执行申请资料',
  '移交法院执行手续',
  '执行排队立案中',
  '执行和解',
  '网络查控资产情况',
  '扣划工资工积金处置抵押物',
  '询价查看不动产情况',
  '拍卖抵押物',
  '终本',
  '恢复执行中',
  '银行要求不起诉',
  '银行要求暂不起诉',
  '银行未交诉讼费撤诉',
  '被告已还清不起诉',
  '被告已还清撤诉',
  '执行盖章中',
  '诉讼盖章中',
]

// 银行要求案件状态选项数组
const bankRequiredCaseStatusOptions = [
  '资料未齐全',
  '资料齐全律所正在准备诉状或正在盖章',
  '资料齐全已移交法院排队',
  '立案后调解',
  '立案前调解',
  '已立案我行申请撤诉',
  '未立案我行申请不诉',
  '已立案未判决',
  '已立案判决未申请执行',
  '已申请执行',
  '执行和解',
  '执行中',
  '终结本次执行',
  '终结执行',
  '执行完毕',
]

// 自动计算诉讼时效功能和保证到期日功能(诉讼时效为借款到期日往后推3年，保证到期日为借款到期日往后推2年)
const handleLoanDueDateChange = (val) => {
  if (!val) {
    formData.bank_case_details.statute_of_limitations = null
    formData.bank_case_details.guarantee_due_date = null
    return
  }

  const formatDateStr = (date) => {
    const yyyy = date.getFullYear()
    const mm = String(date.getMonth() + 1).padStart(2, '0')
    const dd = String(date.getDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
  }

  // 1. 自动计算诉讼时效 (固定推3年)
  const dateLimitation = new Date(val)
  dateLimitation.setFullYear(dateLimitation.getFullYear() + 3)
  formData.bank_case_details.statute_of_limitations = formatDateStr(dateLimitation)

  // 2. 只有存在担保人时，才自动计算保证到期日 (推2年)
  if (formData.party_bank_guarantors && formData.party_bank_guarantors.length > 0) {
    const dateGuarantee = new Date(val)
    dateGuarantee.setFullYear(dateGuarantee.getFullYear() + 2)
    formData.bank_case_details.guarantee_due_date = formatDateStr(dateGuarantee)
  } else {
    // 如果没有担保人，确保该字段为空
    formData.bank_case_details.guarantee_due_date = null
  }
}

// ================= 当事人操作方法 =================
// 1. 委托银行
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

// 2. 借款人
const addBorrower = () => {
  formData.party_bank_borrowers.push({
    party_type: '借款人',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeBorrower = (index) => {
  formData.party_bank_borrowers.splice(index, 1)
}

// 3. 担保人
const addGuarantor = () => {
  formData.party_bank_guarantors.push({
    party_type: '担保人',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })

  // 添加担保人时，如果已经填了借款到期日，自动触发推算
  if (formData.bank_case_details.loan_due_date) {
    handleLoanDueDateChange(formData.bank_case_details.loan_due_date)
  }
}

const removeGuarantor = (index) => {
  formData.party_bank_guarantors.splice(index, 1)

  // 如果把担保人全部删光了，自动清空保证到期日
  if (formData.party_bank_guarantors.length === 0) {
    formData.bank_case_details.guarantee_due_date = null
  }
}

// 4. 第三人
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

// 5. 原告
const addPlaintiff = () => {
  formData.party_plaintiffs.push({
    party_type: '原告',
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

// 6. 被告
const addDefendant = () => {
  formData.party_defendants.push({
    party_type: '被告',
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

// 7.其他当事人
const addOtherParty = () => {
  formData.party_others.push({
    party_type: '',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeOtherParty = (index) => {
  formData.party_others.splice(index, 1)
}
</script>

<style scoped>
/* 办案流程区划样式 */
.workflow-divider {
  margin-top: 35px;
  margin-bottom: 25px;
}
.workflow-divider :deep(.el-divider__text) {
  font-size: 15px;
  font-weight: bold;
  color: #303133;
}
.execution-zone :deep(.el-divider__text) {
  color: #c0392b; /* 执行阶段使用更醒目的颜色区分 */
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
  padding: 16px 12px 4px 12px;
}

/* 委托银行样式 */
.client-card .party-card-header {
  background-color: #ecf5ff;
}
.client-card .party-index-label {
  color: #409eff;
}
.client-card {
  border-left: 3px solid #409eff;
}
/* 原告样式 */
.plaintiff-card .party-card-header {
  background-color: #f0f9eb;
}
.plaintiff-card .party-index-label {
  color: #67c23a;
}
.plaintiff-card {
  border-left: 3px solid #67c23a;
}
/* 被告样式 */
.defendant-card .party-card-header {
  background-color: #fdf6ec;
}
.defendant-card .party-index-label {
  color: #e6a23c;
}
.defendant-card {
  border-left: 3px solid #e6a23c;
}
/* 借款人样式 */
.borrower-card .party-card-header {
  background-color: #e6fffb;
}
.borrower-card .party-index-label {
  color: #13c2c2;
}
.borrower-card {
  border-left: 3px solid #13c2c2;
}
/* 担保人样式 */
.guarantor-card .party-card-header {
  background-color: #fff7e6;
}
.guarantor-card .party-index-label {
  color: #d48806;
}
.guarantor-card {
  border-left: 3px solid #d48806;
}
/* 第三人样式 */
.third-party-card .party-card-header {
  background-color: #ebdcfc;
}
.third-party-card .party-index-label {
  color: #6d14d7;
}
.third-party-card {
  border-left: 3px solid #6d14d7;
}
/* 其他当事人样式 */
.other-party-card .party-card-header {
  background-color: #f4f4f5;
}
.other-party-card .party-index-label {
  color: #909399;
}
.other-party-card {
  border-left: 3px solid #909399;
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
/* =======================================
   移动端响应式适配 CSS
   ======================================= */
@media screen and (max-width: 768px) {
  /* 1. 强制所有 el-col 列占满 100% 宽度，打破原来的 span="8" 等限制 */
  :deep(.el-col) {
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }

  /* 2. 强制表单项纵向排列（标签在上，输入框在下） */
  :deep(.el-form-item) {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 18px;
  }

  /* 3. 覆盖子组件内联写的 label-width="150px" 等属性 */
  :deep(.el-form-item__label) {
    width: 100% !important;
    justify-content: flex-start;
    padding-bottom: 4px;
    line-height: 20px;
    text-align: left;
  }

  /* 4. 当事人卡片头部按钮和标签可能因为太长而重叠，允许换行 */
  .party-card-header {
    flex-wrap: wrap;
    gap: 8px;
  }

  /* 5. 调整空状态提示的内边距 */
  .empty-tip,
  .empty-tip-simple {
    padding: 10px;
  }
}
</style>
