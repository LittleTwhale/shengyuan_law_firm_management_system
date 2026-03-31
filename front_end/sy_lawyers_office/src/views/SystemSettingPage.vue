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
            />
            <el-button type="primary" @click="fetchUsers">刷新列表</el-button>
          </div>

          <el-table :data="filteredUsers" border stripe v-loading="loading">
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

            <el-table-column label="最后更新时间" min-width="180">
              <template #default="{ row }">
                {{ row.updated_at || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统公告管理" name="announcements">
        <div class="tab-content">
          <div class="toolbar" style="margin-bottom: 20px">
            <el-button type="primary" @click="openNoticeForm()">发布新公告</el-button>
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
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="version" label="绑定版本" width="100" />
            <el-table-column prop="publisher_name" label="发布人" width="100" />

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

            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import SystemAnnouncementForm from '@/components/SystemAnnouncementForm.vue'

const activeTab = ref('permissions')
const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')

// --- 公告管理状态 ---
const announcementsList = ref([])
const noticeLoading = ref(false)
const noticeFormVisible = ref(false)
const currentNotice = ref(null)

// 新增：公告分页状态
const noticePage = ref(1)
const noticePageSize = ref(20)
const noticeTotal = ref(0)

// 获取用户及权限列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/system/users_with_permissions')

    users.value = res.data.map((u) => ({
      ...u,
      permissions: u.permissions || {
        can_review_case: false,
        can_approve_seal: false,
        can_access_admin: false,
        finance_manage: false,
        party_admin: false,
        volume_manage: false,
      },
    }))
  } catch (err) {
    console.error(err)
    ElMessage.error('获取用户权限列表失败，请检查后端接口')
  } finally {
    loading.value = false
  }
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

const filteredUsers = computed(() => {
  if (!searchKeyword.value) return users.value
  const lowerKey = searchKeyword.value.toLowerCase()
  return users.value.filter(
    (u) =>
      (u.real_name && u.real_name.toLowerCase().includes(lowerKey)) ||
      (u.accounts && u.accounts.toLowerCase().includes(lowerKey)),
  )
})

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

// 新增：处理分页大小变化
const handleNoticeSizeChange = (val) => {
  noticePageSize.value = val
  noticePage.value = 1
  fetchAnnouncements()
}

// 新增：处理页码变化
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
</style>
