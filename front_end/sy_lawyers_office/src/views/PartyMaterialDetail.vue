<template>
  <div class="detail-page" v-loading="loading">
    <div class="content-wrapper" v-if="material">
      <div class="article-header">
        <h1 class="title">{{ material.title }}</h1>
        <div class="meta-info">
          <span
            ><el-icon><Calendar /></el-icon> 发布时间：{{ formatDate(material.created_at) }}</span
          >
          <span
            ><el-icon><Document /></el-icon> 文号：{{ material.document_number || '无' }}</span
          >
          <span
            ><el-icon><OfficeBuilding /></el-icon> 发文单位：{{
              material.issuing_authority || '未知'
            }}</span
          >
          <span
            ><el-icon><User /></el-icon> 发布人：{{ material.publisher_name }}</span
          >
          <span
            ><el-icon><View /></el-icon> 阅读量：{{ material.view_count }}</span
          >
        </div>
      </div>

      <el-divider />

      <div class="article-content" v-html="material.content || '暂无内容'"></div>

      <div
        class="attachment-section"
        v-if="material.attachments && material.attachments.length > 0"
      >
        <div class="attach-title">
          <el-icon><Paperclip /></el-icon> 附件下载与预览
        </div>

        <div class="attach-list-wrapper">
          <div v-for="file in material.attachments" :key="file.id" class="attach-item">
            <div class="file-icon">
              <el-icon v-if="isImage(file.file_name)"><Picture /></el-icon>
              <el-icon v-else-if="isDoc(file.file_name)"><DocumentCopy /></el-icon>
              <el-icon v-else><Paperclip /></el-icon>
            </div>

            <div class="file-info">
              <div class="file-name">{{ file.file_name }}</div>
              <div class="file-meta">
                {{ (file.file_size / 1024).toFixed(1) }} KB | {{ formatDate(file.created_at) }}
              </div>
            </div>

            <div class="file-actions">
              <el-button
                type="primary"
                link
                size="small"
                @click="handlePreview(file)"
                v-if="canPreview(file)"
              >
                <el-icon><View /></el-icon> 预览
              </el-button>

              <el-button type="primary" link size="small" @click="downloadFile(file)">
                <el-icon><Download /></el-icon> 下载
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-else description="资料不存在或已被删除" />

    <el-dialog
      v-model="previewVisible"
      title="文件预览"
      width="min(95%, 800px)"
      top="5vh"
      destroy-on-close
      class="preview-dialog"
    >
      <div class="preview-container" v-loading="previewLoading">
        <img v-if="previewType === 'image'" :src="previewUrl" class="preview-image" alt="preview" />
        <iframe
          v-else-if="previewType === 'pdf'"
          :src="previewUrl"
          class="preview-iframe"
          frameborder="0"
        ></iframe>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// 引入更多图标用于优化界面
