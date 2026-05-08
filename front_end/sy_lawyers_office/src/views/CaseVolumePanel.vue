<template>
  <div class="case-volume-panel" v-loading="globalLoading">
    <div class="panel-layout">
      <div class="volume-sidebar">
        <div class="sidebar-header">
          <span>卷宗目录</span>
          <el-button
            v-if="canEdit"
            type="primary"
            link
            icon="Plus"
            size="small"
            @click="openCreateVolumeDialog"
            >新建</el-button
          >
        </div>

        <el-scrollbar>
          <div
            v-for="vol in volumes"
            :key="vol.id"
            class="volume-item"
            :class="{ active: currentVolumeId === vol.id }"
            @click="selectVolume(vol)"
          >
            <div class="vol-icon">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="vol-info">
              <div class="vol-name" :title="vol.name">{{ vol.name }}</div>

              <div v-if="vol.physical_location" class="vol-location" :title="vol.physical_location">
                <el-icon><Location /></el-icon> {{ vol.physical_location }}
              </div>

              <div class="vol-meta">
                <el-tag size="small" type="info" effect="plain"
                  >{{ vol.files ? vol.files.length : 0 }} 份</el-tag
                >
                <el-tag
                  v-if="vol.merged_file_path"
                  size="small"
                  type="success"
                  effect="dark"
                  style="transform: scale(0.8)"
                  >已合并</el-tag
                >
              </div>
            </div>
            <div class="vol-actions" v-if="canEdit">
              <el-dropdown trigger="click" @command="(cmd) => handleVolumeCommand(cmd, vol)">
                <el-icon class="action-icon"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit_info">编辑信息</el-dropdown-item>
                    <el-dropdown-item command="delete" style="color: #f56c6c"
                      >删除卷宗</el-dropdown-item
                    >
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <el-empty v-if="volumes.length === 0" description="暂无卷宗册" :image-size="60">
            <el-button v-if="canEdit" type="primary" size="small" @click="openCreateVolumeDialog"
              >立即创建</el-button
            >
          </el-empty>
        </el-scrollbar>
      </div>

      <div class="file-content">
        <div v-if="currentVolumeId" class="content-wrapper">
          <div class="toolbar">
            <div class="toolbar-left">
              <h3 class="current-title">{{ currentVolume?.name }}</h3>

              <el-tag
                v-if="currentVolume?.physical_location"
                type="info"
                effect="plain"
                size="small"
                style="margin-right: 10px"
              >
                <el-icon style="vertical-align: middle; margin-right: 4px"><Location /></el-icon>
                存放于: {{ currentVolume.physical_location }}
              </el-tag>

              <el-tag type="warning" effect="plain" v-if="!canEdit">仅查看模式</el-tag>

              <div class="search-bar-compact">
                <el-input
                  v-model="metaKeyword"
                  placeholder="检索文件名/摘要/标签..."
                  size="small"
                  clearable
                  class="file-search-input meta-search-input"
                >
                  <template #prefix>
                    <el-icon><Document /></el-icon>
                  </template>
                </el-input>
                <el-input
                  v-model="ocrKeyword"
                  placeholder="检索OCR全文..."
                  size="small"
                  clearable
                  class="file-search-input ocr-search-input"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-button type="primary" link size="small" @click="clearSearch">清空</el-button>
              </div>

              <el-radio-group v-model="viewMode" size="small" class="view-mode-group">
                <el-radio-button label="list">列表排序</el-radio-button>
                <el-radio-button label="group">按分类分组</el-radio-button>
              </el-radio-group>

              <div v-if="viewMode === 'list' && canEdit" class="drag-tip">
                <el-icon><Rank /></el-icon> 按住图标拖拽排序
              </div>
            </div>
            <div class="toolbar-right">
              <el-tooltip content="刷新当前列表数据" placement="top">
                <el-button icon="Refresh" @click="refreshCurrentVolume" class="tool-btn"
                  >刷新</el-button
                >
              </el-tooltip>

              <template v-if="canEdit">
                <el-button
                  type="primary"
                  :icon="Upload"
                  @click="showUploadDialog = true"
                  class="tool-btn"
                  >上传文件</el-button
                >
                <el-button
                  type="success"
                  :icon="Connection"
                  class="tool-btn"
                  :loading="merging"
                  @click="handleMergeVolume"
                  >生成电子卷宗</el-button
                >
              </template>

              <el-tooltip content="在线预览已合并的电子卷宗" placement="top">
                <el-button
                  v-if="currentVolume?.merged_file_path"
                  type="primary"
                  :icon="View"
                  plain
                  class="tool-btn"
                  @click="previewMergedFile"
                  >预览全卷</el-button
                >
              </el-tooltip>

              <el-tooltip content="下载包含目录和所有文件的完整PDF" placement="top">
                <el-button
                  v-if="currentVolume?.merged_file_path"
                  type="warning"
                  :icon="Download"
                  plain
                  class="tool-btn"
                  @click="downloadMergedFile"
                  >下载全卷PDF</el-button
                >
              </el-tooltip>
            </div>
          </div>

          <el-skeleton :loading="fileSearchLoading" animated :rows="10">
            <template #default>
              <el-table
                v-if="viewMode === 'list'"
                ref="dragTableRef"
                :data="fileList"
                row-key="id"
                stripe
                style="width: 100%; margin-top: 10px"
                height="calc(100vh - 300px)"
              >
                <el-table-column width="40" align="center" v-if="canEdit">
                  <template #default>
                    <el-icon
                      class="drag-handle"
                      style="cursor: move; color: #909399; font-size: 16px"
                      ><Rank
                    /></el-icon>
                  </template>
                </el-table-column>

                <el-table-column label="序号" type="index" width="60" align="center" />

                <el-table-column label="文件名" min-width="200">
                  <template #default="{ row }">
                    <div class="file-name-cell">
                      <el-icon v-if="isPdf(row.file_type)" style="color: #f56c6c"
                        ><Document
                      /></el-icon>
                      <el-icon v-else-if="isImage(row.file_type)" style="color: #409eff"
                        ><Picture
                      /></el-icon>
                      <el-icon v-else style="color: #909399"><DocumentCopy /></el-icon>
                      <span
                        class="fname"
                        @click="handlePreview(row)"
                        v-html="DOMPurify.sanitize(row.file_name)"
                      ></span>
                      <el-tag
                        v-if="row.ocr_content"
                        type="success"
                        size="small"
                        effect="plain"
                        round
                        style="transform: scale(0.8); margin-left: 5px"
                        >OCR</el-tag
                      >
                    </div>
                    <div v-if="row.ocr_content && (metaKeyword || ocrKeyword)" class="ocr-snippet">
                      <el-icon><Search /></el-icon>
                      <span v-html="DOMPurify.sanitize(row.ocr_content)"></span>
                    </div>
                    <div v-if="row.summary" class="row-summary">{{ row.summary }}</div>
                  </template>
                </el-table-column>

                <el-table-column prop="category" label="分类" width="120" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" effect="light">{{ row.category || '未分类' }}</el-tag>
                  </template>
                </el-table-column>

                <el-table-column label="标签" min-width="120">
                  <template #default="{ row }">
                    <div class="tags-cell">
                      <el-tag v-for="t in row.tags || []" :key="t" size="small" type="info">{{
                        t
                      }}</el-tag>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="sort_order" label="排序权重" width="80" align="center" />

                <el-table-column label="全卷页码" width="100" align="center">
                  <template #default="{ row }">
                    <span v-if="row.page_start" class="page-badge">
                      P{{ row.page_start }} - P{{ row.page_end }}
                    </span>
                    <span v-else style="color: #ccc">-</span>
                  </template>
                </el-table-column>

                <el-table-column prop="uploader_name" label="上传人" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" type="info" effect="plain">{{
                      row.uploader_name || '未知'
                    }}</el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="created_at" label="上传时间" width="160" align="center">
                  <template #default="{ row }">
                    {{ formatTime(row.created_at) }}
                  </template>
                </el-table-column>

                <el-table-column
                  label="操作"
                  :width="isMobile ? 200 : 220"
                  align="center"
                  :fixed="isMobile ? false : 'right'"
                >
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="handlePreview(row)"
                      >预览</el-button
                    >
                    <el-button link type="primary" size="small" @click="handleDownload(row)"
                      >下载</el-button
                    >
                    <el-button
                      v-if="canEdit"
                      link
                      type="warning"
                      size="small"
                      @click="openEditDialog(row)"
                      >编辑</el-button
                    >
                    <el-button
                      v-if="canEdit"
                      link
                      type="danger"
                      size="small"
                      @click="handleDeleteFile(row)"
                      >删除</el-button
                    >
                  </template>
                </el-table-column>
              </el-table>

              <el-scrollbar
                v-else
                height="calc(100vh - 300px)"
                class="grouped-view"
                style="margin-top: 10px"
              >
                <el-collapse v-model="activeNames">
                  <el-collapse-item v-for="(files, cat) in groupedFiles" :key="cat" :name="cat">
                    <template #title>
                      <div class="group-header">
                        <el-icon><FolderOpened /></el-icon>
                        <span class="cat-name">{{ cat }}</span>
                        <el-tag size="small" round>{{ files.length }} 份</el-tag>
                      </div>
                    </template>

                    <el-table :data="files" :show-header="true" size="small" border>
                      <el-table-column label="排序" prop="sort_order" width="60" align="center" />
                      <el-table-column label="文件名" min-width="200">
                        <template #default="{ row }">
                          <div class="file-name-cell">
                            <span
                              class="fname"
                              @click="handlePreview(row)"
                              v-html="DOMPurify.sanitize(row.file_name)"
                            ></span>
                            <el-tag
                              v-if="row.ocr_content"
                              type="success"
                              size="small"
                              effect="plain"
                              round
                              style="transform: scale(0.8)"
                              >OCR</el-tag
                            >
                          </div>
                          <div
                            v-if="row.ocr_content && (metaKeyword || ocrKeyword)"
                            class="ocr-snippet"
                            style="
                              font-size: 12px;
                              color: #666;
                              margin-top: 4px;
                              padding: 4px 8px;
                              background: #f9f9f9;
                              border-radius: 4px;
                            "
                          >
                            <el-icon><Search /></el-icon>
                            <span v-html="DOMPurify.sanitize(row.ocr_content)"></span>
                          </div>
                          <div v-if="row.summary" class="row-summary">{{ row.summary }}</div>
                        </template>
                      </el-table-column>
                      <el-table-column label="标签" min-width="100">
                        <template #default="{ row }">
                          <el-tag
                            v-for="t in row.tags || []"
                            :key="t"
                            size="small"
                            style="margin-right: 4px"
                            >{{ t }}</el-tag
                          >
                        </template>
                      </el-table-column>
                      <el-table-column label="全卷页码" width="100" align="center">
                        <template #default="{ row }">
                          <span v-if="row.page_start" class="page-badge"
                            >P{{ row.page_start }}-{{ row.page_end }}</span
                          >
                        </template>
                      </el-table-column>

                      <el-table-column
                        prop="uploader_name"
                        label="上传人"
                        width="100"
                        align="center"
                      >
                        <template #default="{ row }">
                          <el-tag size="small" type="info" effect="plain">{{
                            row.uploader_name || '未知'
                          }}</el-tag>
                        </template>
                      </el-table-column>

                      <el-table-column
                        prop="created_at"
                        label="上传时间"
                        width="150"
                        align="center"
                      >
                        <template #default="{ row }">
                          {{ formatTime(row.created_at) }}
                        </template>
                      </el-table-column>

                      <el-table-column
                        label="操作"
                        width="180"
                        align="center"
                        :fixed="isMobile ? false : 'right'"
                      >
                        <template #default="{ row }">
                          <el-button link type="primary" size="small" @click="handlePreview(row)"
                            >预览</el-button
                          >
                          <el-button link type="primary" size="small" @click="handleDownload(row)"
                            >下载</el-button
                          >
                          <el-button
                            v-if="canEdit"
                            link
                            type="warning"
                            size="small"
                            @click="openEditDialog(row)"
                            >编辑</el-button
                          >
                          <el-button
                            v-if="canEdit"
                            link
                            type="danger"
                            size="small"
                            @click="handleDeleteFile(row)"
                            >删除</el-button
                          >
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-collapse-item>
                </el-collapse>

                <el-empty v-if="Object.keys(groupedFiles).length === 0" description="暂无文件" />
              </el-scrollbar>
            </template>
          </el-skeleton>
        </div>

        <el-empty v-else description="请选择左侧卷宗册查看详情" />
      </div>
    </div>

    <BatchUploadDialog
      v-if="currentVolumeId"
      v-model:visible="showUploadDialog"
      :volume-id="currentVolumeId"
      :base-sort-order="maxSortOrder"
      @success="refreshCurrentVolume"
    />

    <el-dialog
      v-model="volDialogVisible"
      :title="volDialogTitle"
      :width="isMobile ? '95%' : '450px'"
      destroy-on-close
      append-to-body
    >
      <el-form
        :model="volForm"
        :label-width="isMobile ? 'auto' : '90px'"
        :label-position="isMobile ? 'top' : 'right'"
        @submit.prevent
      >
        <el-form-item label="卷宗名称" required>
          <el-input
            v-model="volForm.name"
            placeholder="如正卷、副卷、卷一、卷二"
            @keyup.enter="submitVolumeForm"
          />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input
            v-model="volForm.physical_location"
            placeholder="纸质卷宗存放位置"
            @keyup.enter="submitVolumeForm"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="volDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitVolumeForm" :loading="volFormLoading"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑文件信息"
      :width="isMobile ? '95%' : '500px'"
      destroy-on-close
      append-to-body
    >
      <el-form
        :model="editForm"
        :label-width="isMobile ? 'auto' : '80px'"
        :label-position="isMobile ? 'top' : 'right'"
      >
        <el-form-item label="文件名">
          <el-input v-model="editForm.file_name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option v-for="opt in categoryOptions" :key="opt" :label="opt" :value="opt" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number
            v-model="editForm.sort_order"
            :min="0"
            controls-position="right"
            style="width: 100%"
          />
          <div class="form-tip">数字越小越靠前，用于合并PDF时的顺序</div>
        </el-form-item>
        <el-form-item label="标签">
          <div class="tag-editor">
            <el-tag
              v-for="(tag, i) in editForm.tags"
              :key="i"
              closable
              @close="editForm.tags.splice(i, 1)"
              >{{ tag }}</el-tag
            >
            <el-input
              v-model="tempEditTag"
              size="small"
              style="width: 80px; margin-left: 5px"
              placeholder="+ Tag"
              @keyup.enter="addEditTag"
              @blur="addEditTag"
            />
          </div>
        </el-form-item>
        <el-form-item label="摘要备注">
          <el-input v-model="editForm.summary" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="previewVisible"
      title="文件预览"
      :width="isMobile ? '100%' : '80%'"
      top="5vh"
      destroy-on-close
    >
      <div
        class="preview-box"
        v-loading="previewLoading"
        :element-loading-text="previewLoadingText"
      >
        <iframe
          v-if="previewUrl && previewType === 'pdf'"
          :src="previewUrl"
          class="preview-frame"
        ></iframe>
        <img
          v-else-if="previewUrl && previewType === 'image'"
          :src="previewUrl"
          class="preview-img"
        />
        <div v-else class="preview-error">无法预览此文件，请下载查看</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch, inject } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  Document,
  DocumentCopy,
  Folder,
  FolderOpened,
  MoreFilled,
  Picture,
  Rank,
  Location,
  Upload,
  Download,
  Connection,
  View,
  Search,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import BatchUploadDialog from '@/components/BatchUploadDialog.vue'
