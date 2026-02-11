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
      <!-- ================= 业务类别 ================= -->
      <el-form-item label="业务类别" prop="case_category">
        <el-select
          v-model="formData.case_category"
          placeholder="请选择业务类别"
          style="width: 100%"
        >
          <el-option label="民事案件" value="民事案件" />
          <el-option label="银行案件" value="银行案件" />
          <el-option label="刑事案件" value="刑事案件" />
          <el-option label="行政案件" value="行政案件" />
          <el-option label="仲裁案件" value="仲裁案件" />
          <el-option label="非诉案件" value="非诉案件" />
          <el-option label="法律顾问业务" value="法律顾问业务" />
          <el-option label="法律援助(民事)" value="法律援助(民事)" />
          <el-option label="法律援助(刑事)" value="法律援助(刑事)" />
        </el-select>
      </el-form-item>

      <!-- ================= 银行案件专属字段 ================= -->
      <template v-if="formData.case_category === '银行案件'">
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
            <el-form-item label="借款人身份证/统信代码" prop="bank_case_details.borrower_id_number">
              <el-input v-model="formData.bank_case_details.borrower_id_number" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否普惠金融" prop="bank_case_details.is_inclusive_finance">
              <el-switch v-model="formData.bank_case_details.is_inclusive_finance" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="担保人" prop="bank_case_details.guarantor">
              <el-input v-model="formData.bank_case_details.guarantor" />
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
              <el-input
                type="textarea"
                v-model="formData.bank_case_details.property_investigation"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="网络查控财产情况" prop="bank_case_details.network_control_status">
              <el-input
                type="textarea"
                v-model="formData.bank_case_details.network_control_status"
              />
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
            <el-form-item
              label="执行和解内容"
              prop="bank_case_details.execution_settlement_content"
            >
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
            <el-form-item
              label="执行回款总金额"
              prop="bank_case_details.execution_collection_amount"
            >
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

      <!-- ================= 当事人信息区域 (优化UI) ================= -->
      <el-divider content-position="left">当事人信息</el-divider>

      <!-- 1. 委托人 (Client) -->
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
              <el-button
                link
                type="danger"
                :icon="Delete"
                size="small"
                @click="removeClient(index)"
              >
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

      <!-- 2. 原告/申请人 (Plaintiff) -->
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

      <!-- 3. 被告/被申请人 (Defendant) -->
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
              <span class="party-index-label">
                被告/被告人/被申请人/被上诉人 #{{ index + 1 }}
              </span>
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

      <!-- 4. 第三人 (ThirdParties) -->
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

      <!-- ================= 通用信息 ================= -->
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
              <el-input
                v-model="formData.second_instance_procuratorate"
                placeholder="二审检察机关"
              />
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
import { ref, reactive, watch, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Delete, Plus, User, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  caseId: { type: [Number, String], default: null },
  currentUserId: { type: [Number, String], default: null }, //  接收当前用户ID
})

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const dialogTitle = computed(() => (props.caseId ? '编辑业务' : '新增业务'))
const courtLabel = computed(() => {
  if (formData.case_category === '仲裁案件') {
    return '仲裁委员会'
  } else if (formData.case_category === '刑事案件') {
    return '审理机构'
  }
  // 默认为 '审理法院'
  return '审理法院'
})
const loading = ref(false)
const formRef = ref(null)
const rawFiles = ref([]) // 新上传的文件
const lawyerOptions = ref([]) // 律师列表

// 定义银行案件初始数据对象
const initialBankDetails = {
  branch_name: null,
  borrower_id_number: null,
  guarantor: null,
  collateral_info: null,
  collateral_location: null,
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
}

const formData = reactive({
  case_category: '民事案件',
  case_code: null,
  commission_date: null,

  // 新增：前端分类管理的当事人列表
  party_clients: [], // 委托人
  party_plaintiffs: [], // 原告/申请人/上诉人
  party_defendants: [], // 被告/被告人/被申请人/被上诉人
  party_third_parties: [], // 第三人

  // 旧字段保留（用于兼容，不直接绑定）
  client_name: null,
  client_id_number: null,
  client_phone: null,
  plaintiff: null,
  defendant: null,
  appellant_info: null,
  extra_appellant_info: null,
  third_party: null,

  case_source: null,
  stage: null,
  cause: null,

  // 律师
  main_lawyer_id: null,
  assistant_lawyer_id: null,
  execution_lawyer_id: null,
  execution_assistant_id: null,

  // 诉讼主体
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

  // 重点修改：使用 bank_case_details
  bank_case_details: JSON.parse(JSON.stringify(initialBankDetails)),

  // 附件列表（仅用于显示）
  attachments: [],
})

