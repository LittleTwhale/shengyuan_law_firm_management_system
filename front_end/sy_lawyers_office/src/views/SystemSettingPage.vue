<template>
  <div class="system-settings-page">
    <div class="header">
      <h2>系统后台管理</h2>
      <el-tag type="danger" effect="dark">超级管理员模式</el-tag>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="settings-tabs">
      <el-tab-pane label="细粒度权限配置" name="permissions">
        <div class="tab-content">
          <div class="toolbar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索姓名或账号"
              style="width: 250px; margin-right: 15px"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">搜索 / 刷新列表</el-button>
          </div>

          <el-table :data="users" border stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" align="center" />
            <el-table-column prop="real_name" label="姓名" width="120" />
            <el-table-column prop="role" label="当前角色" width="100">
              <template #default="{ row }">
                <el-tag :type="getRoleTag(row.role)">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="position" label="职位" width="150" />

            <el-table-column label="案件审核权" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.can_review_case"
                  @change="updatePermission(row, 'can_review_case')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="印章审批权" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.can_approve_seal"
                  @change="updatePermission(row, 'can_approve_seal')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="财务管理权" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.finance_manage"
                  @change="updatePermission(row, 'finance_manage')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="党建资料管理" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.party_admin"
                  @change="updatePermission(row, 'party_admin')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="电子卷宗管理" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.volume_manage"
                  @change="updatePermission(row, 'volume_manage')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="后台管理权" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.can_access_admin"
                  :disabled="currentUserRole !== 'owner' || row.role === 'owner'"
                  @change="updatePermission(row, 'can_access_admin')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="查看全部银行案件事项" width="150" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.permissions.can_view_all_bank_events"
                  @change="updatePermission(row, 'can_view_all_bank_events')"
                  active-text="开启"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="最后更新时间" min-width="180">
              <template #default="{ row }">
                {{ row.updated_at || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <div
            class="pagination-wrapper"
            style="margin-top: 20px; display: flex; justify-content: flex-end"
          >
            <el-pagination
              v-model:current-page="userPage"
              v-model:page-size="userPageSize"
              :total="userTotal"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @size-change="handleUserSizeChange"
              @current-change="handleUserCurrentChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统公告管理" name="announcements">
        <div class="tab-content">
          <div class="overview-cards">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card shadow="hover" class="stat-card">
                  <div class="stat-icon" style="background-color: #e8f3ff; color: #165dff">
                    <el-icon><DataLine /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-title">系统累计公告</div>
                    <div class="stat-value">
                      {{ noticeTotal }} <span class="stat-unit">条</span>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="hover" class="stat-card action-card" @click="openNoticeForm()">
                  <div class="stat-icon" style="background-color: #e6f8ea; color: #13ce66">
                    <el-icon><Plus /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div
                      class="stat-title"
                      style="color: #13ce66; font-weight: bold; font-size: 16px"
                    >
                      发布新公告
                    </div>
                    <div class="stat-desc">点击创建图文公告或更新日志</div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <div
            class="toolbar"
            style="
              margin-bottom: 20px;
              display: flex;
              justify-content: space-between;
              align-items: center;
            "
          >
            <h3 style="margin: 0; color: #303133; font-size: 16px">公告列表</h3>
            <el-button type="primary" @click="fetchAnnouncements" plain>刷新列表</el-button>
          </div>

          <el-table :data="announcementsList" border stripe v-loading="noticeLoading">
            <el-table-column prop="id" label="ID" width="60" align="center" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.type === 'update_log' ? 'success' : 'info'">
                  {{ row.type === 'update_log' ? '更新日志' : '常规公告' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="version" label="绑定版本" width="100" />
            <el-table-column prop="publisher_name" label="发布人" width="100" />

            <el-table-column label="阅读情况" width="120" align="center">
              <template #default="{ row }">
                <el-button link type="primary" @click="openReadStatusDialog(row)"
                  >查看明细</el-button
                >
              </template>
            </el-table-column>

            <el-table-column label="发布状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  @change="toggleNoticeStatus(row)"
                  style="--el-switch-on-color: #13ce66"
                />
              </template>
            </el-table-column>

            <el-table-column label="发布时间" prop="created_at" width="180" />

            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="info" size="small" @click="openPreviewDialog(row)"
                  >预览</el-button
                >
                <el-button link type="primary" size="small" @click="openNoticeForm(row)"
                  >编辑</el-button
                >
                <el-button link type="danger" size="small" @click="deleteNotice(row.id)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>

          <div
            class="pagination-wrapper"
            style="margin-top: 20px; display: flex; justify-content: flex-end"
          >
            <el-pagination
              v-model:current-page="noticePage"
              v-model:page-size="noticePageSize"
              :total="noticeTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="handleNoticeSizeChange"
              @current-change="handleNoticeCurrentChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统运维管理" name="ops_management">
        <div class="tab-content">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="24" :md="10" style="margin-bottom: 20px">
              <el-card shadow="hover" class="ops-card">
                <template #header>
                  <div class="card-header">
                    <span style="font-weight: bold; font-size: 16px">用户解析缓存池</span>
                    <el-button type="primary" link @click="fetchCacheStats">刷新状态</el-button>
                  </div>
                </template>
                <div v-loading="cacheLoading" class="cache-stats-body">
                  <div class="stat-item">
                    <span>总缓存条目:</span>
                    <span class="stat-num">{{ cacheStats.total_entries || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span>活跃(未过期)条目:</span>
                    <span class="stat-num" style="color: #13ce66">{{
                      cacheStats.active_entries || 0
                    }}</span>
                  </div>
                  <div class="stat-item">
                    <span>缓存系统状态:</span>
                    <el-tag
                      :type="cacheStats.cache_hit_potential ? 'success' : 'info'"
                      size="small"
                    >
                      {{ cacheStats.cache_hit_potential ? '运行中 / 有效命中' : '空闲 / 无数据' }}
                    </el-tag>
                  </div>

                  <el-divider border-style="dashed" />
                  <div class="cache-action">
                    <p style="font-size: 12px; color: #909399; margin-bottom: 10px">
                      如遇到用户修改姓名后日志记录未更新，可手动清空缓存强制回源。
                    </p>
                    <el-button type="danger" :icon="Delete" plain @click="clearCache"
                      >一键清空用户缓存</el-button
                    >
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="24" :md="14">
              <el-card shadow="hover" class="ops-card">
                <template #header>
                  <div class="card-header">
                    <span style="font-weight: bold; font-size: 16px">系统运行日志下载</span>
                  </div>
                </template>
                <div class="log-export-body">
                  <el-alert
                    title="系统日志按自然日生成和切分。包含了系统API访问记录、状态码、响应耗时等信息。超过30天的日志将被自动清理。"
                    type="info"
                    show-icon
                    :closable="false"
                    style="margin-bottom: 20px"
                  />

                  <div class="export-form">
                    <span style="font-size: 14px; font-weight: 500; margin-right: 15px"
                      >选择日志日期:</span
                    >
                    <el-date-picker
                      v-model="logDate"
                      type="date"
                      placeholder="请选择日期"
                      format="YYYY-MM-DD"
                      value-format="YYYY-MM-DD"
                      :disabled-date="(time) => time.getTime() > Date.now()"
                      style="width: 200px; margin-right: 15px"
                    />
                    <el-button type="success" :loading="exportingLog" @click="exportLog">
                      <el-icon style="margin-right: 5px"><Download /></el-icon> 导出该日日志
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
      <el-tab-pane label="服务器资源监控" name="monitor">
        <div class="monitor-dashboard">
          <!-- 刷新频率控制器 -->
          <div class="refresh-bar">
            <span class="refresh-label">数据刷新频率:</span>
            <el-select
              v-model="refreshInterval"
              @change="handleIntervalChange"
              style="width: 140px"
              size="small"
              effect="dark"
            >
              <el-option label="极速 (0.1秒)" :value="100" />
              <el-option label="高频 (1秒)" :value="1000" />
              <el-option label="快速 (3秒)" :value="3000" />
              <el-option label="标准 (5秒)" :value="5000" />
              <el-option label="平缓 (10秒)" :value="10000" />
              <el-option label="暂停刷新" :value="0" />
            </el-select>
          </div>

          <!-- 第一行：核心资源卡片（带 sparkline） -->
          <el-row :gutter="16" class="stat-row">
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + cpuColor }">
                <div class="stat-label">CPU 使用率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" :style="{ color: cpuColor }">{{
                    monitorData.cpu?.percent ?? '--'
                  }}</span>
                  <span class="stat-unit">%</span>
                </div>
                <div class="stat-sparkline" ref="cpuSparkRef"></div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + memColor }">
                <div class="stat-label">内存使用率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" :style="{ color: memColor }">{{
                    monitorData.memory?.percent ?? '--'
                  }}</span>
                  <span class="stat-unit">%</span>
                </div>
                <div class="stat-detail">
                  {{ monitorData.memory?.used_gb ?? '--' }} /
                  {{ monitorData.memory?.total_gb ?? '--' }} GB
                </div>
                <div class="stat-sparkline" ref="memSparkRef"></div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + diskCColor }">
                <div class="stat-label">磁盘 C: 使用率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" :style="{ color: diskCColor }">{{
                    monitorData.disk_c?.percent ?? '--'
                  }}</span>
                  <span class="stat-unit">%</span>
                </div>
                <div class="stat-detail">
                  {{ monitorData.disk_c?.used_gb ?? '--' }} /
                  {{ monitorData.disk_c?.total_gb ?? '--' }} GB
                </div>
                <div class="stat-sparkline" ref="diskCSparkRef"></div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + diskDColor }">
                <div class="stat-label">磁盘 D: 使用率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" :style="{ color: diskDColor }">{{
                    monitorData.disk_d?.percent ?? '--'
                  }}</span>
                  <span class="stat-unit">%</span>
                </div>
                <div class="stat-detail">
                  {{ monitorData.disk_d?.used_gb ?? '--' }} /
                  {{ monitorData.disk_d?.total_gb ?? '--' }} GB
                </div>
                <div class="stat-sparkline" ref="diskDSparkRef"></div>
              </div>
            </el-col>
          </el-row>

          <!-- 第二行：QPS / 活跃用户 / 网络 -->
          <el-row :gutter="16" class="stat-row">
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card compact" style="border-top: 3px solid #ff6b6b">
                <div class="stat-label">API 实时 QPS</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" style="color: #ff6b6b">{{
                    monitorData.qps ?? '--'
                  }}</span>
                  <span class="stat-unit">req/s</span>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card compact" style="border-top: 3px solid #feca57">
                <div class="stat-label">在线活跃用户 (15min)</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" style="color: #feca57">{{
                    monitorData.active_users ?? '--'
                  }}</span>
                  <span class="stat-unit">人</span>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card compact" style="border-top: 3px solid #6c5ce7">
                <div class="stat-label">网络下载速率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" style="color: #6c5ce7">{{
                    networkDelta?.recv ?? '--'
                  }}</span>
                  <span class="stat-unit">KB/s</span>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="grafana-stat-card compact" style="border-top: 3px solid #00b894">
                <div class="stat-label">网络上传速率</div>
                <div class="stat-value-wrap">
                  <span class="stat-big-num" style="color: #00b894">{{
                    networkDelta?.sent ?? '--'
                  }}</span>
                  <span class="stat-unit">KB/s</span>
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- 第三行：CPU + 内存趋势 -->
          <el-row :gutter="16">
            <el-col :xs="24" :md="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">CPU 负载趋势</span>
                  <span class="panel-subtitle">{{
                    refreshInterval > 0 ? `更新间隔 ${refreshInterval / 1000}s` : '已暂停刷新'
                  }}</span>
                </div>
                <div class="panel-chart" ref="cpuChartRef"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">内存使用趋势</span>
                  <span class="panel-subtitle">{{
                    refreshInterval > 0 ? `更新间隔 ${refreshInterval / 1000}s` : '已暂停刷新'
                  }}</span>
                </div>
                <div class="panel-chart" ref="memChartRef"></div>
              </div>
            </el-col>
          </el-row>

          <!-- 第四行：磁盘 I/O + 网络流量 -->
          <el-row :gutter="16">
            <el-col :xs="24" :md="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">磁盘 I/O 读写速率</span>
                  <span class="panel-subtitle">KB/s</span>
                </div>
                <div class="panel-chart" ref="diskIOChartRef"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">网络流量实时速率</span>
                  <span class="panel-subtitle">KB/s</span>
                </div>
                <div class="panel-chart" ref="netChartRef"></div>
              </div>
            </el-col>
          </el-row>

          <!-- 第五行：C 盘 + D 盘环形图 -->
          <el-row :gutter="16">
            <el-col :xs="24" :sm="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">磁盘 C: 空间分布</span>
                </div>
                <div class="panel-chart panel-chart-sm" ref="diskCChartRef"></div>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">磁盘 D: 空间分布</span>
                </div>
                <div class="panel-chart panel-chart-sm" ref="diskDChartRef"></div>
              </div>
            </el-col>
          </el-row>

          <!-- 第六行：全站数据概览 Liquid Fill 水波球 -->
          <el-row :gutter="16">
            <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">案件总数</span>
                </div>
                <div class="panel-chart panel-chart-sm" ref="caseLiquidRef"></div>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">电子卷宗</span>
                </div>
                <div class="panel-chart panel-chart-sm" ref="volumeLiquidRef"></div>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
              <div class="grafana-panel">
                <div class="panel-header">
                  <span class="panel-title">律师人数</span>
                </div>
                <div class="panel-chart panel-chart-sm" ref="lawyerLiquidRef"></div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>

    <SystemAnnouncementForm
      v-model:visible="noticeFormVisible"
      :edit-data="currentNotice"
      @refresh="fetchAnnouncements"
    />

    <el-dialog
      v-model="readStatusVisible"
      title="公告阅读情况明细"
      width="700px"
      center
      destroy-on-close
    >
      <div v-loading="readStatusLoading" style="min-height: 200px">
        <el-tabs v-model="readStatusTab">
          <el-tab-pane :label="`已读人员 (${readUsers.length})`" name="read">
            <el-table :data="readUsers" border stripe max-height="400">
              <el-table-column prop="real_name" label="姓名" min-width="120" />
              <el-table-column prop="role" label="角色" width="120">
                <template #default="{ row }">
                  <el-tag :type="getRoleTag(row.role)">{{ row.role }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="read_at" label="阅读时间" width="180" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane :label="`未读人员 (${unreadUsers.length})`" name="unread">
            <el-table :data="unreadUsers" border stripe max-height="400">
              <el-table-column prop="real_name" label="姓名" min-width="120" />
              <el-table-column prop="role" label="角色" width="120">
                <template #default="{ row }">
                  <el-tag :type="getRoleTag(row.role)">{{ row.role }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="180">
                <template #default>
                  <el-tag type="danger" effect="plain">尚未阅读</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="公告预览 (用户视角)" width="750px" center>
      <div class="preview-container" v-loading="previewLoading">
        <h2 class="preview-title">{{ previewData?.title }}</h2>
        <div class="preview-meta">
          <span>发布人：{{ previewData?.publisher_name }}</span>
          <span style="margin: 0 10px">|</span>
          <span>发布时间：{{ previewData?.created_at }}</span>
          <el-tag v-if="previewData?.version" size="small" style="margin-left: 10px"
            >v{{ previewData?.version }}</el-tag
          >
        </div>
        <el-divider border-style="dashed" />
        <div class="rich-text-content" v-html="previewData?.content"></div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="previewVisible = false">关闭预览</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataLine, Plus, Download, Delete } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import 'echarts-liquidfill'
import SystemAnnouncementForm from '@/components/SystemAnnouncementForm.vue'

const activeTab = ref('permissions')
const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')
const currentUserRole = localStorage.getItem('role')

// 用户列表的分页状态
const userPage = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)

