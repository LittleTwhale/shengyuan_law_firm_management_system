<template>
  <div class="electronic-seal-page">
    <div class="header">
      <h2>电子用印管理</h2>
      <div class="header-actions">
        <el-button v-if="isAdmin" type="primary" @click="showCreateSealDialog = true">
          <el-icon><Plus /></el-icon> 上传印章
        </el-button>
        <el-button type="primary" @click="showApplyDialog = true">
          <el-icon><EditPen /></el-icon> 新建申请
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="seal-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="印章库" name="seals" v-if="isAdmin">
        <el-table :data="sealList" border v-loading="loading.seals">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="印章预览" width="120" align="center">
            <template #default="{ row }">
              <el-image
                v-if="row.imageUrl"
                :src="row.imageUrl"
                :preview-src-list="[row.imageUrl]"
                class="seal-preview-img"
                fit="contain"
              />
              <div
                v-else
                class="seal-preview-img"
                v-loading="true"
                style="width: 50px; height: 50px; margin: 0 auto"
              ></div>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="印章名称" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">{{
                row.is_active ? '启用' : '禁用'
              }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="created_at"
            label="上传时间"
            :formatter="(row, column, cellValue) => formatDate(cellValue)"
          />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button
                size="small"
                :type="row.is_active ? 'warning' : 'success'"
                @click="toggleSealStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" type="danger" @click="deleteSeal(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="我的申请" name="my_applications">
        <div class="table-toolbar">
          <el-input
            v-model="searchKeyword.myApplications"
            placeholder="搜索文件名"
            clearable
            style="width: 240px"
            @keyup.enter="onSearch('my_applications')"
            @clear="onSearch('my_applications')"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="myApplications" border v-loading="loading.applications">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="original_file_name" label="文件名" show-overflow-tooltip />
          <el-table-column prop="seal.name" label="申请印章" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="apply_reason" label="用印原因" show-overflow-tooltip />
          <el-table-column
            prop="created_at"
            label="申请时间"
            :formatter="(row, column, cellValue) => formatDate(cellValue)"
            width="160"
          />
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.stamped_file_path"
                size="small"
                type="success"
                @click="downloadStampedFile(row.id, row.original_file_name)"
              >
                下载盖章件
              </el-button>
              <el-text v-else type="info" size="small">暂无文件</el-text>

              <el-button
                v-if="row.status !== '已通过'"
                size="small"
                type="danger"
                style="margin-left: 10px"
                @click="deleteApplication(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="pagination.myApplications.total > 0"
          class="table-pagination"
          v-model:current-page="pagination.myApplications.page"
          v-model:page-size="pagination.myApplications.pageSize"
          :total="pagination.myApplications.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange('my_applications')"
          @size-change="onPageChange('my_applications')"
        />
      </el-tab-pane>

      <el-tab-pane label="待审核申请" name="pending" v-if="canReview">
        <div class="table-toolbar">
          <el-input
            v-model="searchKeyword.pending"
            placeholder="搜索文件名或申请人"
            clearable
            style="width: 280px"
            @keyup.enter="onSearch('pending')"
            @clear="onSearch('pending')"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="pendingApplications" border v-loading="loading.pending">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="applicant.real_name" label="申请人" width="100" />
          <el-table-column prop="original_file_name" label="文件名" show-overflow-tooltip />
          <el-table-column prop="seal.name" label="申请印章" />
          <el-table-column prop="apply_reason" label="用印原因" show-overflow-tooltip />
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="handleApproveAndStamp(row)">
                <el-icon><Edit /></el-icon> 盖章
              </el-button>
              <el-button size="small" type="danger" @click="openRejectDialog(row)">
                <el-icon><CircleClose /></el-icon> 拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="pagination.pending.total > 0"
          class="table-pagination"
          v-model:current-page="pagination.pending.page"
          v-model:page-size="pagination.pending.pageSize"
          :total="pagination.pending.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange('pending')"
          @size-change="onPageChange('pending')"
        />
      </el-tab-pane>

      <el-tab-pane label="已通过申请" name="approved" v-if="canReview">
        <div class="table-toolbar">
          <el-input
            v-model="searchKeyword.approved"
            placeholder="搜索文件名或申请人"
            clearable
            style="width: 280px"
            @keyup.enter="onSearch('approved')"
            @clear="onSearch('approved')"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="approvedApplications" border v-loading="loading.approved">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="applicant.real_name" label="申请人" width="100" />
          <el-table-column prop="original_file_name" label="文件名" show-overflow-tooltip />
          <el-table-column prop="seal.name" label="申请印章" />
          <el-table-column prop="apply_reason" label="用印原因" show-overflow-tooltip />
          <el-table-column
            prop="created_at"
            label="申请时间"
            :formatter="(row, column, cellValue) => formatDate(cellValue)"
            width="160"
          />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.stamped_file_path"
                size="small"
                type="success"
                @click="downloadStampedFile(row.id, row.original_file_name)"
              >
                下载盖章件
              </el-button>
              <el-text v-else type="info" size="small">暂无文件</el-text>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="pagination.approved.total > 0"
          class="table-pagination"
          v-model:current-page="pagination.approved.page"
          v-model:page-size="pagination.approved.pageSize"
          :total="pagination.approved.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange('approved')"
          @size-change="onPageChange('approved')"
        />
      </el-tab-pane>

      <el-tab-pane label="已拒绝申请" name="rejected" v-if="canReview">
        <div class="table-toolbar">
          <el-input
            v-model="searchKeyword.rejected"
            placeholder="搜索文件名或申请人"
            clearable
            style="width: 280px"
            @keyup.enter="onSearch('rejected')"
            @clear="onSearch('rejected')"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-table :data="rejectedApplications" border v-loading="loading.rejected">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="applicant.real_name" label="申请人" width="100" />
          <el-table-column prop="original_file_name" label="文件名" show-overflow-tooltip />
          <el-table-column prop="seal.name" label="申请印章" />
          <el-table-column prop="apply_reason" label="用印原因" show-overflow-tooltip />
          <el-table-column prop="review_remark" label="拒绝原因" show-overflow-tooltip />
          <el-table-column
            prop="created_at"
            label="申请时间"
            :formatter="(row, column, cellValue) => formatDate(cellValue)"
            width="160"
          />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="danger"
                @click="deleteApplication(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="pagination.rejected.total > 0"
          class="table-pagination"
          v-model:current-page="pagination.rejected.page"
          v-model:page-size="pagination.rejected.pageSize"
          :total="pagination.rejected.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange('rejected')"
          @size-change="onPageChange('rejected')"
        />
      </el-tab-pane>
    </el-tabs>

    <el-dialog title="上传电子印章" v-model="showCreateSealDialog" width="500px">
      <el-form :model="sealForm" label-width="100px">
        <el-form-item label="印章名称" required>
          <el-input v-model="sealForm.name" placeholder="例如：公章" />
        </el-form-item>
        <el-form-item label="印章图片" required>
          <el-upload
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => (sealForm.file = file.raw)"
            accept=".png,.jpg,.jpeg"
          >
            <el-button type="primary">点击上传图片</el-button>
            <template #tip><div class="el-upload__tip">建议使用透明背景的PNG图片</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSealDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSeal" :loading="loading.submitting"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      title="新建用印申请"
      v-model="showApplyDialog"
      width="500px"
      @close="resetApplyForm"
      destroy-on-close
    >
      <el-form :model="applyForm" label-width="100px">
        <el-form-item label="选择印章" required>
          <el-select v-model="applyForm.seal_id" placeholder="请选择">
            <el-option v-for="s in activeSeals" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用印原因">
          <el-input v-model="applyForm.apply_reason" type="textarea" />
        </el-form-item>
        <el-form-item label="待盖章文件" required>
          <el-upload
            ref="applyUploadRef"
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => (applyForm.file = file.raw)"
            accept=".pdf,.doc,.docx"
          >
            <el-button type="primary">上传文件</el-button>
            <template #tip><div class="el-upload__tip">支持 Word 或 PDF</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateApplication" :loading="loading.submitting"
          >提交申请</el-button
        >
      </template>
    </el-dialog>

    <el-dialog title="拒绝用印申请" v-model="showRejectDialog" width="400px" destroy-on-close>
      <h3>申请详情</h3>
      <p><strong>申请人：</strong> {{ currentAuditRow?.applicant?.real_name }}</p>
      <p><strong>文件：</strong> {{ currentAuditRow?.original_file_name }}</p>
      <p><strong>原因：</strong> {{ currentAuditRow?.apply_reason || '无' }}</p>
      <el-divider />
      <el-form :model="currentAuditRow" label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input v-model="auditRemark" placeholder="请输入拒绝原因" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleReject" :loading="loading.submitting"
          >确定拒绝</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      title="盖章操作"
      v-model="showAuditDialog"
      fullscreen
      class="audit-dialog"
      destroy-on-close
    >
      <div
        class="audit-container"
        v-loading="loading.pdfProcessing"
        element-loading-text="正在处理PDF..."
      >
        <div class="pdf-workspace">
          <div
            class="canvas-wrapper"
            :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
          >
            <canvas ref="pdfCanvasRef"></canvas>

            <div
              class="draggable-seal"
              :style="{
                left: sealX + 'px',
                top: sealY + 'px',
                width: sealWidth + 'px',
                height: sealHeight + 'px',
                backgroundImage: `url(${currentSealUrl})`,
              }"
              @mousedown="startDrag"
            >
              <div class="resize-handle" @mousedown.stop="startResize"></div>
            </div>
          </div>
        </div>

        <div class="audit-controls">
          <h3>申请详情</h3>
          <p><strong>申请人：</strong> {{ currentAuditRow?.applicant?.real_name }}</p>
          <p><strong>文件：</strong> {{ currentAuditRow?.original_file_name }}</p>
          <p><strong>原因：</strong> {{ currentAuditRow?.apply_reason || '无' }}</p>
          <el-divider />

          <h3>盖章操作</h3>
          <div>
            <el-alert
              title="请拖拽左侧印章到指定位置，并确认页码"
              type="info"
              :closable="false"
              style="margin-bottom: 10px"
            />

            <div class="pagination-controls">
              <el-button @click="changePage(-1)" :disabled="currentPage <= 1">上一页</el-button>
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <el-button @click="changePage(1)" :disabled="currentPage >= totalPages"
                >下一页</el-button
              >
            </div>

            <el-button
              type="primary"
              size="large"
              @click="confirmStamping"
              :loading="loading.stamping"
              style="width: 100%; margin-top: 20px"
            >
              确认盖章并完成
            </el-button>
            <el-button
              @click="showAuditDialog = false"
              style="width: 100%; margin-top: 10px; margin-left: 0"
              >取消/退出</el-button
            >
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, EditPen, Edit, CircleClose, Search } from '@element-plus/icons-vue' // 引入所需图标
import request from '@/utils/request' // 修改为引入封装好的 request

