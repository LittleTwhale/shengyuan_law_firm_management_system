<template>
  <div class="library-layout">
    <!-- 顶部搜索栏 -->
    <header class="library-header">
      <div class="header-left">
        <el-icon class="header-back" @click="$router.push('/main')"><ArrowLeft /></el-icon>
        <h1 class="header-title">
          <el-icon :size="24"><Notebook /></el-icon>
          法律图书馆
        </h1>
        <span v-if="stats.total_laws" class="header-stats">
          {{ stats.total_laws }} 部法律 · {{ stats.total_articles.toLocaleString() }} 条条文
        </span>
      </div>
      <div class="header-search">
        <el-input
          v-model="keyword"
          placeholder="搜索法律条文，如'故意杀人'、'合同无效'..."
          :prefix-icon="Search"
          size="large"
          clearable
          class="search-input"
          @clear="clearSearch"
          @keyup.enter="doSearch"
        />
        <el-button type="primary" size="large" @click="doSearch" :loading="searching">
          <el-icon><Search /></el-icon>
          检索
        </el-button>
      </div>
    </header>

    <!-- 主体三栏区域 -->
    <div class="library-body">
      <!-- ========== 左栏：分类书架 ========== -->
      <aside class="left-panel" :class="{ 'panel-hidden': !showLeftPanel }">
        <div class="panel-inner">
          <div class="panel-header">
            <el-icon><Collection /></el-icon>
            <span>分类书架</span>
            <el-input
              v-model="categoryFilter"
              placeholder="筛选分类..."
              size="small"
              clearable
              class="category-filter-input"
            />
          </div>
          <div class="category-list">
            <div
              v-for="cat in filteredCategories"
              :key="cat.name"
              class="category-card"
              :class="{ active: selectedCategory === cat.name }"
              :style="{ '--cat-color': getCategoryColor(cat.name) }"
              @click="selectCategory(cat.name)"
            >
              <div class="cat-info">
                <span class="cat-name">{{ cat.name }}</span>
                <span class="cat-count">{{ cat.count.toLocaleString() }} 条</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 移动端左栏遮罩 -->
      <div v-if="showLeftPanel && isMobile" class="panel-overlay" @click="showLeftPanel = false" />

      <!-- ========== 中栏：法律目录 ========== -->
      <section class="mid-panel" :class="{ 'panel-hidden': !showMidPanel }">
        <!-- 分类视图：展示该分类下的法律列表 -->
        <div v-if="!activeLaw" class="law-list-view">
          <div class="panel-header">
            <el-icon><Reading /></el-icon>
            <span>{{ selectedCategory || '请选择分类' }}</span>
            <span v-if="lawList.length" class="header-count">{{ lawList.length }} 部</span>
          </div>
          <div class="law-list">
            <div v-for="law in lawList" :key="law" class="law-item" @click="openLaw(law)">
              <span class="law-icon">📜</span>
              <el-tooltip :content="law" placement="top" :show-after="500" effect="dark">
                <span class="law-name">{{ law }}</span>
              </el-tooltip>
              <el-icon class="law-arrow"><ArrowRight /></el-icon>
            </div>
            <el-empty
              v-if="!selectedCategory"
              description="请从左侧书架选择分类"
              :image-size="60"
            />
            <el-empty v-else-if="!lawList.length" description="该分类下暂无法律" :image-size="60" />
          </div>
        </div>

        <!-- 法律目录树视图 -->
        <div v-else class="toc-view">
          <div class="panel-header">
            <el-button text size="small" @click="resetLaw">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-tooltip :content="activeLaw" placement="top" :show-after="500" effect="dark">
              <span class="toc-law-title">{{ activeLaw }}</span>
            </el-tooltip>
            <span class="header-count">{{ lawStructure?.total_articles || 0 }} 条</span>
          </div>
          <div class="toc-tree" v-loading="structureLoading">
            <div v-if="lawStructure?.chapters?.length" class="chapter-list">
              <div v-for="(ch, ci) in lawStructure.chapters" :key="ci" class="toc-chapter">
                <div class="toc-chapter-title" @click="toggleChapter(ci)">
                  <el-icon>
                    <ArrowRight v-if="collapsedChapters[ci]" />
                    <ArrowDown v-else />
                  </el-icon>
                  <span>{{ ch.title }}</span>
                  <span class="toc-count"
                    >{{ (ch.sections?.length || 0) + (ch.articles?.length || 0) }} 条</span
                  >
                </div>
                <div v-show="!collapsedChapters[ci]" class="toc-chapter-body">
                  <!-- 节 -->
                  <div v-for="(sec, si) in ch.sections" :key="'s' + si" class="toc-section">
                    <div class="toc-section-title">{{ sec.title }}</div>
                    <div
                      v-for="art in sec.articles"
                      :key="art.id"
                      class="toc-article"
                      :class="{ active: activeArticle?.id === art.id }"
                      @click="loadArticle(art)"
                    >
                      {{ art.article_number }}
                    </div>
                  </div>
                  <!-- 直属条文 -->
                  <div
                    v-for="art in ch.articles"
                    :key="art.id"
                    class="toc-article"
                    :class="{ active: activeArticle?.id === art.id }"
                    @click="loadArticle(art)"
                  >
                    {{ art.article_number }}
                  </div>
                </div>
              </div>
            </div>
            <el-skeleton v-if="structureLoading" :rows="8" animated />
          </div>
        </div>
      </section>

      <!-- 移动端中栏遮罩 -->
      <div v-if="showMidPanel && isMobile" class="panel-overlay" @click="showMidPanel = false" />

      <!-- ========== 右栏：阅读 / 搜索结果 ========== -->
      <main class="right-panel">
        <!-- 搜索模式 -->
        <div v-if="searchMode" class="search-results-view">
          <div class="panel-header">
            <span>搜索结果</span>
            <el-button text size="small" @click="clearSearch">退出搜索</el-button>
          </div>
          <div class="search-summary" v-if="searched">
            共找到 <strong>{{ searchTotal }}</strong> 条相关法律条文
          </div>
          <div class="search-list" v-loading="searching">
            <div
              v-for="item in searchResults"
              :key="item.id"
              class="search-card"
              @click="viewSearchResult(item)"
            >
              <div class="search-card-top">
                <span
                  class="search-card-tag"
                  :style="{ background: getCategoryColor(item.law_category) }"
                >
                  {{ item.law_category }}
                </span>
                <span class="search-card-law">{{ item.law_name }}</span>
                <span class="search-card-article">{{ item.article_number }}</span>
              </div>
              <div
                class="search-card-content"
                v-html="DOMPurify.sanitize(item.content_highlighted || item.content)"
              />
            </div>
            <el-empty
              v-if="searched && !searching && !searchResults.length"
              description="未找到匹配的法律条文"
              :image-size="80"
            />
          </div>
          <div class="search-pagination" v-if="searchTotal > searchPageSize">
            <el-pagination
              v-model:current-page="searchPage"
              :page-size="searchPageSize"
              :total="searchTotal"
              layout="prev, pager, next"
              small
              @current-change="doSearch"
            />
          </div>
        </div>

        <!-- 阅读模式 -->
        <div v-else class="reader-view">
          <!-- 空状态 -->
          <div v-if="!activeArticle" class="reader-empty">
            <div class="welcome-box">
              <div class="welcome-icon">⚖️</div>
              <h3>欢迎使用法律图书馆</h3>
              <p>从左栏选择分类 → 中栏选择法律 → 目录中点击条文开始阅读</p>
              <p class="welcome-hint">也可以使用顶部搜索框直接检索法条</p>
            </div>
          </div>

          <!-- 条文阅读 -->
          <div v-else class="reader-content">
            <div class="reader-toolbar">
              <el-tooltip :content="activeArticle.law_name || activeLaw" placement="top" :show-after="500" effect="dark">
              <span class="reader-law-name">{{ activeArticle.law_name || activeLaw }}</span>
            </el-tooltip>
              <div class="reader-toolbar-actions">
                <el-button text size="small" @click="copyArticle">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button
                  text
                  size="small"
                  :disabled="!prevArticleId"
                  @click="loadArticle({ id: prevArticleId })"
                >
                  <el-icon><ArrowLeft /></el-icon>
                  上一条
                </el-button>
                <el-button
                  text
                  size="small"
                  :disabled="!nextArticleId"
                  @click="loadArticle({ id: nextArticleId })"
                >
                  下一条
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="reader-article">
              <div class="reader-article-header">
                <span class="reader-article-num">{{ activeArticle.article_number }}</span>
                <span v-if="activeArticle.chapter" class="reader-article-chapter">{{
                  activeArticle.chapter
                }}</span>
                <span v-if="activeArticle.section" class="reader-article-section">{{
                  activeArticle.section
                }}</span>
              </div>
              <div class="reader-article-body" v-html="renderMarkdown(activeArticle.content)" />
            </div>
          </div>
        </div>

        <!-- 移动端底部工具栏 -->
        <div v-if="isMobile" class="mobile-toolbar">
          <el-button
            :type="showLeftPanel ? 'primary' : 'default'"
            size="small"
            @click="toggleMobilePanel('left')"
          >
            <el-icon><Collection /></el-icon>
            分类
          </el-button>
          <el-button
            :type="showMidPanel ? 'primary' : 'default'"
            size="small"
            @click="toggleMobilePanel('mid')"
          >
            <el-icon><Reading /></el-icon>
            目录
          </el-button>
          <el-button
            :type="!showLeftPanel && !showMidPanel ? 'primary' : 'default'"
            size="small"
            @click="resetPanel"
          >
            <el-icon><Document /></el-icon>
            阅读
          </el-button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Notebook,
  Collection,
  Reading,
  ArrowLeft,
  ArrowRight,
  ArrowDown,
  CopyDocument,
  Document,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import request from '@/utils/request'