import Sortable from 'sortablejs'
import { debounce } from 'lodash-es'
import DOMPurify from 'dompurify'

// 注入父组件传下来的响应式状态
const isMobile = inject('isMobile', ref(false))

const props = defineProps({
  caseId: {
    type: [Number, String],
    required: true,
  },
})

// State
const globalLoading = ref(false)
const volumes = ref([])
const currentVolumeId = ref(null)
const currentVolume = ref(null)
const fileList = ref([])

// Permission State
const canEdit = ref(false)

// UI State
const showUploadDialog = ref(false)
const merging = ref(false)
const viewMode = ref('list')
const activeNames = ref([])

// 文件搜索状态 — 双关键词
const metaKeyword = ref('')
const ocrKeyword = ref('')
const fileSearchLoading = ref(false)

// 轮询计时器引用
let mergePollingTimer = null

// --- 卷宗 新建/编辑 State ---
const volDialogVisible = ref(false)
const volDialogTitle = ref('')
const volFormLoading = ref(false)
const volForm = ref({
  id: null,
  name: '',
  physical_location: '',
})

// File Edit State
const editDialogVisible = ref(false)
const submitting = ref(false)
const tempEditTag = ref('')
const editForm = ref({
  id: null,
  file_name: '',
  category: '',
  sort_order: 0,
  tags: [],
  summary: '',
})
const categoryOptions = ['证据材料', '法律文书', '起诉/答辩状', '笔录资料', '备考表', '其他材料']

