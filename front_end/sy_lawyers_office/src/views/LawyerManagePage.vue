<template>
  <div class="lawyer-management">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          class="search-input"
          v-model="searchKeyword"
          placeholder="请输入检索条件"
          clearable
          @clear="fetchUsers"
          @keyup.enter="fetchUsers"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" icon="el-icon-plus" @click="openDialog()"> 新增用户 </el-button>
      </div>
    </div>

    <div class="content-area">
      <el-table :data="pagedData" border stripe style="width: 100%; height: 100%">
        <el-table-column prop="id" label="ID" min-width="70" />
        <el-table-column prop="accounts" label="账号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="real_name" label="姓名" min-width="110" show-overflow-tooltip />
        <el-table-column prop="role" label="角色" min-width="100" />
        <el-table-column prop="position" label="职位" min-width="130" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="170" show-overflow-tooltip />
        <el-table-column label="操作" min-width="130" fixed="right">
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
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="filteredList.length"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[10, 15, 20]"
        background
      />
    </div>

    <el-dialog
      class="responsive-dialog"
      :title="editUser ? '编辑用户' : '新增用户'"
      v-model="dialogVisible"
    >
      <el-form
        :model="form"
        :rules="formRules"
        ref="formRef"
        label-width="80px"
        class="custom-form"
      >
        <el-form-item label="账号" prop="accounts">
          <el-input v-model="form.accounts" :disabled="editUser" placeholder="请输入账号" />
        </el-form-item>

        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入姓名" />
        </el-form-item>

        <el-form-item label="职位" prop="position">
          <el-input v-model="form.position" placeholder="请输入职位" />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role"  style="width: 100%">
            <el-option label="普通用户" value="user" />

            <el-option v-if="hasAuthorizePower" label="管理员" value="admin" />
          </el-select>
        </el-form-item>

        <el-form-item label="密码" prop="password" v-if="editUser">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="不填则不修改密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="密码" prop="password" v-else>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue' // 引入搜索图标
import request from '@/utils/request'

// 当前用户角色
const role = localStorage.getItem('role')
const userPermissions = JSON.parse(localStorage.getItem('permissions') || '{}')
const canAccessAdmin = userPermissions.can_access_admin === true
// 判断当前用户是否拥有“管理授权”的权力
const hasAuthorizePower = computed(() => {
  return role === 'owner' || (role === 'admin' && canAccessAdmin)
})

// 用户列表及搜索
const users = ref([])
const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(15)

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
  return users.value.filter(
    (u) =>
      u.accounts.includes(searchKeyword.value) ||
      u.real_name.includes(searchKeyword.value) ||
      u.position.includes(searchKeyword.value) ||
      u.role.includes(searchKeyword.value),
  )
})
const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// --------------------------
// 权限控制
// --------------------------
const canEdit = (row) => {
  // 有权限的管理员可以修改其他管理员
  if (role === 'owner' || canAccessAdmin) return row.role !== 'owner'
  if (role === 'admin') {
    // 普通管理员只能编辑普通用户（user）
    return row.role === 'user'
  }
  return false
}
const canDelete = (row) => canEdit(row)

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
    { min: 3, max: 20, message: '账号长度需为3~20位', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  position: [{ required: true, message: '请输入职位', trigger: 'blur' }],
  password: [
    {
      validator: (_, value, callback) => {
        // 编辑时允许密码为空
        if (editUser.value && !value) return callback()
        if (!value) return callback(new Error('请输入密码'))
        if (value.length < 6 || value.length > 20) return callback(new Error('密码长度需为6~20位'))
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// --------------------------
// 接口请求
// --------------------------
const fetchUsers = async () => {
  try {
    const res = await request.get('/lawyer_manage/users')
    users.value = res.data || []
  } catch (err) {
    console.error('获取用户列表失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取用户列表失败')
  }
}

// --------------------------
// 保存用户信息
// --------------------------
const handleSave = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return // 表单验证不通过

    try {
      const payload = { ...form.value }
      if (editUser.value && !payload.password) {
        delete payload.password // 空密码不提交
      }

      if (editUser.value) {
        // 编辑：PUT 请求
        await request.put(`/lawyer_manage/users/${form.value.id}`, payload)
        ElMessage.success('用户信息已更新')
      } else {
        // 新增：POST 请求
        await request.post('/lawyer_manage/users', payload)
        ElMessage.success('用户已新增')
      }

      dialogVisible.value = false
      await fetchUsers()
    } catch (err) {
      console.error('保存失败:', err)
      ElMessage.error(err.response?.data?.detail || '保存失败')
    }
  })
}

// --------------------------
// 删除用户
// --------------------------
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 ${row.real_name} 吗？`, '提示', { type: 'warning' })

    await request.delete(`/lawyer_manage/users/${row.id}`)

    ElMessage.success('用户已删除')
    await fetchUsers()
  } catch (err) {
    if (err !== 'cancel') {
      // 排除用户取消删除的情况
      console.error('删除失败:', err)
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

// --------------------------
// 初始化
// --------------------------
onMounted(() => fetchUsers())
</script>

<style scoped>
/* 容器采用卡片式设计，更具现代感 */
.lawyer-management {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px); /* 预留边距 */
  margin: 20px;
  padding: 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

/* 顶部工具栏适配 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap; /* 允许换行 */
}

.search-input {
  width: 280px;
}

/* 表格区域 */
.content-area {
  flex: 1;
  overflow: hidden; /* 防止外层滚动，将滚动交给 el-table 内部 */
  position: relative;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

/* 修复 Element Plus 文本溢出显示 */
:deep(.el-table .cell) {
  white-space: nowrap;
}

/* 分页容器 */
.pagination-container {
  width: 100%;
  margin-top: 20px;
  display: flex;
  justify-content: flex-end; /* PC端靠右对齐更符合直觉 */
}

/* 弹窗全局宽度控制 */
:deep(.responsive-dialog) {
  width: 90% !important;
  max-width: 500px !important;
  border-radius: 8px;
}

/* --- 移动端响应式适配 (视口宽度 <= 768px) --- */
@media (max-width: 768px) {
  .lawyer-management {
    margin: 10px;
    padding: 16px;
    height: calc(100vh - 20px);
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-left,
  .toolbar-right,
  .search-input {
    width: 100%;
  }

  .toolbar-right .el-button {
    width: 100%; /* 移动端按钮撑满 */
  }

  /* --- 修复操作列过宽的问题 --- */
  /* 缩小表格内按钮的内边距，节省空间 */
  :deep(.el-table .el-button--small) {
    padding: 5px 8px;
    margin-left: 0;
    margin-right: 4px;
  }
  :deep(.el-table .el-button--small:last-child) {
    margin-right: 0;
  }

  /* --- 修复分页器溢出的问题 --- */
  /* 在手机端隐藏“总条数”和“多少条/页”下拉框，只保留上下页和页码 */
  :deep(.el-pagination__sizes),
  :deep(.el-pagination__total),
  :deep(.el-pagination__jump) {
    display: none !important;
  }

  .pagination-container {
    justify-content: center;
    overflow-x: auto;
    padding-bottom: 10px;
    width: 100%;
  }

  :deep(.el-pagination) {
    flex-wrap: nowrap;
  }
}
</style>
