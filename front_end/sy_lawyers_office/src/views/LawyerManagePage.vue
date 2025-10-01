<template>
  <div class="lawyer-management">
    <!-- 顶部搜索与操作区 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入检索条件"
          clearable
          @clear="fetchUsers"
          @keyup.enter="fetchUsers"
          style="width: 250px"
        />
      </div>
      <div class="toolbar-right">
        <el-button type="primary" icon="el-icon-plus" @click="openDialog()">
          新增用户
        </el-button>
      </div>
    </div>

    <!-- 用户表格 -->
    <div class="content-area">
      <el-table :data="pagedData" border stripe style="flex: 1;">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="accounts" label="账号" width="150" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="position" label="职位" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="220">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="openDialog(scope.row)"
              v-if="canEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
              v-if="canDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="filteredList.length"
          layout="total, prev, pager, next, sizes"
          :page-sizes="[10, 15, 20]"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="editUser ? '编辑用户' : '新增用户'" v-model="dialogVisible">
      <!-- 表单：绑定 formRules 实现验证 -->
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <!-- 账号 -->
        <el-form-item label="账号" prop="accounts">
          <el-input v-model="form.accounts" :disabled="editUser" />
        </el-form-item>

        <!-- 姓名 -->
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>

        <!-- 职位 -->
        <el-form-item label="职位" prop="position">
          <el-input v-model="form.position" />
        </el-form-item>

        <!-- 角色选择 -->
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" :disabled="role === 'admin'">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" v-if="role === 'owner'" />
          </el-select>
        </el-form-item>

        <!-- 密码 -->
        <!-- 编辑用户时可为空，不修改密码 -->
        <el-form-item label="密码" prop="password" v-if="editUser">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="不填则不修改密码"
          />
        </el-form-item>

        <!-- 新增用户时密码必填 -->
        <el-form-item label="密码" prop="password" v-else>
          <el-input v-model="form.password" type="password" />
        </el-form-item>
      </el-form>

      <!-- 弹窗底部按钮 -->
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 当前用户角色
const role = sessionStorage.getItem('role')

// 用户列表及搜索
const users = ref([])
const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(5)

// 弹窗控制
const dialogVisible = ref(false)
const editUser = ref(false)
const form = ref({})
const formRef = ref(null) // 表单引用

// --------------------------
// 计算属性：搜索和分页
// --------------------------
const filteredList = computed(() => {
  if (!searchKeyword.value) return users.value
  return users.value.filter(u =>
    u.accounts.includes(searchKeyword.value) ||
    u.real_name.includes(searchKeyword.value) ||
    u.position.includes(searchKeyword.value) ||
    u.role.includes(searchKeyword.value)
  )
})
const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// --------------------------
// 权限控制
// --------------------------
const canEdit = row => {
  if (role === 'owner') return row.role !== 'owner'
  if (role === 'admin') return row.role === 'user'
  return false
}
const canDelete = row => canEdit(row)

// --------------------------
// 弹窗操作
// --------------------------
const openDialog = (row = null) => {
  if (row) {
    editUser.value = true
    form.value = { ...row }
  } else {
    editUser.value = false
    form.value = { accounts: '', real_name: '', position: '', role: 'user', password: '' }
  }
  dialogVisible.value = true
}

// --------------------------
// 表单验证规则
// --------------------------
const formRules = {
  accounts: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度需为3~20位', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  position: [
    { required: true, message: '请输入职位', trigger: 'blur' }
  ],
  password: [
    {
      validator: (_, value, callback) => {
        // 编辑时允许密码为空
        if (editUser.value && !value) return callback()
        if (!value) return callback(new Error('请输入密码'))
        if (value.length < 6 || value.length > 20)
          return callback(new Error('密码长度需为6~20位'))
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// --------------------------
// 接口请求
// --------------------------
const fetchUsers = async () => {
  try {
    const res = await fetch(`http://127.0.0.1:8001/lawyer_manage/users?role=${role}`)
    if (!res.ok) {
      ElMessage.error('获取用户列表失败')
      return
    }
    users.value = await res.json()
  } catch (err) {
    ElMessage.error(err.message)
  }
}

// --------------------------
// 保存用户信息
// --------------------------
const handleSave = () => {
  formRef.value.validate(async valid => {
    if (!valid) return // 表单验证不通过

    try {
      const payload = { ...form.value }
      if (editUser.value && !payload.password) {
        delete payload.password // 空密码不提交
      }

      if (editUser.value) {
        const res = await fetch(`http://127.0.0.1:8001/lawyer_manage/users/${form.value.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        if (!res.ok) {
          ElMessage.error('更新失败')
          return
        }
        ElMessage.success('用户信息已更新')
      } else {
        const res = await fetch(`http://127.0.0.1:8001/lawyer_manage/users`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        if (!res.ok) {
          ElMessage.error('新增失败')
          return
        }
        ElMessage.success('用户已新增')
      }

      dialogVisible.value = false
      await fetchUsers()
    } catch (err) {
      ElMessage.error(err.message)
    }
  })
}

// --------------------------
// 删除用户
// --------------------------
const handleDelete = async row => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 ${row.real_name} 吗？`, '提示', { type: 'warning' })
    const res = await fetch(`http://127.0.0.1:8001/lawyer_manage/users/${row.id}`, { method: 'DELETE' })
    if (!res.ok) {
      ElMessage.error('删除失败')
      return
    }
    ElMessage.success('用户已删除')
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.message)
  }
}

// --------------------------
// 初始化
// --------------------------
onMounted(() => fetchUsers())
</script>

<style scoped>
.lawyer-management {
  display: flex;
  flex-direction: column;
  height: 100vh; /* 整个页面高度 */
  padding: 20px;
}
/* 弹窗样式 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.content-area {
  display: flex;
  flex-direction: column;
  flex: 0.9; /* 占满剩余空间 */
  overflow: hidden;
  position: relative;
}
::v-deep(.el-table .cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 分页容器居中 */
.pagination-container {
  width: 100%;
  margin-top: 20px;
  text-align: center;
}
</style>