// Preview State
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('pdf')
const previewLoading = ref(false)
// 动态加载文字
const previewLoadingText = ref('加载中...')

// Drag Sort State
const dragTableRef = ref(null)
let sortableInstance = null

// Init
onMounted(async () => {
  await fetchPermissions()
  await loadVolumes()
})

// 组件销毁前清理可能存在的轮询定时器，防止内存泄漏
onBeforeUnmount(() => {
  if (mergePollingTimer) clearInterval(mergePollingTimer)
})

// 监听 caseId 变化
watch(
  () => props.caseId,
  () => {
    currentVolumeId.value = null
    fileList.value = []
    loadVolumes()
  },
)

const maxSortOrder = computed(() => {
  if (!fileList.value || fileList.value.length === 0) return 0
  return fileList.value.reduce(
    (acc, cur) => ((cur.sort_order || 0) > acc ? cur.sort_order : acc),
    0,
  )
})
const groupedFiles = computed(() => {
  const groups = {}
  categoryOptions.forEach((c) => (groups[c] = []))
  groups['其他'] = []
  fileList.value.forEach((file) => {
    const cat = file.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(file)
  })
  Object.keys(groups).forEach((k) => {
    if (groups[k].length === 0) delete groups[k]
    else groups[k].sort((a, b) => a.sort_order - b.sort_order)
  })
  return groups
})

