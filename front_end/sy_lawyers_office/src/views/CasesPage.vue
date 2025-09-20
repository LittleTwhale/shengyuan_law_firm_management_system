<template>
  <div class="cases-container">
    <!-- 顶部标题和按钮 -->
    <div class="content-header">
      <h2>案件管理</h2>
      <el-button type="primary" @click="showAddCaseDialog = true">新增案件</el-button>
    </div>

    <!-- 案件表格 -->
    <el-table :data="caseList" border style="width:100%">
      <el-table-column prop="id" label="案件编号" width="100" />
      <el-table-column prop="type" label="案件类型" width="120" />
      <el-table-column prop="client" label="委托人" />
      <el-table-column prop="fee" label="收费(元)" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button type="text" size="small" @click="editCase(scope.$index, scope.row)">编辑</el-button>
          <el-button type="text" size="small" @click="deleteCase(scope.$index, scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增案件弹窗 -->
    <el-dialog title="新增案件" v-model:visible="showAddCaseDialog" width="500px">
      <el-form :model="newCase" label-width="120px">
        <el-form-item label="案件类型">
          <el-select v-model="newCase.type" placeholder="选择案件类型">
            <el-option label="民事" value="民事"></el-option>
            <el-option label="刑事" value="刑事"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="委托人">
          <el-input v-model="newCase.client" placeholder="请输入委托人"></el-input>
        </el-form-item>
        <el-form-item label="收费">
          <el-input v-model="newCase.fee" type="number" placeholder="请输入收费金额"></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="newCase.status" placeholder="选择状态">
            <el-option label="待审批" value="待审批"></el-option>
            <el-option label="进行中" value="进行中"></el-option>
            <el-option label="已结案" value="已结案"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddCaseDialog = false">取消</el-button>
          <el-button type="primary" @click="addCase">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 弹窗控制
const showAddCaseDialog = ref(false)

// 新增案件表单
const newCase = reactive({
  type: '',
  client: '',
  fee: 0,
  status: '待审批'
})

// 案件数据
const caseList = ref([
  { id: 1, type: '民事', client: '王小明', fee: 5000, status: '进行中' },
  { id: 2, type: '刑事', client: '李四', fee: 8000, status: '待审批' }
])

// 添加案件
const addCase = () => {
  if (!newCase.type || !newCase.client) {
    ElMessage.warning('请完整填写案件信息')
    return
  }
  const id = caseList.value.length
    ? caseList.value[caseList.value.length - 1].id + 1
    : 1
  caseList.value.push({ id, ...newCase })
  ElMessage.success('案件添加成功')

  // 重置表单
  showAddCaseDialog.value = false
  newCase.type = ''
  newCase.client = ''
  newCase.fee = 0
  newCase.status = '待审批'
}

// 编辑案件
const editCase = (i, row) => {
  ElMessage.info(`编辑案件 ${row.id} 功能待实现`)
}

// 删除案件
const deleteCase = (i, row) => {
  caseList.value.splice(i, 1)
  ElMessage.success(`案件 ${row.id} 已删除`)
}
</script>

<style scoped>
.cases-container {
  padding: 20px;
}
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