// ============================== 响应式状态 ==============================

// 统计
const stats = ref({ total_laws: 0, total_articles: 0 })

// 分类
const categories = ref([])
const selectedCategory = ref('')
const categoryFilter = ref('')

// 法律列表
const lawList = ref([])

// 当前法律 & 结构
const activeLaw = ref('')
const lawStructure = ref(null)
const structureLoading = ref(false)
const collapsedChapters = ref({})

// 当前条文
const activeArticle = ref(null)

// 搜索
const keyword = ref('')
const searching = ref(false)
const searched = ref(false)
const searchMode = ref(false)
const searchResults = ref([])
const searchTotal = ref(0)
const searchPage = ref(1)
const searchPageSize = 15

// 移动端面板
const isMobile = ref(false)
const showLeftPanel = ref(false)
const showMidPanel = ref(false)

// ============================== 计算属性 ==============================

const filteredCategories = computed(() => {
  const f = categoryFilter.value.trim().toLowerCase()
  if (!f) return categories.value
  return categories.value.filter((c) => c.name.toLowerCase().includes(f))
})

// 当前阅读条文的前后导航
const allArticleIds = computed(() => {
  if (!lawStructure.value?.chapters) return []
  const ids = []
  for (const ch of lawStructure.value.chapters) {
    for (const art of ch.articles || []) ids.push(art.id)
    for (const sec of ch.sections || []) {
      for (const art of sec.articles || []) ids.push(art.id)
    }
  }
  return ids
})
const prevArticleId = computed(() => {
  if (!activeArticle.value) return null
  const ids = allArticleIds.value
  const idx = ids.indexOf(activeArticle.value.id)
  return idx > 0 ? ids[idx - 1] : null
})
const nextArticleId = computed(() => {
  if (!activeArticle.value) return null
  const ids = allArticleIds.value
  const idx = ids.indexOf(activeArticle.value.id)
  return idx < ids.length - 1 ? ids[idx + 1] : null
})