watch(groupedFiles, (val) => {
  activeNames.value = Object.keys(val)
})

const initSortable = () => {
  if (!dragTableRef.value || !canEdit.value) return
  const el = dragTableRef.value.$el.querySelector('.el-table__body-wrapper tbody')
  if (!el) return
  if (sortableInstance) sortableInstance.destroy()
  sortableInstance = Sortable.create(el, {
    handle: '.drag-handle',
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: async ({ newIndex, oldIndex }) => {
      if (newIndex === oldIndex) return
      const targetRow = fileList.value.splice(oldIndex, 1)[0]
      fileList.value.splice(newIndex, 0, targetRow)
      const updates = fileList.value.map((item, index) => ({
        id: item.id,
        sort_order: (index + 1) * 10,
      }))
      try {
        await request.post('/electronic_volumes/files/batch_sort', updates)
        ElMessage.success('排序更新成功')
        fileList.value.forEach((item, index) => {
          item.sort_order = (index + 1) * 10
        })
      } catch (err) {
        console.error(err)
        ElMessage.error('排序保存失败')
        await refreshCurrentVolume()
      }
    },
  })
}

watch(
  [() => viewMode.value, () => fileList.value],
  async ([mode, list]) => {
    if (mode === 'list' && list.length > 0) {
      await nextTick()
      initSortable()
    }
  },
  { flush: 'post' },
)

