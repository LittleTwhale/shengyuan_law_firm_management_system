<template>
  <div class="standalone-volume-panel" v-loading="globalLoading">
    <!-- 顶部导航与信息头 -->
    <div class="info-header-card">
      <div class="header-top">
        <el-button link :icon="ArrowLeft" @click="goBack" class="back-btn">返回卷宗中心</el-button>
        <div v-if="canEdit" class="header-actions">
          <el-button type="primary" link :icon="Edit" size="small" @click="openEditInfoDialog"
            >编辑信息</el-button
          >
          <el-button type="danger" link :icon="Delete" size="small" @click="handleDeleteVolume"
            >删除卷宗</el-button
          >
        </div>
      </div>
      <div class="header-body">
        <h2 class="volume-title">
          <el-icon class="title-icon"><Folder /></el-icon>
          独立卷宗 · {{ volumeInfo.name }}
        </h2>
        <div class="info-tags">
          <span v-if="volumeInfo.client_name" class="info-item">
            <el-icon><User /></el-icon> 委托人：{{ volumeInfo.client_name }}
          </span>
          <span v-if="volumeInfo.client_phone" class="info-item">
            <el-icon><Phone /></el-icon> {{ volumeInfo.client_phone }}
          </span>
          <span v-if="volumeInfo.main_lawyer_name" class="info-item">
            <el-icon><Avatar /></el-icon> 主办律师：{{ volumeInfo.main_lawyer_name }}
          </span>
          <el-tag v-if="volumeInfo.category" size="small" effect="plain" class="info-tag">{{
            volumeInfo.category
          }}</el-tag>
          <el-tag
            v-if="volumeInfo.physical_location"
            size="small"
            type="info"
            effect="plain"
            class="info-tag"
          >
            <el-icon style="vertical-align: middle"><Location /></el-icon>
            {{ volumeInfo.physical_location }}
          </el-tag>
        </div>
        <p v-if="volumeInfo.case_description" class="info-desc">
          {{ volumeInfo.case_description }}
        </p>
      </div>
    </div>

    <!-- 文件管理区域（仿 CaseVolumePanel 右栏） -->
    <div class="file-content">
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="search-bar-compact">
            <el-input
              v-model="metaKeyword"
              placeholder="检索文件名/摘要/标签..."
              size="small"
              clearable
              class="file-search-input meta-search-input"
            >
              <template #prefix
                ><el-icon><Document /></el-icon
              ></template>
            </el-input>
            <el-input
              v-model="ocrKeyword"
              placeholder="检索OCR全文..."
              size="small"
              clearable
              class="file-search-input ocr-search-input"
            >
              <template #prefix
                ><el-icon><Search /></el-icon
              ></template>
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
          <el-tooltip content="刷新当前列表" placement="top">
            <el-button icon="Refresh" @click="refreshVolume" class="tool-btn">刷新</el-button>
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
              v-if="volumeInfo.merged_file_path"
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
              v-if="volumeInfo.merged_file_path"
              type="warning"
              :icon="Download"
              plain
              class="tool-btn"
              @click="downloadMergedFile"
              >下载全卷PDF</el-button
            >
          </el-tooltip>

          <el-tooltip content="导出全卷所有文件的OCR识别文本" placement="top">
            <el-button
              v-if="volumeId && hasOcrInVolume"
              type="success"
              :icon="Document"
              plain
              class="tool-btn"
              @click="handleExportVolumeOcr"
              >导出全卷OCR</el-button
            >
          </el-tooltip>
        </div>
      </div>

      <el-skeleton :loading="fileSearchLoading" animated :rows="10">
        <template #default>
          <!-- 列表视图 -->
          <el-table
            v-if="viewMode === 'list'"
            ref="dragTableRef"
            :data="fileList"
            row-key="id"
            stripe
            style="width: 100%; margin-top: 10px"
            height="calc(100vh - 360px)"
          >
            <el-table-column width="40" align="center" v-if="canEdit">
              <template #default>
                <el-icon class="drag-handle" style="cursor: move; color: #909399; font-size: 16px"
                  ><Rank
                /></el-icon>
              </template>
            </el-table-column>

            <el-table-column label="序号" type="index" width="60" align="center" />

            <el-table-column label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="file-name-cell">
                  <el-icon v-if="isPdf(row.file_type)" style="color: #f56c6c"><Document /></el-icon>
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
                <div
                  v-if="row.summary"
                  class="row-summary"
                  v-html="DOMPurify.sanitize(row.summary)"
                ></div>
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
                  <el-tag v-for="t in row.tags || []" :key="t" size="small" type="info">
                    <span v-html="DOMPurify.sanitize(t)"></span>
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="sort_order" label="排序权重" width="80" align="center" />

            <el-table-column label="全卷页码" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.page_start" class="page-badge"
                  >P{{ row.page_start }} - P{{ row.page_end }}</span
                >
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
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>

            <el-table-column
              label="操作"
              :width="isMobile ? 220 : 260"
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
                  v-if="row.ocr_status === 'skipped'"
                  link
                  type="warning"
                  size="small"
                  @click="handleTriggerOcr(row)"
                  >识别文字</el-button
                >
                <el-button
                  v-if="row.ocr_content"
                  link
                  type="success"
                  size="small"
                  @click="handleExportOcr(row)"
                  >导出OCR</el-button
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

          <!-- 分组视图 -->
          <el-scrollbar
            v-else
            height="calc(100vh - 360px)"
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
                    </template>
                  </el-table-column>
                  <el-table-column label="标签" min-width="100">
                    <template #default="{ row }">
                      <el-tag
                        v-for="t in row.tags || []"
                        :key="t"
                        size="small"
                        style="margin-right: 4px"
                      >
                        <span v-html="DOMPurify.sanitize(t)"></span>
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="全卷页码" width="100" align="center">
                    <template #default="{ row }">
                      <span v-if="row.page_start" class="page-badge"
                        >P{{ row.page_start }}-{{ row.page_end }}</span
                      >
                    </template>
                  </el-table-column>
                  <el-table-column prop="uploader_name" label="上传人" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag size="small" type="info" effect="plain">{{
                        row.uploader_name || '未知'
                      }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="created_at" label="上传时间" width="150" align="center">
                    <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
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
                        v-if="row.ocr_content"
                        link
                        type="success"
                        size="small"
                        @click="handleExportOcr(row)"
                        >导出OCR</el-button
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

    <!-- 批量上传对话框 -->
    <BatchUploadDialog
      v-if="volumeId"
      v-model:visible="showUploadDialog"
      :volume-id="volumeId"
      :base-sort-order="maxSortOrder"
      @success="refreshVolume"
    />

    <!-- 编辑卷宗信息对话框 -->
    <el-dialog
      v-model="infoDialogVisible"
      title="编辑卷宗信息"
      :width="isMobile ? '95%' : '550px'"
      destroy-on-close
      append-to-body
    >
      <el-form
        :model="infoForm"
        :label-width="isMobile ? 'auto' : '100px'"
        :label-position="isMobile ? 'top' : 'right'"
        @submit.prevent
      >
        <el-form-item label="卷宗名称" required>
          <el-input v-model="infoForm.name" />
        </el-form-item>
        <el-row :gutter="16" v-if="!isMobile">
          <el-col :span="12">
            <el-form-item label="委托人姓名"
              ><el-input v-model="infoForm.client_name"
            /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托人电话"
              ><el-input v-model="infoForm.client_phone"
            /></el-form-item>
          </el-col>
        </el-row>
        <template v-else>
          <el-form-item label="委托人姓名"
            ><el-input v-model="infoForm.client_name"
          /></el-form-item>
          <el-form-item label="委托人电话"
            ><el-input v-model="infoForm.client_phone"
          /></el-form-item>
        </template>
        <el-row :gutter="16" v-if="!isMobile">
          <el-col :span="12">
            <el-form-item label="主办律师"
              ><el-input v-model="infoForm.main_lawyer_name"
            /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="案件类别">
              <el-select v-model="infoForm.category" style="width: 100%" clearable>
                <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <template v-else>
          <el-form-item label="主办律师"
            ><el-input v-model="infoForm.main_lawyer_name"
          /></el-form-item>
          <el-form-item label="案件类别">
            <el-select v-model="infoForm.category" style="width: 100%" clearable>
              <el-option v-for="c in caseCategories" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="简要描述">
          <el-input v-model="infoForm.case_description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="infoForm.physical_location" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="infoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInfoUpdate" :loading="infoSubmitting"
          >保存</el-button
        >
      </template>
    </el-dialog>

    <!-- 文件编辑对话框 -->
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
        <el-form-item label="文件名"><el-input v-model="editForm.file_name" /></el-form-item>
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

    <!-- 预览对话框 -->
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
          alt="预览图片"/>
        <div v-else class="preview-error">无法预览此文件，请下载查看</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Delete,
  Document,
  DocumentCopy,
  Folder,
  FolderOpened,
  Picture,
  Rank,
  Location,
  Upload,
  Download,
  Connection,
  View,
  Search,
  User,
  Phone,
  Avatar,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import BatchUploadDialog from '@/components/BatchUploadDialog.vue'
import Sortable from 'sortablejs'
import { debounce } from 'lodash-es'
import DOMPurify from 'dompurify'

const isMobile = inject('isMobile', ref(false))
const route = useRoute()
const router = useRouter()

const volumeId = computed(() => Number(route.params.volumeId))

// 状态
const globalLoading = ref(false)
const volumeInfo = ref({})
const fileList = ref([])
const canEdit = ref(false)

// UI 状态
const showUploadDialog = ref(false)
const merging = ref(false)
const viewMode = ref('list')
const activeNames = ref([])
const metaKeyword = ref('')
const ocrKeyword = ref('')
const fileSearchLoading = ref(false)

let mergePollingTimer = null
let ocrPollingTimer = null

// 文件分类选项
const categoryOptions = ['证据材料', '法律文书', '起诉/答辩状', '笔录资料', '备考表', '其他材料']
const caseCategories = [
  '民事案件',
  '银行案件',
  '刑事案件',
  '行政案件',
  '非诉业务',
  '执行案件',
  '劳动仲裁',
  '商事仲裁',
  '法律顾问业务',
  '法律援助(民事)',
  '法律援助(刑事)',
  '法律援助(行政)',
]

// 编辑卷宗信息
const infoDialogVisible = ref(false)
const infoSubmitting = ref(false)
const infoForm = ref({
  name: '',
  client_name: '',
  client_phone: '',
  main_lawyer_name: '',
  category: '',
  case_description: '',
  physical_location: '',
})

// 文件编辑
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

// 预览
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('pdf')
const previewLoading = ref(false)
const previewLoadingText = ref('加载中...')

// 拖拽
const dragTableRef = ref(null)
let sortableInstance = null

// 计算属性
const maxSortOrder = computed(() => {
  if (!fileList.value.length) return 0
  return fileList.value.reduce(
    (acc, cur) => ((cur.sort_order || 0) > acc ? cur.sort_order : acc),
    0,
  )
})

// 当前卷宗内是否存在有OCR内容的文件
const hasOcrInVolume = computed(() => {
  return fileList.value.some((f) => f.ocr_content)
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

// 初始化
onMounted(async () => {
  await fetchPermissions()
  await refreshVolume()
})

onBeforeUnmount(() => {
  if (mergePollingTimer) clearInterval(mergePollingTimer)
  if (ocrPollingTimer) clearInterval(ocrPollingTimer)
})

// 权限
const fetchPermissions = async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return
  try {
    const userRes = await request.get(`/user/profile/info?user_id=${userId}`)
    const userInfo = userRes.data
    const isSuper =
      userInfo.role === 'owner' || (userInfo.permissions && userInfo.permissions.volume_manage)
    if (isSuper) {
      canEdit.value = true
      return
    }
    // 加载卷宗详情判断创建者
    const volRes = await request.get(`/electronic_volumes/${volumeId.value}`)
    volumeInfo.value = volRes.data
    canEdit.value = volRes.data.created_by === Number(userId)
  } catch (err) {
    console.error('权限获取失败', err)
    canEdit.value = false
  }
}

// 刷新
const refreshVolume = async () => {
  if (!volumeId.value) return
  globalLoading.value = true
  try {
    const res = await request.get(`/electronic_volumes/${volumeId.value}`)
    volumeInfo.value = res.data
    fileList.value = res.data.files || []
    fileList.value.sort((a, b) => a.sort_order - b.sort_order)
    metaKeyword.value = ''
    ocrKeyword.value = ''
  } catch (err) {
    console.error(err)
    ElMessage.error('加载卷宗失败')
  } finally {
    globalLoading.value = false
  }
}

// 搜索
const handleFileSearch = async () => {
  if (!volumeId.value) return
  fileSearchLoading.value = true
  try {
    const metaKw = metaKeyword.value.trim()
    const ocrKw = ocrKeyword.value.trim()
    if (!metaKw && !ocrKw) {
      await refreshVolume()
      return
    }
    const res = await request.get(`/electronic_volumes/${volumeId.value}/files`, {
      params: { meta_keyword: metaKw || undefined, ocr_keyword: ocrKw || undefined },
    })
    fileList.value = res.data.items || []
    fileList.value.sort((a, b) => a.sort_order - b.sort_order)
  } catch (err) {
    console.error('搜索失败', err)
    ElMessage.error('文件搜索失败')
  } finally {
    fileSearchLoading.value = false
  }
}

const debouncedFileSearch = debounce(() => handleFileSearch(), 400)
watch([metaKeyword, ocrKeyword], () => debouncedFileSearch())

const clearSearch = () => {
  metaKeyword.value = ''
  ocrKeyword.value = ''
}

// 拖拽
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
        await refreshVolume()
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

watch(volumeId, () => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
})

// 卷宗信息编辑
const openEditInfoDialog = () => {
  infoForm.value = {
    name: volumeInfo.value.name || '',
    client_name: volumeInfo.value.client_name || '',
    client_phone: volumeInfo.value.client_phone || '',
    main_lawyer_name: volumeInfo.value.main_lawyer_name || '',
    category: volumeInfo.value.category || '',
    case_description: volumeInfo.value.case_description || '',
    physical_location: volumeInfo.value.physical_location || '',
  }
  infoDialogVisible.value = true
}

const submitInfoUpdate = async () => {
  if (!infoForm.value.name.trim()) {
    ElMessage.warning('请输入卷宗名称')
    return
  }
  infoSubmitting.value = true
  try {
    await request.put(`/electronic_volumes/${volumeId.value}`, {
      name: infoForm.value.name,
      client_name: infoForm.value.client_name || undefined,
      client_phone: infoForm.value.client_phone || undefined,
      main_lawyer_name: infoForm.value.main_lawyer_name || undefined,
      category: infoForm.value.category || undefined,
      case_description: infoForm.value.case_description || undefined,
      physical_location: infoForm.value.physical_location || undefined,
    })
    ElMessage.success('更新成功')
    infoDialogVisible.value = false
    await refreshVolume()
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  } finally {
    infoSubmitting.value = false
  }
}

// 文件编辑
const openEditDialog = (row) => {
  editForm.value = JSON.parse(JSON.stringify(row))
  if (!editForm.value.tags) editForm.value.tags = []
  tempEditTag.value = ''
  editDialogVisible.value = true
}

const addEditTag = () => {
  const val = tempEditTag.value.trim()
  if (val && !editForm.value.tags.includes(val)) editForm.value.tags.push(val)
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
    await refreshVolume()
  } catch (err) {
    console.error(err)
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
    await refreshVolume()
  } catch (err) {
    console.error(err)
  }
}