// 公告管理状态
const announcementsList = ref([])
const noticeLoading = ref(false)
const noticeFormVisible = ref(false)
const currentNotice = ref(null)

// 公告分页状态
const noticePage = ref(1)
const noticePageSize = ref(10)
const noticeTotal = ref(0)

// =====================================
// 权限与用户列表逻辑
// =====================================
const fetchUsers = async () => {
  loading.value = true
  try {
    const skip = (userPage.value - 1) * userPageSize.value
    const res = await request.get('/admin/system/users_with_permissions', {
      params: {
        skip: skip,
        limit: userPageSize.value,
        keyword: searchKeyword.value || undefined, // 传递搜索关键词
      },
    })

    // 解析新的数据结构
    users.value = (res.data.items || []).map((u) => ({
      ...u,
      permissions: u.permissions || {
        can_review_case: false,
        can_approve_seal: false,
        can_access_admin: false,
        finance_manage: false,
        party_admin: false,
        volume_manage: false,
        can_view_all_bank_events: false,
      },
    }))
    userTotal.value = res.data.total || 0
  } catch (err) {
    console.error(err)
    ElMessage.error('获取用户权限列表失败，请检查后端接口')
  } finally {
    loading.value = false
  }
}

// 专门处理搜索的逻辑（每次搜索应该回到第一页）
const handleSearch = () => {
  userPage.value = 1
  fetchUsers()
}