const formRules = {
  case_category: [{ required: true, message: '请选择业务类别', trigger: 'change' }],
  commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
  // 移除了原有的 client_name, client_id_number 的校验，改为行内校验
}

// 当事人操作方法
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
    party_type: defaultType, // 默认值
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
    party_type: defaultType, // 默认值
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

    // 填充通用数据
    Object.keys(formData).forEach((key) => {
      // 跳过数组类型的字段，避免直接覆盖
      if (
        [
          'bank_case_details',
          'attachments',
          'party_clients',
          'party_plaintiffs',
          'party_defendants',
        ].includes(key)
      )
        return
      if (data[key] !== undefined) {
        formData[key] = data[key]
      }
    })

    // 处理当事人数据
    formData.party_clients = []
    formData.party_plaintiffs = []
    formData.party_defendants = []
    formData.party_third_parties = []

    if (data.parties && data.parties.length > 0) {
      // 如果有新版数据，按类型分发
      data.parties.forEach((p) => {
        if (p.party_type === '委托人') {
          formData.party_clients.push(p)
        } else if (['原告', '申请人', '上诉人'].includes(p.party_type)) {
          formData.party_plaintiffs.push(p)
        } else if (['被告', '被告人', '被申请人', '被上诉人'].includes(p.party_type)) {
          formData.party_defendants.push(p)
        } else if (p.party_type === '第三人') {
          formData.party_third_parties.push(p)
        }
      })
    } else {
      // 兼容旧数据：如果 parties 为空但有旧字段
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

    // 如果没有任何委托人，默认添加一行方便输入
    if (formData.party_clients.length === 0) {
      addClient()
    }

    // 显式处理律师对象映射（如果后端返回的是对象而非ID）
    if (data.main_lawyer && data.main_lawyer.id) formData.main_lawyer_id = data.main_lawyer.id
    if (data.assistant_lawyer && data.assistant_lawyer.id)
      formData.assistant_lawyer_id = data.assistant_lawyer.id
    if (data.execution_lawyer && data.execution_lawyer.id)
      formData.execution_lawyer_id = data.execution_lawyer.id
    if (data.execution_assistant && data.execution_assistant.id)
      formData.execution_assistant_id = data.execution_assistant.id

    // 填充银行案件数据 (读取 bank_case_details)
    if (data.case_category === '银行案件' && data.bank_case_details) {
      formData.bank_case_details = { ...initialBankDetails, ...data.bank_case_details }
    } else {
      formData.bank_case_details = JSON.parse(JSON.stringify(initialBankDetails))
    }

    // 加载附件
    await loadFormAttachments(props.caseId)
  } catch (err) {
    console.error(err)
    ElMessage.error('加载业务数据失败')
  }
}

// 下载附件
const downloadFormAttachment = (attachmentId) => {
  window.open(`http://127.0.0.1:8002/attachments/${attachmentId}/download`, '_blank')
}

// 删除附件
const deleteFormAttachment = async (attachmentId) => {
  try {
    await ElMessageBox.confirm('确定要永久删除该附件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await axios.delete(`http://127.0.0.1:8002/attachments/${attachmentId}`)
    ElMessage.success('附件删除成功')
    formData.attachments = formData.attachments.filter((item) => item.uid !== attachmentId)
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除附件失败:', err)
      ElMessage.error('删除附件失败')
    }
  }
}