// 引入 PDF 相关库
import * as pdfjsLib from 'pdfjs-dist'
import { PDFDocument } from 'pdf-lib'

// 配置 PDF.js Worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `/pdfjs/pdf.worker.min.mjs`

// --- 基础状态 ---
// 移除 API_BASE 常量，直接使用 request 的相对路径
const currentUserId = parseInt(localStorage.getItem('user_id'))
const currentUserRole = localStorage.getItem('role')
const currentUserPermissions = ref({})
const isAdmin = computed(() => ['admin', 'owner'].includes(currentUserRole))

// 判断用户是否为授权审核人的计算属性
const canReview = computed(() => {
  // 1. Owner 永远有权限
  if (currentUserRole === 'owner') return true

  // 2. 检查权限字典中的开关
  // 注意：后端返回的可能是 null 或 undefined，给予默认值 false
  return currentUserPermissions.value?.can_approve_seal === true
})

const activeTab = ref(isAdmin.value ? 'seals' : 'my_applications')
const loading = reactive({
  seals: false,
  applications: false,
  pending: false,
  approved: false,
  rejected: false,
  submitting: false,
  pdfProcessing: false,
  stamping: false,
})

const sealList = ref([])
const activeSeals = ref([])
const myApplications = ref([])
const pendingApplications = ref([])
const approvedApplications = ref([])
const rejectedApplications = ref([])

