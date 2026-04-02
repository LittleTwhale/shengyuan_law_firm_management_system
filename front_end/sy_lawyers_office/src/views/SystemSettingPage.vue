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
                  :disabled="row.role === 'owner'"
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
import { ref, onMounted, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataLine, Plus } from '@element-plus/icons-vue' // 引入所需的图标
import SystemAnnouncementForm from '@/components/SystemAnnouncementForm.vue'

const activeTab = ref('permissions')
const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')

// 新增：用户列表的分页状态
const userPage = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)

// --- 公告管理状态 ---
const announcementsList = ref([])
const noticeLoading = ref(false)
const noticeFormVisible = ref(false)
const currentNotice = ref(null)

// 公告分页状态
const noticePage = ref(1)
const noticePageSize = ref(10)
const noticeTotal = ref(0)

// 获取用户及权限列表
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
    const errorMessage = err.response?.data?.detail || '权限更新失败，请稍后重试'
    ElMessage.error(errorMessage)
  }
}

const getRoleTag = (role) => {
  if (role === 'owner') return 'danger'
  if (role === 'admin') return 'warning'
  return 'info'
}

// --- 公告管理方法 ---
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
// 新增：公告预览相关逻辑
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
// 新增：阅读情况相关逻辑
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

/* --- 新增概览卡片样式 --- */
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

/* --- 富文本预览区域样式约束 --- */
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
</style>
