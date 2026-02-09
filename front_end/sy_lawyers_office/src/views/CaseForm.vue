<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    width="1000px"
    destroy-on-close
    @close="handleCancel"
    top="5vh"
  >
    <el-form :model="formData" :rules="formRules" ref="formRef" label-width="160px">
      <el-form-item label="案件类别" prop="case_category">
        <el-select v-model="formData.case_category" placeholder="请选择案件类别">
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
          <el-form-item label="委托人" prop="client_name">
            <el-input v-model="formData.client_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="委托人身份证/税号" prop="client_id_number">
            <el-input v-model="formData.client_id_number" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" prop="client_phone">
            <el-input v-model="formData.client_phone" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="案件来源" prop="case_source">
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
          <el-form-item label="原告/申请人" prop="plaintiff">
            <el-input v-model="formData.plaintiff" />
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
          <el-form-item label="被告" prop="defendant">
            <el-input v-model="formData.defendant" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="上诉人" prop="appellant_info">
            <el-input v-model="formData.appellant_info" placeholder="上诉人信息" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="被上诉人" prop="extra_appellant_info">
            <el-input
              v-model="formData.extra_appellant_info"
              placeholder="被上诉人或被告诉讼补充"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12" v-if="formData.case_category !== '刑事案件'">
          <el-form-item label="第三人" prop="third_party">
            <el-input v-model="formData.third_party" placeholder="请输入第三人" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="案号" prop="case_code">
            <el-input v-model="formData.case_code" placeholder="请输入案号" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="审理法院" prop="court">
            <el-input v-model="formData.court" />
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
          <el-form-item label="案件地点" prop="location">
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
          <el-form-item label="案件收入" prop="case_income">
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
          <div class="el-upload__tip">选择文件后，点击底部的“确定”按钮保存案件时会自动上传。</div>
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
import { ref, reactive, watch, defineProps, defineEmits, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  caseId: { type: [Number, String], default: null },
  currentUserId: { type: [Number, String], default: null }, // 新增: 接收当前用户ID
})

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const dialogTitle = computed(() => (props.caseId ? '编辑案件' : '新增案件'))
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

  // 诉讼主体
  plaintiff: null,
  defendant: null,
  appellant_info: null,
  extra_appellant_info: null,
  third_party: null,
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
  case_category: [{ required: true, message: '请选择案件类别', trigger: 'change' }],
  commission_date: [{ required: true, message: '请选择委托日期', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入委托人', trigger: 'blur' }],
  main_lawyer_id: [{ required: true, message: '请选择主办律师', trigger: 'change' }],
  client_id_number: [{ required: true, message: '请输入委托人身份证或单位税号', trigger: 'blur' }],
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
      if (key !== 'bank_case_details' && key !== 'attachments' && data[key] !== undefined) {
        formData[key] = data[key]
      }
    })

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
    ElMessage.error('加载案件数据失败')
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
          client_name: null,
          main_lawyer_id: null,
          assistant_lawyer_id: null,
          execution_lawyer_id: null,
          execution_assistant_id: null,
          // ... 其他字段重置 ...
          bank_case_details: JSON.parse(JSON.stringify(initialBankDetails)),
          attachments: [],
        })

        // 新增案件时，默认当前用户为主办律师
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
      loading.value = true
      try {
        const submitData = JSON.parse(JSON.stringify(formData))

        // 如果不是银行案件，清空详情
        if (submitData.case_category !== '银行案件') {
          submitData.bank_case_details = null
        }

        // 移除 attachments 字段避免后端报错
        delete submitData.attachments

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
            ElMessage.warning('案件已保存，但部分附件上传失败，请检查')
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
</style>