// 分页状态
const pagination = reactive({
  seals: { page: 1, pageSize: 10, total: 0 },
  myApplications: { page: 1, pageSize: 10, total: 0 },
  pending: { page: 1, pageSize: 10, total: 0 },
  approved: { page: 1, pageSize: 10, total: 0 },
  rejected: { page: 1, pageSize: 10, total: 0 },
})

// 搜索关键词（按 tab 分别维护）
const searchKeyword = reactive({
  myApplications: '',
  pending: '',
  approved: '',
  rejected: '',
})

// --- 表单状态 ---
const applyUploadRef = ref(null)

const showCreateSealDialog = ref(false)
const sealForm = reactive({ name: '', file: null })

const showApplyDialog = ref(false)
const applyForm = reactive({ seal_id: null, apply_reason: '', file: null })

// --- 审核与盖章状态 ---
const showAuditDialog = ref(false) // 盖章操作弹窗
const showRejectDialog = ref(false) // 拒绝操作弹窗
const currentAuditRow = ref(null)
const auditRemark = ref('') // 拒绝原因/审核意见

// --- PDF 可视化相关状态 ---
const pdfCanvasRef = ref(null)
let pdfDoc = null
const currentPage = ref(1)
const totalPages = ref(0)
const canvasWidth = ref(0)
const canvasHeight = ref(0)
let dynamicPdfScale = 1.0