// 处理用户分页大小变化
const handleUserSizeChange = (val) => {
  userPageSize.value = val
  userPage.value = 1
  fetchUsers()
}

// 处理用户页码变化
const handleUserCurrentChange = (val) => {
  userPage.value = val
  fetchUsers()
}

// 更新权限
const updatePermission = async (user, permissionType) => {
  try {
    await request.put(`/admin/system/permissions/${user.id}`, {
      [permissionType]: user.permissions[permissionType],
    })
    ElMessage.success(`已更新 ${user.real_name} 的权限设置`)
  } catch (err) {
    console.error(err)
    user.permissions[permissionType] = !user.permissions[permissionType]
    ElMessage.error(err.response?.data?.detail || '权限更新失败，请稍后重试')
  }
}

const getRoleTag = (role) => {
  if (role === 'owner') return 'danger'
  if (role === 'admin') return 'warning'
  return 'info'
}

// =====================================
// 公告管理逻辑
// =====================================
const fetchAnnouncements = async () => {
  noticeLoading.value = true
  try {
    // 增加分页参数传递
    const skip = (noticePage.value - 1) * noticePageSize.value
    const res = await request.get('/system/announcements', {
      params: {
        skip: skip,
        limit: noticePageSize.value,
      },
    })
    announcementsList.value = res.data.items || []
    noticeTotal.value = res.data.total || 0 // 接收总条数
  } catch (e) {
    console.error(e)
    ElMessage.error('获取公告列表失败')
  } finally {
    noticeLoading.value = false
  }
}