// 重置
const resetLaw = () => {
  activeLaw.value = ''
  lawStructure.value = null
}

const resetPanel = () => {
  showLeftPanel.value = false
  showMidPanel.value = false
}

// ============================== 分类配色 ==============================

const categoryColors = {
  宪法: '#e74c3c',
  宪法相关法: '#c0392b',
  刑法: '#e67e22',
  民法典: '#8e44ad',
  民法商法: '#2ecc71',
  行政法: '#3498db',
  经济法: '#1abc9c',
  社会法: '#f39c12',
  诉讼与非诉讼程序法: '#2980b9',
  行政法规: '#16a085',
  司法解释: '#d35400',
  部门规章: '#7f8c8d',
  其他: '#95a5a6',
}

function getCategoryColor(name) {
  return categoryColors[name] || '#6366f1'
}
// ============================== 响应式检测 ==============================

function checkDevice() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    showLeftPanel.value = true
    showMidPanel.value = true
  } else {
    showLeftPanel.value = false
    showMidPanel.value = false
  }
}

// ============================== 数据加载 ==============================

async function loadStats() {
  try {
    const res = await request.get('/legal/stats')
    stats.value = res.data
  } catch (e) {
    ElMessage.error('加载统计数据失败')
    console.error('加载统计数据失败', e)
  }
}

