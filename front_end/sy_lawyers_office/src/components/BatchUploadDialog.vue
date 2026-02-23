<template>
  <el-dialog
    title="批量上传卷宗文件"
    :model-value="visible"
    width="980px"
    @close="handleClose"
    :close-on-click-modal="false"
    destroy-on-close
    append-to-body
    class="batch-upload-dialog"
  >
    <div class="upload-container">
      <el-upload
        class="upload-area"
        drag
        action="#"
        multiple
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          <div class="main-text">将文件拖到此处，或 <em>点击选择</em></div>
          <div class="sub-text">支持 Word、PDF、图片 (JPG/PNG) 等格式，单次可选择多个</div>
        </div>
      </el-upload>

      <transition name="el-fade-in">
        <div v-if="fileList.length > 0" class="file-list-card">
          <div class="list-header">
            <div class="header-left">
              <span class="title">待上传清单</span>
              <el-tag type="info" size="small" round>{{ fileList.length }} 个文件</el-tag>
            </div>
            <el-button type="danger" link size="small" icon="Delete" @click="clearAll">
              清空列表
            </el-button>
          </div>

          <el-table
            :data="fileList"
            border
            stripe
            size="small"
            style="width: 100%"
            max-height="350"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column label="文件名" prop="name" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="filename-cell">
                  <el-icon v-if="row.name.endsWith('.pdf')" color="#F56C6C"><Document /></el-icon>
                  <el-icon v-else-if="row.name.match(/\.(doc|docx)$/)" color="#409EFF"
                    ><Document
                  /></el-icon>
                  <el-icon v-else color="#909399"><Document /></el-icon>
                  <span style="margin-left: 5px">{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="大小" width="80" align="center">
              <template #default="{ row }">
                <span style="color: #909399; font-size: 12px">{{ formatFileSize(row.size) }}</span>
              </template>
            </el-table-column>

            <el-table-column label="归属分类" width="130" align="center">
              <template #default="{ row }">
                <el-select v-model="row.category" size="small" placeholder="请选择">
                  <el-option v-for="opt in categoryOptions" :key="opt" :label="opt" :value="opt" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="标签 (回车添加)" width="150">
              <template #default="{ row }">
                <div class="tag-input-wrapper">
                  <el-tag
                    v-for="(tag, idx) in row.tags"
                    :key="idx"
                    closable
                    size="small"
                    @close="row.tags.splice(idx, 1)"
                    style="margin-right: 4px; margin-bottom: 2px"
                  >
                    {{ tag }}
                  </el-tag>
                  <el-input
                    v-model="row.tempTag"
                    class="input-new-tag"
                    size="small"
                    placeholder="+ Tag"
                    @keyup.enter="addTag(row)"
                    @blur="addTag(row)"
                  />
                </div>
              </template>
            </el-table-column>

            <el-table-column label="摘要/备注" min-width="120">
              <template #default="{ row }">
                <el-input
                  v-model="row.summary"
                  size="small"
                  placeholder="可选备注..."
                  type="textarea"
                  :rows="1"
                  resize="none"
                />
              </template>
            </el-table-column>

            <el-table-column label="排序" width="80" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.sort_order"
                  size="small"
                  :min="0"
                  controls-position="right"
                  style="width: 100%"
                />
              </template>
            </el-table-column>

            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'ready'" type="info" size="small">待上传</el-tag>
                <el-tag v-if="row.status === 'uploading'" size="small">
                  <el-icon class="is-loading"><Loading /></el-icon> 上传中
                </el-tag>
                <el-tag v-if="row.status === 'success'" type="success" size="small">
                  <el-icon><Check /></el-icon> 成功
                </el-tag>
                <el-tooltip v-if="row.status === 'fail'" :content="row.errorMsg" placement="top">
                  <el-tag type="danger" size="small" style="cursor: help">
                    <el-icon><Warning /></el-icon> 失败
                  </el-tag>
                </el-tooltip>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="60" align="center" fixed="right">
              <template #default="{ row, $index }">
                <el-button
                  type="danger"
                  link
                  :icon="Delete"
                  title="移除此文件"
                  :disabled="row.status === 'uploading' || row.status === 'success'"
                  @click="removeFile($index)"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </transition>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-tip">
          <span v-if="uploading">
            <el-icon class="is-loading"><Loading /></el-icon> 正在处理列队... 请勿关闭窗口
          </span>
        </div>
        <div>
          <el-button @click="handleClose" :disabled="uploading">取 消</el-button>
          <el-button
            type="primary"
            @click="startUpload"
            :loading="uploading"
            :disabled="fileList.length === 0"
          >
            {{ uploading ? '上传中...' : '开始上传' }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled, Loading, Delete, Check, Warning, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const props = defineProps({
  visible: Boolean,
  volumeId: {
    type: [Number, String],
    required: true,
  },
  baseSortOrder: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:visible', 'success'])

const uploading = ref(false)
const fileList = ref([])

// 预设分类选项 (建议后续可从字典接口获取)
const categoryOptions = ['证据材料', '法律文书', '起诉/答辩状', '笔录资料', '备考表', '其他材料']

// 监听文件选择
const handleFileChange = (uploadFile) => {
  // 去重检查
  const isExist = fileList.value.some((f) => f.uid === uploadFile.uid)
  if (isExist) return

  // 默认排序权重：基于当前列表长度自动递增，步长为10
  const currentBatchOffset = fileList.value.length + 1
  const nextSort = props.baseSortOrder + currentBatchOffset * 10

  fileList.value.push({
    uid: uploadFile.uid,
    name: uploadFile.name,
    size: uploadFile.size, // 保存文件大小
    raw: uploadFile.raw,
    category: '证据材料', // 默认分类
    sort_order: nextSort,

    // === 新增字段 ===
    tags: [], // 存储标签数组
    tempTag: '', // 输入框临时值
    summary: '', // 摘要

    status: 'ready', // ready, uploading, success, fail
    errorMsg: '',
  })
}

// 新增：添加标签逻辑
const addTag = (row) => {
  const val = row.tempTag ? row.tempTag.trim() : ''
  if (val && !row.tags.includes(val)) {
    row.tags.push(val)
  }
  row.tempTag = ''
}

// 移除单个文件
const removeFile = (index) => {
  fileList.value.splice(index, 1)
}

// 清空所有
const clearAll = () => {
  if (uploading.value) return
  fileList.value = []
}

// 关闭弹窗
const handleClose = () => {
  if (uploading.value) {
    ElMessage.warning('正在上传中，请稍候')
    return
  }
  fileList.value = []
  emit('update:visible', false)
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 开始批量上传
const startUpload = async () => {
  const pendingFiles = fileList.value.filter((f) => f.status === 'ready' || f.status === 'fail')
  if (pendingFiles.length === 0) {
    ElMessage.warning('没有待上传的文件')
    return
  }

  uploading.value = true
  let successCount = 0

  // 这里的并发处理逻辑：保持原有 Promise.allSettled 结构，适合批量上传
  const promises = pendingFiles.map(async (item) => {
    item.status = 'uploading'

    const formData = new FormData()
    // 注意：字段名必须与后端 API (electronic_volume_api.py) 的 Form 定义一致
    formData.append('volume_id', props.volumeId)
    formData.append('file', item.raw)
    formData.append('category', item.category)
    formData.append('sort_order', item.sort_order)

    // === 传输新增字段 ===
    if (item.summary) formData.append('summary', item.summary)
    // Tags 需要转 JSON 字符串传输，后端 schema 已支持解析
    if (item.tags && item.tags.length > 0) {
      formData.append('tags', JSON.stringify(item.tags))
    }

    try {
      await request.post('/electronic_volumes/files', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 0, // 0 表示不设置超时限制，或者使用 120000 (2分钟)
        // 可以在这里添加 onUploadProgress 处理进度条
      })
      item.status = 'success'
      successCount++
    } catch (err) {
      console.error(err)
      item.status = 'fail'
      // 提取后端返回的详细错误信息
      item.errorMsg = err.response?.data?.detail || '上传失败'
    }
  })

  await Promise.allSettled(promises)
  uploading.value = false

  if (successCount === pendingFiles.length) {
    ElMessage.success(`成功上传 ${successCount} 个文件`)
    // 为了体验更好，成功后延迟 0.5 秒关闭，让用户看到全绿的状态
    setTimeout(() => {
      handleClose()
      emit('success')
    }, 500)
  } else {
    ElMessage.warning(`上传完成，其中 ${pendingFiles.length - successCount} 个文件失败，请检查`)
    // 部分失败时，保留弹窗，并通知父组件刷新（可能部分已经入库）
    emit('success')
  }
}
</script>

<style scoped>
.upload-container {
  padding: 0 10px;
}

/* 优化上传区域样式 */
.upload-area :deep(.el-upload-dragger) {
  padding: 30px;
  background-color: #f8f9fa;
  border: 2px dashed #dcdfe6;
  transition: all 0.3s;
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background-color: #ecf5ff;
}
.el-icon--upload {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}
.main-text {
  font-size: 15px;
  color: #303133;
  margin-bottom: 5px;
}
.sub-text {
  font-size: 12px;
  color: #909399;
}

/* 列表区域样式 */
.file-list-card {
  margin-top: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px; /* 圆角增加 */
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05); /* 轻微阴影 */
  background: white;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

/* 表格内样式 */
.filename-cell {
  display: flex;
  align-items: center;
}

/* 底部样式 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.footer-tip {
  font-size: 12px;
  color: #e6a23c;
}

/* 新增：标签输入样式 */
.tag-input-wrapper {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
.input-new-tag {
  width: 60px;
  height: 24px;
  line-height: 24px;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
