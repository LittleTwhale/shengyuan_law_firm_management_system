<template>
  <el-dialog
    v-model="dialogVisible"
    title="📂 全局文件穿透搜索 (OCR内容检索)"
    width="800px"
    destroy-on-close
    append-to-body
  >
    <div class="global-search-wrapper">
      <el-input
        v-model="keyword"
        placeholder="输入关键词搜索所有电子卷宗文件内容..."
        :prefix-icon="Search"
        size="large"
        clearable
        class="global-search-input"
      />

      <el-scrollbar height="500px" class="search-result-area">
        <div v-if="!keyword" class="search-placeholder">
          <el-empty description="输入关键词开始搜索" :image-size="80" />
        </div>

        <div v-else-if="searchLoading" class="search-loading">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else-if="results.length === 0" class="search-empty">
          <el-empty description="未找到匹配的文件" :image-size="80" />
        </div>

        <div v-else class="result-list">
          <div
            v-for="item in results"
            :key="item.id"
            class="result-card"
            @click="openFileCase(item)"
          >
            <div class="card-top">
              <span class="card-filename" v-html="DOMPurify.sanitize(item.file_name)"></span>
              <el-tag size="small" effect="light">{{ item.category || '未分类' }}</el-tag>
            </div>
            <div
              v-if="item.ocr_content"
              class="card-ocr"
              v-html="DOMPurify.sanitize(item.ocr_content)"
            ></div>
            <div class="card-bottom">
              <el-icon><Document /></el-icon>
              <span>{{ item.case_number || '-' }}</span>
              <el-divider direction="vertical" />
              <el-icon><Folder /></el-icon>
              <span>{{ item.volume_name || '-' }}</span>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { debounce } from 'lodash-es'
import DOMPurify from 'dompurify'
import { Search, Document, Folder } from '@element-plus/icons-vue'
import request from '@/utils/request.js'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

// 当对话框关闭时，清空搜索记录
watch(dialogVisible, (newVal) => {
  if (!newVal) {
    keyword.value = ''
    results.value = []
  }
})

const keyword = ref('')
const results = ref([])
const searchLoading = ref(false)

const doSearch = async () => {
  const kw = keyword.value.trim()
  if (!kw) {
    results.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await request.get('/electronic_volumes/files/search', {
      params: { keyword: kw, page_size: 20 },
    })
    results.value = res.data.items || []
  } catch (err) {
    console.error('全局文件搜索失败', err)
    results.value = []
  } finally {
    searchLoading.value = false
  }
}

const debouncedSearch = debounce(() => {
  doSearch()
}, 400)

watch(keyword, () => {
  debouncedSearch()
})

const openFileCase = (item) => {
  if (!item.case_id) return
  window.open(`/main/cases/${item.case_id}?tab=volume`)
}
</script>

<style scoped>
.global-search-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.global-search-input {
  font-size: 15px;
}

.search-result-area {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
}

.search-placeholder,
.search-loading,
.search-empty {
  padding: 60px 20px;
}

.result-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s;
}

.result-card:hover {
  background: #f5f7fa;
  border-color: #c6e2ff;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.card-filename {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-ocr {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f9f9f9;
  border-radius: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* 旧版 Chrome/Safari/Edge */
  line-clamp: 3; /* 标准属性（新版浏览器用）*/
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-bottom {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
}

:deep(.search-highlight) {
  color: #f56c6c;
  background-color: rgba(245, 108, 108, 0.1);
  font-weight: bold;
  border-radius: 2px;
  padding: 0 2px;
}

.card-ocr :deep(.search-highlight) {
  background-color: #fff176;
  color: #d32f2f;
}
</style>