// 印章拖拽状态
const currentSealUrl = ref('')
const sealX = ref(100)
const sealY = ref(100)
const sealWidth = ref(127)
const sealHeight = ref(127)
let isDragging = false
let isResizing = false
let startX = 0,
  startY = 0
const cachedPdfBytes = ref(null) // 缓存预览PDF，避免确认盖章时重复请求

// ==========================================
// 1. 数据加载与管理
// ==========================================
onMounted(() => {
  fetchUserProfile()
  fetchSeals()
  fetchMyApplications()
  if (isAdmin.value) fetchPendingApplications()
  if (canReview.value) {
    fetchApprovedApplications()
    fetchRejectedApplications()
  }
})
const fetchUserProfile = async () => {
  try {
    const res = await request.get(`/user/profile/info`) // 移除 user_id 参数，由后端 Token 解析
    // 如果 permissions 为空，给一个空对象防止报错
    currentUserPermissions.value = res.data.permissions || {}
  } catch (err) {
    console.error('获取用户信息失败', err)
    ElMessage.warning('无法获取用户权限信息，部分功能可能受限')
  }
}

const resetApplyForm = () => {
  // 1. 重置表单数据
  applyForm.seal_id = null
  applyForm.apply_reason = ''
  applyForm.file = null

  // 2. 清空上传组件的文件列表
  if (applyUploadRef.value) {
    applyUploadRef.value.clearFiles()
  }
}

const handleTabChange = (tab) => {
  if (tab === 'seals') fetchSeals()
  if (tab === 'my_applications') fetchMyApplications()
  if (tab === 'pending') fetchPendingApplications()
  if (tab === 'approved') fetchApprovedApplications()
  if (tab === 'rejected') fetchRejectedApplications()
}

const fetchSeals = async () => {
  loading.seals = true
  try {
    const res = await request.get(`/electronic_seal/seals`)

    // 由于 Token 验证原因，前端拉取图片不再能直接拼接 URL 给 img 标签，需要先获取 Blob
    const sealsWithImages = await Promise.all(
      res.data.map(async (s) => {
        try {
          const imgRes = await request.get(
            `/electronic_seal/seals/${s.id}/image?t=${new Date().getTime()}`,
            {
              responseType: 'blob',
            },
          )
          s.imageUrl = URL.createObjectURL(imgRes.data)
        } catch (e) {
          console.error(`无法加载印章 ${s.id} 的图片`, e)
          s.imageUrl = '' // 获取失败时给予空处理
        }
        return s
      }),
    )

    sealList.value = sealsWithImages
    activeSeals.value = sealsWithImages.filter((s) => s.is_active)
  } catch (err) {
    console.error(err)
  }
  loading.seals = false
}

