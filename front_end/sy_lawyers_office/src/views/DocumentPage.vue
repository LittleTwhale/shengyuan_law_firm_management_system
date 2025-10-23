<template>
  <div class="document-page">
    <!-- 页面头部 -->
    <div class="header">
      <h2>文书模板</h2>
      <!-- 管理员专属：上传按钮 -->
      <el-button
        v-if="isAdmin"
        type="primary"
        @click="showUploadDialog = true"
      >
        <el-icon><Upload /></el-icon>上传模板
      </el-button>
    </div>

    <!-- 模板列表区域 -->
    <div class="templates-container">
      <!-- 模板卡片 -->
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        @click="handlePreview(template.id)"
      >
        <!-- 卡片内容 -->
        <div class="card-content">
          <!-- 图标根据文件类型显示 -->
          <div class="file-icon">
            <el-icon v-if="isWordFile(template.file_type)"><Document /></el-icon>
            <el-icon v-else-if="isPdfFile(template.file_type)"><Document class="pdf-icon" /></el-icon>
            <el-icon v-else-if="isImageFile(template.file_type)"><PictureFilled /></el-icon>
            <el-icon v-else><Document /></el-icon>
          </div>
          <div class="file-info">
            <h3 class="file-name">{{ template.name }}</h3>
            <p class="file-meta">{{ formatFileSize(template.file_size) }} · {{ formatDate(template.created_at) }}</p>
          </div>
        </div>

        <!-- 悬浮详情层 -->
        <div class="card-hover-detail">
          <div class="detail-header">
            <h3>{{ template.name }}</h3>
            <span class="file-type-tag">{{ getFileTypeText(template.file_type) }}</span>
          </div>
          <div class="detail-body">
            <p class="description">{{ template.description || '无描述信息' }}</p>
            <div class="detail-meta">
              <p>上传人: {{ template.uploader.real_name || '未知' }}</p>
              <p>上传时间: {{ formatDateTime(template.created_at) }}</p>
              <p>文件大小: {{ formatFileSize(template.file_size) }}</p>
            </div>
          </div>
          <div class="detail-actions">
            <el-button
              size="small"
              type="primary"
              @click.stop="handlePreview(template.id)"
            >
              <el-icon><View /></el-icon>预览
            </el-button>
            <el-button
              size="small"
              @click.stop="handleDownload(template.id, template.name)"
            >
              <el-icon><Download /></el-icon>下载
            </el-button>
            <el-button
              v-if="isAdmin"
              size="small"
              type="danger"
              @click.stop="handleDelete(template.id)"
            >
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-if="templates.length === 0 ">
        <el-empty description="暂无文书模板，请上传"></el-empty>
      </div>
     </div>

    <!-- 上传模板弹窗 -->
    <el-dialog
      title="上传文书模板"
      v-model="showUploadDialog"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-upload
        class="upload-area"
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="uploadFileList"
        :limit="1"
        :on-exceed="handleExceed"
      >
        <el-button type="primary" :loading="isUploading">
          <el-icon><Upload /></el-icon> 选择文件
        </el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持上传：Word(.doc,.docx)、PDF(.pdf)、图片(.jpg,.png,.gif)
          </div>
        </template>
      </el-upload>

      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="80px" style="margin-top: 20px;">
        <el-form-item label="标题" prop="name">
          <el-input
            v-model="uploadForm.name"
            placeholder="请输入模板标题"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            placeholder="请输入模板描述（可选）"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleUploadSubmit"
          :disabled="!canUpload || isUploading"
        >
          <el-icon v-if="!isUploading"><Check /></el-icon>
          <el-icon v-if="isUploading"><Loading /></el-icon>
          {{ isUploading ? '上传中...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog
      :title="previewTitle"
      v-model="showPreviewDialog"
      width="90%"
      height="90vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="preview-container" >
        <!-- 预览内容 -->
          <!-- 图片预览 -->
          <img
            v-if="previewType === 'image'"
            :src="previewUrl"
            class="image-preview"
            alt="模板预览"
          />

          <!-- PDF预览 -->
          <iframe
            v-else-if="previewType === 'pdf'"
            :src="previewUrl"
            class="pdf-iframe"
          />

          <!-- 不支持的类型 -->
          <div v-else class="unsupported-preview">
            <el-icon class="unsupported-icon"><QuestionFilled /></el-icon>
            <p>不支持在线预览该类型文件，请下载查看</p>
            <el-button
              type="primary"
              @click="handleDownload(currentPreviewId, previewTitle)"
              style="margin-top: 10px;"
            >
              <el-icon><Download /></el-icon>下载文件
            </el-button>
          </div>
        </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import {
  Document, PictureFilled, Upload, View, Download,
  Delete, Check, Loading, QuestionFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'

// 基础变量
const templates = ref([])
const isAdmin = computed(() => {
  const role = sessionStorage.getItem('role')
  return role === 'admin' || role === 'owner'
})

// 上传相关变量
const showUploadDialog = ref(false)
const uploadFileList = ref([])
const isUploading = ref(false)
const canUpload = computed(() => uploadFileList.value.length > 0)
const uploadForm = reactive({
  name: '',
  description: ''
})
const uploadRules = {
  name: [
    { required: true, message: '请输入模板标题', trigger: 'blur' },
    { max: 100, message: '标题不能超过100字', trigger: 'blur' }
  ],
  description: [{ max: 500, message: '描述不能超过500字', trigger: 'blur' }]
}
const uploadFormRef = ref(null)
const uploadRef = ref(null)

// 预览相关变量
const showPreviewDialog = ref(false)
const previewUrl = ref('')
const previewTitle = ref('')
const previewType = ref('')
const currentPreviewId = ref(null)

// 页面加载时获取模板列表
onMounted(() => {
  fetchTemplates()
})

// 获取模板列表
const fetchTemplates = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8002/template/document')
    templates.value = res.data
  } catch (err) {
    console.error('获取模板列表失败:', err)
    ElMessage.error('获取模板列表失败，请重试')
  }
}

// 文件类型判断
const isWordFile = (fileType) => {
  return [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ].includes(fileType)
}

const isPdfFile = (fileType) => {
  return fileType === 'application/pdf'
}

const isImageFile = (fileType) => {
  return fileType?.startsWith('image/')
}

// 获取文件类型文本
const getFileTypeText = (fileType) => {
  if (isWordFile(fileType)) return 'Word文档'
  if (isPdfFile(fileType)) return 'PDF文档'
  if (isImageFile(fileType)) return '图片文件'
  return '其他文件'
}

// 格式化文件大小（kb转MB）
const formatFileSize = (kb) => {
  if (!kb) return '0 KB'  // 防止空值 / Guard clause

  // 如果文件小于1MB（1024KB），显示KB
  if (kb < 1024) {
    return kb.toFixed(2) + ' KB'
  }

  // 否则显示为MB
  const mb = kb / 1024
  return mb.toFixed(2) + ' MB'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

// 上传文件变更处理
const handleFileChange = (file, fileList) => {
  uploadFileList.value = fileList
}

// 超出文件数量限制
const handleExceed = () => {
  ElMessage.warning('每次只能上传一个文件')
}

// 提交上传
const handleUploadSubmit = async () => {
  if (!canUpload.value) return

  // 表单验证
  await uploadFormRef.value.validate()

  const file = uploadFileList.value[0].raw
  const formData = new FormData()
  formData.append('file', file)
  const templateName = uploadForm.name
  const uploadedBy = sessionStorage.getItem('user_id')
  formData.append('description', uploadForm.description)

  isUploading.value = true
  try {
    await axios.post(
      `http://127.0.0.1:8002/template/document?name=${encodeURIComponent(templateName)}&uploaded_by=${uploadedBy}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    ElNotification({
      title: '成功',
      message: '模板上传成功',
      type: 'success'
    })
    showUploadDialog.value = false
    // 重置表单
    uploadFileList.value = []
    uploadForm.description = ''
    uploadForm.name = ''
    // 刷新列表
    await fetchTemplates()
  } catch (err) {
    console.error('模板上传失败:', err)
    ElMessage.error('模板上传失败，请重试')
  } finally {
    isUploading.value = false
  }
}

// 预览模板
const handlePreview = async (templateId) => {
  currentPreviewId.value = templateId
  showPreviewDialog.value = true

  try {
    // 获取模板信息
    const infoRes = await axios.get(`http://127.0.0.1:8002/template/document/${templateId}`)
    previewTitle.value = infoRes.data.name
    const fileType = infoRes.data.file_type

    // 直接使用URL而非blob，避免比例问题
    const previewUrlTemp = `http://127.0.0.1:8002/template/document/${templateId}/preview`

    // 判断预览类型
    if (fileType.startsWith('image/')) {
      previewType.value = 'image'
      previewUrl.value = previewUrlTemp
    } else if (['application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(fileType)) {
      previewType.value = 'pdf'
      previewUrl.value = previewUrlTemp
    } else {
      previewType.value = 'other'
    }
  } catch (err) {
    console.error('模板预览失败:', err)
    ElMessage.error(err.response?.data?.detail || '模板预览失败')
  }
}

// 下载模板
const handleDownload = async (templateId, fileName) => {
  try {
    const response = await axios.get(`http://127.0.0.1:8002/template/document/${templateId}/download`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: response.headers['content-type'] })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.click()
    window.URL.revokeObjectURL(downloadUrl)

    ElNotification({
      title: '成功',
      message: '模板下载成功',
      type: 'success'
    })
  } catch (err) {
    console.error('模板下载失败:', err)
    ElMessage.error('模板下载失败，请重试')
  }
}

// 删除模板
const handleDelete = async (templateId) => {
  if (!confirm('确定要删除该模板吗？此操作不可恢复')) return

  try {
    await axios.delete(`http://127.0.0.1:8002/template/document/${templateId}`)
    ElMessage.success('模板删除成功')
    await fetchTemplates() // 刷新列表
  } catch (err) {
    console.error('模板删除失败:', err)
    ElMessage.error(err.response?.data?.detail || '模板删除失败，请重试')
  }
}
</script>

<style scoped>
/* ============ 全局布局 ============ */
.document-page {
  padding: 20px;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #333;
  background-color: #f8f9fb;
}

/* 标题栏样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9edf3;
}

.header h2 {
  font-size: 22px;
  color: #2c3e50;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* ============ 模板卡片区域 ============ */
.templates-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 24px;
  justify-content: center;
  align-items: stretch;
}

/* 单个卡片（A4比例） */
.template-card {
  width: 220px;
  aspect-ratio: 1 / 1.414;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
  cursor: pointer;
}

.template-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

/* 卡片内容 */
.card-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  text-align: center;
}

.file-icon {
  font-size: 50px;
  color: #4e8cff;
  margin-bottom: 14px;
}

/* PDF 图标单独配色 */
.file-icon .pdf-icon {
  color: #e53e3e;
}
.file-info {
  width: 100%;
}

.file-name {
  font-size: 15px;
  font-weight: 500;
  margin: 0 0 6px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: #999;
}

/* ============ 悬浮详情层 ============ */
.card-hover-detail {
  position: absolute;
  inset: 0;
  background-color: #ffffff;
  border-radius: 14px;
  padding: 16px;
  box-sizing: border-box;
  transform: translateY(100%);
  transition: transform 0.3s ease;
  overflow-y: auto;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
  z-index: 2;
}

.template-card:hover .card-hover-detail {
  transform: translateY(0);
}

/* 详情标题 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed #eee;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.detail-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-type-tag {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* 描述与元数据 */
.description {
  color: #555;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
  max-height: 60px;
  overflow-y: auto;
}

.detail-meta {
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
}

.detail-meta p {
  margin: 4px 0;
}

/* 操作区 */
.detail-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* ============ 空状态 ============ */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
  color: #999;
}

/* ============ 上传区域 ============ */
.upload-area {
  border: 2px dashed #cfd8e3;
  border-radius: 10px;
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s ease;
  background: #fafbfc;
}

.upload-area:hover {
  border-color: #4e8cff;
  background-color: #f0f7ff;
}

/* ============ 预览对话框 ============ */
.preview-container {
  width: 100%;
  height: calc(90vh - 100px); /* 增加底部留白，避免内容溢出 */
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto; /* 允许滚动查看大文件 */
  padding: 20px;
  box-sizing: border-box;
}

.image-preview {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain; /* 保持原始比例，不拉伸 */
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* 增加阴影提升层次感 */
  background: #fff;
  padding: 10px;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.unsupported-preview {
  text-align: center;
  color: #666;
}

.unsupported-icon {
  font-size: 64px;
  margin-bottom: 20px;
  color: #ccc;
}

</style>