// 处理分页大小变化
const handleNoticeSizeChange = (val) => {
  noticePageSize.value = val
  noticePage.value = 1
  fetchAnnouncements()
}

// 处理页码变化
const handleNoticeCurrentChange = (val) => {
  noticePage.value = val
  fetchAnnouncements()
}

const openNoticeForm = (row = null) => {
  currentNotice.value = row
  noticeFormVisible.value = true
}

const toggleNoticeStatus = async (row) => {
  try {
    await request.put(`/system/announcements/${row.id}`, { is_active: row.is_active })
    ElMessage.success('状态已更新')
  } catch (e) {
    row.is_active = !row.is_active
    console.error(e)
    ElMessage.error('状态更新失败')
  }
}

const deleteNotice = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该公告吗？', '提示', { type: 'warning' })
    await request.delete(`/system/announcements/${id}`)
    ElMessage.success('删除成功')

    // 细节优化：如果当前页只剩最后一条数据被删除，且不是第一页，则页码减一
    if (announcementsList.value.length === 1 && noticePage.value > 1) {
      noticePage.value--
    }
    fetchAnnouncements()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// =====================================
// 公告预览相关逻辑
// =====================================
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref(null)

const openPreviewDialog = async (row) => {
  previewVisible.value = true
  previewLoading.value = true
  try {
    // 获取最新详情以确保正文富文本是最新的
    const res = await request.get(`/system/announcements/${row.id}`)
    previewData.value = res.data
  } catch (e) {
    console.error(e)
    ElMessage.error('获取预览数据失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

// =====================================
// 阅读情况相关逻辑
// =====================================
const readStatusVisible = ref(false)
const readStatusLoading = ref(false)
const readStatusTab = ref('read')
const readStatusList = ref([])

// 计算属性：分离已读和未读数据
const readUsers = computed(() => readStatusList.value.filter((u) => u.is_read))
const unreadUsers = computed(() => readStatusList.value.filter((u) => !u.is_read))

const openReadStatusDialog = async (row) => {
  readStatusVisible.value = true
  readStatusLoading.value = true
  readStatusTab.value = 'read' // 默认打开已读Tab
  try {
    const res = await request.get(`/system/announcements/${row.id}/read_status`)
    readStatusList.value = res.data || []
  } catch (e) {
    console.error(e)
    ElMessage.error('获取阅读情况失败')
  } finally {
    readStatusLoading.value = false
  }
}

// =====================================
// 运维管理逻辑 (缓存与日志)
// =====================================
const cacheStats = ref({})
const cacheLoading = ref(false)
const logDate = ref('')
const exportingLog = ref(false)

// 1. 获取缓存统计
const fetchCacheStats = async () => {
  cacheLoading.value = true
  try {
    const res = await request.get('/system/cache-stats')
    // 处理包装的数据结构，根据后端的封装这里一般是 res.data 或 res.data.data
    cacheStats.value = res.data.data || res.data || {}
  } catch (e) {
    console.error(e)
    ElMessage.error('获取缓存统计失败')
  } finally {
    cacheLoading.value = false
  }
}

// 2. 清空缓存
const clearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空全局用户信息缓存吗？这将导致短时间内 API 鉴权全部回源查询数据库。',
      '风险操作警告',
      { confirmButtonText: '确定清空', cancelButtonText: '取消', type: 'warning' },
    )
    await request.post('/system/clear-user-cache')
    ElMessage.success('缓存已强制清空')
    fetchCacheStats()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清空缓存失败')
  }
}