async function loadCategories() {
  try {
    const res = await request.get('/legal/categories')
    categories.value = res.data.categories || []
  } catch (e) {
    console.error('加载分类失败', e)
    ElMessage.error('加载分类失败')
  }
}

async function selectCategory(catName) {
  if (selectedCategory.value === catName) {
    selectedCategory.value = ''
    lawList.value = []
    return
  }
  selectedCategory.value = catName
  activeLaw.value = ''
  lawStructure.value = null
  activeArticle.value = null
  searchMode.value = false

  // 移动端：选完分类自动展示中栏
  if (isMobile.value) {
    showLeftPanel.value = false
    showMidPanel.value = true
  }

  try {
    const res = await request.get('/legal/laws', { params: { category: catName } })
    lawList.value = res.data.laws || []
  } catch (e) {
    console.error('加载法律列表失败', e)
    ElMessage.error('加载法律列表失败')
  }
}

async function openLaw(lawName) {
  activeLaw.value = lawName
  activeArticle.value = null
  structureLoading.value = true

  // 移动端：选完法律自动展示阅读区
  if (isMobile.value) {
    showMidPanel.value = false
  }

  try {
    const res = await request.get('/legal/structure', { params: { law_name: lawName } })
    lawStructure.value = res.data
    collapsedChapters.value = {}
    // 自动加载第一条
    const firstArticle = findFirstArticle(res.data)
    if (firstArticle) {
      await loadArticle(firstArticle)
    }
  } catch (e) {
    console.error('加载法律结构失败', e)
    ElMessage.error('加载法律结构失败')
  } finally {
    structureLoading.value = false
  }
}

function findFirstArticle(structure) {
  if (!structure?.chapters?.length) return null
  for (const ch of structure.chapters) {
    if (ch.articles?.length) return ch.articles[0]
    for (const sec of ch.sections || []) {
      if (sec.articles?.length) return sec.articles[0]
    }
  }
  return null
}

async function loadArticle(art) {
  try {
    const res = await request.get('/legal/articles', {
      params: { law_name: activeLaw.value || art.law_name, page: 1, page_size: 500 },
    })
    const allArts = res.data.articles || []
    const match = allArts.find((a) => a.id === art.id)
    if (match) {
      activeArticle.value = { ...match, law_name: activeLaw.value }
    }
  } catch (e) {
    console.error('加载条文失败', e)
    ElMessage.error('加载条文失败')
  }
}

function toggleChapter(idx) {
  collapsedChapters.value[idx] = !collapsedChapters.value[idx]
}

// ============================== 搜索 ==============================

async function doSearch() {
  const kw = keyword.value.trim()
  if (!kw) return

  searching.value = true
  searched.value = true
  searchMode.value = true
  activeArticle.value = null

  if (isMobile.value) {
    showLeftPanel.value = false
    showMidPanel.value = false
  }

  try {
    const params = { keyword: kw, page: searchPage.value, page_size: searchPageSize }
    if (selectedCategory.value) params.law_category = selectedCategory.value
    const res = await request.get('/legal/search', { params })
    searchResults.value = res.data.items || []
    searchTotal.value = res.data.total || 0
  } catch (e) {
    console.error('搜索失败', e)
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

function clearSearch() {
  searchMode.value = false
  searched.value = false
  keyword.value = ''
  searchResults.value = []
  searchTotal.value = 0
  searchPage.value = 1
}

async function viewSearchResult(item) {
  // 加载该条文所属法律的目录结构
  activeLaw.value = item.law_name
  structureLoading.value = true
  try {
    const res = await request.get('/legal/structure', { params: { law_name: item.law_name } })
    lawStructure.value = res.data
    collapsedChapters.value = {}
  } catch (e) {
    console.error('加载法律结构失败', e)
    ElMessage.error('加载法律结构失败')
  } finally {
    structureLoading.value = false
  }
  // 直接展示该条文
  activeArticle.value = {
    id: item.id,
    article_number: item.article_number,
    chapter: item.chapter,
    section: item.section,
    content: item.content,
    law_name: item.law_name,
  }
  searchMode.value = false
}

// ============================== 工具方法 ==============================

function renderMarkdown(text) {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text))
}

