<template>
  <div class="announcement-center">
    <div class="page-header">
      <div class="header-title">
        <el-icon class="title-icon"><ChatDotRound /></el-icon>
        <h2>消息与公告中心</h2>
      </div>
    </div>

    <div class="list-container" v-loading="loading">
      <el-empty v-if="announcements.length === 0" description="暂无历史公告" />

      <el-row :gutter="20">
        <el-col :span="24" v-for="item in announcements" :key="item.id" class="card-col">
          <el-card
            class="announcement-card"
            :class="{ 'is-unread': !item.is_read }"
            shadow="never"
            @click="openDetail(item)"
          >
            <div class="card-layout">
              <div class="card-icon-area">
                <div class="icon-circle" :class="item.type">
                  <el-icon v-if="item.type === 'update_log'"><Promotion /></el-icon>
                  <el-icon v-else-if="item.type === 'case_review'"><Warning /></el-icon>
                  <el-icon v-else><Notification /></el-icon>
                </div>
              </div>

              <div class="card-content-area">
                <div class="card-top">
                  <div class="title-wrap">
                    <span class="unread-dot" v-if="!item.is_read"></span>
                    <span class="card-title" :title="item.title">{{ item.title }}</span>
                    <el-tag
                      v-if="item.version"
                      size="small"
                      class="version-tag"
                      type="primary"
                      effect="light"
                      round
                    >
                      v{{ item.version }}
                    </el-tag>
                  </div>
                  <span class="card-date">{{ formatDate(item.created_at) }}</span>
                </div>

                <div class="card-desc">
                  <p class="summary-text">{{ stripHtml(item.content) }}</p>
                </div>

                <div class="card-bottom">
                  <span class="publisher">
                    <el-icon><User /></el-icon>
                    {{ item.publisher_name || '系统' }}
                  </span>
                  <el-button link type="primary" class="read-more-btn">
                    查看详情 <el-icon class="read-more-icon"><ArrowRight /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-area" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          class="custom-pagination"
        />
      </div>
    </div>

    <el-dialog
      v-model="detailVisible"
      title="公告详情"
      class="detail-dialog custom-dialog"
      destroy-on-close
      align-center
    >
      <div v-if="currentDetail" class="detail-container">
        <h2 class="detail-title">{{ currentDetail.title }}</h2>
        <div class="detail-meta">
          <span class="meta-item"
            >类型：{{ currentDetail.type === 'update_log' ? '更新日志' : currentDetail.type === 'case_review' ? '审核驳回' : '系统公告' }}</span
          >
          <span class="meta-item" v-if="currentDetail.version"
            >版本：v{{ currentDetail.version }}</span
          >
          <span class="meta-item">时间：{{ formatDate(currentDetail.created_at) }}</span>
          <span class="meta-item">发布人：{{ currentDetail.publisher_name }}</span>
        </div>
        <el-divider border-style="dashed" class="custom-divider" />
        <div class="rich-text-content" v-html="currentDetail.content"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ChatDotRound, Promotion, Notification, ArrowRight, User, Warning } from '@element-plus/icons-vue'

const loading = ref(false)
const announcements = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const detailVisible = ref(false)
const currentDetail = ref(null)

const fetchAnnouncements = async () => {
  loading.value = true
  try {
    const res = await request.get('/system/announcements/center/list', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
      },
    })
    announcements.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取公告列表失败', err)
  } finally {
    loading.value = false
  }
}

const openDetail = async (item) => {
  currentDetail.value = item
  detailVisible.value = true

  // 如果未读，调用接口标记为已读，并消除本地红点
  if (!item.is_read) {
    try {
      await request.post(`/system/announcements/${item.id}/read`)
      item.is_read = true // 前端消点
    } catch (e) {
      console.error('标记已读失败', e)
    }
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchAnnouncements()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchAnnouncements()
}

// 辅助：提取富文本纯文本用于摘要展示
const stripHtml = (html) => {
  if (!html) return '暂无内容概要...'
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  const text = tmp.textContent || tmp.innerText || ''
  return text.length > 80 ? text.substring(0, 80) + '...' : text
}

// 辅助：格式化时间
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  fetchAnnouncements()
})
</script>

<style scoped>
/* 整体布局 */
.announcement-center {
  padding: 10px 20px;
  background-color: #f7f9fc;
  min-height: calc(100vh - 100px);
  border-radius: 12px;
}

.page-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-title {
  display: flex;
  align-items: center;
  color: #1f2329;
}

.title-icon {
  font-size: 28px;
  color: #165dff;
  margin-right: 12px;
}

.header-title h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 列表容器 */
.list-container {
  max-width: 1000px;
  margin: 0 auto;
}

.card-col {
  margin-bottom: 20px;
}

/* 卡片样式高级化 */
.announcement-card {
  border-radius: 16px;
  border: 1px solid #e5e8ef;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.announcement-card:hover {
  transform: translateY(-4px);
  border-color: #c3d4ff;
  box-shadow: 0 12px 32px rgba(22, 93, 255, 0.1) !important;
}

/* 未读状态卡片特殊高亮 */
.announcement-card.is-unread {
  background: linear-gradient(145deg, #ffffff 0%, #f4f7ff 100%);
  border-left: 5px solid #165dff;
}

.card-layout {
  display: flex;
  align-items: flex-start;
  padding: 8px;
}

.card-icon-area {
  margin-right: 24px;
}

.icon-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s;
}