// 3. 导出日志
const exportLog = async () => {
  if (!logDate.value) {
    ElMessage.warning('请先选择要导出的日志日期')
    return
  }
  exportingLog.value = true
  try {
    // 调用后端的下载接口，并声明响应类型为 blob 格式文件流
    const response = await request.get('/system/export-log', {
      params: { date: logDate.value },
      responseType: 'blob',
    })

    // 如果接口返回了 JSON，说明报错了 (比如404 日志不存在)
    if (response.data.type === 'application/json') {
      const reader = new FileReader()
      reader.onload = () => {
        const errorMsg = JSON.parse(reader.result)
        ElMessage.error(errorMsg.detail || '该日期暂无日志文件')
      }
      reader.readAsText(response.data)
      return
    }

    // 下载文件处理
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `system_log_${logDate.value}.log`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`${logDate.value} 日志导出成功`)
  } catch (e) {
    console.error(e)
    ElMessage.error('该日期可能无日志文件，或导出请求失败')
  } finally {
    exportingLog.value = false
  }
}

// =====================================
// 服务器资源监控逻辑
// =====================================
const MAX_HISTORY = 30 // 保留最近 30 个数据点
const monitorData = ref({})
const siteStats = ref({ cases: 0, volumes: 0, lawyers: 0 })
const monitorTimer = ref(null)
const refreshInterval = ref(5000) // 默认刷新间隔 5000ms (5秒)
const history = ref({
  cpu: [],
  mem: [],
  disk_c: [],
  disk_d: [],
  recv: [],
  sent: [],
  disk_read: [],
  disk_write: [],
  timestamps: [],
})
const networkDelta = ref({ sent: 0, recv: 0 })
let prevNetwork = null

// 图表容器引用 (sparklines)
const cpuSparkRef = ref(null)
const memSparkRef = ref(null)
const diskCSparkRef = ref(null)
const diskDSparkRef = ref(null)
// 图表容器引用 (大图)
const cpuChartRef = ref(null)
const memChartRef = ref(null)
const diskIOChartRef = ref(null)
const netChartRef = ref(null)
const diskCChartRef = ref(null)
const diskDChartRef = ref(null)
// 图表容器引用 (水波球)
const caseLiquidRef = ref(null)
const volumeLiquidRef = ref(null)
const lawyerLiquidRef = ref(null)

// 图表实例
let cpuSparkChart = null
let memSparkChart = null
let diskCSparkChart = null
let diskDSparkChart = null
let cpuChart = null
let memChart = null
let diskIOChart = null
let netChart = null
let diskCChart = null
let diskDChart = null
let caseLiquidChart = null
let volumeLiquidChart = null
let lawyerLiquidChart = null

// 根据阈值返回颜色 (Grafana 风格: 绿 → 黄 → 红)
const cpuColor = computed(() => {
  const v = monitorData.value.cpu?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const memColor = computed(() => {
  const v = monitorData.value.memory?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const diskCColor = computed(() => {
  const v = monitorData.value.disk_c?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const diskDColor = computed(() => {
  const v = monitorData.value.disk_d?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})

/** 创建一个迷你 sparkline 的 ECharts 配置 */
function makeSparkOption(data, color) {
  return {
    grid: { top: 2, right: 2, bottom: 2, left: 2 },
    xAxis: { show: false, data: data.map((_, i) => i) },
    yAxis: { show: false, min: 0, max: 100 },
    series: [
      {
        type: 'line',
        data,
        smooth: true,
        symbol: 'none',
        lineStyle: { color, width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' },
          ]),
        },
        animation: true,
      },
    ],
  }
}

/** 初始化顶部迷你 sparkline 图表（4 个核心资源卡片） */
function initSparkCharts() {
  const emptyOpt = makeSparkOption([0], '#909399')
  cpuSparkChart = echarts.init(cpuSparkRef.value)
  cpuSparkChart.setOption(emptyOpt)
  memSparkChart = echarts.init(memSparkRef.value)
  memSparkChart.setOption(emptyOpt)
  diskCSparkChart = echarts.init(diskCSparkRef.value)
  diskCSparkChart.setOption(emptyOpt)
  diskDSparkChart = echarts.init(diskDSparkRef.value)
  diskDSparkChart.setOption(emptyOpt)
}

/** 初始化 CPU 趋势大图 */
function initCpuChart() {
  cpuChart = echarts.init(cpuChartRef.value)
  cpuChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#a0a4b0', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#67c23a', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103,194,58,0.3)' },
            { offset: 1, color: 'rgba(103,194,58,0.02)' },
          ]),
        },
        markLine: {
          silent: true,
          data: [
            { yAxis: 90, lineStyle: { color: '#f56c6c', type: 'dashed' } },
            { yAxis: 70, lineStyle: { color: '#e6a23c', type: 'dashed' } },
          ],
          symbol: 'none',
          label: { formatter: '{c}%' },
        },
      },
    ],
  })
}

/** 初始化内存趋势大图 */
function initMemChart() {
  memChart = echarts.init(memChartRef.value)
  memChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#a0a4b0', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#409eff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ]),
        },
        markLine: {
          silent: true,
          data: [
            { yAxis: 90, lineStyle: { color: '#f56c6c', type: 'dashed' } },
            { yAxis: 70, lineStyle: { color: '#e6a23c', type: 'dashed' } },
          ],
          symbol: 'none',
          label: { formatter: '{c}%' },
        },
      },
    ],
  })
}