watch(currentVolumeId, () => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
})

// --- 权限逻辑 ---
const fetchPermissions = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const caseRes = await request.get(`/cases/${props.caseId}`)
    const caseInfo = caseRes.data
    const userRes = await request.get(`/user/profile/info?user_id=${userId}`)
    const userInfo = userRes.data
    const isSuper =
      userInfo.role === 'owner' || (userInfo.permissions && userInfo.permissions.volume_manage)
    const lawyerFields = [
      caseInfo.main_lawyer,
      caseInfo.assistant_lawyer,
      caseInfo.execution_lawyer,
      caseInfo.execution_assistant,
    ]
    const relatedLawyerIds = lawyerFields
      .map((lawyer) => lawyer?.id)
      .filter((id) => id !== undefined && id !== null)
      .map(String)
    const isRelated = relatedLawyerIds.includes(String(userId))
    const isApproved = caseInfo.review_status === '已审核'
    canEdit.value = (isSuper || isRelated) && isApproved
  } catch (err) {
    console.error('权限获取失败', err)
    canEdit.value = false
  }
}

// --- 卷宗册逻辑 ---
const loadVolumes = async () => {
  if (!props.caseId) return
  globalLoading.value = true
  try {
    const res = await request.get(`/electronic_volumes/case/${props.caseId}`)
    volumes.value = res.data
    if (!currentVolumeId.value && volumes.value.length > 0) {
      selectVolume(volumes.value[0])
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('加载卷宗列表失败')
  } finally {
    globalLoading.value = false
  }
}
const selectVolume = (vol) => {
  currentVolumeId.value = vol.id
  currentVolume.value = vol
  fileList.value = vol.files || []
  fileList.value.sort((a, b) => a.sort_order - b.sort_order)
  // 切换卷宗时清空搜索关键词
  metaKeyword.value = ''
  ocrKeyword.value = ''
}
const refreshCurrentVolume = async () => {
  if (!currentVolumeId.value) return
  try {
    const res = await request.get(`/electronic_volumes/${currentVolumeId.value}`)
    currentVolume.value = res.data
    fileList.value = res.data.files || []
    fileList.value.sort((a, b) => a.sort_order - b.sort_order)
    const idx = volumes.value.findIndex((v) => v.id === currentVolumeId.value)
    if (idx !== -1) {
      volumes.value[idx] = res.data
    }
  } catch (err) {
    console.error(err)
  }
}

// 文件搜索：调用后端接口搜索当前卷宗内的文件（支持双关键词组合）
const handleFileSearch = async () => {
  if (!currentVolumeId.value) return
  fileSearchLoading.value = true
  try {
    const metaKw = metaKeyword.value.trim()
    const ocrKw = ocrKeyword.value.trim()
    if (!metaKw && !ocrKw) {
      // 关键词均为空，恢复完整列表
      await refreshCurrentVolume()
      return
    }
    const res = await request.get(`/electronic_volumes/${currentVolumeId.value}/files`, {
      params: {
        meta_keyword: metaKw || undefined,
        ocr_keyword: ocrKw || undefined,
      },
    })
    fileList.value = res.data.items || []
    fileList.value.sort((a, b) => a.sort_order - b.sort_order)
  } catch (err) {
    console.error('文件搜索失败', err)
    ElMessage.error('文件搜索失败')
  } finally {
    fileSearchLoading.value = false
  }
}

// 清空双搜索框
const clearSearch = () => {
  metaKeyword.value = ''
  ocrKeyword.value = ''
}

// 防抖即时搜索：同时监听两个关键词，400ms 防抖自动触发
const debouncedFileSearch = debounce(() => {
  handleFileSearch()
}, 400)

watch([metaKeyword, ocrKeyword], () => {
  debouncedFileSearch()
})

// --- 卷宗增改逻辑 ---
const openCreateVolumeDialog = () => {
  volForm.value = { id: null, name: '', physical_location: '' }
  volDialogTitle.value = '新建卷宗'
  volDialogVisible.value = true
}
const openEditVolumeDialog = (vol) => {
  volForm.value = { id: vol.id, name: vol.name, physical_location: vol.physical_location }
  volDialogTitle.value = '编辑卷宗信息'
  volDialogVisible.value = true
}
const submitVolumeForm = async () => {
  if (!volForm.value.name) {
    ElMessage.warning('请输入卷宗名称')
    return
  }

  volFormLoading.value = true
  try {
    if (volForm.value.id) {
      // 更新
      await request.put(`/electronic_volumes/${volForm.value.id}`, {
        name: volForm.value.name,
        physical_location: volForm.value.physical_location,
      })
      ElMessage.success('更新成功')
    } else {
      // 新建
      await request.post('/electronic_volumes/', {
        case_id: props.caseId,
        name: volForm.value.name,
        physical_location: volForm.value.physical_location,
        sort_order: 0,
      })
      ElMessage.success('创建成功')
    }
    volDialogVisible.value = false
    await loadVolumes()

    // 如果是编辑当前选中的，更新显示
    if (volForm.value.id && currentVolumeId.value === volForm.value.id && currentVolume.value) {
      currentVolume.value.name = volForm.value.name
      currentVolume.value.physical_location = volForm.value.physical_location
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('操作失败')
  } finally {
    volFormLoading.value = false
  }
}
const handleVolumeCommand = async (cmd, vol) => {
  if (cmd === 'edit_info') openEditVolumeDialog(vol)
  else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除该卷宗及其所有文件吗？此操作不可恢复！', '警告', {
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      })
      await request.delete(`/electronic_volumes/${vol.id}`)
      ElMessage.success('删除成功')
      currentVolumeId.value = null
      currentVolume.value = null
      fileList.value = []
      await loadVolumes()
    } catch (e) {
      console.error(e)
    }
  }
}

