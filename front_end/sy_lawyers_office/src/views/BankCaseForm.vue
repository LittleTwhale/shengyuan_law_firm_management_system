<template>
  <div class="bank-case-form">
    <el-divider content-position="left">银行案件 - 当事人信息</el-divider>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">委托银行</span>
        <el-button type="primary" plain size="small" :icon="Plus" @click="addClient">
          添加委托银行
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_clients" :key="'client_' + index">
        <div class="party-card client-card">
          <div class="party-card-header">
            <span class="party-index-label">
              <el-icon><OfficeBuilding /></el-icon> 委托银行 #{{ index + 1 }}
            </span>
            <el-button link type="danger" :icon="Delete" size="small" @click="removeClient(index)">
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item
                  label="银行名称"
                  :prop="'party_clients.' + index + '.name'"
                  :rules="{ required: true, message: '请输入银行名称', trigger: 'blur' }"
                  label-width="90px"
                >
                  <el-input v-model="item.name" placeholder="请输入银行名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="联系电话"
                  :prop="'party_clients.' + index + '.phone'"
                  label-width="80px"
                >
                  <el-input v-model="item.phone" placeholder="联系电话" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item
                  label="统信代码"
                  :prop="'party_clients.' + index + '.id_number'"
                  label-width="80px"
                >
                  <el-input v-model="item.id_number" placeholder="统一社会信用代码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="负责人" label-width="60px">
                  <el-input v-model="item.legal_representative" placeholder="负责人/法定代表人" />
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
        <el-button type="success" plain size="small" :icon="Plus" @click="addPlaintiff">
          添加原告/申请人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_plaintiffs" :key="'plaintiff_' + index">
        <div class="party-card plaintiff-card">
          <div class="party-card-header">
            <span class="party-index-label"> 原告/申请人 #{{ index + 1 }} </span>
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
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="50px"
                  :prop="'party_plaintiffs.' + index + '.party_type'"
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
              <el-col :span="6">
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
        暂无原告/申请人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">被告/被申请人/被上诉人</span>
        <el-button type="warning" plain size="small" :icon="Plus" @click="addDefendant">
          添加被告/被申请人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_defendants" :key="'defendant_' + index">
        <div class="party-card defendant-card">
          <div class="party-card-header">
            <span class="party-index-label"> 被告/被申请人 #{{ index + 1 }} </span>
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
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="50px"
                  :prop="'party_defendants.' + index + '.party_type'"
                >
                  <el-select v-model="item.party_type">
                    <el-option label="被告" value="被告" />
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
              <el-col :span="6">
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
        暂无被告/被申请人信息
      </div>
    </div>

    <div class="party-section">
      <div class="party-section-header">
        <span class="section-title">借款人</span>
        <el-button color="#13c2c2" plain size="small" :icon="Plus" @click="addBorrower">
          添加借款人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_bank_borrowers" :key="'borrower_' + index">
        <div class="party-card borrower-card">
          <div class="party-card-header">
            <span class="party-index-label"> 借款人 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeBorrower(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  label-width="90px"
                  :prop="'party_bank_borrowers.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.name" placeholder="借款人姓名或公司名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="身份证/统信代码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="60px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
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
        <el-button color="#d4b106" plain size="small" :icon="Plus" @click="addGuarantor">
          添加担保人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_bank_guarantors" :key="'guarantor_' + index">
        <div class="party-card guarantor-card">
          <div class="party-card-header">
            <span class="party-index-label"> 担保人 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeGuarantor(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item
                  label="姓名/名称"
                  label-width="90px"
                  :prop="'party_bank_guarantors.' + index + '.name'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.name" placeholder="担保人姓名或公司名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="电话" label-width="60px">
                  <el-input v-model="item.phone" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="身份证/统信代码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地址" label-width="50px">
                  <el-input v-model="item.address" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人" label-width="60px">
                  <el-input v-model="item.legal_representative" placeholder="法定代表人 (选填)" />
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
              <el-col :span="12">
                <el-form-item label="证件号" label-width="70px">
                  <el-input v-model="item.id_number" placeholder="选填" />
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
        <el-button color="#909399" plain size="small" :icon="Plus" @click="addOtherParty">
          添加其他当事人
        </el-button>
      </div>

      <template v-for="(item, index) in formData.party_others" :key="'other_' + index">
        <div class="party-card other-party-card">
          <div class="party-card-header">
            <span class="party-index-label"> 其他 #{{ index + 1 }} </span>
            <el-button
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="removeOtherParty(index)"
            >
              删除
            </el-button>
          </div>
          <div class="party-card-body">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-form-item
                  label="类型"
                  label-width="50px"
                  :prop="'party_others.' + index + '.party_type'"
                  :rules="{ required: true, message: '必填', trigger: 'blur' }"
                >
                  <el-input v-model="item.party_type" placeholder="如: 见证人" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item
                  label="姓名"
                  label-width="50px"
                  :prop="'party_others.' + index + '.name'"
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
              <el-col :span="6">
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
      <div v-if="formData.party_others.length === 0" class="empty-tip-simple">
        暂无其他当事人信息
      </div>
    </div>

    <template v-if="formData.bank_case_details">
      <el-divider content-position="left">银行案件 - 借贷基础信息</el-divider>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="支行名称" prop="bank_case_details.branch_name">
            <el-input v-model="formData.bank_case_details.branch_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户经理" prop="bank_case_details.account_manager">
            <el-input v-model="formData.bank_case_details.account_manager" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否普惠金融" prop="bank_case_details.is_inclusive_finance">
            <el-switch v-model="formData.bank_case_details.is_inclusive_finance" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="抵/质押物信息" prop="bank_case_details.collateral_info">
            <el-input type="textarea" v-model="formData.bank_case_details.collateral_info" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="抵押物位置" prop="bank_case_details.collateral_location">
            <el-input v-model="formData.bank_case_details.collateral_location" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">银行案件 - 金额与期限</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="贷款本金" prop="bank_case_details.loan_principal">
            <el-input-number
              v-model="formData.bank_case_details.loan_principal"
              :precision="2"
              :step="1000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="诉讼标的金额(含利息)"
            prop="bank_case_details.litigation_target_amount"
          >
            <el-input-number
              v-model="formData.bank_case_details.litigation_target_amount"
              :precision="2"
              :step="1000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="信用卡违约金" prop="bank_case_details.credit_card_penalty">
            <el-input-number
              v-model="formData.bank_case_details.credit_card_penalty"
              :precision="2"
              :step="100"
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
        <el-col :span="12">
          <el-form-item label="诉讼时效" prop="bank_case_details.statute_of_limitations">
            <el-input v-model="formData.bank_case_details.statute_of_limitations" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">银行案件 - 诉讼流程</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="取材料人" prop="bank_case_details.material_fetcher">
            <el-input v-model="formData.bank_case_details.material_fetcher" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="盖章日" prop="bank_case_details.seal_date">
            <el-date-picker
              v-model="formData.bank_case_details.seal_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="材料提交法院日" prop="bank_case_details.material_submission_date">
            <el-date-picker
              v-model="formData.bank_case_details.material_submission_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="诉前催收情况" prop="bank_case_details.pre_litigation_collection">
            <el-input
              type="textarea"
              v-model="formData.bank_case_details.pre_litigation_collection"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="裁判摘要" prop="bank_case_details.judgment_summary">
            <el-input type="textarea" v-model="formData.bank_case_details.judgment_summary" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="支持律师费金额" prop="bank_case_details.lawyer_fee_supported">
            <el-input-number
              v-model="formData.bank_case_details.lawyer_fee_supported"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item
            label="被告支付律师费金额"
            prop="bank_case_details.defendant_paid_lawyer_fee"
          >
            <el-input-number
              v-model="formData.bank_case_details.defendant_paid_lawyer_fee"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="是否还清" prop="bank_case_details.is_settled">
            <el-switch v-model="formData.bank_case_details.is_settled" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">银行案件 - 执行与财产查控</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="执行案号" prop="bank_case_details.execution_case_number">
            <el-input v-model="formData.bank_case_details.execution_case_number" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="执行立案时间" prop="bank_case_details.execution_filing_date">
            <el-date-picker
              v-model="formData.bank_case_details.execution_filing_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="执行法官" prop="bank_case_details.execution_judge">
            <el-input v-model="formData.bank_case_details.execution_judge" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="借款人工作单位" prop="bank_case_details.borrower_work_unit">
            <el-input v-model="formData.bank_case_details.borrower_work_unit" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否为恢复执行" prop="bank_case_details.is_execution_recovery">
            <el-switch v-model="formData.bank_case_details.is_execution_recovery" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行本金金额" prop="bank_case_details.execution_principal">
            <el-input-number
              v-model="formData.bank_case_details.execution_principal"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行律师费金额" prop="bank_case_details.execution_lawyer_fee">
            <el-input-number
              v-model="formData.bank_case_details.execution_lawyer_fee"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="财产调查情况" prop="bank_case_details.property_investigation">
            <el-input type="textarea" v-model="formData.bank_case_details.property_investigation" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="网络查控财产情况" prop="bank_case_details.network_control_status">
            <el-input type="textarea" v-model="formData.bank_case_details.network_control_status" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="承办人执行方案" prop="bank_case_details.execution_plan">
            <el-input type="textarea" v-model="formData.bank_case_details.execution_plan" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="法院执行措施" prop="bank_case_details.court_execution_measures">
            <el-input
              type="textarea"
              v-model="formData.bank_case_details.court_execution_measures"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="查封冻结标的及时间" prop="bank_case_details.seizure_freeze_info">
            <el-input type="textarea" v-model="formData.bank_case_details.seizure_freeze_info" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">银行案件 - 拍卖、结案与回款</el-divider>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="拍卖程序" prop="bank_case_details.auction_status">
            <el-input v-model="formData.bank_case_details.auction_status" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="拍卖变卖成交价" prop="bank_case_details.auction_deal_price">
            <el-input-number
              v-model="formData.bank_case_details.auction_deal_price"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="执行和解内容" prop="bank_case_details.execution_settlement_content">
            <el-input
              type="textarea"
              v-model="formData.bank_case_details.execution_settlement_content"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="终本时间" prop="bank_case_details.procedure_termination_date">
            <el-date-picker
              v-model="formData.bank_case_details.procedure_termination_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="16">
          <el-form-item label="终本原因" prop="bank_case_details.termination_reason">
            <el-input v-model="formData.bank_case_details.termination_reason" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="终结执行时间" prop="bank_case_details.execution_conclusion_date">
            <el-date-picker
              v-model="formData.bank_case_details.execution_conclusion_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="恢复执行时间" prop="bank_case_details.execution_recovery_date">
            <el-date-picker
              v-model="formData.bank_case_details.execution_recovery_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="还清时间" prop="bank_case_details.payoff_date">
            <el-date-picker
              v-model="formData.bank_case_details.payoff_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行回款总金额" prop="bank_case_details.execution_collection_amount">
            <el-input-number
              v-model="formData.bank_case_details.execution_collection_amount"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行回款来源" prop="bank_case_details.collection_source">
            <el-input v-model="formData.bank_case_details.collection_source" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="调解案件履行跟踪情况" prop="bank_case_details.mediation_tracking">
            <el-input type="textarea" v-model="formData.bank_case_details.mediation_tracking" />
          </el-form-item>
        </el-col>
      </el-row>
    </template>

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

      <el-col :span="12">
        <el-form-item label="案号" prop="case_code">
          <el-input v-model="formData.case_code" placeholder="请输入案号" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="审理法院" prop="court">
          <el-input v-model="formData.court" placeholder="请输入审理法院" />
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
      <el-col :span="24">
        <el-form-item label="案件详情" prop="details">
          <el-input
            v-model="formData.details"
            type="textarea"
            :rows="3"
            placeholder="其他补充详情"
          />
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
    </el-row>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { Plus, Delete, OfficeBuilding, Warning } from '@element-plus/icons-vue'

defineProps({
  // ormData prop，只保留只读数据
  lawyerOptions: {
    type: Array,
    default: () => [],
  },
  currentUserId: {
    type: [Number, String],
    default: null,
  },
})
// 通过注入获取父组件提供的响应式对象
// 这将返回父组件中 reactive 定义的 formData 引用
const formData = inject('caseFormData')

// ================= 当事人操作方法 (银行案件专属逻辑) =================

// 1. 委托银行 (复用 party_clients 数组)
const addClient = () => {
  formData.party_clients.push({
    party_type: '委托人', // 依然存为委托人，但前端显示为“委托银行”
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

// 2. 借款人 (操作 party_bank_borrowers 数组)
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

// 3. 担保人 (操作 party_bank_guarantors 数组)
const addGuarantor = () => {
  formData.party_bank_guarantors.push({
    party_type: '担保人',
    name: '',
    phone: '',
    id_number: '',
    address: '',
    legal_representative: '',
  })
}
const removeGuarantor = (index) => {
  formData.party_bank_guarantors.splice(index, 1)
}

// 4. 第三人 (操作 party_third_parties 数组)
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

// 5. 原告操作 (party_plaintiffs)
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

// 6. 被告操作 (party_defendants)
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

// 7.其他当事人操作 (party_others)
const addOtherParty = () => {
  formData.party_others.push({
    party_type: '', // 留空让用户填
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

/* 委托银行样式 (类似委托人，但使用更正式的蓝色) */
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

/* 借款人样式 (青色系，区分于普通原告) */
.borrower-card .party-card-header {
  background-color: #e6fffb;
}
.borrower-card .party-index-label {
  color: #13c2c2;
}
.borrower-card {
  border-left: 3px solid #13c2c2;
}

/* 担保人样式 (金/棕色系，区分于普通被告) */
.guarantor-card .party-card-header {
  background-color: #fff7e6;
}
.guarantor-card .party-index-label {
  color: #d48806; /* Gold/Bronze */
}
.guarantor-card {
  border-left: 3px solid #d48806;
}

/* 第三人样式 (保持一致) */
.third-party-card .party-card-header {
  background-color: #ebdcfc;
}
.third-party-card .party-index-label {
  color: #6d14d7;
}
.third-party-card {
  border-left: 3px solid #6d14d7;
}

/*  其他当事人样式 (灰色系) */
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
</style>