/** 创建一个环形图配置 */
function makeDonutOption(used, free, usedColor) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} GB ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['55%', '80%'],
        center: ['50%', '55%'],
        emphasis: { label: { fontSize: 18, fontWeight: 'bold' } },
        label: { show: false },
        data: [
          { value: used, name: '已用', itemStyle: { color: usedColor } },
          { value: free, name: '可用', itemStyle: { color: '#2a2d35' } },
        ],
      },
    ],
  }
}

/** 初始化磁盘 C: 环形图 */
function initDiskCChart() {
  diskCChart = echarts.init(diskCChartRef.value)
  diskCChart.setOption(makeDonutOption(0, 1, '#409eff'))
}

/** 初始化磁盘 D: 环形图 */
function initDiskDChart() {
  diskDChart = echarts.init(diskDChartRef.value)
  diskDChart.setOption(makeDonutOption(0, 1, '#409eff'))
}

/** 初始化磁盘 I/O 读写速率双线图 */
function initDiskIOChart() {
  diskIOChart = echarts.init(diskIOChartRef.value)
  diskIOChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['读取', '写入'], right: 10, textStyle: { color: '#a0a4b0', fontSize: 12 } },
    grid: { top: 30, right: 20, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      name: 'KB/s',
      nameTextStyle: { color: '#a0a4b0' },
      axisLabel: { color: '#a0a4b0' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        name: '读取',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#ff6b6b', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,107,107,0.3)' },
            { offset: 1, color: 'rgba(255,107,107,0.02)' },
          ]),
        },
      },
      {
        name: '写入',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#feca57', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(254,202,87,0.3)' },
            { offset: 1, color: 'rgba(254,202,87,0.02)' },
          ]),
        },
      },
    ],
  })
}

/** 初始化 3 个水波球 (Liquid Fill) 图表 */
function initLiquidCharts() {
  const makeLiquid = (color1, color2, defaultText) => ({
    series: [
      {
        type: 'liquidFill',
        data: [0],
        radius: '80%',
        center: ['50%', '52%'],
        color: [
          {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: color1 },
              { offset: 1, color: color2 },
            ],
          },
        ],
        backgroundStyle: { color: '#1a1c23' },
        outline: { show: false },
        shape: 'roundRect',
        amplitude: 6,
        waveLength: '80%',
        // 使用水波球自带的 label 替代 graphic
        label: {
          show: true,
          color: '#d0d2d8', // 没被水淹没时的文字颜色
          insideColor: '#ffffff', // 被水淹没时的文字颜色（反色效果）
          fontSize: 22,
          fontWeight: 'bold',
          formatter: defaultText, // 动态传入默认文字
        },
      },
    ],
  })

  caseLiquidChart = echarts.init(caseLiquidRef.value)
  caseLiquidChart.setOption(makeLiquid('#409eff', '#0050b3', '--\n案件'))

  volumeLiquidChart = echarts.init(volumeLiquidRef.value)
  volumeLiquidChart.setOption(makeLiquid('#13ce66', '#0d8a44', '--\n卷宗'))

  lawyerLiquidChart = echarts.init(lawyerLiquidRef.value)
  lawyerLiquidChart.setOption(makeLiquid('#6c5ce7', '#4a3db5', '--\n律师'))
}

/** 初始化网络流量趋势大图 (双线面积图) */
function initNetChart() {
  netChart = echarts.init(netChartRef.value)
  netChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['下载', '上传'], right: 10, textStyle: { color: '#a0a4b0', fontSize: 12 } },
    grid: { top: 30, right: 20, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      name: 'KB/s',
      nameTextStyle: { color: '#a0a4b0' },
      axisLabel: { color: '#a0a4b0' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        name: '下载',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#6c5ce7', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(108,92,231,0.3)' },
            { offset: 1, color: 'rgba(108,92,231,0.02)' },
          ]),
        },
      },
      {
        name: '上传',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#00b894', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,184,148,0.3)' },
            { offset: 1, color: 'rgba(0,184,148,0.02)' },
          ]),
        },
      },
    ],
  })
}

/** 计算网络速率 (通过与上次数据的差值) */
function calcNetworkDelta(network) {
  if (!prevNetwork) {
    prevNetwork = {
      bytes_recv: network.bytes_recv,
      bytes_sent: network.bytes_sent,
      time: Date.now(),
    }
    return { sent: 0, recv: 0 }
  }
  const elapsed = (Date.now() - prevNetwork.time) / 1000
  if (elapsed <= 0) return { sent: 0, recv: 0 }

  // (当前字节 - 历史字节) / 1024 = 增量KB， 再除以秒数得到 KB/s
  const recvDelta = Math.max(
    0,
    ((network.bytes_recv - prevNetwork.bytes_recv) / 1024) / elapsed,
  )
  const sentDelta = Math.max(
    0,
    ((network.bytes_sent - prevNetwork.bytes_sent) / 1024) / elapsed,
  )

  prevNetwork = {
    bytes_recv: network.bytes_recv,
    bytes_sent: network.bytes_sent,
    time: Date.now(),
  }

  // 保留2位小数让视觉更平滑，如果不需要小数可以用 Math.round
  return {
    sent: sentDelta.toFixed(2),
    recv: recvDelta.toFixed(2)
  }
}