function copyArticle() {
  if (!activeArticle.value) return
  const text = `${activeArticle.value.article_number}\n${activeArticle.value.content}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      ElMessage.success('已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

function toggleMobilePanel(panel) {
  if (panel === 'left') {
    showLeftPanel.value = !showLeftPanel.value
    if (showLeftPanel.value) showMidPanel.value = false
  } else {
    showMidPanel.value = !showMidPanel.value
    if (showMidPanel.value) showLeftPanel.value = false
  }
}

// ============================== 生命周期 ==============================

onMounted(async () => {
  checkDevice()
  window.addEventListener('resize', checkDevice)
  await Promise.all([loadStats(), loadCategories()])
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDevice)
})
</script>

<style scoped>
/* ========================= 基础布局 ========================= */
.library-layout {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
  background: #f5f6fa;
  border-radius: 12px;
  overflow: hidden;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========================= 顶部搜索栏 ========================= */
.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  gap: 24px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.header-back {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.header-back:hover {
  opacity: 1;
}
.header-title {
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  margin: 0;
}
.header-stats {
  font-size: 13px;
  opacity: 0.7;
  white-space: nowrap;
}
.header-search {
  display: flex;
  gap: 10px;
  flex: 1;
  max-width: 600px;
  min-width: 280px;
}
.search-input {
  flex: 1;
}
.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: none;
  border-radius: 8px;
}
.search-input :deep(.el-input__inner) {
  color: #fff;
}
.search-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}
.search-input :deep(.el-input__prefix) {
  color: rgba(255, 255, 255, 0.6);
}

/* ========================= 主体三栏 ========================= */
.library-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* ========================= 左栏：分类书架 ========================= */
.left-panel {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #eef0f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.3s ease;
  z-index: 10;
}
.panel-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #f0f2f5;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.header-count {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
  margin-left: auto;
}
.category-filter-input {
  width: 100%;
  margin-top: 6px;
}

.category-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 12px;
}
.category-list::-webkit-scrollbar {
  width: 4px;
}
.category-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.category-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  margin-bottom: 6px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
  background: #fafbfc;
}
.category-card:hover {
  background: #f0f3ff;
  transform: translateX(3px);
}
:root {
  --cat-color: #6366f1; /* 提供一个默认值，让静态检查满意 */
}
.category-card.active {
  background: #eef2ff;
  border-left-color: var(--cat-color, #6366f1);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}
.cat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.cat-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.cat-count {
  font-size: 12px;
  color: #909399;
}

/* ========================= 中栏：法律目录 ========================= */
.mid-panel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #eef0f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.3s ease;
  z-index: 9;
}

.law-list-view,
.toc-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.law-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}
.law-list::-webkit-scrollbar {
  width: 4px;
}
.law-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.law-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 3px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 14px;
  color: #303133;
}
.law-item:hover {
  background: #f0f3ff;
}
.law-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.law-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.law-arrow {
  color: #c0c4cc;
  flex-shrink: 0;
  font-size: 12px;
}

/* 章节目录树 */
.toc-law-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.toc-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.toc-tree::-webkit-scrollbar {
  width: 4px;
}
.toc-tree::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.toc-chapter {
  margin-bottom: 2px;
}
.toc-chapter-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 0;
}
.toc-chapter-title:hover {
  background: #f5f6fa;
}
.toc-count {
  margin-left: auto;
  font-size: 11px;
  color: #909399;
  font-weight: 400;
}
.toc-chapter-body {
  padding-left: 12px;
}
.toc-section {
  margin: 2px 0;
}
.toc-section-title {
  padding: 8px 16px 6px 28px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}
.toc-article {
  padding: 7px 16px 7px 28px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  border-radius: 6px;
  margin: 1px 8px;
  transition: all 0.15s;
}
.toc-article:hover {
  background: #eef2ff;
  color: #6366f1;
}
.toc-article.active {
  background: #eef2ff;
  color: #6366f1;
  font-weight: 600;
}

/* ========================= 右栏：阅读区 ========================= */
.right-panel {
  flex: 1;
  background: #fafbfc;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 欢迎页 */
.reader-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome-box {
  text-align: center;
  color: #909399;
}
.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.welcome-box h3 {
  font-size: 20px;
  color: #606266;
  margin: 0 0 8px;
}
.welcome-box p {
  margin: 4px 0;
  font-size: 14px;
}
.welcome-hint {
  color: #c0c4cc;
  font-size: 13px !important;
}

/* 阅读器 */
.reader-view,
.search-results-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.reader-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.reader-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #eef0f5;
  flex-shrink: 0;
}
.reader-law-name {
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 320px;
}
.reader-toolbar-actions {
  display: flex;
  gap: 4px;
}
.reader-article {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
}
.reader-article::-webkit-scrollbar {
  width: 6px;
}
.reader-article::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}
.reader-article-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #eef0f5;
  flex-wrap: wrap;
}
.reader-article-num {
  font-size: 18px;
  font-weight: 700;
  color: #6366f1;
  background: #eef2ff;
  padding: 4px 12px;
  border-radius: 6px;
}
.reader-article-chapter {
  font-size: 13px;
  color: #909399;
}
.reader-article-section {
  font-size: 13px;
  color: #c0c4cc;
}
.reader-article-body {
  font-size: 16px;
  line-height: 2.1;
  color: #303133;
  text-align: justify;
}

/* ========================= 搜索结果 ========================= */
.search-summary {
  padding: 12px 20px;
  font-size: 13px;
  color: #606266;
  background: #fff;
  border-bottom: 1px solid #eef0f5;
  flex-shrink: 0;
}
.search-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
}
.search-list::-webkit-scrollbar {
  width: 6px;
}
.search-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}
.search-card {
  background: #fff;
  border: 1px solid #eef0f5;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.search-card:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.08);
  transform: translateY(-1px);
}
.search-card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.search-card-tag {
  font-size: 11px;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.search-card-law {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.search-card-article {
  font-size: 12px;
  color: #6366f1;
  font-weight: 500;
}
.search-card-content {
  font-size: 13px;
  line-height: 1.8;
  color: #555;
}
.search-card-content :deep(mark) {
  background: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}
.search-pagination {
  display: flex;
  justify-content: center;
  padding: 12px;
  background: #fff;
  border-top: 1px solid #eef0f5;
  flex-shrink: 0;
}

/* ========================= 移动端适配 ========================= */
.panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 8;
}
.mobile-toolbar {
  display: none;
}

@media (max-width: 1200px) {
  .left-panel {
    width: 230px;
  }
  .mid-panel {
    width: 240px;
  }
  .reader-article {
    padding: 24px 28px;
  }
}

@media (max-width: 992px) {
  .left-panel {
    width: 220px;
  }
  .mid-panel {
    width: 220px;
  }
  .header-stats {
    display: none;
  }
}

@media (max-width: 768px) {
  .library-layout {
    height: calc(100vh - 120px);
    border-radius: 0;
  }
  .library-header {
    padding: 10px 12px;
    gap: 8px;
  }
  .header-title {
    font-size: 16px;
  }
  .header-stats {
    display: none;
  }
  .header-search {
    min-width: 0;
    flex: 1;
  }
  .header-search .el-button {
    padding: 0 12px;
    font-size: 13px;
  }

  .left-panel,
  .mid-panel {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    width: 280px;
    max-width: 85vw;
    z-index: 20;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
    transform: translateX(-100%);
  }
  .left-panel:not(.panel-hidden),
  .mid-panel:not(.panel-hidden) {
    transform: translateX(0);
  }
  .panel-hidden {
    transform: translateX(-100%);
  }

  .right-panel {
    width: 100%;
  }
  .reader-article {
    padding: 16px;
    font-size: 15px;
  }
  .reader-article-body {
    font-size: 15px;
    line-height: 1.9;
  }
  .search-list {
    padding: 8px;
  }
  .search-card {
    padding: 12px;
  }

  .mobile-toolbar {
    display: flex;
    justify-content: space-around;
    padding: 8px 12px;
    background: #fff;
    border-top: 1px solid #eef0f5;
    flex-shrink: 0;
    gap: 8px;
  }
  .mobile-toolbar .el-button {
    flex: 1;
  }
}
</style>
