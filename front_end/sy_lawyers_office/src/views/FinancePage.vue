<template>
  <div class="finance-page">
    <div class="header-stats" v-loading="statsLoading">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="stat-card card-income">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">总回款金额 (实收)</div>
                <div class="stat-value">{{ formatCurrency(stats.total_income) }}</div>
              </div>
              <div class="stat-icon icon-success">
                <el-icon><Money /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="stat-card card-invoice">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">总开票金额 (票据)</div>
                <div class="stat-value">{{ formatCurrency(stats.total_invoiced) }}</div>
              </div>
              <div class="stat-icon icon-warning">
                <el-icon><Tickets /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="stat-card card-contract">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">总合同金额 (合同)</div>
                <div class="stat-value">{{ formatCurrency(stats.total_contract) }}</div>
              </div>
              <div class="stat-icon icon-primary">
                <el-icon><DocumentCopy /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="stat-card card-records">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">财务记录数</div>
                <div class="stat-value">{{ stats.count_records }} <span class="unit">笔</span></div>
              </div>
              <div class="stat-icon icon-info">
                <el-icon><DataLine /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 月度回款趋势图 -->
    <el-card shadow="hover" class="chart-card" v-if="!isMobile">
      <div class="chart-header">
        <span class="chart-title">月度收支趋势（近12个月）</span>
      </div>
      <div ref="monthlyChartRef" class="chart-container"></div>
    </el-card>

    <el-card class="main-content-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索业务号/委托人"
            class="filter-item search-input"
            clearable
            prefix-icon="Search"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />

          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="shortcuts"
            class="filter-item date-input"
            @change="handleSearch"
            clearable
          />

          <el-select
            v-model="queryParams.case_category"
            placeholder="案件类别"
            clearable
            class="filter-item select-input"
            @change="handleSearch"
          >
            <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
          </el-select>

          <el-select
            v-model="queryParams.lawyer_id"
            placeholder="主办律师"
            clearable
            filterable
            class="filter-item select-input"
            @change="handleSearch"
          >
            <el-option
              v-for="lawyer in lawyers"
              :key="lawyer.id"
              :label="lawyer.real_name"
              :value="lawyer.id"
            />
          </el-select>

          <el-button type="primary" icon="Search" @click="handleSearch" class="search-btn"
            >查询</el-button
          >
        </div>

        <div class="toolbar-right">
          <el-dropdown trigger="click" @command="saveColVisibility" v-if="!isMobile">
            <el-button plain>
              <el-icon><Operation /></el-icon> 列设置
            </el-button>
            <template #dropdown>
              <el-dropdown-menu class="col-dropdown">
                <el-dropdown-item v-for="(_, key) in columnVisible" :key="key" :command="key">
                  <el-checkbox
                    v-model="columnVisible[key]"
                    :label="columnLabels[key]"
                    @change="saveColVisibility"
                    @click.stop
                  />
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button type="success" plain :loading="exportLoading" @click="handleExport" class="export-btn">
            <el-icon><Download /></el-icon> {{ exportLoading ? '导出中...' : '导出报表' }}
          </el-button>
        </div>
      </div>

      <!-- 快捷筛选标签 -->
      <div class="quick-filters" v-if="!isMobile">
        <span class="filter-label">快捷筛选：</span>
        <el-tag
          :type="queryParams.quick_filter === null ? 'primary' : 'info'"
          :effect="queryParams.quick_filter === null ? 'dark' : 'plain'"
          class="filter-tag"
          @click="setQuickFilter(null)"
        >全部</el-tag>
        <el-tag
          :type="queryParams.quick_filter === 'unpaid' ? 'danger' : 'info'"
          :effect="queryParams.quick_filter === 'unpaid' ? 'dark' : 'plain'"
          class="filter-tag"
          @click="setQuickFilter('unpaid')"
        >欠款案件</el-tag>
        <el-tag
          :type="queryParams.quick_filter === 'uninvoiced' ? 'warning' : 'info'"
          :effect="queryParams.quick_filter === 'uninvoiced' ? 'dark' : 'plain'"
          class="filter-tag"
          @click="setQuickFilter('uninvoiced')"
        >未开票案件</el-tag>
        <el-tag
          :type="queryParams.quick_filter === 'risk_agency' ? '' : 'info'"
          :effect="queryParams.quick_filter === 'risk_agency' ? 'dark' : 'plain'"
          class="filter-tag"
          @click="setQuickFilter('risk_agency')"
        >风险代理</el-tag>
      </div>

      <el-table
        :data="financeList"
        border
        stripe
        v-loading="tableLoading"
        class="custom-table"
        show-summary
        :summary-method="getSummaries"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column
          prop="case.case_number"
          label="业务号"
          min-width="200"
          :fixed="isMobile ? false : 'left'"
        >
          <template #default="{ row }">
            <el-link
              v-if="row.case"
              type="primary"
              :underline="false"
              class="case-link"
              @click="goToCaseDetail(row.case_id)"
            >
              {{ row.case.case_number }}
            </el-link>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column label="委托人" min-width="200" v-if="columnVisible.client">
          <template #default="{ row }">
            <span class="client-name">{{ row.case ? getClientNames(row.case.parties) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="主办律师" width="100" show-overflow-tooltip v-if="columnVisible.lawyer">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain" v-if="row.case && row.case.main_lawyer">
              {{ row.case.main_lawyer.real_name }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="合同金额" width="120" align="right" v-if="columnVisible.contract">
          <template #default="{ row }">
            <span
              class="font-mono contract-text"
              :class="{ 'text-purple': row.total_invoiced_amount > 0 }"
            >
              {{ formatCurrency(row.contract_amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="已回款" width="120" align="right" v-if="columnVisible.received">
          <template #default="{ row }">
            <span class="amount-received">{{ formatCurrency(row.total_received_amount) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="律师总领款" width="120" align="right" v-if="columnVisible.withdrawal">
          <template #default="{ row }">
            <span class="text-purple">{{ formatCurrency(row.total_withdrawal_amount) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="已开票" width="120" align="right" v-if="columnVisible.invoiced">
          <template #default="{ row }">
            <span v-if="row.total_invoiced_amount > 0" class="status-dot purple">
              {{ formatCurrency(row.total_invoiced_amount) }}
            </span>
            <span v-else class="text-gray-light">
              {{ formatCurrency(row.total_invoiced_amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="未开票" width="120" align="right" v-if="columnVisible.uninvoiced">
          <template #default="{ row }">
            <span v-if="row.uninvoiced_amount > 0" class="status-dot orange">
              {{ formatCurrency(row.uninvoiced_amount) }}
            </span>
            <span v-else class="text-gray-light">
              {{ formatCurrency(row.uninvoiced_amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="税费" width="100" align="right" v-if="columnVisible.tax">
          <template #default="{ row }">
            <span
              :class="{
                'text-gray-light':
                  calculateTax(row.total_invoiced_amount, row.total_received_amount) <= 0,
                'text-cyan': calculateTax(row.total_invoiced_amount, row.total_received_amount) > 0,
              }"
            >
              {{
                formatCurrency(calculateTax(row.total_invoiced_amount, row.total_received_amount))
              }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="风险金" width="100" align="right" v-if="columnVisible.risk">
          <template #default="{ row }">
            <span
              :class="{
                'text-gray-light':
                  calculateRiskFund(row.total_invoiced_amount, row.total_received_amount) <= 0,
                'text-indigo':
                  calculateRiskFund(row.total_invoiced_amount, row.total_received_amount) > 0,
              }"
            >
              {{
                formatCurrency(
                  calculateRiskFund(row.total_invoiced_amount, row.total_received_amount),
                )
              }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="欠款" width="120" align="right" v-if="columnVisible.unpaid">
          <template #default="{ row }">
            <span v-if="row.unpaid_amount > 0" class="status-dot red">
              {{ formatCurrency(row.unpaid_amount) }}
            </span>
            <span v-else class="text-gray-light">
              {{ formatCurrency(row.unpaid_amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="余额" width="120" align="right" v-if="columnVisible.balance">
          <template #default="{ row }">
            <span class="font-bold" :class="calculateBalance(row) >= 0 ? 'text-green' : 'text-red'">
              {{ formatCurrency(calculateBalance(row)) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          width="120"
          align="center"
          :fixed="isMobile ? false : 'right'"
        >
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetailDrawer(row)"> 财务详情 </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          background
          :small="isMobile"
          :pager-count="isMobile ? 5 : 7"
          :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 15, 30, 50, 100, 500, 1000]"
          @current-change="handlePageChange"
          @size-change="
            (size) => {
              pagination.pageSize = size
              loadData()
            }
          "
        />
      </div>
    </el-card>

    <el-drawer
      v-model="drawerVisible"
      title="财务详情管理"
      :size="drawerSize"
      destroy-on-close
      class="finance-drawer"
      @closed="() => { if (drawerChartInstance) { drawerChartInstance.dispose(); drawerChartInstance = null } }"
    >
      <div v-if="currentFinance" class="drawer-content">
        <el-row :gutter="15" class="responsive-row">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-contract">
              <div class="icon-wrapper">
                <el-icon><DocumentCopy /></el-icon>
              </div>
              <div class="info-wrapper">
                <div class="label">合同金额</div>
                <div class="value">{{ formatCurrency(currentFinance.contract_amount) }}</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-income">
              <div class="icon-wrapper">
                <el-icon><Money /></el-icon>
              </div>
              <div class="info-wrapper">
                <div class="label">已回款 (实收)</div>
                <div class="value green">
                  {{ formatCurrency(currentFinance.total_received_amount) }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-unpaid">
              <div class="icon-wrapper">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="info-wrapper">
                <div class="label">未付 (欠款)</div>
                <div class="value red">{{ formatCurrency(currentFinance.unpaid_amount) }}</div>
                <div
                  class="sub-label"
                  v-if="currentFinance.risk_agency_content && currentFinance.contract_amount <= 0"
                >
                  (手动维护)
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-uninvoiced">
              <div class="icon-wrapper">
                <el-icon><Tickets /></el-icon>
              </div>
              <div class="info-wrapper">
                <div class="label">未开票</div>
                <div class="value orange">
                  {{ formatCurrency(currentFinance.uninvoiced_amount) }}
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="15" class="responsive-row last-stat-row">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-withdraw">
              <div class="icon-wrapper">
                <el-icon><Wallet /></el-icon>
              </div>
              <div class="info-wrapper">
                <div class="label">律师总领款</div>
                <div class="value purple">
                  {{ formatCurrency(currentFinance.total_withdrawal_amount) }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-basic" style="background: #fdf6ec">
              <div class="info-wrapper" style="text-align: center">
                <div class="label">扣减税费 (15%)</div>
                <div class="value orange">
                  -{{
                    formatCurrency(
                      calculateTax(
                        currentFinance.total_invoiced_amount,
                        currentFinance.total_received_amount,
                      ),
                    )
                  }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-basic" style="background: #fef0f0">
              <div class="info-wrapper" style="text-align: center">
                <div class="label">扣减风险金 (5%, 5w封顶)</div>
                <div class="value red">
                  -{{
                    formatCurrency(
                      calculateRiskFund(
                        currentFinance.total_invoiced_amount,
                        currentFinance.total_received_amount,
                      ),
                    )
                  }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="detail-stat-box box-basic" style="background: #f0f9eb">
              <div class="info-wrapper" style="text-align: center">
                <div class="label">最终可用余额</div>
                <div class="value green font-bold">
                  {{ formatCurrency(calculateBalance(currentFinance)) }}
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 案件收支走势图 -->
        <div class="drawer-chart-wrapper" v-if="!isMobile && currentFinance && currentFinance.records && currentFinance.records.length">
          <div ref="drawerChartRef" class="drawer-chart"></div>
        </div>

        <div class="info-card">
          <div class="card-title-row">
            <span class="title">案件基础信息</span>
            <div class="drawer-actions" v-if="hasPermission">
              <el-button type="primary" link icon="Edit" @click="openEditSummary"
                >修改信息 / 调整余额</el-button
              >
            </div>
          </div>
          <el-descriptions :column="isMobile ? 1 : 2" border class="custom-descriptions">
            <el-descriptions-item label="业务号">{{
              currentFinance.case ? currentFinance.case.case_number : '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="委托人">{{
              currentFinance.case ? getClientNames(currentFinance.case.parties) : '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="主办律师">{{
              currentFinance.case && currentFinance.case.main_lawyer ? currentFinance.case.main_lawyer.real_name : '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="合同金额">
              <span class="font-bold">{{ formatCurrency(currentFinance.contract_amount) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="风险代理约定" :span="isMobile ? 1 : 2">
              <span style="white-space: pre-wrap">{{
                currentFinance.risk_agency_content || '-'
              }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="备注">{{
              currentFinance.remarks || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider class="custom-divider" />

        <div class="section-container">
          <div class="section-header">
            <div class="header-left">
              <h3>收支记录 (流水)</h3>
              <el-tag type="info" effect="plain" size="small" round style="margin-left: 10px"
                >{{ currentFinance.records.length }} 笔</el-tag
              >
            </div>
            <el-button
              v-if="hasPermission"
              type="primary"
              size="small"
              @click="openAddRecord"
            >
              <el-icon><Plus /></el-icon> 新增收支
            </el-button>
          </div>
          <el-table
            :data="currentFinance.records"
            border
            size="small"
            stripe
            style="margin-bottom: 20px"
            :header-cell-style="{ background: '#fafafa' }"
          >
            <el-table-column prop="transaction_date" label="日期" min-width="110" />
            <el-table-column prop="record_type" label="类型" min-width="90">
              <template #default="{ row }">
                <el-tag
                  :type="row.record_type === 'income' ? 'success' : 'danger'"
                  effect="light"
                  size="small"
                  >{{ row.record_type === 'income' ? '收款' : '退款' }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" align="right" min-width="100">
              <template #default="{ row }">
                <span :class="row.record_type === 'income' ? 'text-green' : 'text-red'">
                  {{ row.record_type === 'income' ? '+' : '-' }} {{ formatCurrency(row.amount) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="payer" label="付款方/收款方" min-width="120" />
            <el-table-column prop="remarks" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator_name" label="操作人" min-width="90">
              <template #default="{ row }">
                <span class="text-gray">{{
                  row.operator_name || getLawyerName(row.operator_id) || '-'
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="120"
              align="center"
              v-if="hasPermission"
              :fixed="isMobile ? false : 'right'"
            >
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openEditRecord(row)"
                  >编辑</el-button
                >
                <el-button type="danger" link size="small" @click="handleDeleteRecord(row.id)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-divider class="custom-divider" />

        <div class="section-container">
          <div class="section-header">
            <div class="header-left">
              <h3>律师领款记录</h3>
              <el-tag type="info" effect="plain" size="small" round style="margin-left: 10px"
                >{{ currentFinance.withdrawals ? currentFinance.withdrawals.length : 0 }} 笔</el-tag
              >
            </div>
            <el-button
              v-if="hasPermission"
              type="success"
              plain
              size="small"
              @click="openAddWithdrawal"
            >
              <el-icon><Wallet /></el-icon> 新增领款
            </el-button>
          </div>
          <el-table
            :data="currentFinance.withdrawals || []"
            border
            size="small"
            stripe
            style="margin-bottom: 20px"
            :header-cell-style="{ background: '#fafafa' }"
          >
            <el-table-column prop="withdrawal_date" label="领款日期" min-width="110" />
            <el-table-column label="领款律师" min-width="120">
              <template #default="{ row }">
                <el-tag type="warning" size="small" effect="plain">
                  {{ row.lawyer_name || getLawyerName(row.lawyer_id) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" align="right" min-width="100">
              <template #default="{ row }">
                <span class="text-purple">{{ formatCurrency(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator_name" label="操作人" min-width="90">
              <template #default="{ row }">
                <span class="text-gray">{{
                  row.operator_name || getLawyerName(row.operator_id) || '-'
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="120"
              align="center"
              v-if="hasPermission"
              :fixed="isMobile ? false : 'right'"
            >
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openEditWithdrawal(row)"
                  >编辑</el-button
                >
                <el-button type="danger" link size="small" @click="handleDeleteWithdrawal(row.id)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-divider class="custom-divider" />

        <div class="section-container">
          <div class="section-header">
            <div class="header-left">
              <h3>发票记录</h3>
              <el-tag type="info" effect="plain" size="small" round style="margin-left: 10px"
                >{{ currentFinance.invoices.length }} 张</el-tag
              >
            </div>
            <el-button
              v-if="hasPermission"
              type="warning"
              plain
              size="small"
              @click="openAddInvoice"
            >
              <el-icon><Plus /></el-icon> 新增发票
            </el-button>
          </div>
          <el-table
            :data="currentFinance.invoices"
            border
            size="small"
            stripe
            :header-cell-style="{ background: '#fafafa' }"
          >
            <el-table-column prop="invoice_date" label="开票日期" min-width="110" />
            <el-table-column prop="invoice_number" label="发票号" min-width="120">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.invoice_number }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="invoice_amount" label="金额" align="right" min-width="100">
              <template #default="{ row }">
                {{ formatCurrency(row.invoice_amount) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="invoice_title"
              label="抬头"
              min-width="150"
              show-overflow-tooltip
            >
              <template #default="{ row }">{{ row.invoice_title || '-' }}</template>
            </el-table-column>
            <el-table-column prop="remarks" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator_name" label="操作人" min-width="90">
              <template #default="{ row }">
                <span class="text-gray">{{
                  row.operator_name || getLawyerName(row.operator_id) || '-'
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="120"
              align="center"
              v-if="hasPermission"
              :fixed="isMobile ? false : 'right'"
            >
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openEditInvoice(row)"
                  >编辑</el-button
                >
                <el-button type="danger" link size="small" @click="handleDeleteInvoice(row.id)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      title="修改财务概览"
      v-model="showEditSummaryDialog"
      :width="editDialogWidth"
      class="custom-dialog"
    >
      <el-form :model="summaryForm" :label-width="isMobile ? '90px' : '120px'" status-icon>
        <el-form-item label="合同金额">
          <el-input-number
            v-model="summaryForm.contract_amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="风险代理约定">
          <el-input
            v-model="summaryForm.risk_agency_content"
            type="textarea"
            :rows="3"
            placeholder="若填写，系统将停止自动计算未付/未开票金额"
          />
        </el-form-item>

        <div style="margin-bottom: 20px; padding: 0 10px">
          <el-alert
            v-if="isAutoCalcMode"
            title="当前为标准模式：余额由系统自动计算"
            type="info"
            :closable="false"
            show-icon
          />
          <el-alert
            v-else
            title="当前为风险/无固定合同模式：请手动维护余额"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>

        <el-form-item label="未付(欠款)">
          <el-input-number
            v-model="summaryForm.unpaid_amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            :disabled="isAutoCalcMode"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="未开票金额">
          <el-input-number
            v-model="summaryForm.uninvoiced_amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            :disabled="isAutoCalcMode"
            controls-position="right"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="summaryForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditSummaryDialog = false">取消</el-button>
        <el-button type="primary" @click="submitSummaryUpdate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      :title="editingRecordId ? '修改收支记录' : '新增收支记录'"
      v-model="showAddRecordDialog"
      :width="dialogWidth"
      class="custom-dialog"
      @closed="editingRecordId = null"
    >
      <el-form :model="recordForm" :label-width="isMobile ? '80px' : '100px'">
        <el-form-item label="类型">
          <el-radio-group v-model="recordForm.record_type">
            <el-radio-button label="income">收款 (收入)</el-radio-button>
            <el-radio-button label="refund">退款 (支出)</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number
            v-model="recordForm.amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="recordForm.transaction_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="收付款方">
          <el-input v-model="recordForm.payer" placeholder="例如：张三 / xx公司" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="recordForm.remarks" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRecordDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRecord">
          {{ editingRecordId ? '保存修改' : '确认登记' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      :title="editingInvoiceId ? '修改发票记录' : '新增发票记录'"
      v-model="showAddInvoiceDialog"
      :width="dialogWidth"
      class="custom-dialog"
      @closed="editingInvoiceId = null"
    >
      <el-form :model="invoiceForm" :label-width="isMobile ? '80px' : '100px'">
        <el-form-item label="发票抬头">
          <el-input v-model="invoiceForm.invoice_title" placeholder="公司名称/个人姓名" />
        </el-form-item>
        <el-form-item label="发票号">
          <el-input v-model="invoiceForm.invoice_number" />
        </el-form-item>
        <el-form-item label="税号">
          <el-input v-model="invoiceForm.tax_number" placeholder="选填" />
        </el-form-item>
        <el-form-item label="开票金额">
          <el-input-number
            v-model="invoiceForm.amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker
            v-model="invoiceForm.invoice_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="invoiceForm.remarks" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddInvoiceDialog = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice">
          {{ editingInvoiceId ? '保存修改' : '确认开票' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      :title="editingWithdrawalId ? '修改律师领款' : '新增律师领款'"
      v-model="showAddWithdrawalDialog"
      :width="dialogWidth"
      class="custom-dialog"
      @closed="editingWithdrawalId = null"
    >
      <el-form :model="withdrawalForm" :label-width="isMobile ? '80px' : '100px'">
        <el-form-item label="领款律师">
          <el-select
            v-model="withdrawalForm.lawyer_id"
            filterable
            placeholder="请选择律师"
            style="width: 100%"
          >
            <el-option
              v-for="lawyer in lawyers"
              :key="lawyer.id"
              :label="lawyer.real_name"
              :value="lawyer.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="领款金额">
          <el-input-number
            v-model="withdrawalForm.amount"
            :precision="2"
            :step="1000"
            style="width: 100%"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="领款日期">
          <el-date-picker
            v-model="withdrawalForm.withdrawal_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="withdrawalForm.remarks" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddWithdrawalDialog = false">取消</el-button>
        <el-button type="primary" @click="submitWithdrawal">
          {{ editingWithdrawalId ? '保存修改' : '确认领款' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import request from '@/utils/request'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  DataLine,
  Download,
  Plus,
  Money,
  Tickets,
  DocumentCopy,
  Warning,
  Wallet,
  Operation,
} from '@element-plus/icons-vue'

const API_BASE = '/finance'
const currentUserId = localStorage.getItem('user_id')
const router = useRouter()

// --- 响应式尺寸适配逻辑 ---
// 列可见性（持久化到 localStorage）
const COL_VIS_KEY = 'finance_col_visibility'
const defaultColumns = {
  client: true,      // 委托人
  lawyer: true,      // 主办律师
  contract: true,    // 合同金额
  received: true,    // 已回款
  withdrawal: true,  // 律师总领款
  invoiced: true,    // 已开票
  uninvoiced: false, // 未开票（默认隐藏）
  tax: false,        // 税费（默认隐藏）
  risk: false,       // 风险金（默认隐藏）
  unpaid: true,      // 欠款
  balance: true,     // 余额
}

const loadColVisibility = () => {
  try {
    const saved = localStorage.getItem(COL_VIS_KEY)
    if (saved) return { ...defaultColumns, ...JSON.parse(saved) }
  } catch { /* ignore */ }
  return { ...defaultColumns }
}

const columnVisible = reactive(loadColVisibility())

const columnLabels = {
  client: '委托人',
  lawyer: '主办律师',
  contract: '合同金额',
  received: '已回款',
  withdrawal: '律师总领款',
  invoiced: '已开票',
  uninvoiced: '未开票',
  tax: '税费',
  risk: '风险金',
  unpaid: '欠款',
  balance: '余额',
}

const saveColVisibility = () => {
  localStorage.setItem(COL_VIS_KEY, JSON.stringify(columnVisible))
}

const isMobile = ref(false)
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

const drawerSize = computed(() => (isMobile.value ? '100%' : '65%'))
const dialogWidth = computed(() => (isMobile.value ? '95%' : '500px'))
const editDialogWidth = computed(() => (isMobile.value ? '95%' : '550px'))

// --- 状态数据 ---
const statsLoading = ref(false)
const tableLoading = ref(false)
const lawyers = ref([])
const caseCategories = [
  '民事案件',
  '银行案件',
  '刑事案件',
  '行政案件',
  '非诉业务',
  '执行案件',
  '劳动仲裁',
  '商事仲裁',
  '法律顾问业务',
  '法律援助(民事)',
  '法律援助(刑事)',
  '法律援助(行政)',
]

// 辅助函数：从 parties 中提取委托人名称
const getClientNames = (parties) => {
  if (!parties || !parties.length) return ''
  return parties
    .filter(p => p.party_type && p.party_type.includes('委托'))
    .map(p => p.name)
    .join('、')
}

const stats = ref({
  total_income: 0,
  total_invoiced: 0,
  total_contract: 0,
  count_records: 0,
})

// 图表相关
const monthlyChartRef = ref(null)
let monthlyChartInstance = null
const drawerChartRef = ref(null)
let drawerChartInstance = null

const financeList = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0,
})

const queryParams = reactive({
  keyword: '',
  dateRange: [],
  case_category: '',
  lawyer_id: null,
  quick_filter: null,
})

// --- 详情抽屉相关 ---
const drawerVisible = ref(false)
const currentFinance = ref(null)
const hasPermission = ref(false)

// --- 弹窗表单数据 ---
const showEditSummaryDialog = ref(false)
const summaryForm = reactive({
  contract_amount: 0,
  risk_agency_content: '',
  unpaid_amount: 0,
  uninvoiced_amount: 0,
  remarks: '',
})

// 编辑模式状态：记录当前正在编辑的记录 ID，null 表示新建模式
const editingRecordId = ref(null)
const editingInvoiceId = ref(null)
const editingWithdrawalId = ref(null)

// 计算属性：判断是否为自动计算模式
const isAutoCalcMode = computed(() => {
  const hasContract = summaryForm.contract_amount > 0
  const hasRisk = summaryForm.risk_agency_content && summaryForm.risk_agency_content.trim() !== ''
  return hasContract && !hasRisk
})

// 收支表单
const showAddRecordDialog = ref(false)
const recordForm = reactive({
  record_type: 'income',
  amount: 0,
  transaction_date: '',
  payer: '',
  remarks: '',
})

// 发票表单
const showAddInvoiceDialog = ref(false)
const invoiceForm = reactive({
  invoice_title: '',
  tax_number: '',
  invoice_number: '',
  amount: 0,
  invoice_date: '',
  remarks: '',
})

// 领款表单
const showAddWithdrawalDialog = ref(false)
const withdrawalForm = reactive({
  lawyer_id: null,
  amount: 0,
  withdrawal_date: '',
  remarks: '',
})

// ---日期范围快捷选项 ---
const shortcuts = [
  {
    text: '今年',
    value: () => {
      const end = new Date()
      const start = new Date(new Date().getFullYear(), 0, 1)
      return [start, end]
    },
  },
  {
    text: '去年',
    value: () => {
      const date = new Date()
      const start = new Date(date.getFullYear() - 1, 0, 1)
      const end = new Date(date.getFullYear() - 1, 11, 31)
      return [start, end]
    },
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    },
  },
  {
    text: '最近90天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    },
  },
]

// --- 初始化 ---
onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('resize', handleChartResize)

  await fetchUserProfile()
  await fetchLawyers()
  await loadData()
})

// 清除监听事件
onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('resize', handleChartResize)
  if (monthlyChartInstance) { monthlyChartInstance.dispose(); monthlyChartInstance = null }
  if (drawerChartInstance) { drawerChartInstance.dispose(); drawerChartInstance = null }
})

const fetchUserProfile = async () => {
  try {
    const res = await request.get(`/user/profile/info?user_id=${currentUserId}`)
    const user = res.data
    hasPermission.value =
      user.role === 'owner' || (user.permissions && user.permissions.finance_manage === true)
  } catch (err) {
    console.error('获取用户信息失败', err)
  }
}

const fetchLawyers = async () => {
  try {
    const res = await request.get('/cases/users/lawyers')
    lawyers.value = res.data || []
  } catch (err) {
    console.error('加载律师列表失败', err)
  }
}

// 辅助函数：根据ID获取律师姓名 (用于领款列表回显)
const getLawyerName = (id) => {
  if (id === 1) {
    return 'super manager'
  }
  const found = lawyers.value.find((l) => l.id === id)
  return found ? found.real_name : '未知人员'
}

// 跳转到案件详情
const goToCaseDetail = (caseId) => {
  if (!caseId) return
  const routeData = router.resolve({ path: `/main/cases/${caseId}` })
  window.open(routeData.href, '_blank')
}

// --- 核心数据加载 ---
const loadData = async () => {
  statsLoading.value = true
  tableLoading.value = true
  try {
    const postBody = {
      start_date:
        queryParams.dateRange && queryParams.dateRange[0] ? queryParams.dateRange[0] : null,
      end_date: queryParams.dateRange && queryParams.dateRange[1] ? queryParams.dateRange[1] : null,
      case_category: queryParams.case_category || null,
      lawyer_id: queryParams.lawyer_id || null,
      keyword: queryParams.keyword || null,
      quick_filter: queryParams.quick_filter || null,
      year: null,
    }

    // 1. 获取统计数据
    const statsRes = await request.post(`${API_BASE}/stats`, postBody)
    stats.value = statsRes.data

    // 2. 获取列表数据
    const listRes = await request.post(`${API_BASE}/list`, postBody, {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      },
    })

    financeList.value = listRes.data.items || []
    pagination.total = listRes.data.total || 0

    // 渲染月度图表
    renderMonthlyChart()
  } catch (err) {
    console.error('加载财务数据失败', err)
    ElMessage.error('加载数据失败')
  } finally {
    statsLoading.value = false
    tableLoading.value = false
  }
}

// --- 月度趋势图表渲染 ---
const renderMonthlyChart = async () => {
  if (isMobile.value || !monthlyChartRef.value) return
  await nextTick()

  try {
    const postBody = {
      start_date: null,
      end_date: null,
      case_category: queryParams.case_category || null,
      lawyer_id: queryParams.lawyer_id || null,
      keyword: queryParams.keyword || null,
      quick_filter: queryParams.quick_filter || null,
      year: null,
    }
    const res = await request.post(`${API_BASE}/monthly-stats`, postBody)
    const data = res.data || []

    if (!monthlyChartInstance) {
      monthlyChartInstance = echarts.init(monthlyChartRef.value)
    }

    const months = data.map(d => d.month)
    const incomes = data.map(d => d.income)
    const refunds = data.map(d => d.refund)
    const nets = data.map(d => d.income - d.refund)

    monthlyChartInstance.setOption({
      color: ['#67c23a', '#f56c6c', '#409eff'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#e4e7ed',
        borderWidth: 1,
        textStyle: { color: '#303133', fontSize: 12 },
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        formatter: (params) => {
          let tip = `<div style="font-weight:600;margin-bottom:6px">${params[0].axisValue}</div>`
          params.forEach(p => {
            tip += `<div style="display:flex;align-items:center;margin:3px 0">
              ${p.marker} ${p.seriesName}:&nbsp;<b>¥${Number(p.value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</b>
            </div>`
          })
          return tip
        }
      },
      legend: {
        data: ['收款', '退费', '净收入'],
        top: 0,
        left: 'center',
        textStyle: { fontSize: 12, color: '#606266' },
        itemWidth: 16,
        itemHeight: 8,
        itemGap: 24,
      },
      grid: { left: 65, right: 25, top: 40, bottom: 35 },
      xAxis: {
        type: 'category',
        data: months,
        axisLine: { lineStyle: { color: '#dcdfe6' } },
        axisTick: { show: false },
        axisLabel: { color: '#909399', fontSize: 11, rotate: months.length > 8 ? 30 : 0 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLabel: { color: '#909399', fontSize: 11, formatter: v => `¥${(v / 10000).toFixed(0)}万` },
      },
      series: [
        {
          name: '收款', type: 'bar', data: incomes,
          barMaxWidth: 48,
          emphasis: { itemStyle: { color: '#95d475' } },
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#95d475' },
              { offset: 1, color: '#67c23a' }
            ])
          },
          animationDelay: (idx) => idx * 30,
        },
        {
          name: '退费', type: 'bar', data: refunds,
          barMaxWidth: 48,
          emphasis: { itemStyle: { color: '#f89898' } },
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f89898' },
              { offset: 1, color: '#f56c6c' }
            ])
          },
          animationDelay: (idx) => idx * 30 + 100,
        },
        {
          name: '净收入', type: 'line', data: nets,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#409eff', width: 2.5 },
          itemStyle: { color: '#409eff', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.25)' },
              { offset: 1, color: 'rgba(64,158,255,0.02)' }
            ])
          },
          animationDelay: (idx) => idx * 30 + 200,
        }
      ],
      animationEasing: 'elasticOut',
      animationDuration: 800,
    }, { notMerge: true })
  } catch (err) {
    console.error('加载月度图表失败', err)
  }
}

// 响应式图表 resize
const handleChartResize = () => {
  if (monthlyChartInstance) monthlyChartInstance.resize()
  if (drawerChartInstance) drawerChartInstance.resize()
}

// --- 抽屉内案件收支走势图 ---
const renderDrawerChart = () => {
  if (isMobile.value) return
  nextTick(() => {
    const container = drawerChartRef.value
    if (!container) return
    if (!currentFinance.value || !currentFinance.value.records) return

    const records = [...currentFinance.value.records].sort(
      (a, b) => (a.transaction_date || '').localeCompare(b.transaction_date || '')
    )

    if (records.length === 0) {
      if (drawerChartInstance) { drawerChartInstance.clear() }
      return
    }

    if (!drawerChartInstance) {
      drawerChartInstance = echarts.init(container)
    }

    // 按日期聚合
    const dateMap = {}
    records.forEach(r => {
      const d = r.transaction_date || ''
      if (!dateMap[d]) dateMap[d] = { income: 0, refund: 0 }
      if (r.record_type === 'income') dateMap[d].income += Number(r.amount || 0)
      else dateMap[d].refund += Number(r.amount || 0)
    })

    const dates = Object.keys(dateMap)
    const incomes = dates.map(d => dateMap[d].income)
    const refunds = dates.map(d => dateMap[d].refund)
    let cum = 0
    const cumulative = dates.map(d => { cum += dateMap[d].income - dateMap[d].refund; return cum })

    drawerChartInstance.setOption({
      color: ['#67c23a', '#f56c6c', '#409eff'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#e4e7ed',
        textStyle: { color: '#303133', fontSize: 11 },
        boxShadow: '0 3px 8px rgba(0,0,0,0.08)',
      },
      legend: {
        data: ['收款', '退费', '累计净收入'],
        top: 0,
        left: 'center',
        textStyle: { fontSize: 11, color: '#606266' },
        itemWidth: 14,
        itemHeight: 7,
        itemGap: 16,
      },
      grid: { left: 55, right: 15, top: 35, bottom: 30 },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#dcdfe6' } },
        axisTick: { show: false },
        axisLabel: { color: '#909399', fontSize: 10, rotate: dates.length > 8 ? 25 : 0 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLabel: { color: '#909399', fontSize: 10, formatter: v => `¥${(v / 10000).toFixed(1)}万` },
      },
      series: [
        {
          name: '收款', type: 'bar', data: incomes,
          barMaxWidth: 40,
          itemStyle: {
            borderRadius: [3, 3, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#95d475' },
              { offset: 1, color: '#67c23a' }
            ])
          },
        },
        {
          name: '退费', type: 'bar', data: refunds,
          barMaxWidth: 40,
          itemStyle: {
            borderRadius: [3, 3, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f89898' },
              { offset: 1, color: '#f56c6c' }
            ])
          },
        },
        {
          name: '累计净收入', type: 'line', data: cumulative,
          smooth: true,
          symbol: 'circle',
          symbolSize: 5,
          lineStyle: { color: '#409eff', width: 2 },
          itemStyle: { color: '#409eff', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.2)' },
              { offset: 1, color: 'rgba(64,158,255,0.02)' }
            ])
          },
        }
      ],
      animationEasing: 'elasticOut',
      animationDuration: 600,
    }, { notMerge: true })
  })
}

// 税费计算 (仅在有回款时计算)
const calculateTax = (invoicedAmount, receivedAmount = 0) => {
  if (Number(receivedAmount) <= 0) return 0
  return Number(invoicedAmount || 0) * 0.15
}

// 风险金计算 (仅在有回款时计算)
const calculateRiskFund = (invoicedAmount, receivedAmount = 0) => {
  if (Number(receivedAmount) <= 0) return 0
  const fund = Number(invoicedAmount || 0) * 0.05
  return Math.min(fund, 50000) // 最高5万元
}

// 账户余额计算
const calculateBalance = (row) => {
  const received = Number(row.total_received_amount || 0)
  const withdrawal = Number(row.total_withdrawal_amount || 0)
  const invoiced = Number(row.total_invoiced_amount || 0)

  // 传入 received 参与判断
  const tax = calculateTax(invoiced, received)
  const riskFund = calculateRiskFund(invoiced, received)

  return received - withdrawal - tax - riskFund
}

// 列表底部合计行计算（按列 label 匹配，兼容列显隐）
const getSummaries = (param) => {
  const { columns, data } = param
  const sums = new Array(columns.length).fill('')
  if (!data || data.length === 0) return sums

  const sum = (key) => data.reduce((acc, item) => acc + Number(item[key] || 0), 0)

  // 预计算所有合计值
  const totals = {
    '合同金额': sum('contract_amount'),
    '已回款': sum('total_received_amount'),
    '律师总领款': sum('total_withdrawal_amount'),
    '已开票': sum('total_invoiced_amount'),
    '未开票': sum('uninvoiced_amount'),
    '欠款': sum('unpaid_amount'),
  }
  // 计算字段
  let totalTax = 0, totalRisk = 0, totalBalance = 0
  data.forEach(item => {
    totalTax += calculateTax(item.total_invoiced_amount, item.total_received_amount)
    totalRisk += calculateRiskFund(item.total_invoiced_amount, item.total_received_amount)
    totalBalance += calculateBalance(item)
  })
  Object.assign(totals, {
    '税费': totalTax,
    '风险金': totalRisk,
    '余额': totalBalance,
  })

  // 按列 label 匹配填充（第一个可见列为"合计"）
  columns.forEach((col, idx) => {
    if (idx === 0 && col.label === '业务号') {
      sums[idx] = '合计'
    } else if (totals[col.label] !== undefined) {
      sums[idx] = formatCurrency(totals[col.label])
    }
  })

  return sums
}

// --- 交互处理 ---
const setQuickFilter = (value) => {
  queryParams.quick_filter = value
  handleSearch()
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = (p) => {
  pagination.page = p
  loadData()
}

// 打开详情抽屉
const openDetailDrawer = async (row) => {
  try {
    const res = await request.get(`${API_BASE}/case/${row.case_id}`)
    currentFinance.value = res.data
    drawerVisible.value = true
    renderDrawerChart()
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '无法获取详情')
  }
}

// 打开编辑弹窗
const openEditSummary = () => {
  if (!currentFinance.value) return
  summaryForm.contract_amount = currentFinance.value.contract_amount
  summaryForm.risk_agency_content = currentFinance.value.risk_agency_content
  summaryForm.remarks = currentFinance.value.remarks
  summaryForm.unpaid_amount = currentFinance.value.unpaid_amount
  summaryForm.uninvoiced_amount = currentFinance.value.uninvoiced_amount

  showEditSummaryDialog.value = true
}

// --- 提交修改：财务概览 ---
const submitSummaryUpdate = async () => {
  if (!currentFinance.value) return
  try {
    await request.put(`${API_BASE}/${currentFinance.value.id}`, {
      contract_amount: summaryForm.contract_amount,
      risk_agency_content: summaryForm.risk_agency_content,
      remarks: summaryForm.remarks,
      unpaid_amount: summaryForm.unpaid_amount,
      uninvoiced_amount: summaryForm.uninvoiced_amount,
    })
    ElMessage.success('更新成功')
    showEditSummaryDialog.value = false
    // 刷新详情
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    // 刷新外部列表
    await loadData()
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  }
}

// --- 提交：新增收支记录 ---
const submitRecord = async () => {
  if (!currentFinance.value) return
  if (recordForm.amount <= 0) return ElMessage.warning('金额必须大于0')
  if (!recordForm.transaction_date) return ElMessage.warning('请选择日期')

  try {
    if (editingRecordId.value) {
      // 编辑模式
      await request.put(`${API_BASE}/record/${editingRecordId.value}`, {
        record_type: recordForm.record_type,
        amount: recordForm.amount,
        transaction_date: recordForm.transaction_date,
        payer: recordForm.payer,
        remarks: recordForm.remarks,
      })
      ElMessage.success('修改成功')
    } else {
      // 新建模式
      await request.post(`${API_BASE}/record`, {
        finance_id: currentFinance.value.id,
        record_type: recordForm.record_type,
        amount: recordForm.amount,
        transaction_date: recordForm.transaction_date,
        payer: recordForm.payer,
        remarks: recordForm.remarks,
      })
      ElMessage.success('登记成功')
    }
    showAddRecordDialog.value = false
    editingRecordId.value = null
    // 重置表单
    Object.assign(recordForm, {
      record_type: 'income',
      amount: 0,
      transaction_date: '',
      payer: '',
      remarks: '',
    })
    // 刷新
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    console.error(err)
    ElMessage.error(editingRecordId.value ? '修改失败' : '登记失败')
  }
}

// 打开编辑收支弹窗
const openAddRecord = () => {
  editingRecordId.value = null
  Object.assign(recordForm, {
    record_type: 'income',
    amount: 0,
    transaction_date: '',
    payer: '',
    remarks: '',
  })
  showAddRecordDialog.value = true
}

const openEditRecord = (row) => {
  editingRecordId.value = row.id
  recordForm.record_type = row.record_type
  recordForm.amount = row.amount
  recordForm.transaction_date = row.transaction_date
  recordForm.payer = row.payer || ''
  recordForm.remarks = row.remarks || ''
  showAddRecordDialog.value = true
}

// --- 删除流水 ---
const handleDeleteRecord = async (recordId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条收支记录吗？系统将重新计算余额。', '警告', {
      type: 'warning',
    })
    await request.delete(`${API_BASE}/record/${recordId}`)
    ElMessage.success('删除成功')
    // 刷新
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// --- 删除发票 ---
const handleDeleteInvoice = async (invoiceId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条发票记录吗？', '警告', {
      type: 'warning',
    })
    await request.delete(`${API_BASE}/invoice/${invoiceId}`)
    ElMessage.success('删除成功')
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// --- 提交：新增发票 ---
const submitInvoice = async () => {
  if (!currentFinance.value) return
  if (invoiceForm.amount <= 0) return ElMessage.warning('金额必须大于0')

  try {
    if (editingInvoiceId.value) {
      await request.put(`${API_BASE}/invoice/${editingInvoiceId.value}`, {
        invoice_title: invoiceForm.invoice_title,
        tax_number: invoiceForm.tax_number,
        invoice_amount: invoiceForm.amount,
        invoice_number: invoiceForm.invoice_number,
        invoice_date: invoiceForm.invoice_date || new Date().toISOString().split('T')[0],
        remarks: invoiceForm.remarks,
      })
      ElMessage.success('修改成功')
    } else {
      await request.post(`${API_BASE}/invoice`, {
        finance_id: currentFinance.value.id,
        invoice_title: invoiceForm.invoice_title,
        tax_number: invoiceForm.tax_number,
        invoice_amount: invoiceForm.amount,
        invoice_number: invoiceForm.invoice_number,
        invoice_date: invoiceForm.invoice_date || new Date().toISOString().split('T')[0],
        remarks: invoiceForm.remarks,
      })
      ElMessage.success('开票记录已添加')
    }
    showAddInvoiceDialog.value = false
    editingInvoiceId.value = null
    Object.assign(invoiceForm, {
      invoice_title: '',
      tax_number: '',
      invoice_number: '',
      amount: 0,
      invoice_date: '',
      remarks: '',
    })
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    console.error(err)
    ElMessage.error(editingInvoiceId.value ? '修改失败' : '添加失败')
  }
}

const openAddInvoice = () => {
  editingInvoiceId.value = null
  Object.assign(invoiceForm, {
    invoice_title: '',
    tax_number: '',
    invoice_number: '',
    amount: 0,
    invoice_date: '',
    remarks: '',
  })
  showAddInvoiceDialog.value = true
}

const openEditInvoice = (row) => {
  editingInvoiceId.value = row.id
  invoiceForm.invoice_title = row.invoice_title || ''
  invoiceForm.tax_number = row.tax_number || ''
  invoiceForm.invoice_number = row.invoice_number || ''
  invoiceForm.amount = row.invoice_amount
  invoiceForm.invoice_date = row.invoice_date
  invoiceForm.remarks = row.remarks || ''
  showAddInvoiceDialog.value = true
}

// ---提交：新增领款 ---
const submitWithdrawal = async () => {
  if (!currentFinance.value) return
  if (!withdrawalForm.lawyer_id) return ElMessage.warning('请选择领款律师')
  if (withdrawalForm.amount <= 0) return ElMessage.warning('金额必须大于0')
  if (!withdrawalForm.withdrawal_date) return ElMessage.warning('请选择领款日期')

  try {
    if (editingWithdrawalId.value) {
      await request.put(`${API_BASE}/withdrawal/${editingWithdrawalId.value}`, {
        lawyer_id: withdrawalForm.lawyer_id,
        amount: withdrawalForm.amount,
        withdrawal_date: withdrawalForm.withdrawal_date,
        remarks: withdrawalForm.remarks,
      })
      ElMessage.success('修改成功')
    } else {
      await request.post(`${API_BASE}/withdrawal`, {
        finance_id: currentFinance.value.id,
        lawyer_id: withdrawalForm.lawyer_id,
        amount: withdrawalForm.amount,
        withdrawal_date: withdrawalForm.withdrawal_date,
        remarks: withdrawalForm.remarks,
      })
      ElMessage.success('领款记录已添加')
    }
    showAddWithdrawalDialog.value = false
    editingWithdrawalId.value = null
    // 重置
    Object.assign(withdrawalForm, {
      lawyer_id: null,
      amount: 0,
      withdrawal_date: '',
      remarks: '',
    })
    // 刷新
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    console.error(err)
    ElMessage.error(editingWithdrawalId.value ? '修改失败' : '添加失败')
  }
}

const openAddWithdrawal = () => {
  editingWithdrawalId.value = null
  Object.assign(withdrawalForm, {
    lawyer_id: null,
    amount: 0,
    withdrawal_date: '',
    remarks: '',
  })
  showAddWithdrawalDialog.value = true
}

const openEditWithdrawal = (row) => {
  editingWithdrawalId.value = row.id
  withdrawalForm.lawyer_id = row.lawyer_id
  withdrawalForm.amount = row.amount
  withdrawalForm.withdrawal_date = row.withdrawal_date
  withdrawalForm.remarks = row.remarks || ''
  showAddWithdrawalDialog.value = true
}

// ---  删除领款 ---
const handleDeleteWithdrawal = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这条领款记录吗？金额将自动回滚。', '提示', {
      type: 'warning',
    })
    await request.delete(`${API_BASE}/withdrawal/${id}`)
    ElMessage.success('删除成功')
    const res = await request.get(`${API_BASE}/case/${currentFinance.value.case_id}`)
    currentFinance.value = res.data
    await loadData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// --- 导出 ---
const exportLoading = ref(false)
const handleExport = async () => {
  exportLoading.value = true
  try {
    // 1. 构造完整的查询参数，与后端 FinanceStatsQuery 对应
    const postBody = {
      // 关键词搜索 (如业务号、委托人)
      keyword: queryParams.keyword || null,

      // 年份筛选
      year: queryParams.year || null,

      // 日期范围
      start_date:
        queryParams.dateRange && queryParams.dateRange[0] ? queryParams.dateRange[0] : null,
      end_date: queryParams.dateRange && queryParams.dateRange[1] ? queryParams.dateRange[1] : null,

      // 案件类别
      case_category: queryParams.case_category || null,

      // 律师筛选
      lawyer_id: queryParams.lawyer_id || null,

      // 快捷筛选
      quick_filter: queryParams.quick_filter || null,
    }

    // 2. 发起请求
    const res = await request.post(`${API_BASE}/export`, postBody, {
      responseType: 'blob', // 关键：必须指定响应类型为 blob
    })

    // 3. 处理文件下载
    // 检查响应头中的 filename (可选)，或者使用自定义文件名
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)

    // 文件名加上时间戳，防止重名
    link.download = `财务统计报表_${new Date().toISOString().slice(0, 10)}.xlsx`

    document.body.appendChild(link) // 兼容 Firefox
    link.click()

    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)

    ElMessage.success('导出成功')
  } catch (err) {
    console.error('导出错误:', err)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exportLoading.value = false
  }
}

// --- 工具函数 ---
const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' })
}
</script>

<style scoped>
.finance-page {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

/* 顶部统计卡片优化 */
.header-stats {
  margin-bottom: 24px;
}
.stat-card {
  border: none;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}
/* 左侧彩色装饰条 */
.card-income {
  border-left: 5px solid #67c23a;
}
.card-invoice {
  border-left: 5px solid #e6a23c;
}
.card-contract {
  border-left: 5px solid #409eff;
}
.card-records {
  border-left: 5px solid #909399;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 5px;
}
.stat-info {
  flex: 1;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
  margin-left: 4px;
}
/* 右侧大图标 */
.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  opacity: 0.8;
}
.icon-success {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}
.icon-warning {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}
.icon-primary {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}
.icon-info {
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
}

/* 月度趋势图表卡片 */
.chart-card {
  margin-bottom: 24px;
  border: none;
  border-radius: 8px;
}
.chart-header {
  margin-bottom: 8px;
}
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}
.chart-container {
  width: 100%;
  height: 320px;
}

/* 主内容卡片 */
.main-content-card {
  border-radius: 8px;
  border: none;
}
.main-content-card :deep(.el-card__body) {
  padding: 24px;
}

/* 快捷筛选标签 */
.quick-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 0;
}
.filter-label {
  font-size: 13px;
  color: #909399;
  margin-right: 4px;
}
.filter-tag {
  cursor: pointer !important;
  transition: all 0.2s;
  user-select: none;
}
.filter-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 列设置下拉 */
.col-dropdown {
  max-height: 320px;
  overflow-y: auto;
  padding: 5px 0;
}
.col-dropdown .el-dropdown-menu__item {
  padding: 4px 16px;
}

/* 工具栏优化 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 15px;
}
.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.filter-item {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.search-input {
  width: 240px;
}
.date-input {
  width: 260px;
}
.select-input {
  width: 160px;
}

/* 表格样式优化 */
.custom-table {
  border-radius: 4px;
  overflow: hidden;
}
/* 合计行加粗 + 浅蓝背景 */
.custom-table :deep(.el-table__footer-wrapper) .el-table__footer td {
  font-weight: 700 !important;
  font-size: 14px !important;
  background: #e8f0fe !important;
  color: #303133 !important;
  border-top: 2px solid #c0c4cc !important;
}
.case-link {
  font-weight: 500;
}
.client-name {
  color: #333;
}
.amount-received {
  color: #67c23a;
  font-weight: 600;
  font-family: monospace;
}
.status-dot {
  font-weight: 600;
  font-family: monospace;
  position: relative;
  padding-left: 10px;
}
/* 状态圆点装饰 */
.status-dot::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-dot.purple {
  color: #6d14d7;
}
.status-dot.purple::before {
  background-color: #6d14d7;
}
.status-dot.orange {
  color: #e6a23c;
}
.status-dot.orange::before {
  background-color: #e6a23c;
}
.status-dot.red {
  color: #f56c6c;
}
.status-dot.red::before {
  background-color: #f56c6c;
}

.text-gray {
  color: #c0c4cc;
}
.text-gray-light {
  color: #dcdfe6;
}
.text-green {
  color: #67c23a;
  font-weight: bold;
}
.text-red {
  color: #f56c6c;
  font-weight: bold;
}
.text-purple {
  color: #6d14d7;
  font-weight: bold;
}
.text-cyan {
  color: #409eff !important;
}
.text-indigo {
  color: #667eea !important;
}
.contract-text {
  font-weight: 800;
  color: #303133;
}
.font-mono {
  font-family: monospace;
  font-weight: 500;
}
.font-bold {
  font-weight: 700;
}

.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* 抽屉优化 */
.drawer-content {
  padding: 0 10px;
}
.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}
.info-card {
  background: #fff;
  margin-bottom: 20px;
}
.custom-descriptions :deep(.el-descriptions__label) {
  width: 120px;
  background-color: #fafafa;
  color: #606266;
  font-weight: 500;
}

/* 详情页统计块 */
.detail-stat-box {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  height: 100%;
}
.icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 20px;
}
.info-wrapper {
  flex: 1;
}
.box-contract .icon-wrapper {
  background: #ecf5ff;
  color: #409eff;
}
.box-income .icon-wrapper {
  background: #f0f9eb;
  color: #67c23a;
}
.box-unpaid .icon-wrapper {
  background: #fef0f0;
  color: #f56c6c;
}
.box-uninvoiced .icon-wrapper {
  background: #fdf6ec;
  color: #e6a23c;
}
/* [新增] 领款 Box 样式 */
.box-withdraw .icon-wrapper {
  background: #f9f0ff;
  color: #6d14d7;
}
.box-basic {
  background: #f5f7fa; /* 纯灰色背景，无图标 */
}

.detail-stat-box .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.detail-stat-box .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
.detail-stat-box .sub-label {
  font-size: 11px;
  color: #f56c6c;
  margin-top: 2px;
}
.detail-stat-box .value.green {
  color: #67c23a;
}
.detail-stat-box .value.red {
  color: #f56c6c;
}
.detail-stat-box .value.orange {
  color: #e6a23c;
}
.detail-stat-box .value.purple {
  color: #6d14d7;
}

.section-container {
  margin-bottom: 30px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.header-left {
  display: flex;
  align-items: center;
}
.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.drawer-chart-wrapper {
  margin: 16px 0;
  padding: 12px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
.drawer-chart {
  width: 100%;
  height: 240px;
}
.custom-divider {
  margin: 30px 0;
}

/* Dialog 优化 */
.custom-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}

/* ---------------- 移动端适配媒体查询 ---------------- */
@media (max-width: 767px) {
  .finance-page {
    padding: 12px;
  }

  /* 头部卡片和抽屉内卡片的垂直间距 */
  .header-stats .el-col,
  .responsive-row .el-col {
    margin-bottom: 12px;
  }
  .last-stat-row .el-col:last-child {
    margin-bottom: 0;
  }

  .main-content-card :deep(.el-card__body) {
    padding: 16px 12px;
  }

  /* 筛选工具栏改为纵向排列 */
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left {
    flex-direction: column;
    width: 100%;
    gap: 10px;
  }

  .toolbar-right {
    width: 100%;
    margin-top: 5px;
  }

  /* 强行撑满输入框和按钮，并解决日期选择器溢出问题 */
  .search-input,
  .date-input,
  .select-input,
  .search-btn,
  .export-btn {
    width: 100% !important;
    max-width: 100%;
    box-sizing: border-box; /* 确保 padding 不会导致溢出 */
  }

  /* 强制重置 Element Plus 日期范围选择器的内部最小宽度 */
  :deep(.el-date-editor.el-input__wrapper) {
    min-width: 0 !important;
    width: 100% !important;
  }
  :deep(.el-date-editor--daterange) {
    max-width: 100%;
  }

  .export-btn {
    margin-left: 0 !important;
  }

  /* 移动端分页容器居中并允许横向滑动 */
  .pagination-container {
    justify-content: center;
    width: 100%;
    overflow-x: auto;
    padding-bottom: 10px;
  }

  /* 防止分页器在极窄屏幕下被强行换行 */
  .pagination-container :deep(.el-pagination) {
    flex-wrap: nowrap;
  }

  /* 抽屉内部头部适配 */
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  /* 调整弹窗内部 padding，防止手机端显得太挤 */
  .custom-dialog :deep(.el-dialog__body) {
    padding: 15px 10px;
  }

  /* 调整描述列表左侧 Label 宽度 */
  .custom-descriptions :deep(.el-descriptions__label) {
    width: 90px;
  }
}
</style>