/** 拉取全站统计数据（仅首次打开 Tab 时请求） */
async function fetchSiteStats() {
  try {
    const res = await request.get('/monitor/site-stats')
    const d = res.data.data || res.data
    siteStats.value = d

    // 更新水波球：填充比例 = 当前值 / 预设最大值 (向上取到整数)
    const caseRatio = Math.min(d.cases / 200, 1)
    const volumeRatio = Math.min(d.volumes / 500, 1)
    const lawyerRatio = Math.min(d.lawyers / 50, 1)

    // 直接在 series 内部更新 data 和 label 的 formatter
    caseLiquidChart?.setOption({
      series: [{ data: [caseRatio, caseRatio], label: { formatter: d.cases + '\n案件' } }],
    })
    volumeLiquidChart?.setOption({
      series: [{ data: [volumeRatio, volumeRatio], label: { formatter: d.volumes + '\n卷宗' } }],
    })
    lawyerLiquidChart?.setOption({
      series: [{ data: [lawyerRatio, lawyerRatio], label: { formatter: d.lawyers + '\n律师' } }],
    })
  } catch (e) {
    console.error('获取全站统计失败:', e)
  }
}

/** 拉取监控数据并更新所有图表 */
async function fetchMonitorData() {
  try {
    const res = await request.get('/monitor/system-info')
    const d = res.data.data || res.data
    monitorData.value = d

    const nd = calcNetworkDelta(d.network)
    networkDelta.value = nd

    const now = new Date().toLocaleTimeString('zh-CN', { hour12: false })

    // 维护历史数据队列
    const h = history.value
    h.cpu.push(d.cpu.percent)
    h.mem.push(d.memory.percent)
    h.disk_c.push(d.disk_c.percent)
    h.disk_d.push(d.disk_d.percent)
    h.recv.push(nd.recv)
    h.sent.push(nd.sent)
    h.disk_read.push(d.disk_io.read_kbps)
    h.disk_write.push(d.disk_io.write_kbps)
    h.timestamps.push(now)
    if (h.cpu.length > MAX_HISTORY) {
      ;[
        'cpu',
        'mem',
        'disk_c',
        'disk_d',
        'recv',
        'sent',
        'disk_read',
        'disk_write',
        'timestamps',
      ].forEach((k) => h[k].shift())
    }

    // 更新迷你 sparklines
    cpuSparkChart?.setOption(makeSparkOption(h.cpu, cpuColor.value))
    memSparkChart?.setOption(makeSparkOption(h.mem, memColor.value))
    diskCSparkChart?.setOption(makeSparkOption(h.disk_c, diskCColor.value))
    diskDSparkChart?.setOption(makeSparkOption(h.disk_d, diskDColor.value))

    const ts = h.timestamps

    // 更新 CPU 趋势大图（颜色随负载动态变化）
    cpuChart?.setOption({
      xAxis: { data: ts },
      series: [
        {
          data: h.cpu,
          lineStyle: { color: cpuColor.value },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: cpuColor.value + '40' },
              { offset: 1, color: cpuColor.value + '05' },
            ]),
          },
        },
      ],
    })

    // 更新内存趋势大图
    memChart?.setOption({ xAxis: { data: ts }, series: [{ data: h.mem }] })

    // 更新磁盘 I/O 图表
    diskIOChart?.setOption({
      xAxis: { data: ts },
      series: [{ data: h.disk_read }, { data: h.disk_write }],
    })

    // 更新网络趋势大图
    netChart?.setOption({ xAxis: { data: ts }, series: [{ data: h.recv }, { data: h.sent }] })

    // 更新 C 盘环形图
    diskCChart?.setOption({
      series: [
        {
          data: [
            { value: d.disk_c.used_gb, name: '已用' },
            { value: d.disk_c.free_gb, name: '可用' },
          ],
        },
      ],
    })

    // 更新 D 盘环形图
    diskDChart?.setOption({
      series: [
        {
          data: [
            { value: d.disk_d.used_gb, name: '已用' },
            { value: d.disk_d.free_gb, name: '可用' },
          ],
        },
      ],
    })
  } catch (e) {
    console.error('获取监控数据失败:', e)
  }
}

/** 启动或重置监控定时器 */
function startMonitorTimer() {
  if (monitorTimer.value) {
    clearInterval(monitorTimer.value)
    monitorTimer.value = null
  }
  // 如果选择的不是“暂停” (0)，则启动新定时器
  if (refreshInterval.value > 0) {
    monitorTimer.value = setInterval(fetchMonitorData, refreshInterval.value)
  }
}

/** 用户手动切换频率时的处理函数 */
function handleIntervalChange(val) {
  startMonitorTimer()
  if (val > 0) {
    fetchMonitorData() // 切换频率后，立刻主动拉取一次最新数据
    ElMessage.success(`刷新频率已切换为 ${val / 1000} 秒`)
  } else {
    ElMessage.warning('数据自动刷新已暂停')
  }
}

/** 销毁所有 ECharts 实例并清除定时器 */
function destroyMonitor() {
  clearInterval(monitorTimer.value)
  monitorTimer.value = null
  prevNetwork = null
  history.value = {
    cpu: [],
    mem: [],
    disk_c: [],
    disk_d: [],
    recv: [],
    sent: [],
    disk_read: [],
    disk_write: [],
    timestamps: [],
  }
  const charts = [
    cpuSparkChart,
    memSparkChart,
    diskCSparkChart,
    diskDSparkChart,
    cpuChart,
    memChart,
    diskIOChart,
    netChart,
    diskCChart,
    diskDChart,
    caseLiquidChart,
    volumeLiquidChart,
    lawyerLiquidChart,
  ]
  charts.forEach((c) => c?.dispose())
  cpuSparkChart = memSparkChart = diskCSparkChart = diskDSparkChart = null
  cpuChart = memChart = diskIOChart = netChart = diskCChart = diskDChart = null
  caseLiquidChart = volumeLiquidChart = lawyerLiquidChart = null
}