// --- 文件操作逻辑 ---

const openEditDialog = (row) => {
  editForm.value = JSON.parse(JSON.stringify(row))
  if (!editForm.value.tags) editForm.value.tags = []
  tempEditTag.value = ''
  editDialogVisible.value = true
}

const addEditTag = () => {
  const val = tempEditTag.value.trim()
  if (val && !editForm.value.tags.includes(val)) {
    editForm.value.tags.push(val)
  }
  tempEditTag.value = ''
}

const submitEdit = async () => {
  submitting.value = true
  try {
    await request.put(`/electronic_volumes/files/${editForm.value.id}`, {
      file_name: editForm.value.file_name,
      category: editForm.value.category,
      sort_order: editForm.value.sort_order,
      tags: editForm.value.tags,
      summary: editForm.value.summary,
    })
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    await refreshCurrentVolume()
  } catch (e) {
    console.error(e)
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
  }
}

const handleDeleteFile = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该文件吗？', '提示', { type: 'warning' })
    await request.delete(`/electronic_volumes/files/${row.id}`)
    ElMessage.success('删除成功')
    await refreshCurrentVolume()
  } catch (e) {
    console.error(e)
    ElMessage.error('删除失败')
  }
}

// ---------------------- 核心改动：下载带进度提示 ----------------------
const downloadBlob = async (url, filename) => {
  let loadingInstance = null
  try {
    // 启动全局加载遮罩层
    loadingInstance = ElLoading.service({
      lock: true,
      text: '正在请求下载，请耐心等待...',
      background: 'rgba(0, 0, 0, 0.7)',
    })

    const res = await request.get(url, {
      responseType: 'blob',
      timeout: 0,
      // 监听下载进度
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          loadingInstance.setText(`正在下载文件: ${percentCompleted}%`)
        } else {
          // 如果后端没返回 total 大小，显示已下载的 MB 数
          const mb = (progressEvent.loaded / 1024 / 1024).toFixed(2)
          loadingInstance.setText(`正在下载文件: ${mb} MB`)
        }
      },
    })

    const blob = new Blob([res.data], {
      type: res.headers['content-type'] || 'application/octet-stream',
    })
    const link = document.createElement('a')
    const href = window.URL.createObjectURL(blob)
    link.href = href
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(href)
    ElMessage.success('下载完成！')
  } catch (err) {
    console.error('下载失败', err)
    ElMessage.error('下载失败，请检查网络或权限')
  } finally {
    // 确保无论成功失败都关闭遮罩层
    if (loadingInstance) {
      loadingInstance.close()
    }
  }
}

const handleDownload = async (row) => {
  const url = `/electronic_volumes/files/${row.id}/download`
  await downloadBlob(url, row.file_name)
}

