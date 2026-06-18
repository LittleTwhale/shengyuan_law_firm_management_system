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
              <el-col :xs="24" :sm="12" :md="8">
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
              <el-col :xs="24" :sm="12" :md="8">
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

          <!-- ========== 桌面端：表格视图 ========== -->
          <div v-show="!isMobile">
            <el-table :data="announcementsList" border stripe v-loading="noticeLoading">
              <el-table-column prop="id" label="ID" width="60" align="center" />
              <el-table-column prop="type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag
                    :type="
                      row.type === 'update_log'
                        ? 'success'
                        : row.type === 'case_review'
                          ? 'danger'
                          : 'info'
                    "
                  >
                    {{
                      row.type === 'update_log'
                        ? '更新日志'
                        : row.type === 'case_review'
                          ? '审核驳回'
                          : '系统公告'
                    }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="标题" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span
                    v-if="row.type === 'case_review' && row.related_case_id"
                    class="case-link-title"
                    @click="goToCase(row.related_case_id)"
                  >
                    {{ row.title }}
                    <el-icon style="margin-left: 4px; font-size: 13px"><Link /></el-icon>
                  </span>
                  <span v-else>{{ row.title }}</span>
                </template>
              </el-table-column>
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
          </div>

          <!-- ========== 移动端：卡片列表视图 ========== -->
          <div v-show="isMobile" class="notice-card-list" v-loading="noticeLoading">
            <div v-for="item in announcementsList" :key="item.id" class="notice-card">
              <!-- 卡片头部：类型标签 + 发布状态开关 -->
              <div class="notice-card-header">
                <div class="notice-card-header-left">
                  <el-tag
                    :type="
                      item.type === 'update_log'
                        ? 'success'
                        : item.type === 'case_review'
                          ? 'danger'
                          : 'info'
                    "
                    size="small"
                  >
                    {{
                      item.type === 'update_log'
                        ? '更新日志'
                        : item.type === 'case_review'
                          ? '审核驳回'
                          : '系统公告'
                    }}
                  </el-tag>
                  <span class="notice-card-id">#{{ item.id }}</span>
                </div>
                <el-switch
                  v-model="item.is_active"
                  @change="toggleNoticeStatus(item)"
                  style="--el-switch-on-color: #13ce66"
                  size="small"
                />
              </div>

              <!-- 卡片标题 -->
              <div class="notice-card-title">
                <span
                  v-if="item.type === 'case_review' && item.related_case_id"
                  class="case-link-title"
                  @click="goToCase(item.related_case_id)"
                >
                  {{ item.title }}
                  <el-icon style="margin-left: 4px; font-size: 12px"><Link /></el-icon>
                </span>
                <span v-else>{{ item.title }}</span>
              </div>

              <!-- 卡片元数据 -->
              <div class="notice-card-meta">
                <span class="meta-item">
                  <span class="meta-label">发布人：</span>{{ item.publisher_name || '-' }}
                </span>
                <span v-if="item.version" class="meta-item">
                  <span class="meta-label">版本：</span>v{{ item.version }}
                </span>
                <span class="meta-item">
                  <span class="meta-label">时间：</span>{{ item.created_at || '-' }}
                </span>
              </div>

              <!-- 卡片操作按钮 -->
              <div class="notice-card-actions">
                <el-button size="small" type="primary" plain @click="openPreviewDialog(item)"
                  >预览</el-button
                >
                <el-button size="small" type="warning" plain @click="openNoticeForm(item)"
                  >编辑</el-button
                >
                <el-button size="small" type="danger" plain @click="openReadStatusDialog(item)"
                  >明细</el-button
                >
                <el-button size="small" type="danger" @click="deleteNotice(item.id)"
                  >删除</el-button
                >
              </div>
            </div>

            <!-- 空状态 -->
            <el-empty
              v-if="!announcementsList.length && !noticeLoading"
              description="暂无公告数据"
            />
          </div>

          <div
            class="pagination-wrapper"
            style="margin-top: 20px; display: flex; justify-content: flex-end"
          >
            <el-pagination
              v-model:current-page="noticePage"
              v-model:page-size="noticePageSize"
              :total="noticeTotal"
              :page-sizes="[10, 20, 50]"
              :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next'"
              :pager-count="isMobile ? 5 : 7"
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
        <ServerMonitor v-if="activeTab === 'monitor'" />
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
      :width="isMobile ? '95%' : '700px'"
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

    <el-dialog
      v-model="previewVisible"
      title="公告预览 (用户视角)"
      :width="isMobile ? '95%' : '750px'"
      center
    >
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
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataLine, Plus, Download, Delete, Link } from '@element-plus/icons-vue'
import SystemAnnouncementForm from '@/components/SystemAnnouncementForm.vue'
import ServerMonitor from '@/components/ServerMonitor.vue'

const router = useRouter()

// 跳转到案件详情（审核驳回公告专用）
const goToCase = (caseId) => {
  if (caseId) {
    router.push(`/main/cases/${caseId}`)
  }
}

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
// 移动端响应式适配
// =====================================
const isMobile = ref(false)
const checkDeviceType = () => {
  isMobile.value = window.innerWidth <= 768
}
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}
onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

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
    await fetchCacheStats()
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

// 监听 Tab 切换，按需加载数据
watch(activeTab, (newTab) => {
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
})

onMounted(() => {
  fetchUsers()
  fetchAnnouncements()
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

/* 审核驳回公告标题 — 可点击跳转至案件详情 */
.case-link-title {
  color: #165dff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: color 0.2s;
}
.case-link-title:hover {
  color: #0a3bb5;
  text-decoration: underline;
}

/* =====================================
   移动端：公告卡片列表样式
   ===================================== */
.notice-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notice-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;
}
.notice-card:active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notice-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.notice-card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.notice-card-id {
  font-size: 12px;
  color: #909399;
}

.notice-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  line-height: 1.5;
  word-break: break-word;
}

.notice-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #606266;
}
.meta-item {
  display: inline-flex;
  align-items: center;
}
.meta-label {
  color: #909399;
  margin-right: 2px;
}

.notice-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}
.notice-card-actions .el-button {
  flex: 1;
  min-width: 0;
}

/* =====================================
   全局移动端适配样式
   ===================================== */
@media (max-width: 768px) {
  .system-settings-page {
    padding: 10px;
  }
  .header h2 {
    font-size: 18px;
  }
  .settings-tabs :deep(.el-tabs__nav-wrap) {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  /* 站点公告分页：移动端隐藏 size 切换 */
  .pagination-wrapper :deep(.el-pagination__sizes) {
    display: none !important;
  }
}
</style>