const fetchMyApplications = async () => {
  loading.applications = true
  try {
    const p = pagination.myApplications
    const res = await request.get(`/electronic_seal/applications`, {
      params: {
        applicant_id: currentUserId,
        page: p.page,
        page_size: p.pageSize,
        search: searchKeyword.myApplications || undefined,
      },
    })
    myApplications.value = res.data.items
    p.total = res.data.total
  } catch (err) {
    console.error(err)
  }
  loading.applications = false
}

const fetchPendingApplications = async () => {
  loading.pending = true
  try {
    const p = pagination.pending
    const res = await request.get(`/electronic_seal/applications`, {
      params: {
        status: '待审核',
        page: p.page,
        page_size: p.pageSize,
        search: searchKeyword.pending || undefined,
      },
    })
    pendingApplications.value = res.data.items
    p.total = res.data.total
  } catch (err) {
    console.error(err)
  }
  loading.pending = false
}

const fetchApprovedApplications = async () => {
  loading.approved = true
  try {
    const p = pagination.approved
    const res = await request.get(`/electronic_seal/applications`, {
      params: {
        status: '已通过',
        page: p.page,
        page_size: p.pageSize,
        search: searchKeyword.approved || undefined,
      },
    })
    approvedApplications.value = res.data.items
    p.total = res.data.total
  } catch (err) {
    console.error(err)
  }
  loading.approved = false
}

const fetchRejectedApplications = async () => {
  loading.rejected = true
  try {
    const p = pagination.rejected
    const res = await request.get(`/electronic_seal/applications`, {
      params: {
        status: '已拒绝',
        page: p.page,
        page_size: p.pageSize,
        search: searchKeyword.rejected || undefined,
      },
    })
    rejectedApplications.value = res.data.items
    p.total = res.data.total
  } catch (err) {
    console.error(err)
  }
  loading.rejected = false
}

// 分页切换与搜索的通用触发
const tabFetchers = {
  seals: fetchSeals,
  my_applications: fetchMyApplications,
  pending: fetchPendingApplications,
  approved: fetchApprovedApplications,
  rejected: fetchRejectedApplications,
}

const onPageChange = (tab) => {
  tabFetchers[tab]?.()
}

const onSearch = (tab) => {
  pagination[tab].page = 1
  tabFetchers[tab]?.()
}

// ... 其他印章和申请操作 ...
const handleCreateSeal = async () => {
  if (!sealForm.name || !sealForm.file) return ElMessage.warning('请填写完整')
  loading.submitting = true
  const fd = new FormData()
  fd.append('name', sealForm.name)
  fd.append('file', sealForm.file)
  // 移除 uploaded_by 和 role，后端已通过 Token 解析

  try {
    await request.post(`/electronic_seal/seals`, fd)
    ElMessage.success('印章上传成功')
    showCreateSealDialog.value = false
    await fetchSeals()
  } catch (err) {
    console.error(err)
    ElMessage.error('上传失败')
  }
  loading.submitting = false
}

const toggleSealStatus = async (row) => {
  try {
    await request.put(`/electronic_seal/seals/${row.id}`, {
      // 移除 role 参数
      is_active: !row.is_active,
    })
    await fetchSeals()
  } catch (err) {
    console.error(err)
    ElMessage.error('操作失败')
  }
}

const deleteSeal = async (row) => {
  if (!confirm('确定删除该印章吗？')) return
  try {
    await request.delete(`/electronic_seal/seals/${row.id}`) // 移除 role 参数
    await fetchSeals()
  } catch (err) {
    console.error(err)
    ElMessage.error('删除失败')
  }
}

const handleCreateApplication = async () => {
  if (!applyForm.seal_id || !applyForm.file) return ElMessage.warning('请填写完整')
  loading.submitting = true
  const fd = new FormData()
  fd.append('seal_id', applyForm.seal_id)
  fd.append('apply_reason', applyForm.apply_reason)
  fd.append('file', applyForm.file)
  // 移除 applicant_id，后端已通过 Token 解析

  try {
    await request.post(`/electronic_seal/applications`, fd)
    ElMessage.success('申请已提交，请等待审核')
    showApplyDialog.value = false
    resetApplyForm()
    await fetchMyApplications()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败')
  }
  loading.submitting = false
}