// ---------------------- 合并卷宗支持后台异步 ----------------------
const handleMergeVolume = async () => {
  if (!fileList.value.length) return ElMessage.warning('卷宗为空，无法合并')
  merging.value = true
  // 锁定触发时的卷宗ID
  const targetVolumeId = currentVolumeId.value
  try {
    ElMessage.info('合并任务已提交，系统正在后台处理，请耐心等待...')

    // 覆盖超时时间，提交任务到后台
    await request.post(`/electronic_volumes/${targetVolumeId}/merge`, null, {
      timeout: 120000,
    })

    // 开启轮询查询合并状态
    startPollingMergeStatus(targetVolumeId)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '合并任务提交失败')
    merging.value = false
  }
}

// 轮询查询合并状态
const startPollingMergeStatus = (volId) => {
  if (mergePollingTimer) clearInterval(mergePollingTimer)
  mergePollingTimer = setInterval(async () => {
    try {
      // 查询该卷宗的最新状态
      const res = await request.get(`/electronic_volumes/${volId}`)

      // 检查后端是否已生成合并文件
      if (res.data.merged_file_path) {
        // 合并完成，停止轮询
        clearInterval(mergePollingTimer)
        mergePollingTimer = null
        ElMessage.success('电子卷宗生成成功！')

        // 只有当用户还在看触发合并的那个卷宗时，才去直接更新视图的 state
        if (currentVolumeId.value === volId) {
          merging.value = false
          currentVolume.value = res.data
        }

        // 刷新左侧卷宗列表以同步“已合并”标签状态
        await loadVolumes()
      }
    } catch (e) {
      console.error('轮询合并状态失败', e)
    }
  }, 3000) // 每 3 秒查一次
}
// ----------------------------------------------------------------------------

// ---------------------- 核心改动：合并文件预览带进度提示 ----------------------
const previewMergedFile = async () => {
  if (!currentVolume.value?.merged_file_path) return
  previewLoading.value = true
  previewVisible.value = true
  previewType.value = 'pdf'
  // 重置加载文本
  previewLoadingText.value = '正在请求全卷预览，请稍候...'
  try {
    const res = await request.get(`/electronic_volumes/${currentVolumeId.value}/preview_merged`, {
      responseType: 'blob',
      timeout: 0,
      // 监听下载进度
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          previewLoadingText.value = `正在加载全卷预览: ${percentCompleted}%`
        } else {
          const mb = (progressEvent.loaded / 1024 / 1024).toFixed(2)
          previewLoadingText.value = `正在加载全卷预览: ${mb} MB`
        }
      },
    })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    previewUrl.value = window.URL.createObjectURL(blob)
  } catch (err) {
    console.error(err)
    ElMessage.error('预览加载失败，文件可能不存在或网络超时')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}
// ----------------------------------------------------------------------------

const downloadMergedFile = async () => {
  if (!currentVolume.value?.merged_file_path) return
  await downloadBlob(
    `/electronic_volumes/${currentVolumeId.value}/download_merged`,
    `${currentVolume.value.name}_全卷.pdf`,
  )
}

// ---------------------- 核心改动：单文件预览带进度提示 ----------------------
const handlePreview = async (row) => {
  previewLoading.value = true
  previewVisible.value = true
  // 重置单文件的提示信息
  previewLoadingText.value = '正在加载预览文件，如果为Word文档可能会耗时稍长...'

  try {
    const res = await request.get(`/electronic_volumes/files/${row.id}/preview`, {
      responseType: 'blob',
      timeout: 0,
      // 单文件（比如大图片或大PDF）也监听进度
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          previewLoadingText.value = `正在下载预览文件: ${percentCompleted}%`
        } else {
          const mb = (progressEvent.loaded / 1024 / 1024).toFixed(2)
          previewLoadingText.value = `正在下载预览文件: ${mb} MB`
        }
      },
    })
    const blob = new Blob([res.data], { type: res.headers['content-type'] })
    previewUrl.value = window.URL.createObjectURL(blob)
    if (res.headers['content-type'].includes('image')) previewType.value = 'image'
    else previewType.value = 'pdf'
  } catch (err) {
    console.error(err)
    ElMessage.error('预览失败或文件正在转换中')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}
// ----------------------------------------------------------------------------

const isPdf = (type) => type?.includes('pdf')
const isImage = (type) => type?.includes('image')
const formatTime = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleString()
}
</script>