import {
  Calendar,
  Document,
  DocumentCopy,
  Download,
  OfficeBuilding,
  Paperclip,
  Picture,
  User,
  View,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request' // 引入 request

const route = useRoute()
const loading = ref(true)
const material = ref(null)

// 预览相关状态
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('pdf') // 'image' or 'pdf'
const previewLoading = ref(false)

onMounted(async () => {
  const id = route.params.id
  if (id) {
    try {
      // 获取详情
      const res = await request.get(`/party_building/materials/${id}`)
      material.value = res.data
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }
})

// 辅助函数：判断文件类型
const isImage = (filename) => /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(filename)
const isDoc = (filename) => /\.(pdf|doc|docx)$/i.test(filename)

// 判断是否支持预览 (PDF, Word, 图片)
const canPreview = (file) => {
  return isImage(file.file_name) || isDoc(file.file_name)
}

// 处理预览逻辑
const handlePreview = async (file) => {
  // 1. 设置加载状态
  previewLoading.value = true
  previewVisible.value = true // 先打开弹窗，显示 loading

  try {
    // 2. 发起请求，注意 responseType 必须是 'blob'
    const res = await request.get(`/party_building/attachments/${file.id}/preview`, {
      responseType: 'blob',
    })

    // 3. 创建本地临时 URL
    // 注意：后端如果转换了 Word 为 PDF，返回的类型应该是 application/pdf
    const blob = new Blob([res.data], {
      type: isImage(file.file_name) ? file.file_type : 'application/pdf',
    })

    // 4. 设置预览 URL
    previewUrl.value = window.URL.createObjectURL(blob)

    // 5. 设置预览类型
    if (isImage(file.file_name)) {
      previewType.value = 'image'
    } else {
      // Word(后端转PDF) 和 PDF 都用 iframe 预览
      previewType.value = 'pdf'
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('文件预览失败')
    previewVisible.value = false // 失败关闭弹窗
  } finally {
    previewLoading.value = false
  }
}

// 点击下载
const downloadFile = async (file) => {
  try {
    ElMessage.info('正在请求下载...')

    // 1. 请求二进制流
    const res = await request.get(`/party_building/attachments/${file.id}/download`, {
      responseType: 'blob',
    })

    // 2. 创建 Blob 对象
    const blob = new Blob([res.data])

    // 3. 创建下载链接
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = file.file_name // 设定下载文件名
    link.style.display = 'none'

    // 4. 触发点击并清理
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href) // 释放内存

    ElMessage.success('下载开始')
  } catch (error) {
    console.error(error)
    ElMessage.error('下载失败')
  }
}

// 监听弹窗关闭，清理 URL 释放内存
watch(previewVisible, (val) => {
  if (!val && previewUrl.value) {
    window.URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
})

const formatDate = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleString()
}
</script>

<style scoped>
.detail-page {
  padding: 40px;
  background-color: #f5f7fa;
  min-height: 100vh;
}
.content-wrapper {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  padding: 40px;
  border-radius: 8px; /* 稍微增大圆角 */
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08); /* 优化阴影 */
}
.title {
  text-align: center;
  font-size: 28px;
  color: #303133;
  margin-bottom: 24px;
  font-weight: 600;
}
.meta-info {
  text-align: center;
  color: #909399;
  font-size: 13px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap; /* 防止小屏幕换行问题 */
  gap: 20px;
  margin-bottom: 10px;
}
.meta-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.article-content {
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  min-height: 200px;
  margin-bottom: 50px;
  padding: 0 10px;
}

/* 附件区域样式优化 */
.attachment-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  margin-top: 30px;
}
.attach-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}

.attach-list-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.attach-item {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.attach-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border-color: #c6e2ff;
}

.file-icon {
  font-size: 24px;
  color: #909399;
  margin-right: 15px;
  display: flex;
  align-items: center;
}

.file-info {
  flex: 1;
  overflow: hidden; /* 防止文件名过长溢出 */
}

.file-name {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}

.file-actions {
  display: flex;
  gap: 10px;
}

/* 预览相关样式 */
.preview-container {
  width: 100%;
  height: 70vh; /* 弹窗高度 */
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  background: #fff;
}

/* ============= 响应式/移动端适配 ============= */
@media (max-width: 768px) {
  .detail-page {
    padding: 10px; /* 减小外围空白 */
  }
  .content-wrapper {
    padding: 20px 15px; /* 减小内部留白 */
  }
  .title {
    font-size: 22px; /* 缩小标题 */
  }
  .meta-info {
    flex-direction: column; /* 手机上元数据垂直排列 */
    align-items: flex-start;
    gap: 8px;
  }
  .article-content {
    padding: 0;
  }
  .attach-item {
    flex-direction: column; /* 附件列表在手机端纵向排列 */
    align-items: flex-start;
    gap: 10px;
  }
  .file-actions {
    width: 100%;
    justify-content: flex-end; /* 操作按钮靠右对齐 */
  }
}
</style>
