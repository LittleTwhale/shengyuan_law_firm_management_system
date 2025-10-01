<template>
  <div class="case-review-page">
    <div class="header">
      <h2>案件审核</h2>
      <el-button type="primary" @click="toggleHistory">
        {{ showHistory ? '返回待审核' : '查看历史记录' }}
      </el-button>
    </div>

    <el-table :data="casesList" style="width: 100%">
      <el-table-column prop="operation_id" label="ID" width="80" />
      <el-table-column prop="case_id" label="案件ID" />
      <el-table-column prop="operation_type" label="操作类型" />
      <el-table-column prop="user_name" label="提交人" />
      <el-table-column label="操作详情">
        <template #default="scope">
          <div v-for="(item, index) in scope.row.details" :key="index">
            <span>{{ item.field }}: </span>
            <span v-if="item.old_value !== null">原值: {{ item.old_value }} </span>
            <span v-if="item.new_value !== null">新值: {{ item.new_value }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column v-if="!showHistory" label="操作">
        <template #default="scope">
          <el-button type="success" size="small" @click="review(scope.row, true)">通过</el-button>
          <el-button type="danger" size="small" @click="review(scope.row, false)">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8001'

const casesList = ref([])
const showHistory = ref(false)
const currentUserId = 1 // TODO: 替换为登录用户动态ID
const currentUserRole = 'admin' // TODO: 替换为登录用户角色

const fetchPendingCases = async () => {
  try {
    const res = await axios.get(`${API_BASE}/case_review/pending`, {
      params: { role: currentUserRole }
    })
    casesList.value = res.data
  } catch (err) {
    console.error(err)
    ElMessage.error('获取待审核案件失败')
  }
}

const fetchAllOperations = async () => {
  try {
    const res = await axios.get(`${API_BASE}/case_review/all`, {
      params: { role: currentUserRole }
    })
    casesList.value = res.data
  } catch (err) {
    console.error(err)
    ElMessage.error('获取历史记录失败')
  }
}

const toggleHistory = () => {
  showHistory.value = !showHistory.value
  if (showHistory.value) {
    fetchAllOperations()
  } else {
    fetchPendingCases()
  }
}

const review = async (row, approved) => {
  try {
    await axios.put(`${API_BASE}/case_review/${row.operation_id}/review`, {
      review_status: approved ? '已通过' : '已拒绝',
      review_user_id: currentUserId
    }, {
      params: { role: currentUserRole }
    })
    ElMessage.success('操作成功')
    await fetchPendingCases()
  } catch (err) {
    console.error(err)
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchPendingCases()
})
</script>

<style scoped>
.case-review-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
</style>