// 监听 Tab 切换，按需加载数据
watch(activeTab, (newTab, oldTab) => {
  if (newTab === 'ops_management') {
    // 自动设置为当天日期
    if (!logDate.value) {
      const today = new Date()
      const yyyy = today.getFullYear()
      const mm = String(today.getMonth() + 1).padStart(2, '0')
      const dd = String(today.getDate()).padStart(2, '0')
      logDate.value = `${yyyy}-${mm}-${dd}`
    }
    fetchCacheStats()
  }
  if (newTab === 'monitor') {
    nextTick(() => {
      initSparkCharts()
      initCpuChart()
      initMemChart()
      initDiskIOChart()
      initNetChart()
      initDiskCChart()
      initDiskDChart()
      initLiquidCharts()
      fetchMonitorData()
      fetchSiteStats()
      startMonitorTimer()
    })
  }
  if (oldTab === 'monitor') {
    destroyMonitor()
  }
})

onMounted(() => {
  fetchUsers()
  fetchAnnouncements()
})

onUnmounted(() => {
  destroyMonitor()
})
</script>

<style scoped>
.system-settings-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.toolbar {
  margin-bottom: 20px;
  display: flex;
}

/* 概览卡片样式 */
.overview-cards {
  margin-bottom: 24px;
}
.stat-card {
  border-radius: 8px;
  border: none;
  background-color: #f9fafc;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  padding: 20px;
}
.action-card {
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(19, 206, 102, 0.2);
}
.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  margin-right: 16px;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}
.stat-unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}
.stat-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* --- 运维管理面板样式 --- */
.ops-card {
  min-height: 300px; /* 将固定的 height 改为 min-height */
  height: 100%; /* 配合 flex 布局，让左右两个卡片在电脑端保持等高 */
  border-radius: 8px;
  box-sizing: border-box;
}

/* 确保 row 在大屏幕上开启 flex 并且允许拉伸，从而实现左右卡片等高 */
.tab-content .el-row {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cache-stats-body .stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  font-size: 14px;
  color: #606266;
}
.cache-stats-body .stat-num {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
.cache-action {
  text-align: center;
  margin-top: 15px;
}
.export-form {
  display: flex;
  align-items: center;
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

/* 富文本预览约束 */
.preview-container {
  padding: 10px 20px;
}
.preview-title {
  text-align: center;
  font-size: 22px;
  color: #303133;
  margin-bottom: 12px;
}
.preview-meta {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 20px;
}
.rich-text-content {
  min-height: 200px;
  max-height: 50vh;
  overflow-y: auto;
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
}
/* 防止富文本里的图片溢出弹窗 */
:deep(.rich-text-content img) {
  max-width: 100% !important;
  height: auto !important;
  border-radius: 8px;
  margin: 10px 0;
}
:deep(.rich-text-content p) {
  margin: 10px 0;
}

/* ========================================
   Grafana 风格监控面板样式
   ======================================== */
.monitor-dashboard {
  background: #1a1c23;
  border-radius: 8px;
  padding: 20px;
  min-height: 600px;
}

/* 刷新频率控制栏 */
.refresh-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.refresh-label {
  font-size: 13px;
  color: #a0a4b0;
}

/* 统计卡片行 */
.stat-row {
  margin-bottom: 0;
}
.grafana-stat-card {
  background: #21232b;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: box-shadow 0.3s;
  min-height: 140px;
}
.grafana-stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}
/* 紧凑模式（第二行 QPS/活跃用户/网络） */
.grafana-stat-card.compact {
  min-height: auto;
  padding: 14px 20px;
}
.grafana-stat-card .stat-label {
  font-size: 12px;
  color: #8e929a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.grafana-stat-card .stat-value-wrap {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}
.grafana-stat-card .stat-big-num {
  font-size: 36px;
  font-weight: 700;
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
  line-height: 1;
}
.grafana-stat-card .stat-unit {
  font-size: 16px;
  color: #8e929a;
  font-weight: 500;
}
.grafana-stat-card .stat-detail {
  font-size: 12px;
  color: #8e929a;
  margin-bottom: 8px;
}
.grafana-stat-card .stat-sparkline {
  width: 100%;
  height: 35px;
}

/* 主面板 */
.grafana-panel {
  background: #21232b;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  height: 100%;
}
.grafana-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #2a2d35;
}
.grafana-panel .panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #d0d2d8;
}
.grafana-panel .panel-subtitle {
  font-size: 11px;
  color: #6b6f78;
}
.grafana-panel .panel-chart {
  width: 100%;
  height: 280px;
}
/* 较矮的图表容器（环形图 / 水波球） */
.grafana-panel .panel-chart-sm {
  width: 100%;
  height: 220px;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .monitor-dashboard {
    padding: 12px 8px;
  }
  .grafana-stat-card {
    padding: 12px 14px;
    margin-bottom: 10px;
    min-height: auto;
  }
  .grafana-stat-card .stat-big-num {
    font-size: 26px;
  }
  .grafana-stat-card .stat-sparkline {
    height: 28px;
  }
  .grafana-panel .panel-chart {
    height: 220px;
  }
  .refresh-bar {
    justify-content: flex-start;
  }
  .refresh-label {
    font-size: 12px;
  }
}
</style>