// 下载
const downloadBlob = async (url, filename) => {
  let loadingInstance = null
  try {
    loadingInstance = ElLoading.service({
      lock: true,
      text: '正在请求下载，请耐心等待...',
      background: 'rgba(0, 0, 0, 0.7)',
    })
    const res = await request.get(url, {
      responseType: 'blob',
      timeout: 0,
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          loadingInstance.setText(
            `正在下载文件: ${Math.round((progressEvent.loaded * 100) / progressEvent.total)}%`,
          )
        } else {
          loadingInstance.setText(
            `正在下载文件: ${(progressEvent.loaded / 1024 / 1024).toFixed(2)} MB`,
          )
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
    ElMessage.error('下载失败')
  } finally {
    if (loadingInstance) loadingInstance.close()
  }
}

const handleDownload = (row) =>
  downloadBlob(`/electronic_volumes/files/${row.id}/download`, row.file_name)

// 手动触发被跳过的大文件 OCR 识别
const handleTriggerOcr = async (row) => {
  try {
    await request.post(`/electronic_volumes/files/${row.id}/trigger_ocr`)
    ElMessage.success('OCR 识别任务已提交，后台处理中')
    row.ocr_status = 'processing'
    ocrPollingTimer = startPollingFileOcrStatus(row.id)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '触发 OCR 失败')
  }
}

// 轮询单个文件的 OCR 状态
const startPollingFileOcrStatus = (fileId) => {
  const timer = setInterval(async () => {
    try {
      const res = await request.get(`/electronic_volumes/files/${fileId}`)
      const status = res.data.ocr_status
      if (status === 'completed') {
        clearInterval(timer)
        ElMessage.success('OCR 识别完成')
        await refreshVolume()
      } else if (status === 'failed') {
        clearInterval(timer)
        ElMessage.warning('OCR 识别未提取到有效内容')
        await refreshVolume()
      }
    } catch (e) {
      console.error('轮询 OCR 状态失败', e)
      clearInterval(timer)
    }
  }, 2000)
  return timer
}

// 导出OCR识别结果（纯文本文件）
const handleExportOcr = (row) => {
  const baseName = row.file_name.replace(/\.[^/.]+$/, '')
  downloadBlob(`/electronic_volumes/files/${row.id}/ocr_text`, baseName + '_OCR.txt')
}

// 导出全卷OCR识别结果（合并为一个纯文本文件）
const handleExportVolumeOcr = () => {
  if (!volumeId.value) return
  const volName = volumeInfo.value?.name || `卷宗${volumeId.value}`
  downloadBlob(
    `/electronic_volumes/${volumeId.value}/ocr_text`,
    volName + '_全卷OCR.txt',
  )
}

// 合并
const handleMergeVolume = async () => {
  if (!fileList.value.length) return ElMessage.warning('卷宗为空，无法合并')
  merging.value = true
  const targetVolumeId = volumeId.value
  try {
    ElMessage.info('合并任务已提交，系统正在后台处理，请耐心等待...')
    await request.post(`/electronic_volumes/${targetVolumeId}/merge`, null, { timeout: 120000 })
    startPollingMergeStatus(targetVolumeId)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '合并任务提交失败')
    merging.value = false
  }
}