// 修改为 Blob 形式下载，保证携带请求头 Auth Token
const downloadStampedFile = async (id, fileName) => {
  try {
    const res = await request.get(`/electronic_seal/applications/${id}/download_stamped`, {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `已盖章_${fileName}.pdf`) // 赋予下载文件名
    document.body.appendChild(link)
    link.click()
    link.parentNode.removeChild(link)
  } catch (err) {
    console.error('下载失败', err)
    ElMessage.error('下载失败，文件可能已丢失或无权限')
  }
}

const deleteApplication = async (row) => {
  const fileType = row.stamped_file_path ? '已盖章文件' : '原始文件'
  const confirmMsg = `确定要删除申请ID ${row.id} 及其所有附件（包含${fileType}）吗？此操作不可逆。`

  if (!confirm(confirmMsg)) return

  try {
    //  调用 DELETE /applications/{application_id} 接口 (移除 user_id 和 role)
    await request.delete(`/electronic_seal/applications/${row.id}`)

    ElMessage.success('用印申请及所有附件已删除')
    await fetchMyApplications() // 重新加载我的申请列表
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

// ==========================================
// 4. 审核与盖章逻辑
// ==========================================

// 打开拒绝弹窗
const openRejectDialog = (row) => {
  currentAuditRow.value = row
  auditRemark.value = ''
  showRejectDialog.value = true
}

// 处理拒绝操作
const handleReject = async () => {
  if (!auditRemark.value) return ElMessage.warning('请填写拒绝原因')
  loading.submitting = true
  try {
    // 调用 PUT /applications/{application_id}/review 接口 (移除 reviewer_id 和 role)
    await request.put(`/electronic_seal/applications/${currentAuditRow.value.id}/review`, {
      status: '已拒绝',
      review_remark: auditRemark.value,
    })

    ElMessage.success('已拒绝')
    showRejectDialog.value = false
    await fetchPendingApplications()
  } catch (err) {
    console.error(err)
    ElMessage.error('操作失败')
  } finally {
    loading.submitting = false
  }
}

// 轮询等待 Word → PDF 后台转换完成
const waitForPreviewPdf = async (applicationId) => {
  if (currentAuditRow.value?.preview_pdf_path) return
  // 最多等待 60 秒，每 2 秒检查一次
  for (let i = 0; i < 30; i++) {
    await new Promise((resolve) => setTimeout(resolve, 2000))
    try {
      const res = await request.get(`/electronic_seal/applications/${applicationId}`)
      if (res.data.preview_pdf_path) {
        currentAuditRow.value.preview_pdf_path = res.data.preview_pdf_path
        return
      }
    } catch (e) {
      // 继续轮询
      console.error(e)
    }
  }
  throw new Error('文件转换超时，请稍后重试')
}

// 处理盖章操作
const handleApproveAndStamp = async (row) => {
  currentAuditRow.value = row
  showAuditDialog.value = true // 打开盖章大屏弹窗
  loading.pdfProcessing = true

  // 重置印章位置
  sealX.value = 100
  sealY.value = 100
  // 重置印章大小
  sealWidth.value = 150
  sealHeight.value = 150

  try {
    // 预加载印章图片URL (因鉴权要求使用 Blob)
    const sealImgRes = await request.get(
      `/electronic_seal/seals/${row.seal.id}/image?t=${new Date().getTime()}`,
      {
        responseType: 'blob',
      },
    )
    currentSealUrl.value = URL.createObjectURL(sealImgRes.data)

    // 等待 Word 文档后台转换完成（如适用）
    await waitForPreviewPdf(row.id)

    // 1. 获取底图 PDF (ArrayBuffer)
    const response = await request.get(`/electronic_seal/applications/${row.id}/preview_pdf`, {
      responseType: 'arraybuffer',
    })
    // 缓存PDF，供确认盖章时使用，避免重复请求
    cachedPdfBytes.value = response.data

    // 2. 加载 PDF.js（使用克隆的 ArrayBuffer，避免 pdf.js Worker 转移导致原 buffer 被 detached）
    const pdfDataForJs = response.data.slice(0)
    const loadingTask = pdfjsLib.getDocument({ data: pdfDataForJs })
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    currentPage.value = 1

    // 3. 渲染第一页
    await renderPage(1)
  } catch (err) {
    console.error(err)
    ElMessage.error('加载文件失败，请检查文件格式或重试')
    showAuditDialog.value = false
  } finally {
    loading.pdfProcessing = false
  }
}

// 渲染 PDF 页面到 Canvas
const renderPage = async (num) => {
  if (!pdfDoc) return

  // 1. 获取 PDF 页面尺寸 (使用默认缩放 1.0)
  const page = await pdfDoc.getPage(num)
  const defaultViewport = page.getViewport({ scale: 1.0 })

  const canvas = pdfCanvasRef.value
  const context = canvas.getContext('2d')

  // 2. 确定可用高度
  // audit-dialog 的 body 高度是 (100vh - 60px)
  // audit-container 占据全部高度
  // pdf-workspace 占据全部高度，其 padding 是 20px (上下各 20px)
  const workspaceHeight = window.innerHeight - 60 - 20 * 2 // 窗口高度 - header高度 - 上下padding

  // 3. 计算动态缩放比例
  // 我们希望 PDF 视图略小于可用高度，留出一定边距 (例如 40px)
  dynamicPdfScale = (workspaceHeight - 40) / defaultViewport.height

  // 4. 应用动态缩放
  // 同时检查宽度，确保它不会导致水平滚动条 (如果PDF页面很宽)
  const availableWidth = window.innerWidth - 300 - 20 * 2 - 40 // 可用宽度
  const widthScale = availableWidth / defaultViewport.width

  // 取高度和宽度缩放比例中较小的一个，确保 PDF 既能适应高度，又不会超过可用宽度
  dynamicPdfScale = Math.min(dynamicPdfScale, widthScale)

  // ------------------------------------------------------------------
  // 渲染部分
  // ------------------------------------------------------------------
  const viewport = page.getViewport({ scale: dynamicPdfScale })

  canvas.height = viewport.height
  canvas.width = viewport.width

  // 更新 Vue 状态用于印章定位
  canvasWidth.value = viewport.width
  canvasHeight.value = viewport.height

  const renderContext = {
    canvasContext: context,
    viewport: viewport,
  }
  await page.render(renderContext).promise
}

const changePage = (delta) => {
  const newPage = currentPage.value + delta
  if (newPage >= 1 && newPage <= totalPages.value) {
    currentPage.value = newPage
    renderPage(newPage)
  }
}

// --- 拖拽逻辑 ---
const startDrag = (e) => {
  if (isResizing) return
  isDragging = true
  startX = e.clientX - sealX.value
  startY = e.clientY - sealY.value
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging) return
  let nx = e.clientX - startX
  let ny = e.clientY - startY

  if (nx < 0) nx = 0
  if (ny < 0) ny = 0
  if (nx + sealWidth.value > canvasWidth.value) nx = canvasWidth.value - sealWidth.value
  if (ny + sealHeight.value > canvasHeight.value) ny = canvasHeight.value - sealHeight.value

  sealX.value = nx
  sealY.value = ny
}

const stopDrag = () => {
  isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// --- 缩放逻辑 ---
const startResize = (e) => {
  isResizing = true
  const startW = sealWidth.value
  const startMX = e.clientX

  const onResize = (moveEvent) => {
    const delta = moveEvent.clientX - startMX
    const newSize = Math.max(50, startW + delta)
    sealWidth.value = newSize
    sealHeight.value = newSize
  }

  const stopResize = () => {
    isResizing = false
    document.removeEventListener('mousemove', onResize)
    document.removeEventListener('mouseup', stopResize)
  }

  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

// ==========================================
// 5. 确认盖章：前端合成 PDF 并上传
// ==========================================
const confirmStamping = async () => {
  loading.stamping = true
  try {
    await executeStamping()
    ElMessage.success('盖章完成，申请状态已更新为”已通过”')
    showAuditDialog.value = false
    await fetchPendingApplications()
    await fetchApprovedApplications()
  } catch (err) {
    console.error(err)
    ElMessage.error('盖章合成或上传失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.stamping = false
  }
}

/** 执行盖章合成与上传（提取为独立函数，避免 throw 在同一函数内被 catch 引发 linter 告警） */
const executeStamping = async () => {
  // 1. 使用缓存的 PDF 字节（handleApproveAndStamp 中已加载），避免重复请求
  const pdfBytes = cachedPdfBytes.value
  if (!pdfBytes) {
    throw new Error('PDF 数据未加载，请重新打开盖章弹窗')
  }

  // 2. 获取印章图片 ArrayBuffer (由于带权限需要通过 request 请求)
  const sealBytes = await request
    .get(
      `/electronic_seal/seals/${currentAuditRow.value.seal.id}/image?t=${new Date().getTime()}`,
      {
        responseType: 'arraybuffer',
      },
    )
    .then((res) => res.data)

  // 3. 使用 pdf-lib 加载 PDF
  const pdfDocLib = await PDFDocument.load(pdfBytes)

  // 4. 检测印章图片格式，支持 PNG 和 JPG
  const uint8 = new Uint8Array(sealBytes.slice(0, 4))
  const isPng = uint8[0] === 0x89 && uint8[1] === 0x50 && uint8[2] === 0x4E && uint8[3] === 0x47
  const isJpg = uint8[0] === 0xFF && uint8[1] === 0xD8 && uint8[2] === 0xFF
  let sealImage
  if (isPng) {
    sealImage = await pdfDocLib.embedPng(sealBytes)
  } else if (isJpg) {
    sealImage = await pdfDocLib.embedJpg(sealBytes)
  } else {
    throw new Error('不支持的印章图片格式，仅支持 PNG/JPG')
  }

  // 5. 获取当前页并计算坐标
  const pages = pdfDocLib.getPages()
  const page = pages[currentPage.value - 1]
  const { width, height } = page.getSize()

  const pdfX = (sealX.value / canvasWidth.value) * width
  // PDF Y 是从下往上，需要转换
  const pdfY = height - ((sealY.value + sealHeight.value) / canvasHeight.value) * height

  const pdfSealWidth = (sealWidth.value / canvasWidth.value) * width
  const pdfSealHeight = (sealHeight.value / canvasHeight.value) * height

  // 6. 绘制印章
  page.drawImage(sealImage, {
    x: pdfX,
    y: pdfY,
    width: pdfSealWidth,
    height: pdfSealHeight,
  })

  // 7. 保存生成新的 PDF
  const pdfDataUri = await pdfDocLib.save()
  const blob = new Blob([pdfDataUri], { type: 'application/pdf' })
  const file = new File([blob], `stamped_${currentAuditRow.value.original_file_name}.pdf`, {
    type: 'application/pdf',
  })

  // 8. 准备上传数据
  const fd = new FormData()
  fd.append('stamped_file', file)

  // 构造日志数据
  const logData = [
    {
      page_number: currentPage.value,
      x: pdfX,
      y: pdfY,
      width: pdfSealWidth,
      height: pdfSealHeight,
    },
  ]
  fd.append('log_data_json', JSON.stringify(logData))

  // 9. 调用 POST /applications/{application_id}/confirm 接口
  await request.post(`/electronic_seal/applications/${currentAuditRow.value.id}/confirm`, fd)
}

// --- 工具函数 (保持不变) ---
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const getStatusType = (status) => {
  if (status === '已通过') return 'success'
  if (status === '已拒绝') return 'danger'
  return 'warning'
}
</script>

<style scoped>
/* 保持不变 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.seal-preview-img {
  width: 50px;
  height: 50px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

/* 审核弹窗样式 */
.audit-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: calc(100vh - 60px);
}

.audit-container {
  display: flex;
  height: 100%;
}

.pdf-workspace {
  flex: 1;
  background-color: #525659;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 20px;
  position: relative;
}

.canvas-wrapper {
  position: relative;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  background: white;
}

.draggable-seal {
  position: absolute;
  cursor: grab;
  background-size: contain;
  background-repeat: no-repeat;
  border: 2px dashed #409eff;
  z-index: 10;
}

.draggable-seal:active {
  cursor: grabbing;
}

.resize-handle {
  width: 10px;
  height: 10px;
  background: #409eff;
  position: absolute;
  right: -5px;
  bottom: -5px;
  cursor: se-resize;
}

.audit-controls {
  width: 300px;
  background: #fff;
  padding: 20px;
  border-left: 1px solid #eee;
  display: flex;
  flex-direction: column;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.table-pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
