<template>
  <div class="electronic-seal-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>电子用印</h2>
      <el-button v-if="isAdmin" type="primary" @click="showCreateSealDialog = true">
        <el-icon><Plus /></el-icon>新增电子印章
      </el-button>
    </div>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" class="seal-tabs">
      <!-- 印章管理标签页 -->
      <el-tab-pane label="印章管理" name="seal-management">
        <!-- 印章列表 -->
        <el-table :data="sealList" border style="width: 100%" v-loading="loading.seals">
          <el-table-column prop="id" label="印章ID" width="80" />
          <el-table-column prop="name" label="印章名称" />
          <el-table-column label="印章预览" width="120">
            <template #default="scope">
              <el-image
                :src="getSealImageUrl(scope.row.id)"
                :preview-src-list="[getSealImageUrl(scope.row.id)]"
                style="width: 60px; height: 60px; object-fit: contain"
              />
            </template>
          </el-table-column>
          <el-table-column prop="image_type" label="文件类型" />
          <el-table-column prop="image_size" label="大小(KB)" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="scope">
              <el-switch
                v-model="scope.row.is_active"
                active-text="启用"
                inactive-text="禁用"
                @change="handleSealStatusChange(scope.row)"
                :disabled="!isAdmin"
              />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" v-if="isAdmin">
            <template #default="scope">
              <el-button
                text
                type="danger"
                @click="handleDeleteSeal(scope.row.id)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 用印申请标签页 -->
      <el-tab-pane label="用印申请" name="seal-application">
        <!-- 申请表单 -->
        <el-card class="application-form-card">
          <template #header>
            <div>新建用印申请</div>
          </template>
          <el-form
            :model="applicationForm"
            :rules="applicationRules"
            ref="applicationFormRef"
            label-width="100px"
          >
            <el-form-item label="选择印章" prop="seal_id">
              <el-select
                v-model="applicationForm.seal_id"
                placeholder="请选择需要使用的印章"
                style="width: 100%"
              >
                <el-option
                  v-for="seal in activeSeals"
                  :key="seal.id"
                  :label="seal.name"
                  :value="seal.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="用印原因" prop="application_reason">
              <el-input
                v-model="applicationForm.application_reason"
                type="textarea"
                :rows="3"
                placeholder="请说明用印原因"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="上传文件" prop="file">
              <el-upload
                class="upload-demo"
                ref="fileUploadRef"
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :file-list="uploadFileList"
                :accept="'.pdf,.doc,.docx'"
                :limit="1"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>选择待盖章文件
                </el-button>
                <template #tip>
                  <div class="el-upload__tip">支持上传PDF、Word(.doc,.docx)格式文件</div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="submitApplication"
                :loading="loading.submitting"
              >
                提交申请
              </el-button>
              <el-button @click="resetApplicationForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 申请记录 -->
        <el-card class="application-list-card" style="margin-top: 20px;">
          <template #header>
            <div>我的用印申请记录</div>
          </template>
          <el-table :data="applicationList" border style="width: 100%" v-loading="loading.applications">
            <el-table-column prop="id" label="申请ID" width="80" />
            <el-table-column prop="file_name" label="文件名称" />
            <el-table-column prop="seal.name" label="使用印章" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag
                  :type="statusTagType(scope.row.status)"
                >{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="申请时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280">
              <template #default="scope">
                <el-button
                  text
                  size="small"
                  @click="handleViewApplication(scope.row)"
                >
                  查看详情
                </el-button>
                <el-button
                  text
                  type="success"
                  size="small"
                  @click="handleSetSealPosition(scope.row)"
                  v-if="scope.row.status === '已通过' && !scope.row.sealed_file_path"
                >
                  设置盖章位置
                </el-button>
                <el-button
                  text
                  type="primary"
                  size="small"
                  @click="handleApplySeal(scope.row)"
                  v-if="scope.row.status === '已通过' && scope.row.seal_positions && scope.row.seal_positions.length > 0 && !scope.row.sealed_file_path"
                >
                  执行盖章
                </el-button>
                <el-button
                  text
                  type="info"
                  size="small"
                  @click="downloadSealedFile(scope.row)"
                  v-if="scope.row.sealed_file_path"
                >
                  下载盖章文件
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 申请审核标签页（仅管理员可见） -->
      <el-tab-pane label="申请审核" name="seal-review" v-if="isAdmin">
        <!-- 待审核列表 -->
        <el-table :data="pendingApplications" border style="width: 100%" v-loading="loading.pending">
          <el-table-column prop="id" label="申请ID" width="80" />
          <el-table-column prop="file_name" label="文件名称" />
          <el-table-column prop="applicant.real_name" label="申请人" />
          <el-table-column prop="seal.name" label="使用印章" />
          <el-table-column prop="application_reason" label="用印原因" show-overflow-tooltip />
          <el-table-column prop="created_at" label="申请时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button
                text
                type="success"
                size="small"
                @click="reviewApplication(scope.row, '已通过')"
              >
                通过
              </el-button>
              <el-button
                text
                type="danger"
                size="small"
                @click="reviewApplication(scope.row, '已拒绝')"
              >
                拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增印章弹窗 -->
    <el-dialog
      title="新增电子印章"
      v-model="showCreateSealDialog"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="sealForm" :rules="sealRules" ref="sealFormRef" label-width="100px">
        <el-form-item label="印章名称" prop="name">
          <el-input
            v-model="sealForm.name"
            placeholder="请输入印章名称（如：公章、合同章）"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="印章图片" prop="file">
          <el-upload
            class="upload-demo"
            ref="sealUploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleSealFileChange"
            :on-remove="handleSealFileRemove"
            :file-list="sealFileList"
            :accept="'.png,.jpg,.jpeg'"
            :limit="1"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>选择印章图片
            </el-button>
            <template #tip>
              <div class="el-upload__tip">支持上传PNG、JPG格式图片</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSealDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="createSeal"
          :loading="loading.creatingSeal"
          :disabled="sealFileList.length === 0"
        >
          确认创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 印章位置设置弹窗 -->
    <el-dialog
      title="设置印章位置"
      v-model="showPositionDialog"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div class="position-setting-container">
        <!-- PDF预览区域 -->
        <div class="pdf-preview">
          <iframe
            :src="previewFileUrl"
            class="pdf-iframe"
            @load="initPdfViewer"
          ></iframe>
        </div>

        <!-- 位置设置控件 -->
        <div class="position-controls">
          <el-form :model="positionForm" label-width="80px">
            <el-form-item label="页码">
              <el-input-number
                v-model="positionForm.page_num"
                :min="1"
                :max="totalPages"
                @change="handlePageChange"
              />
            </el-form-item>
            <el-form-item label="X坐标">
              <el-input-number v-model="positionForm.x" :min="0" :max="1000" />
            </el-form-item>
            <el-form-item label="Y坐标">
              <el-input-number v-model="positionForm.y" :min="0" :max="1000" />
            </el-form-item>
            <el-form-item label="宽度">
              <el-input-number v-model="positionForm.width" :min="10" :max="500" />
            </el-form-item>
            <el-form-item label="高度">
              <el-input-number v-model="positionForm.height" :min="10" :max="500" />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                @click="addSealPosition"
              >
                添加位置
              </el-button>
              <el-button @click="resetPositionForm">重置</el-button>
            </el-form-item>
          </el-form>

          <div class="position-list">
            <h4>已添加位置</h4>
            <div class="position-item" v-for="(pos, index) in currentPositions" :key="index">
              页码: {{ pos.page_num }} - X: {{ pos.x }}, Y: {{ pos.y }} ({{ pos.width }}×{{ pos.height }})
              <el-button
                text
                type="danger"
                size="small"
                @click="removePosition(index)"
              >
                删除
              </el-button>
            </div>
            <div v-if="currentPositions.length === 0" class="empty-positions">
              暂无位置配置
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPositionDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveSealPositions"
          :disabled="currentPositions.length === 0"
          :loading="loading.savingPositions"
        >
          保存位置设置
        </el-button>
      </template>
    </el-dialog>

    <!-- 申请详情弹窗 -->
    <el-dialog
      title="用印申请详情"
      v-model="showDetailDialog"
      width="600px"
    >
      <el-descriptions :column="1" border v-if="currentApplication">
        <el-descriptions-item label="申请ID">{{ currentApplication.id }}</el-descriptions-item>
        <el-descriptions-item label="文件名称">{{ currentApplication.file_name }}</el-descriptions-item>
        <el-descriptions-item label="使用印章">{{ currentApplication.seal?.name }}</el-descriptions-item>
        <el-descriptions-item label="用印原因">{{ currentApplication.application_reason || '无' }}</el-descriptions-item>
        <el-descriptions-item label="申请状态">
          <el-tag :type="statusTagType(currentApplication.status)">{{ currentApplication.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请人">{{ currentApplication.applicant?.real_name }}</el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ formatDateTime(currentApplication.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="审核人" v-if="currentApplication.reviewer">
          {{ currentApplication.reviewer.real_name }}
        </el-descriptions-item>
        <el-descriptions-item label="审核时间" v-if="currentApplication.review_time">
          {{ formatDateTime(currentApplication.review_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="审核备注" v-if="currentApplication.review_remark">
          {{ currentApplication.review_remark }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'

// 响应式数据
const activeTab = ref('seal-management')
const sealList = ref([])
const applicationList = ref([])
const pendingApplications = ref([])
const uploadFileList = ref([])
const sealFileList = ref([])

// 弹窗控制
const showCreateSealDialog = ref(false)
const showPositionDialog = ref(false)
const showDetailDialog = ref(false)

// 当前操作数据
const currentApplication = ref(null)
const currentPositions = ref([])
const previewFileUrl = ref('')
const totalPages = ref(1)

// 加载状态
const loading = reactive({
  seals: false,
  applications: false,
  pending: false,
  submitting: false,
  creatingSeal: false,
  savingPositions: false
})

// 表单数据
const sealForm = reactive({
  name: ''
})

const applicationForm = reactive({
  seal_id: null,
  application_reason: '',
  file: null
})

const positionForm = reactive({
  page_num: 1,
  x: 100,
  y: 100,
  width: 100,
  height: 100
})

// 计算属性
const isAdmin = computed(() => {
  const role = sessionStorage.getItem('role')
  return role === 'admin' || role === 'owner'
})

const currentUserId = computed(() => {
  return parseInt(sessionStorage.getItem('user_id') || '0')
})

const activeSeals = computed(() => {
  return sealList.value.filter(seal => seal.is_active)
})

// 表单验证规则
const sealRules = {
  name: [
    { required: true, message: '请输入印章名称', trigger: 'blur' },
    { max: 100, message: '印章名称不能超过100字', trigger: 'blur' }
  ],
  file: [{ required: true, message: '请上传印章图片', trigger: 'change' }]
}

const applicationRules = {
  seal_id: [{ required: true, message: '请选择印章', trigger: 'change' }],
  application_reason: [{ required: false, message: '请说明用印原因', trigger: 'blur' }],
  file: [{ required: true, message: '请上传待盖章文件', trigger: 'change' }]
}

// 组件引用
const sealFormRef = ref(null)
const applicationFormRef = ref(null)
const fileUploadRef = ref(null)
const sealUploadRef = ref(null)

// 生命周期
onMounted(() => {
  fetchSealList()
  fetchApplicationList()
  if (isAdmin.value) {
    fetchPendingApplications()
  }
})

// API调用函数
const fetchSealList = async () => {
  loading.seals = true
  try {
    const res = await axios.get('http://127.0.0.1:8002/electronic_seal/')
    sealList.value = res.data
  } catch (error) {
    console.error('获取印章列表失败:', error)
    ElMessage.error('获取印章列表失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.seals = false
  }
}

const fetchApplicationList = async () => {
  loading.applications = true
  try {
    const res = await axios.get('http://127.0.0.1:8002/electronic_seal/applications', {
      params: { applicant_id: currentUserId.value }
    })
    applicationList.value = res.data
  } catch (error) {
    console.error('获取申请列表失败:', error)
    ElMessage.error('获取申请列表失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.applications = false
  }
}

const fetchPendingApplications = async () => {
  loading.pending = true
  try {
    const res = await axios.get('http://127.0.0.1:8002/electronic_seal/applications', {
      params: { application_status: encodeURIComponent("待审核") }
    })
    pendingApplications.value = res.data
  } catch (error) {
    console.error('获取待审核列表失败:', error)
    ElMessage.error('获取待审核列表失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.pending = false
  }
}

// 印章管理功能
const handleSealStatusChange = async (seal) => {
  try {
    await axios.put(`http://127.0.0.1:8002/electronic_seal/${seal.id}`, {
      is_active: seal.is_active
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败：' + (error.response?.data?.detail || error.message))
    // 失败时回滚状态
    seal.is_active = !seal.is_active
  }
}

const handleSealFileChange = (file) => {
  sealFileList.value = [file]
}

const handleSealFileRemove = () => {
  sealFileList.value = []
}

const createSeal = async () => {
  try {
    await sealFormRef.value.validate()
    if (sealFileList.value.length === 0) {
      ElMessage.warning('请上传印章图片')
      return
    }

    loading.creatingSeal = true
    const formData = new FormData()
    formData.append('name', sealForm.name)
    formData.append('file', sealFileList.value[0].raw)

    await axios.post('http://127.0.0.1:8002/electronic_seal/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElNotification({
      title: '成功',
      message: '印章创建成功',
      type: 'success'
    })
    showCreateSealDialog.value = false
    await fetchSealList()
    // 重置表单
    sealForm.name = ''
    sealFileList.value = []
    sealFormRef.value.resetFields()
  } catch (error) {
    console.error('创建印章失败:', error)
    ElMessage.error('创建印章失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.creatingSeal = false
  }
}

const handleDeleteSeal = async (sealId) => {
  try {
    await ElMessageBox.confirm('确定要删除该印章吗？此操作不可恢复', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await axios.delete(`http://127.0.0.1:8002/electronic_seal/${sealId}`)
    ElMessage.success('印章删除成功')
    await fetchSealList()
  } catch (error) {
    if (error.name !== 'CanceledError') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败：' + (error.response?.data?.detail || error.message))
    }
  }
}

// 用印申请功能
const handleFileChange = (file) => {
  uploadFileList.value = [file]
  applicationForm.file = file.raw
}

const handleFileRemove = () => {
  uploadFileList.value = []
  applicationForm.file = null
}

const submitApplication = async () => {
  try {
    await applicationFormRef.value.validate()
    if (uploadFileList.value.length === 0) {
      ElMessage.warning('请上传待盖章文件')
      return
    }

    loading.submitting = true
    const formData = new FormData()
    formData.append('file_name', uploadFileList.value[0].name)
    formData.append('seal_id', applicationForm.seal_id)
    formData.append('application_reason', applicationForm.application_reason)
    formData.append('applicant_id', currentUserId.value)
    formData.append('file', applicationForm.file)

    await axios.post('http://127.0.0.1:8002/electronic_seal/applications', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElNotification({
      title: '成功',
      message: '申请提交成功',
      type: 'success'
    })
    resetApplicationForm()
    await fetchApplicationList()
  } catch (error) {
    console.error('提交申请失败:', error)
    ElMessage.error('提交申请失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.submitting = false
  }
}

const resetApplicationForm = () => {
  applicationForm.seal_id = null
  applicationForm.application_reason = ''
  applicationForm.file = null
  uploadFileList.value = []
  fileUploadRef.value.clearFiles()
  applicationFormRef.value.resetFields()
}

// 审核功能
const reviewApplication = async (application, status) => {
  try {
    const reviewRemark = await ElMessageBox.prompt(
      `请输入${status === '已通过' ? '通过' : '拒绝'}原因`,
      `确认${status === '已通过' ? '通过' : '拒绝'}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入审核备注（可选）'
      }
    )

    await axios.put(`http://127.0.0.1:8002/electronic_seal/applications/${application.id}/review`, {
      status,
      review_remark: reviewRemark.value,
      reviewer_id: currentUserId.value
    })

    ElMessage.success('审核操作成功')
    await fetchPendingApplications()
    await fetchApplicationList()
  } catch (error) {
    if (error.name !== 'CanceledError') {
      console.error('审核失败:', error)
      ElMessage.error('审核失败：' + (error.response?.data?.detail || error.message))
    }
  }
}

// 印章位置设置
const handleSetSealPosition = async (application) => {
  currentApplication.value = application
  currentPositions.value = application.seal_positions || []

  // 获取文件预览URL - 这里需要根据实际后端接口调整
  previewFileUrl.value = `http://127.0.0.1:8002/electronic_seal/applications/${application.id}/preview`
  showPositionDialog.value = true
}

const addSealPosition = () => {
  currentPositions.value.push({ ...positionForm })
}

const removePosition = (index) => {
  currentPositions.value.splice(index, 1)
}

const resetPositionForm = () => {
  positionForm.page_num = 1
  positionForm.x = 100
  positionForm.y = 100
  positionForm.width = 100
  positionForm.height = 100
}

const saveSealPositions = async () => {
  try {
    loading.savingPositions = true
    await axios.post(
      `http://127.0.0.1:8002/electronic_seal/applications/${currentApplication.value.id}/positions`,
      currentPositions.value
    )

    ElMessage.success('位置设置保存成功')
    showPositionDialog.value = false
    await fetchApplicationList()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.savingPositions = false
  }
}

// 执行盖章
const handleApplySeal = async (application) => {
  try {
    await axios.post(`http://127.0.0.1:8002/electronic_seal/applications/${application.id}/apply`)
    ElNotification({
      title: '成功',
      message: '盖章成功',
      type: 'success'
    })
    await fetchApplicationList()
  } catch (error) {
    console.error('盖章失败:', error)
    ElMessage.error('盖章失败：' + (error.response?.data?.detail || error.message))
  }
}

// 查看申请详情
const handleViewApplication = async (application) => {
  try {
    const res = await axios.get(`http://127.0.0.1:8002/electronic_seal/applications/${application.id}`)
    currentApplication.value = res.data
    showDetailDialog.value = true
  } catch (error) {
    console.error('获取申请详情失败:', error)
    ElMessage.error('获取申请详情失败：' + (error.response?.data?.detail || error.message))
  }
}

// 下载盖章文件
const downloadSealedFile = async (application) => {
  try {
    const response = await axios.get(
      `http://127.0.0.1:8002/electronic_seal/applications/${application.id}/download`,
      { responseType: 'blob' }
    )

    const blob = new Blob([response.data], { type: response.headers['content-type'] })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `sealed_${application.file_name}.pdf`
    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElNotification({
      title: '成功',
      message: '文件下载成功',
      type: 'success'
    })
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败：' + (error.response?.data?.detail || error.message))
  }
}

// 辅助函数
const getSealImageUrl = (sealId) => {
  return `http://127.0.0.1:8002/electronic_seal/${sealId}/image`
}

const statusTagType = (status) => {
  const typeMap = {
    '待审核': 'warning',
    '已通过': 'success',
    '已拒绝': 'danger'
  }
  return typeMap[status] || 'info'
}

const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

const initPdfViewer = () => {
  // 初始化PDF预览器逻辑
  console.log('PDF加载完成')
}

const handlePageChange = (page) => {
  // 处理页码变化
  console.log('切换到页码', page)
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.seal-tabs {
  margin-bottom: 20px;
}

.application-form-card {
  margin-bottom: 20px;
}

.position-setting-container {
  display: flex;
  gap: 20px;
  height: 60vh;
}

.pdf-preview {
  flex: 1;
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.position-controls {
  width: 300px;
  overflow-y: auto;
}

.position-list {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #eee;
}

.position-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
}

.empty-positions {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 20px;
}
</style>