const startPollingMergeStatus = (volId) => {
  if (mergePollingTimer) clearInterval(mergePollingTimer)
  mergePollingTimer = setInterval(async () => {
    try {
      const res = await request.get(`/electronic_volumes/${volId}`)
      if (res.data.merged_file_path) {
        clearInterval(mergePollingTimer)
        mergePollingTimer = null
        ElMessage.success('电子卷宗生成成功！')
        if (volumeId.value === volId) {
          merging.value = false
          volumeInfo.value = res.data
        }
        await refreshVolume()
      }
    } catch (e) {
      console.error('轮询合并状态失败', e)
    }
  }, 3000)
}

const previewMergedFile = async () => {
  if (!volumeInfo.value.merged_file_path) return
  previewLoading.value = true
  previewVisible.value = true
  previewType.value = 'pdf'
  previewLoadingText.value = '正在请求全卷预览，请稍候...'
  try {
    const res = await request.get(`/electronic_volumes/${volumeId.value}/preview_merged`, {
      responseType: 'blob',
      timeout: 0,
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total)
          previewLoadingText.value = `正在加载全卷预览: ${Math.round((progressEvent.loaded * 100) / progressEvent.total)}%`
        else
          previewLoadingText.value = `正在加载全卷预览: ${(progressEvent.loaded / 1024 / 1024).toFixed(2)} MB`
      },
    })
    previewUrl.value = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  } catch (err) {
    console.error(err)
    ElMessage.error('预览加载失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

const downloadMergedFile = () => {
  if (!volumeInfo.value.merged_file_path) return
  downloadBlob(
    `/electronic_volumes/${volumeId.value}/download_merged`,
    `${volumeInfo.value.name}_全卷.pdf`,
  )
}

// 预览
const handlePreview = async (row) => {
  previewLoading.value = true
  previewVisible.value = true
  previewLoadingText.value = '正在加载预览文件...'
  try {
    const res = await request.get(`/electronic_volumes/files/${row.id}/preview`, {
      responseType: 'blob',
      timeout: 0,
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total)
          previewLoadingText.value = `正在下载预览文件: ${Math.round((progressEvent.loaded * 100) / progressEvent.total)}%`
        else
          previewLoadingText.value = `正在下载预览文件: ${(progressEvent.loaded / 1024 / 1024).toFixed(2)} MB`
      },
    })
    previewUrl.value = window.URL.createObjectURL(
      new Blob([res.data], { type: res.headers['content-type'] }),
    )
    previewType.value = res.headers['content-type'].includes('image') ? 'image' : 'pdf'
  } catch (err) {
    console.error(err)
    ElMessage.error('预览失败或文件正在转换中')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

const isPdf = (type) => type?.includes('pdf')
const isImage = (type) => type?.includes('image')
const formatTime = (val) => (val ? new Date(val).toLocaleString() : '')

const goBack = () => router.push('/main/volumes')

const handleDeleteVolume = async () => {
  try {
    await ElMessageBox.confirm('确定要删除该独立卷宗及其所有文件吗？此操作不可恢复！', '警告', {
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
    await request.delete(`/electronic_volumes/${volumeId.value}`)
    ElMessage.success('删除成功')
    await router.push('/main/volumes')
  } catch (err) {
    if (err !== 'cancel') console.error(err)
  }
}
</script>

<style scoped>
.standalone-volume-panel {
  height: 100%;
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 信息头卡片 */
.info-header-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
}
.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.back-btn {
  font-size: 14px;
}
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.header-body {
  padding: 0;
}
.volume-title {
  margin: 0 0 10px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  color: #e6a23c;
  font-size: 22px;
}
.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 8px;
}
.info-item {
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}
.info-tag {
  margin: 0;
}
.info-desc {
  font-size: 13px;
  color: #909399;
  margin: 8px 0 0 0;
  line-height: 1.5;
}

/* 文件区 */
.file-content {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}
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
.tool-btn {
  margin-left: 0 !important;
}

/* 搜索栏 */
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

.view-mode-group {
  margin-left: 20px;
}
.drag-tip {
  margin-left: 15px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 文件表格 */
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
.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
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

/* 分组视图 */
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
.row-summary {
  font-size: 12px;
  color: #909399;
  margin-left: 24px;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 预览 */
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
.preview-error {
  color: #909399;
  font-size: 16px;
}

/* OCR 搜索高亮 */
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
  max-height: 120px;
  overflow-y: auto;
}
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

.sortable-ghost {
  opacity: 0.8;
  color: #fff !important;
  background: #409eff !important;
}
.drag-handle:active {
  cursor: grabbing;
}

/* ============ 响应式 ============ */
@media screen and (max-width: 992px) {
  .standalone-volume-panel {
    padding: 12px;
  }
  .info-header-card {
    padding: 12px 14px;
  }
  .volume-title {
    font-size: 17px;
  }
  .info-tags {
    gap: 8px;
  }
  .file-content {
    padding: 12px;
  }
  .file-search-input {
    width: 140px;
  }
  .file-search-input:focus-within {
    width: 200px;
  }
}

@media screen and (max-width: 768px) {
  .standalone-volume-panel {
    padding: 8px;
  }
  .info-header-card {
    padding: 10px 12px;
  }
  .volume-title {
    font-size: 15px;
  }
  .info-tags {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .search-bar-compact {
    width: 100%;
    flex-wrap: wrap;
  }
  .file-search-input {
    flex: 1;
    min-width: 100px;
  }
  .file-search-input:focus-within {
    flex: 1.5;
  }
  .view-mode-group {
    margin-left: 0;
    width: 100%;
  }
  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }
  .tool-btn {
    flex: 1;
    min-width: 60px;
    padding: 8px 6px;
    font-size: 12px;
  }
}
</style>
