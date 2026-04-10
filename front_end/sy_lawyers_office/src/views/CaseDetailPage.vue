<template>
  <div class="case-detail">
    <el-page-header @back="goBack" title="返回" />

    <h2 class="page-title">业务详情与卷宗</h2>

    <el-tabs v-model="activeTab" type="border-card" class="detail-tabs">
      <el-tab-pane label="业务详情" name="detail">
        <el-card
          class="detail-card"
          v-loading="loading"
          shadow="never"
          style="border: none; margin-top: 0"
        >
          <BankCaseDetail v-if="caseData.case_category === '银行案件'" :case-data="caseData" />
          <GeneralCaseDetail v-else :case-data="caseData" />

          <el-divider />
          <el-descriptions
            title="系统信息"
            :column="isMobile ? 1 : 2"
            :direction="isMobile ? 'vertical' : 'horizontal'"
            border
          >
            <el-descriptions-item label="创建时间">{{
              formatDateTime(caseData.created_at)
            }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{
              formatDateTime(caseData.updated_at)
            }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />
          <el-descriptions
            title="业务附件"
            border
            :column="1"
            :direction="isMobile ? 'vertical' : 'horizontal'"
          >
            <el-descriptions-item label="附件列表">
              <div class="attachment-list">
                <div v-if="attachments.length === 0 && !loadingAttachments" class="no-attachments">
                  暂无附件
                </div>

                <template v-else>
                  <div v-if="!isMobile" class="table-responsive">
                    <el-table
                      :data="attachments"
                      border
                      style="width: 100%; margin-top: 10px; min-width: 500px"
                    >
                      <el-table-column prop="file_name" label="文件名" min-width="150" />
                      <el-table-column
                        prop="uploader"
                        label="上传人"
                        min-width="100"
                        :formatter="(row) => row.uploader?.real_name || '-'"
                      />
                      <el-table-column
                        prop="file_size"
                        label="文件大小"
                        width="100"
                        :formatter="formatFileSize"
                      />
                      <el-table-column
                        prop="uploaded_at"
                        label="上传时间"
                        min-width="160"
                        :formatter="(row, column, cellValue) => formatDateTime(cellValue)"
                      />
                      <el-table-column label="操作" width="140" fixed="right">
                        <template #default="scope">
                          <el-button size="small" @click="previewAttachment(scope.row)">
                            预览
                          </el-button>
                          <el-button size="small" @click="downloadAttachment(scope.row)">
                            下载
                          </el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>

                  <div v-else class="mobile-attachment-list">
                    <el-card
                      v-for="item in attachments"
                      :key="item.attachment_id"
                      class="mobile-attachment-card"
                      shadow="hover"
                    >
                      <div class="file-header">
                        <span class="file-name">{{ item.file_name }}</span>
                      </div>
                      <div class="file-info">
                        <div class="info-item">上传人: {{ item.uploader?.real_name || '-' }}</div>
                        <div class="info-item">大 小: {{ formatFileSize(item) }}</div>
                        <div class="info-item">时 间: {{ formatDateTime(item.uploaded_at) }}</div>
                      </div>
                      <div class="file-actions">
                        <el-button
                          size="small"
                          type="primary"
                          plain
                          @click="previewAttachment(item)"
                          >预览</el-button
                        >
                        <el-button size="small" @click="downloadAttachment(item)">下载</el-button>
                      </div>
                    </el-card>
                  </div>
                </template>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="电子卷宗" name="volume" :lazy="true">
        <CaseVolumePanel v-if="caseId" :case-id="caseId" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="showFilePreview"
      :title="previewTitle"
      width="90%"
      height="90vh"
      :close-on-click-modal="false"
      destroy-on-close
      @closed="handlePreviewClose"
    >
      <div class="preview-container">
        <img
          v-if="previewType === 'image'"
          :src="previewUrl"
          class="image-preview"
          alt="预览图片"
          @error="handleImageError"
        />
        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="pdf-iframe" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

// 引入拆分的组件
import GeneralCaseDetail from './GeneralCaseDetail.vue'
import CaseVolumePanel from '@/views/CaseVolumePanel.vue'
import BankCaseDetail from './BankCaseDetail.vue'

// -------------------------- 响应式/移动端适配相关 --------------------------
const isMobile = ref(false)
const checkDeviceType = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)
  loadCaseDetail()
  // 如果 URL 参数中有 tab=volume，自动切换到卷宗 Tab
  if (route.query.tab === 'volume') {
    activeTab.value = 'volume'
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})

// 向下层子组件提供移动端状态
provide('isMobile', isMobile)
// ---------------------------------------------------------------------------

