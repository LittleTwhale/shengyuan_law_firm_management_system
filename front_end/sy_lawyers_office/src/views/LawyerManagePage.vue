<template>
  <div class="lawyer-management">
    <!-- 顶部搜索与操作区 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="请输入检索条件"
        clearable
        @clear="filterData"
        @keyup.enter="filterData"
        style="width: 250px"
      />
      <el-button
        type="primary"
        icon="el-icon-plus"
        @click="openDialog()"
      >
        新增用户
      </el-button>
    </div>

    <!-- 内容区：表格 + 底部分页 -->
    <div class="content-area">
      <!-- 用户表格 -->
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
          :page-sizes="[ 10, 15, 20]"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="editUser ? '编辑用户' : '新增用户'" v-model="dialogVisible">
      <el-form :model="form">
        <el-form-item label="账号">
          <el-input v-model="form.accounts" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" />
        </el-form-item>
        <el-form-item label="角色" v-if="role === 'owner'">
          <el-select v-model="form.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" v-if="!editUser">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 当前角色（模拟登录角色，可改为 'user' / 'admin' / 'owner'）
const role = localStorage.getItem('role') || 'owner'

// 模拟数据
const mockUsers = ref([
  { id: 1, accounts: 'zhangsan', real_name: '张三', role: 'user', position: '实习律师', created_at: '2025-01-10 09:30' },
  { id: 2, accounts: 'lisi', real_name: '李四', role: 'admin', position: '合伙人', created_at: '2025-02-15 14:20' },
  { id: 3, accounts: 'wangwu', real_name: '王五', role: 'user', position: '专职律师', created_at: '2025-03-01 11:05' },
  { id: 4, accounts: 'owner1', real_name: '赵六', role: 'owner', position: '主任律师', created_at: '2025-03-12 16:45' },
  { id: 5, accounts: 'heqi', real_name: '何七', role: 'user', position: '兼职律师', created_at: '2025-04-03 18:10' },
  { id: 6, accounts: 'sunqi', real_name: '孙七', role: 'user', position: '兼职律师', created_at: '2025-04-18 12:30' },
  { id: 7, accounts: 'liqi', real_name: '李七', role: 'user', position: '兼职律师', created_at: '2025-04-28 17:00' },
  { id: 8, accounts: 'zhouqi', real_name: '周七', role: 'user', position: '兼职律师', created_at: '2025-05-05 13:45' },
  { id: 9, accounts: 'zhouqi', real_name: '周八', role: 'user', position: '兼职律师', created_at: '2025-05-12 14:30' },
  { id: 10, accounts: 'zhouqi', real_name: '周九', role: 'user', position: '兼职律师', created_at: '2025-05-19 15:15' },
  { id: 11, accounts: 'zhouqi', real_name: '周十', role: 'user', position: '兼职律师', created_at: '2025-05-26 16:30' },
  { id: 12, accounts: 'zhouqi', real_name: '周十一', role: 'user', position: '兼职律师', created_at: '2025-05-31 17:45' },
  { id: 13, accounts: 'zhouqi', real_name: '周十二', role: 'user', position: '兼职律师', created_at: '2025-06-02 18:00' },
  { id: 14, accounts: 'zhouqi', real_name: '周十三', role: 'user', position: '兼职律师', created_at: '2025-06-07 19:15' },
  { id: 15, accounts: 'zhouqi', real_name: '周十四', role: 'user', position: '兼职律师', created_at: '2025-06-12 19:30' },
])

// 搜索和分页
const searchKeyword = ref('')
const filteredList = computed(() => {
  if (!searchKeyword.value) return mockUsers.value
  return mockUsers.value.filter(
    (u) =>
      u.accounts.includes(searchKeyword.value) ||
      u.real_name.includes(searchKeyword.value) ||
      u.position.includes(searchKeyword.value) ||
      u.role.includes(searchKeyword.value)
  )
})

const page = ref(1)
const pageSize = ref(5)
const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// 弹窗
const dialogVisible = ref(false)
const editUser = ref(false)
const form = ref({})

// 权限控制
const canEdit = (row) => {
  if (role === 'owner') return row.role !== 'owner'
  if (role === 'admin') return row.role === 'user'
  return false
}
const canDelete = (row) => canEdit(row)

const openDialog = (row = null) => {
  if (row) {
    editUser.value = true
    form.value = { ...row }
  } else {
    editUser.value = false
    form.value = {
      id: Date.now(),
      accounts: '',
      real_name: '',
      position: '',
      role: 'user',
      password: '',
      created_at: new Date().toISOString().slice(0, 19).replace('T', ' ')
    }
  }
  dialogVisible.value = true
}

const handleSave = () => {
  if (editUser.value) {
    const index = mockUsers.value.findIndex((u) => u.id === form.value.id)
    if (index !== -1) {
      mockUsers.value[index] = { ...form.value }
      ElMessage.success('用户信息已更新')
    }
  } else {
    mockUsers.value.push({ ...form.value })
    ElMessage.success('用户已新增')
  }
  dialogVisible.value = false
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除用户 ${row.real_name} 吗？`, '提示', {
    type: 'warning'
  })
    .then(() => {
      mockUsers.value = mockUsers.value.filter((u) => u.id !== row.id)
      ElMessage.success('用户已删除')
    })
    .catch(() => {})
}

const filterData = () => {
  page.value = 1 // 搜索后重置到第一页
}
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
  gap: 10px;
  margin-bottom: 10px;
}
.content-area {
  display: flex;
  flex-direction: column;
  flex: 0.9; /* 占满剩余空间 */
  overflow: hidden;
  position: relative;
}
/* 分页容器居中 */
.pagination-container {
  width: 100%;
  margin-top: 20px;
  text-align: center;
}
</style>
