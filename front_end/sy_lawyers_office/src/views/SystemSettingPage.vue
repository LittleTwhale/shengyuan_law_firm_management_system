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

      <el-tab-pane label="全局参数设置" name="configs">
        <el-empty description="此处可用于配置系统公告、文件上传大小限制等全局参数"></el-empty>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const activeTab = ref('permissions')
const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')

// 获取用户及权限列表
const fetchUsers = async () => {
  loading.value = true
  try {
    // 包含 permissions 字段的用户列表接口
    const res = await request.get('/admin/system/users_with_permissions')

    // 数据预处理：确保 permissions 对象存在，防止报错
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
    // 失败回滚视图状态
    user.permissions[permissionType] = !user.permissions[permissionType]

    // 动态提取后端的错误提示 (针对 FastAPI 的 HTTPException 结构)
    const errorMessage = err.response?.data?.detail || '权限更新失败，请稍后重试'

    // 使用 ElMessage 展示清晰的中文提示
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

onMounted(() => {
  fetchUsers()
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