const route = useRoute()
const router = useRouter()
const activeTab = ref('detail')
const caseData = ref({})
const loading = ref(false)
const caseId = route.params.id

// 附件相关变量
const attachments = ref([])
const attachmentFileList = ref([])
const loadingAttachments = ref(false)

const goBack = () => {
  // 1. 如果有明确的来源参数，直接跳转回来源页
  if (route.query.from) {
    router.push(route.query.from)
  }
  // 2. 如果没有来源，且浏览器的历史记录只有1条（说明是新标签页打开的）
  else if (window.history.length <= 1) {
    // 尝试关闭当前新标签页
    window.close()
    // 兜底方案：如果因为浏览器安全策略无法关闭，则强制跳转回总业务列表
    setTimeout(() => {
      router.push('/main/cases')
    }, 100)
  }
  // 3. 正常情况：在当前标签页跳转的，直接后退
  else {
    router.back()
  }
}

const loadCaseDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/cases/${caseId}`)
    caseData.value = res.data || {}

    // 权限判断逻辑
    const role = localStorage.getItem('role')
    const currentUserId = localStorage.getItem('user_id')
    const mainLawyerId = caseData.value.main_lawyer?.id
    const assistantLawyerId = caseData.value.assistant_lawyer?.id
    const assistantLawyer2Id = caseData.value.assistant_lawyer_2?.id
    const executionLawyerId = caseData.value.execution_lawyer?.id
    const executionAssistantId = caseData.value.execution_assistant?.id

    if (
      role === 'user' &&
      String(mainLawyerId) !== String(currentUserId) &&
      String(assistantLawyerId) !== String(currentUserId) &&
      String(assistantLawyer2Id) !== String(currentUserId) &&
      String(executionLawyerId) !== String(currentUserId) &&
      String(executionAssistantId) !== String(currentUserId)
    ) {
      ElMessage.error('您没有权限查看此业务')
      await router.push('/main/cases')
    } else {
      // 加载业务附件
      await loadAttachments()
    }
  } catch (err) {
    console.error('加载业务详情失败:', err)
    ElMessage.error('加载业务详情失败')
    await router.push('/main/cases')
  } finally {
    loading.value = false
  }
}

// 加载案件附件
const loadAttachments = async () => {
  if (!caseId) return
  loadingAttachments.value = true
  try {
    const res = await request.get(`/attachments/case/${caseId}`)
    attachments.value = res.data
    // 转换为上传组件需要的格式
    attachmentFileList.value = res.data.map((item) => ({
      name: item.file_name,
      url: `/attachments/${item.attachment_id}/download`,
      uid: item.attachment_id,
    }))
  } catch (err) {
    console.error('加载附件失败:', err)
    ElMessage.error('加载附件失败')
  } finally {
    loadingAttachments.value = false
  }
}

// 文件大小转换方法
const formatFileSize = (row) => {
  // 假设file_size单位是字节，转换为KB或MB并保留两位小数
  if (!row.file_size) return '0 KB'
  if (row.file_size < 1024 * 1024) {
    return (row.file_size / 1024).toFixed(2) + ' KB'
  }
  const mbSize = row.file_size / (1024 * 1024)
  return mbSize.toFixed(2) + ' MB'
}

// 下载附件
const downloadAttachment = async (attachment) => {
  try {
    ElMessage.info('正在获取文件，请稍候...')

    // 1. 发起请求，注意 responseType: 'blob' 必须加上
    const res = await request.get(`/attachments/${attachment.attachment_id}/download`, {
      responseType: 'blob',
    })

    // 2. 获取文件名（从传入的 attachment 对象中获取，或者从响应头 Content-Disposition 提取）
    const fileName = attachment.file_name || '附件下载'

    // 3. 创建 Blob URL 并触发下载
    const blob = new Blob([res.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName

    // 兼容 Firefox 触发点击
    document.body.appendChild(link)
    link.click()

    // 4. 清理内存
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (err) {
    console.error('下载附件失败:', err)
    ElMessage.error('附件下载失败，请检查网络或权限')
  }
}

// 预览相关
const showFilePreview = ref(false)
const previewUrl = ref('')
const previewType = ref('') // 'image' 或 'pdf'
const previewTitle = ref('文件预览')

const previewAttachment = async (attachment) => {
  const fileType = attachment.file_type || ''

  // 1. 先判断是否支持预览
  const isImage = fileType.startsWith('image/')
  const previewableTypes = [
    'application/pdf',
    'application/msword', // .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  ]
  const isPdfOrWord = previewableTypes.includes(fileType)

  if (!isImage && !isPdfOrWord) {
    ElMessage.info('该文件类型不支持直接预览，建议下载查看')
    return
  }

  // 2. 发起携带 Token 的请求获取文件流
  try {
    ElMessage.info('正在加载预览，请稍候...')

    // 使用统一的 request 请求，附带 responseType: 'blob'
    const res = await request.get(`/attachments/${attachment.attachment_id}/preview`, {
      responseType: 'blob',
    })

    // 确定 Blob 的 MIME 类型 (特别注意：后端将 Word 转成了 PDF，所以此处可以强制指定为 pdf 格式)
    let contentType = fileType
    if (isPdfOrWord && !fileType.includes('pdf')) {
      contentType = 'application/pdf'
    }

    // 创建本地临时 URL
    const blob = new Blob([res.data], { type: contentType })
    const objectUrl = window.URL.createObjectURL(blob)

    // 3. 赋值并打开预览弹窗
    if (isImage) {
      previewType.value = 'image'
      previewTitle.value = `图片预览：${attachment.file_name}`
    } else {
      previewType.value = 'pdf'
      previewTitle.value = `PDF预览：${attachment.file_name}`
    }
    previewUrl.value = objectUrl
    showFilePreview.value = true
  } catch (err) {
    console.error('获取预览失败:', err)
    ElMessage.error('预览加载失败，请检查网络或权限')
  }
}

// 关闭预览时清理资源
const handlePreviewClose = () => {
  // 检查是否是blob URL，若是则释放
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    try {
      // 释放blob URL内存
      window.URL.revokeObjectURL(previewUrl.value)
    } catch (e) {
      console.warn('释放blob URL失败:', e)
    }
    // 清空URL，避免残留
    previewUrl.value = ''
  }
  // 清空其他预览状态
  previewTitle.value = ''
  previewType.value = ''
}

// 图片加载失败处理
const handleImageError = (e) => {
  e.target.src = 'https://placeholder.pics/svg/800x600/CCCCCC/666666/图片加载失败'
  console.error('图片预览加载失败')
}

const formatDateTime = (dateVal) => {
  if (!dateVal) return ''
  let timestamp

  // 处理时间戳（数字类型）
  if (typeof dateVal === 'number') {
    // 处理秒级时间戳（如果是10位数字）
    if (dateVal.toString().length === 10) {
      dateVal *= 1000
    }
    timestamp = dateVal
  }
  // 处理字符串类型
  else if (typeof dateVal === 'string') {
    // 尝试多种常见格式转换
    const formats = [
      // 尝试不添加Z的情况（本地时间）
      dateVal.replace(' ', 'T'),
      // 尝试添加Z的情况（UTC时间）
      dateVal.replace(' ', 'T') + 'Z',
      // 尝试直接解析原始字符串
      dateVal,
    ]

    // 尝试各种格式，找到能正确解析的
    for (const fmt of formats) {
      const tempDate = new Date(fmt)
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime()
        break
      }
    }
  }
  // 处理Date对象
  else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime()
  }

  // 验证时间戳是否有效
  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal)
    return '无效日期'
  }

  const date = new Date(timestamp)

  // 使用toLocaleString()同时显示日期和时间
  // 可以通过参数自定义格式，例如：
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false, // 24小时制
  })
}
</script>

<style scoped>
.case-detail {
  padding: 20px;
}
.page-title {
  text-align: center;
  font-size: 22px;
  font-weight: bold;
  color: #333;
  margin: 15px 0 25px 0;
}
.detail-card {
  margin-top: 10px;
  line-height: 1.6;
}
.attachment-list {
  margin-top: 10px;
}
.no-attachments {
  color: #999;
  padding: 10px;
  text-align: center;
}

/* 附件表格横向滚动适配 */
.table-responsive {
  width: 100%;
  overflow-x: auto;
}

/* 移动端附件卡片样式 */
.mobile-attachment-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mobile-attachment-card {
  --el-card-padding: 12px;
}
.file-header {
  margin-bottom: 8px;
}
.file-name {
  font-weight: bold;
  color: #303133;
  word-break: break-all;
  font-size: 14px;
}
.file-info {
  font-size: 12px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.8;
}
.info-item {
  display: flex;
  justify-content: flex-start;
}
.file-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #ebeef5;
  padding-top: 10px;
}

.preview-container {
  width: 100%;
  height: calc(90vh - 100px);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
}
.image-preview {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
.pdf-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #ffffff;
  border-radius: 4px;
}

/* 移动端细微样式调整 */
@media screen and (max-width: 768px) {
  .case-detail {
    padding: 10px;
  }
  .page-title {
    font-size: 18px;
    margin: 10px 0 15px 0;
  }
}
</style>