.announcement-card:hover .icon-circle {
  transform: scale(1.05);
}

.icon-circle.update_log {
  background: linear-gradient(135deg, #85d655, #67c23a);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.3);
}

.icon-circle.general_notice {
  background: linear-gradient(135deg, #4080ff, #165dff);
  box-shadow: 0 6px 16px rgba(22, 93, 255, 0.3);
}

.icon-circle.case_review {
  background: linear-gradient(135deg, #f6a742, #e6a23c);
  box-shadow: 0 6px 16px rgba(230, 162, 60, 0.35);
}

.card-content-area {
  flex: 1;
  min-width: 0; /* 防止flex子项被内容撑爆 */
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

/* 未读红点动效 */
.unread-dot {
  flex-shrink: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #f53f3f;
  box-shadow: 0 0 0 3px rgba(245, 63, 63, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(245, 63, 63, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(245, 63, 63, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(245, 63, 63, 0);
  }
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2329;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 450px;
}

.version-tag {
  font-weight: 600;
  flex-shrink: 0;
}

.card-date {
  font-size: 14px;
  color: #86909c;
  flex-shrink: 0;
}

.card-desc {
  margin-bottom: 16px;
}

.summary-text {
  margin: 0;
  font-size: 15px;
  color: #4e5969;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f2f3f5;
  padding-top: 12px;
}

.publisher {
  font-size: 14px;
  color: #86909c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.read-more-btn {
  font-size: 14px;
  font-weight: 500;
}

.read-more-icon {
  margin-left: 2px;
  transition: transform 0.3s;
}

.announcement-card:hover .read-more-icon {
  transform: translateX(4px);
}

.pagination-area {
  margin-top: 30px;
  display: flex;
  justify-content: flex-end;
  padding-bottom: 20px;
}

/* === 详情弹窗定制 === */
:deep(.custom-dialog) {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15) !important;
  width: 700px;
  max-width: 95vw;
}

:deep(.custom-dialog .el-dialog__header) {
  padding: 24px 24px 10px;
  margin-right: 0;
}

:deep(.custom-dialog .el-dialog__title) {
  font-weight: 600;
  font-size: 18px;
}

:deep(.custom-dialog .el-dialog__body) {
  padding: 0; /* 移除默认内边距，完全由 detail-container 控制 */
}

/* 核心：修复溢出且增加美观的内部滚动 */
.detail-container {
  padding: 10px 32px 32px;
  max-height: 65vh; /* 限制弹窗内容最大高度 */
  overflow-y: auto; /* 允许内部滚动 */
  overflow-x: hidden;
  box-sizing: border-box;
}

/* 美化弹窗内部滚动条 */
.detail-container::-webkit-scrollbar {
  width: 6px;
}
.detail-container::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}
.detail-container::-webkit-scrollbar-track {
  background: transparent;
}

.detail-title {
  font-size: 24px;
  color: #1f2329;
  margin-top: 0;
  margin-bottom: 16px;
  text-align: center;
  font-weight: 600;
  line-height: 1.4;
}

.detail-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 14px;
  color: #86909c;
  flex-wrap: wrap;
  background: #f7f8fa;
  padding: 12px;
  border-radius: 8px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
}

.custom-divider {
  margin: 24px 0;
  border-color: #e5e6eb;
}

.rich-text-content {
  color: #1f2329;
  line-height: 1.8;
  font-size: 16px;
  word-wrap: break-word;
}

/* 终极修复富文本图片/视频溢出问题 */
.rich-text-content :deep(img),
.rich-text-content :deep(video),
.rich-text-content :deep(iframe) {
  max-width: 100% !important;
  height: auto !important;
  border-radius: 12px;
  margin: 20px auto;
  display: block; /* 强制块级元素，防止内联排版导致的一系列问题 */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
  object-fit: contain;
}

.rich-text-content :deep(p) {
  margin-bottom: 1em;
}

.rich-text-content :deep(a) {
  color: #165dff;
  text-decoration: none;
}
.rich-text-content :deep(a:hover) {
  text-decoration: underline;
}

/* =========================================
   移动端响应式适配 (小于 768px 时生效)
========================================= */
@media (max-width: 768px) {
  .announcement-center {
    padding: 10px;
  }

  .header-title h2 {
    font-size: 20px;
  }

  /* 卡片调整为更紧凑的布局 */
  .card-layout {
    padding: 0;
  }

  .card-icon-area {
    margin-right: 12px;
  }

  .icon-circle {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .card-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  /* 允许移动端标题换行，而不是截断 */
  .card-title {
    max-width: 100%;
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    font-size: 16px;
  }

  .card-date {
    font-size: 12px;
  }

  .summary-text {
    font-size: 14px;
    -webkit-line-clamp: 3;
    line-clamp: 3;
  }

  /* 弹窗宽度完全贴合移动端 */
  :deep(.custom-dialog) {
    width: 92% !important;
  }

  .detail-container {
    padding: 10px 16px 20px;
    max-height: 70vh; /* 移动端增加高度比例 */
  }

  .detail-title {
    font-size: 20px;
  }

  .detail-meta {
    gap: 10px;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .pagination-area {
    justify-content: center;
  }

  /* 移动端下隐藏分页组件的某些复杂部分 */
  .custom-pagination {
    --el-pagination-button-width: 30px;
  }
  .custom-pagination :deep(.el-pagination__sizes),
  .custom-pagination :deep(.el-pagination__jump) {
    display: none !important;
  }
}
</style>