<style scoped>
.case-volume-panel {
  height: 100%;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.panel-layout {
  display: flex;
  height: 100%;
}
/* Sidebar Styles */
.volume-sidebar {
  width: 240px;
  border-right: 1px solid #e4e7ed;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  height: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
  border-bottom: 1px solid #ebeef5;
  font-weight: bold;
  color: #303133;
}
.volume-item {
  display: flex;
  align-items: flex-start; /* 调整对齐 */
  padding: 12px 15px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f2f5;
}
.volume-item:hover {
  background-color: #ecf5ff;
}
.volume-item.active {
  background-color: #d9ecff;
  border-right: 3px solid #409eff;
}
.vol-icon {
  font-size: 20px;
  color: #e6a23c;
  margin-right: 10px;
  margin-top: 2px; /* 图标微调 */
}
.vol-info {
  flex: 1;
  overflow: hidden;
}
.vol-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 位置信息样式 */
.vol-location {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vol-meta {
  display: flex;
  gap: 5px;
}
.vol-actions {
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: 5px;
}
.volume-item:hover .vol-actions {
  opacity: 1;
}

/* Content Styles */
.file-content {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.content-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 修改点：允许工具栏换行并增加上下间距 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

/* 修改点：允许左右两侧内部元素也响应式换行 */
.toolbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

/* 修改点：移除原本为了电脑端设置的 margin，交由 flex gap 控制间距 */
.tool-btn {
  margin-left: 0 !important;
}

.current-title {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
.view-mode-group {
  margin-left: 20px;
}
.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.fname {
  cursor: pointer;
  color: #606266;
  font-weight: 500;
}
.fname:hover {
  color: #409eff;
  text-decoration: underline;
}
.page-badge {
  background: #f0f9eb;
  color: #67c23a;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

/* Preview Styles */
.preview-box {
  width: 100%;
  height: 70vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f2f2f2;
}
.preview-frame {
  width: 100%;
  height: 100%;
  border: none;
}
.preview-img {
  max-width: 100%;
  max-height: 100%;
}

.row-summary {
  font-size: 12px;
  color: #909399;
  margin-left: 24px;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  font-size: 14px;
  margin-left: 10px;
}
.cat-name {
  color: #303133;
}
/* 搜索栏紧凑样式：双输入框并排 */
.search-bar-compact {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-search-input {
  width: 200px;
  transition: width 0.3s ease;
}
.file-search-input:focus-within {
  width: 300px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  line-height: 1.2;
}
.tag-editor {
  border: 1px solid #dcdfe6;
  padding: 5px;
  border-radius: 4px;
  min-height: 32px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.drag-tip {
  margin-left: 15px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
.sortable-ghost {
  opacity: 0.8;
  color: #fff !important;
  background: #409eff !important;
}
.drag-handle:active {
  cursor: grabbing;
}

/* =======================================
   平板与移动端响应式适配 CSS
   ======================================= */
@media screen and (max-width: 992px) {
  /* 强制上下分栏，兼容平板竖屏 */
  .panel-layout {
    flex-direction: column;
  }

  /* 顶部目录栏变为横向且高度受限，可内部滚动 */
  .volume-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 2px solid #e4e7ed;
    height: 180px; /* 给平板/移动端适当缩减目录高度 */
    flex-shrink: 0;
  }

  .file-content {
    padding: 10px;
  }

  /* 平板端搜索栏适配 */
  .file-search-input {
    width: 160px;
  }
  .file-search-input:focus-within {
    width: 220px;
  }
}

@media screen and (max-width: 768px) {
  /* 仅针对小屏幕手机的极致适配 */

  .search-bar-compact {
    width: 100%;
    flex-wrap: wrap;
  }
  .file-search-input {
    flex: 1;
    min-width: 120px;
  }
  .file-search-input:focus-within {
    flex: 1.5;
  }

  .view-mode-group {
    margin-left: 0;
    width: 100%; /* 让分组按钮占满一行 */
  }

  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }

  /* 让按钮均分宽度并防止文字截断 */
  .tool-btn {
    flex: 1;
    min-width: 80px;
    padding: 8px 10px;
  }

  /* 移动端强制显示三个点操作按钮，不需要 hover 才显示 */
  .vol-actions {
    opacity: 1;
  }

  /* 移动端操作列宽度更紧凑 */
  :deep(.el-table .cell) {
    padding-left: 5px;
    padding-right: 5px;
  }
}

:deep(.search-highlight) {
  color: #f56c6c;
  background-color: rgba(245, 108, 108, 0.1);
  font-weight: bold;
  border-radius: 2px;
  padding: 0 2px;
}
.ocr-snippet {
  font-size: 13px;
  color: #606266;
  margin-top: 6px;
  padding: 8px 10px;
  background: #f4f4f5;
  border-left: 3px solid #409eff;
  border-radius: 0 4px 4px 0;
  line-height: 1.6;
  word-break: break-all;

  /* 限制最大高度并支持内滚动 */
  max-height: 120px;
  overflow-y: auto;
}

/* 美化 OCR 摘要区域的滚动条 */
.ocr-snippet::-webkit-scrollbar {
  width: 6px;
}
.ocr-snippet::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}
.ocr-snippet::-webkit-scrollbar-track {
  background: transparent;
}

.ocr-snippet :deep(.search-highlight) {
  background-color: #fff176;
  color: #d32f2f;
}
</style>
