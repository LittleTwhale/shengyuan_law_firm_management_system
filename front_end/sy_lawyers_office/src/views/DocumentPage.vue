<template>
  <div class="document-page">
    <div class="header">
      <h2>文书模板</h2>
      <el-button v-if="isAdmin" type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>上传模板
      </el-button>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索模板名称..."
          prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-select v-model="filterType" placeholder="所有类型" clearable class="filter-select">
          <el-option label="Word 文档" value="word" />
          <el-option label="PDF 文档" value="pdf" />
          <el-option label="图片文件" value="image" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="viewMode" size="default">
          <el-radio-button label="grid" title="网格视图">
            <el-icon><Grid /></el-icon>
          </el-radio-button>
          <el-radio-button label="list" title="列表视图">
            <el-icon><Menu /></el-icon>
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-skeleton :loading="isLoading" animated>
      <template #template>
        <div class="templates-container" :class="viewMode">
          <el-skeleton-item
            v-for="i in 8"
            :key="i"
            variant="rect"
            class="template-card skeleton-card"
          />
        </div>
      </template>

      <template #default>
        <div class="templates-container" :class="viewMode">
          <div
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            @click="handlePreview(template.id)"
          >
            <div class="mobile-more-btn" @click.stop="openMobileDrawer(template)">
              <el-icon><MoreFilled /></el-icon>
            </div>

            <div class="card-content">
              <div class="file-icon">
                <el-icon v-if="isWordFile(template.file_type)"><Document /></el-icon>
                <el-icon v-else-if="isPdfFile(template.file_type)"
                  ><Document class="pdf-icon"
                /></el-icon>
                <el-icon v-else-if="isImageFile(template.file_type)"><PictureFilled /></el-icon>
                <el-icon v-else><Document /></el-icon>
              </div>

              <div class="file-info">
                <h3 class="file-name">{{ template.name }}</h3>
                <p class="file-meta">
                  <span v-if="viewMode === 'list'" class="file-type-text"
                    >{{ getFileTypeText(template.file_type) }} ·
                  </span>
                  {{ formatFileSize(template.file_size) }} · {{ formatDate(template.created_at) }}
                  <span v-if="viewMode === 'list'">
                    · 上传人: {{ template.uploader?.real_name || '未知' }}</span
                  >
                </p>
                <p v-if="viewMode === 'list'" class="file-desc list-only">
                  {{ template.description || '无描述信息' }}
                </p>
              </div>

              <div v-if="viewMode === 'list'" class="list-actions desktop-only-flex">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click.stop="handlePreview(template.id)"
                >
                  <el-icon><View /></el-icon>预览
                </el-button>
                <el-button
                  size="small"
                  plain
                  @click.stop="handleDownload(template.id, template.name)"
                >
                  <el-icon><Download /></el-icon>下载
                </el-button>
                <el-button
                  v-if="isAdmin"
                  size="small"
                  type="danger"
                  plain
                  @click.stop="handleDelete(template.id)"
                >
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </div>
            </div>

            <div v-if="viewMode === 'grid'" class="card-hover-detail desktop-only">
              <div class="detail-header">
                <h3>{{ template.name }}</h3>
                <span class="file-type-tag">{{ getFileTypeText(template.file_type) }}</span>
              </div>
              <div class="detail-body">
                <p class="description">{{ template.description || '无描述信息' }}</p>
                <div class="detail-meta">
                  <p>上传人: {{ template.uploader?.real_name || '未知' }}</p>
                  <p>上传时间: {{ formatDateTime(template.created_at) }}</p>
                  <p>文件大小: {{ formatFileSize(template.file_size) }}</p>
                </div>
              </div>
              <div class="detail-actions">
                <el-button size="small" type="primary" @click.stop="handlePreview(template.id)">
                  <el-icon><View /></el-icon>预览
                </el-button>
                <el-button size="small" @click.stop="handleDownload(template.id, template.name)">
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

          <div class="empty-state" v-if="filteredTemplates.length === 0">
            <el-empty
              :description="templates.length === 0 ? '暂无文书模板，请上传' : '没有符合条件的模板'"
            ></el-empty>
          </div>
        </div>
      </template>
    </el-skeleton>

    <el-drawer
      v-model="showMobileDrawer"
      direction="btt"
      size="auto"
      :with-header="false"
      class="mobile-drawer"
    >
      <div v-if="currentMobileTemplate" class="mobile-action-sheet">
        <div class="sheet-header">
          <div class="sheet-title">
            <h3>{{ currentMobileTemplate.name }}</h3>
            <span class="file-type-tag">{{
              getFileTypeText(currentMobileTemplate.file_type)
            }}</span>
          </div>
          <p class="sheet-meta">
            {{ formatFileSize(currentMobileTemplate.file_size) }} ·
            {{ formatDateTime(currentMobileTemplate.created_at) }}
          </p>
          <p class="sheet-desc">{{ currentMobileTemplate.description || '无描述信息' }}</p>
        </div>

        <div class="sheet-actions">
          <el-button block type="primary" @click="handleMobileAction('preview')">
            <el-icon><View /></el-icon> 预览文件
          </el-button>
          <el-button block @click="handleMobileAction('download')">
            <el-icon><Download /></el-icon> 下载文件
          </el-button>
          <el-button block type="danger" v-if="isAdmin" @click="handleMobileAction('delete')" plain>
            <el-icon><Delete /></el-icon> 删除模板
          </el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      title="上传文书模板"
      v-model="showUploadDialog"
      class="responsive-dialog"
      :close-on-click-modal="false"
    >
      <el-upload
        class="upload-area"
        ref="uploadRef"
        action="#"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="uploadFileList"
        :limit="1"
        :on-exceed="handleExceed"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持上传：Word(.doc,.docx)、PDF(.pdf)、图片(.jpg,.png,.gif)
          </div>
        </template>
      </el-upload>

      <el-form
        :model="uploadForm"
        :rules="uploadRules"
        ref="uploadFormRef"
        label-width="50px"
        label-position="top"
        style="margin-top: 20px"
      >
        <el-form-item label="标题" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入模板标题" maxlength="100" />
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
        <el-button type="primary" @click="handleUploadSubmit" :disabled="!canUpload || isUploading">
          <el-icon v-if="!isUploading"><Check /></el-icon>
          <el-icon v-if="isUploading"><Loading /></el-icon>
          {{ isUploading ? '上传中...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      :title="previewTitle"
      v-model="showPreviewDialog"
      class="responsive-preview-dialog"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="preview-container">
        <img
          v-if="previewType === 'image'"
          :src="previewUrl"
          class="image-preview"
          alt="模板预览"
        />

        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="pdf-iframe" />

        <div v-else class="unsupported-preview">
          <el-icon class="unsupported-icon"><QuestionFilled /></el-icon>
          <p>不支持在线预览该类型文件，请下载查看</p>
          <el-button
            type="primary"
            @click="handleDownload(currentPreviewId, previewTitle)"
            style="margin-top: 10px"
          >
            <el-icon><Download /></el-icon>下载文件
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import request from '@/utils/request'
import { uploadToCOS } from '@/utils/cosUpload'
import {
  Document,
  PictureFilled,
  Upload,
  UploadFilled,
  View,
  Download,
  Delete,
  Check,
  Loading,
  QuestionFilled,
  Grid,
  Menu,
  MoreFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'

// 基础变量
const templates = ref([])
const isLoading = ref(true) // 骨架屏加载状态
const isAdmin = computed(() => {
  const role = localStorage.getItem('role')
  return role === 'admin' || role === 'owner'
})

// 工具栏变量 (搜索、过滤、视图)
const searchQuery = ref('')
const filterType = ref('')
const viewMode = ref('grid') // 'grid' 或 'list'

// 移动端抽屉变量
const showMobileDrawer = ref(false)
const currentMobileTemplate = ref(null)

// 上传相关变量
const showUploadDialog = ref(false)
const uploadFileList = ref([])
const isUploading = ref(false)
const canUpload = computed(() => uploadFileList.value.length > 0)
const uploadForm = reactive({
  name: '',
  description: '',
})
const uploadRules = {
  name: [
    { required: true, message: '请输入模板标题', trigger: 'blur' },
    { max: 100, message: '标题不能超过100字', trigger: 'blur' },
  ],
  description: [{ max: 500, message: '描述不能超过500字', trigger: 'blur' }],
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

// 组件销毁时释放内存，防止 Blob URL 导致内存泄漏
onUnmounted(() => {
  if (previewUrl.value) {
    window.URL.revokeObjectURL(previewUrl.value)
  }
})

// 获取模板列表
const fetchTemplates = async () => {
  isLoading.value = true
  try {
    const res = await request.get('/template/document')
    templates.value = res.data
  } catch (err) {
    console.error('获取模板列表失败:', err)
    ElMessage.error('获取模板列表失败，请重试')
  } finally {
    isLoading.value = false
  }
}

// 过滤后的模板列表计算属性
const filteredTemplates = computed(() => {
  return templates.value.filter((template) => {
    // 搜索匹配
    const matchSearch = template.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    // 类型匹配
    let matchType = true
    if (filterType.value === 'word') matchType = isWordFile(template.file_type)
    if (filterType.value === 'pdf') matchType = isPdfFile(template.file_type)
    if (filterType.value === 'image') matchType = isImageFile(template.file_type)

    return matchSearch && matchType
  })
})

// 文件类型判断
const isWordFile = (fileType) => {
  return [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
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
  if (!kb) return '0 KB' // 防止空值 / Guard clause

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

// 移动端打开抽屉
const openMobileDrawer = (template) => {
  currentMobileTemplate.value = template
  showMobileDrawer.value = true
}

// 移动端抽屉操作分发
const handleMobileAction = (action) => {
  showMobileDrawer.value = false
  const template = currentMobileTemplate.value
  if (!template) return

  if (action === 'preview') handlePreview(template.id)
  if (action === 'download') handleDownload(template.id, template.name)
  if (action === 'delete') handleDelete(template.id)
}

// 上传文件变更处理
const handleFileChange = (file, fileList) => {
  uploadFileList.value = fileList
  // 自动填充文件名为标题（如果没有填写的话）
  if (!uploadForm.name && file.name) {
    // 移除文件后缀作为默认标题
    uploadForm.name = file.name.replace(/\.[^/.]+$/, '')
  }
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
  formData.append('description', uploadForm.description)

  isUploading.value = true
  try {
    const res = await request.post(
      `/template/document?name=${encodeURIComponent(templateName)}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      },
    )
    // COS 模式 + 非 Word 文件：后端返回 STS 临时凭证，需前端直传 COS
    if (res.data?.type === 'COS') {
      const result = await uploadToCOS(file, res.data)
      if (!result.success) {
        throw new Error(result.error || 'COS 上传失败')
      }
      // 回写模板文件大小（KB），静默失败不影响主流程
      request.patch(`/template/document/${res.data.template_id}/size`, null, {
        params: { file_size: Math.round(result.file_size / 1024) }
      }).catch(() => {})
    }
    ElNotification({
      title: '成功',
      message: '模板上传成功',
      type: 'success',
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

  // 【新增】释放上一次预览的内存
  if (previewUrl.value) {
    window.URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }

  try {
    // 获取模板信息
    // 使用 request 且去掉了本地硬编码域名
    const infoRes = await request.get(`/template/document/${templateId}`)
    previewTitle.value = infoRes.data.name
    const fileType = infoRes.data.file_type

    // 判断预览类型
    if (fileType.startsWith('image/')) {
      previewType.value = 'image'
    } else if (
      [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ].includes(fileType)
    ) {
      previewType.value = 'pdf'
    } else {
      previewType.value = 'other'
      return // 不支持预览类型，直接返回由界面展示不支持
    }

    // 安全地获取预览流，解决 img/iframe 无法在 Header 传 Token 导致被后端拦截的问题
    const previewRes = await request.get(`/template/document/${templateId}/preview`, {
      responseType: 'blob', // 强制指定接收二进制流
    })

    // 生成临时的本地访问 URL 绑定到 dom 上
    const blob = new Blob([previewRes.data], { type: previewRes.headers['content-type'] })
    previewUrl.value = window.URL.createObjectURL(blob)
  } catch (err) {
    console.error('模板预览失败:', err)
    ElMessage.error(err.response?.data?.detail || '模板预览失败')
  }
}

// 下载模板
const handleDownload = async (templateId, fileName) => {
  try {
    // 【修改】使用 request 并在配置中处理 blob 下载
    const response = await request.get(`/template/document/${templateId}/download`, {
      responseType: 'blob',
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
      type: 'success',
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
    // 【修改】使用 request 且去掉了本地硬编码域名
    await request.delete(`/template/document/${templateId}`)
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
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  background-color: #f8f9fb;
  min-height: 100vh;
}

/* ============ 标题与工具栏 ============ */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9edf3;
}

.header h2 {
  font-size: 22px;
  color: #2c3e50;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 280px;
}

.search-input {
  max-width: 260px;
}

.filter-select {
  max-width: 160px;
}

/* ============ 模板卡片区域 (Grid 视图) ============ */
.templates-container.grid {
  display: grid;
  /* 响应式网格：自适应宽度，最小160px */
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 180px), 1fr));
  gap: 20px;
  justify-content: center;
  align-items: stretch;
}

.templates-container.grid .template-card {
  width: 100%;
  aspect-ratio: 1 / 1.414; /* 保持 A4 比例 */
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
  position: relative;
  cursor: pointer;
  border: 1px solid transparent;
}

.templates-container.grid .template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
  border-color: #e4e9f2;
}

/* ============ 模板卡片区域 (List 视图) ============ */
.templates-container.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.templates-container.list .template-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  cursor: pointer;
  position: relative;
}

.templates-container.list .template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.templates-container.list .card-content {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 0;
  text-align: left;
  gap: 20px;
  width: 100%;
}

.templates-container.list .file-icon {
  font-size: 36px;
  margin-bottom: 0;
  flex-shrink: 0;
}

.templates-container.list .file-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  overflow: hidden; /* 防止长文本撑破 flex 布局 */
}

.templates-container.list .file-name {
  font-size: 16px;
  margin-bottom: 4px;
}

/* 列表视图专属的描述与操作样式 */
.file-type-text {
  color: #409eff;
  font-weight: 500;
}

.file-desc.list-only {
  font-size: 13px;
  color: #666;
  margin: 6px 0 0 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* 单行截断，防止列表太高 */
}

.list-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0; /* 保证按钮区不会被压缩 */
}

/* ============ 卡片内部公共内容 ============ */
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
  font-size: 48px;
  color: #4e8cff;
  margin-bottom: 12px;
}

/* PDF 图标单独配色 */
.file-icon .pdf-icon {
  color: #e53e3e;
}

.file-info {
  width: 100%;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 6px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}

.file-meta {
  font-size: 12px;
  color: #999;
  margin: 0;
}

/* 移动端专属按钮 (默认隐藏) */
.mobile-more-btn {
  display: none;
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 6px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  color: #666;
  z-index: 5;
}

.templates-container.list .mobile-more-btn {
  top: 50%;
  transform: translateY(-50%);
  right: 16px;
}

/* ============ 悬浮详情层 (仅 Grid 模式显示，毛玻璃质感) ============ */
.card-hover-detail {
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.88); /* 半透明背景 */
  backdrop-filter: blur(8px); /* 毛玻璃滤镜 */
  -webkit-backdrop-filter: blur(8px);
  padding: 16px;
  box-sizing: border-box;
  opacity: 0;
  pointer-events: none;
  transition: all 0.3s ease;
  overflow-y: auto;
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.templates-container.grid .template-card:hover .card-hover-detail {
  opacity: 1;
  pointer-events: auto;
}

/* 详情内部结构 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.detail-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
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
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
  margin-left: 8px;
}

.detail-body {
  flex: 1;
}

.description {
  color: #555;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* 限制描述显示3行 */
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.detail-meta {
  font-size: 12px;
  color: #777;
}
.detail-meta p {
  margin: 4px 0;
}

.detail-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 10px;
}
.detail-actions .el-button {
  margin: 0;
}

/* ============ 空状态与骨架屏 ============ */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
}
.skeleton-card {
  width: 100%;
  aspect-ratio: 1 / 1.414;
  border-radius: 12px;
}
.templates-container.list .skeleton-card {
  aspect-ratio: auto;
  height: 80px;
}

/* ============ 移动端底部抽屉内容 ============ */
.mobile-action-sheet {
  padding: 0 20px 20px;
}
.sheet-header {
  margin-bottom: 24px;
  text-align: center;
}
.sheet-title {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.sheet-title h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}
.sheet-meta {
  color: #999;
  font-size: 13px;
  margin: 0 0 12px 0;
}
.sheet-desc {
  color: #666;
  font-size: 14px;
  background: #f8f9fb;
  padding: 12px;
  border-radius: 8px;
  text-align: left;
}
.sheet-actions .el-button {
  width: 100%;
  margin: 0 0 12px 0;
  height: 44px;
  font-size: 15px;
}

/* ============ 响应式调整 (适配手机/平板) ============ */
/* 当设备不支持 hover (触摸屏) 或 屏幕宽度小于 768px 时 */
@media (hover: none), (max-width: 768px) {
  .desktop-only,
  .desktop-only-flex {
    display: none !important; /* 完全隐藏电脑端的hover遮罩层和列表按钮 */
  }
  .mobile-more-btn {
    display: block; /* 显示移动端点击按钮 */
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-left {
    flex-direction: column;
    min-width: 100%;
  }
  .search-input,
  .filter-select {
    max-width: 100%;
  }
}

/* 覆盖 Element Plus 弹窗的默认宽度设置，实现自适应 */
:deep(.responsive-dialog),
:deep(.responsive-preview-dialog) {
  width: 90% !important;
  max-width: 600px;
}
:deep(.responsive-preview-dialog) {
  max-width: 1200px; /* 预览弹窗可以更大一些 */
}

/* ============ 预览容器 ============ */
.preview-container {
  width: 100%;
  height: calc(85vh - 100px);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
  padding: 10px;
  box-sizing: border-box;
}

.image-preview {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  background: #fff;
  padding: 8px;
  border-radius: 8px;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.unsupported-preview {
  text-align: center;
  color: #666;
}
.unsupported-icon {
  font-size: 64px;
  margin-bottom: 16px;
  color: #cbd5e1;
}
</style>