// 加载表单中的附件列表
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
    ElMessage.error('加载附件失败')
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      fetchLawyers()
      if (props.caseId) {
        fetchCaseDetail()
      } else {
        // 重置表单
        if (formRef.value) formRef.value.resetFields()
        // 手动重置 reactive 对象到初始状态（略繁琐，简化处理）
        Object.assign(formData, {
          case_category: '民事案件',
          case_code: null, // 重置案号
          commission_date: null,
          main_lawyer_id: null,
          assistant_lawyer_id: null,
          execution_lawyer_id: null,
          execution_assistant_id: null,
          // ... 其他字段重置 ...
          bank_case_details: JSON.parse(JSON.stringify(initialBankDetails)),
          attachments: [],

          // 重置当事人
          party_clients: [],
          party_plaintiffs: [],
          party_defendants: [],
        })

        // 新增时默认添加一个空委托人
        addClient()

        // 新增业务时，默认当前用户为主办律师
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
      // 额外逻辑校验
      if (formData.party_clients.length === 0) {
        ElMessage.error('请至少添加一位委托人')
        return
      }

      loading.value = true
      try {
        const submitData = JSON.parse(JSON.stringify(formData))

        // ================== 修复代码开始 ==================
        // 1. 兼容旧字段：将 party_clients 的第一个人信息填入旧字段
        // 后端报错是因为 client_name 为 null，这里强制转为字符串
        if (submitData.party_clients && submitData.party_clients.length > 0) {
          const firstClient = submitData.party_clients[0]
          submitData.client_name = firstClient.name || ''
          submitData.client_phone = firstClient.phone || ''
          submitData.client_id_number = firstClient.id_number || ''
        } else {
          //以此防止万一为空的情况（虽然上面校验过了）
          submitData.client_name = ''
        }
        // ================== 修复代码结束 ==================

        // 如果不是银行案件，清空详情
        if (submitData.case_category !== '银行案件') {
          submitData.bank_case_details = null
        }

        // 合并当事人数据
        submitData.parties = [
          ...formData.party_clients,
          ...formData.party_plaintiffs,
          ...formData.party_defendants,
          ...formData.party_third_parties,
        ]

        // 移除前端临时数组和附件字段
        delete submitData.party_clients
        delete submitData.party_plaintiffs
        delete submitData.party_defendants
        delete submitData.party_third_parties
        delete submitData.attachments

        // ================== ✨ 新增：利益冲突检测逻辑开始 ==================
        try {
          const conflictRes = await axios.post(
            'http://127.0.0.1:8002/cases/check_conflict',
            submitData,
          )

          if (conflictRes.data.has_conflict) {
            // 格式化冲突详情为 HTML
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

            // 弹出确认框
            await ElMessageBox.confirm(warningHtml, '可能存在利益冲突', {
              dangerouslyUseHTMLString: true,
              confirmButtonText: '强制提交',
              cancelButtonText: '取消提交',
              confirmButtonClass: 'el-button--danger', // 让确认按钮变红，警示用户
              type: 'warning',
              closeOnClickModal: false,
              width: '600px',
            })
            // 如果用户点击确认，代码继续向下执行；
            // 如果用户点击取消，会抛出 error 并在 catch 中被捕获，终止提交
          }
        } catch (conflictErr) {
          // 处理用户点击“取消”的情况
          if (conflictErr === 'cancel') {
            loading.value = false
            return // 终止整个 handleSubmit
          }
          // 如果接口报错（如网络错误），通常选择提示并允许用户尝试提交，或者阻断
          // 这里选择仅记录日志，防止因检测服务挂了导致无法立案
          console.error('利益冲突检测服务异常', conflictErr)
        }
        // ================== ✨ 新增：利益冲突检测逻辑结束 ==================

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

        // 修改后的附件上传逻辑：循环调用单文件接口
        if (rawFiles.value.length > 0 && targetCaseId) {
          const uploadPromises = rawFiles.value.map((fileItem) => {
            const fd = new FormData()
            // 注意：Element Plus 的 file-list 中，真实文件对象在 .raw 属性中
            // 如果是原生 file 对象则直接使用
            const file = fileItem.raw || fileItem

            // 1. 字段名改为单数 'file'，匹配后端 @router.post("/")
            fd.append('file', file)
            // 2. 补充必填参数 case_id
            fd.append('case_id', targetCaseId)
            // 3. 补充必填参数 uploaded_by (使用 props.currentUserId)
            // 如果未传 currentUserId，这里默认给 1，防止报错
            fd.append('uploaded_by', props.currentUserId || 1)

            // 4. URL 改为 /attachments/ (去掉 /upload/)
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

onMounted(() => {
  // 初始加载逻辑
})
</script>

<style scoped>
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
