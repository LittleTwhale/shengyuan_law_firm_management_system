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
                :src="getSealImageUrl(row.id)"
                :preview-src-list="[getSealImageUrl(row.id)]"
                class="seal-preview-img"
                fit="contain"
              />
            </template>
          </el-table-column>
          <el-table-column prop="name" label="印章名称" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间"
                           :formatter="(row, column, cellValue) => formatDate(cellValue)" />
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
          <el-table-column prop="created_at" label="申请时间"
                           :formatter="(row, column, cellValue) => formatDate(cellValue)" width="160" />
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.stamped_file_path"
                size="small"
                type="success"
                @click="downloadStampedFile(row.id)"
              >
                下载盖章件
              </el-button>
              <el-text v-else type="info" size="small">暂无文件</el-text>

              <el-button
                size="small"
                type="danger"
                style="margin-left: 10px;"
                @click="deleteApplication(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="待审核申请" name="pending" v-if="isAdmin">
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
            :on-change="(file) => sealForm.file = file.raw"
            accept=".png,.jpg,.jpeg"
          >
            <el-button type="primary">点击上传图片</el-button>
            <template #tip><div class="el-upload__tip">建议使用透明背景的PNG图片</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSealDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSeal" :loading="loading.submitting">确定</el-button>
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
            ref="applyUploadRef"  action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="(file) => applyForm.file = file.raw"
            accept=".pdf,.doc,.docx"
          >
            <el-button type="primary">上传文件</el-button>
            <template #tip><div class="el-upload__tip">支持 Word 或 PDF</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateApplication" :loading="loading.submitting">提交申请</el-button>
      </template>
    </el-dialog>

    <el-dialog
      title="拒绝用印申请"
      v-model="showRejectDialog"
      width="400px"
      destroy-on-close
    >
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
        <el-button type="danger" @click="handleReject" :loading="loading.submitting">确定拒绝</el-button>
      </template>
    </el-dialog>


    <el-dialog
      title="盖章操作"
      v-model="showAuditDialog"
      fullscreen
      class="audit-dialog"
      destroy-on-close
    >
      <div class="audit-container" v-loading="loading.pdfProcessing" element-loading-text="正在处理PDF...">

        <div class="pdf-workspace">
          <div class="canvas-wrapper" :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }">
            <canvas ref="pdfCanvasRef"></canvas>

            <div
              class="draggable-seal"
              :style="{
                left: sealX + 'px',
                top: sealY + 'px',
                width: sealWidth + 'px',
                height: sealHeight + 'px',
                backgroundImage: `url(${currentSealUrl})`
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
            <el-alert title="请拖拽左侧印章到指定位置，并确认页码" type="info" :closable="false" style="margin-bottom: 10px;" />

            <div class="pagination-controls">
              <el-button @click="changePage(-1)" :disabled="currentPage <= 1">上一页</el-button>
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <el-button @click="changePage(1)" :disabled="currentPage >= totalPages">下一页</el-button>
            </div>

            <el-button type="primary" size="large" @click="confirmStamping" :loading="loading.stamping" style="width: 100%; margin-top: 20px;">
              确认盖章并完成
            </el-button>
            <el-button @click="showAuditDialog = false" style="width: 100%; margin-top: 10px; margin-left: 0;">取消/退出</el-button>
          </div>
        </div>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, EditPen, Edit, CircleClose } from '@element-plus/icons-vue' // 引入所需图标

// 引入 PDF 相关库
import * as pdfjsLib from 'pdfjs-dist'
import { PDFDocument } from 'pdf-lib'

// 配置 PDF.js Worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `/pdfjs/pdf.worker.min.mjs`

// --- 基础状态 ---
const API_BASE = 'http://127.0.0.1:8002/electronic_seal'
const currentUserId = parseInt(sessionStorage.getItem('user_id'))
const currentUserRole = sessionStorage.getItem('role')
const isAdmin = computed(() => ['admin', 'owner'].includes(currentUserRole))

const activeTab = ref(isAdmin.value ? 'seals' : 'my_applications')
const loading = reactive({
  seals: false,
  applications: false,
  pending: false,
  submitting: false,
  pdfProcessing: false,
  stamping: false
})

const sealList = ref([])
const activeSeals = ref([])
const myApplications = ref([])
const pendingApplications = ref([])

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
const sealWidth = ref(150)
const sealHeight = ref(150)
let isDragging = false
let isResizing = false
let startX = 0, startY = 0

// ==========================================
// 1. 数据加载与管理
// ==========================================
onMounted(() => {
  fetchSeals()
  fetchMyApplications()
  if (isAdmin.value) fetchPendingApplications()
})

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
}

const fetchSeals = async () => {
  loading.seals = true
  try {
    const res = await axios.get(`${API_BASE}/seals`)
    sealList.value = res.data
    activeSeals.value = res.data.filter(s => s.is_active)
  } catch (err) { console.error(err) }
  loading.seals = false
}

const fetchMyApplications = async () => {
  loading.applications = true
  try {
    const res = await axios.get(`${API_BASE}/applications`, { params: { applicant_id: currentUserId } })
    myApplications.value = res.data
  } catch (err) { console.error(err) }
  loading.applications = false
}

const fetchPendingApplications = async () => {
  loading.pending = true
  try {
    const res = await axios.get(`${API_BASE}/applications`, { params: { status: '待审核' } })
    pendingApplications.value = res.data
  } catch (err) { console.error(err) }
  loading.pending = false
}

const getSealImageUrl = (sealId) => `${API_BASE}/seals/${sealId}/image`

// ... 其他印章和申请操作 ...
const handleCreateSeal = async () => {
  if (!sealForm.name || !sealForm.file) return ElMessage.warning('请填写完整')
  loading.submitting = true
  const fd = new FormData()
  fd.append('name', sealForm.name)
  fd.append('file', sealForm.file)
  fd.append('uploaded_by', currentUserId)
  fd.append('role', currentUserRole)

  try {
    await axios.post(`${API_BASE}/seals`, fd)
    ElMessage.success('印章上传成功')
    showCreateSealDialog.value = false
    await fetchSeals()
  } catch (err) {
    console.error(err)
    ElMessage.error('上传失败') }
  loading.submitting = false
}

const toggleSealStatus = async (row) => {
  try {
    await axios.put(`${API_BASE}/seals/${row.id}?role=${currentUserRole}`, { is_active: !row.is_active })
    await fetchSeals()
  } catch (err) {
    console.error(err)
    ElMessage.error('操作失败')
  }
}

const deleteSeal = async (row) => {
  if(!confirm('确定删除该印章吗？')) return
  try {
    await axios.delete(`${API_BASE}/seals/${row.id}?role=${currentUserRole}`)
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
  fd.append('applicant_id', currentUserId)

  try {
    await axios.post(`${API_BASE}/applications`, fd)
    ElMessage.success('申请已提交，请等待审核')
    showApplyDialog.value = false
    resetApplyForm()
    await fetchMyApplications()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败')
  }
  loading.submitting = false
}

const downloadStampedFile = (id) => {
  window.open(`${API_BASE}/applications/${id}/download_stamped`, '_blank')
}

const deleteApplication = async (row) => {
  const fileType = row.stamped_file_path ? '已盖章文件' : '原始文件';
  const confirmMsg = `确定要删除申请ID ${row.id} 及其所有附件（包含${fileType}）吗？此操作不可逆。`;

  if(!confirm(confirmMsg)) return

  try {
    //  调用 DELETE /applications/{application_id} 接口
    await axios.delete(`${API_BASE}/applications/${row.id}`, {
      params: {
        user_id: currentUserId,
        role: currentUserRole
      }
    })

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
    // 调用 PUT /applications/{application_id}/review 接口
    await axios.put(`${API_BASE}/applications/${currentAuditRow.value.id}/review`, {
      status: '已拒绝',
      review_remark: auditRemark.value,
      reviewer_id: currentUserId
    }, { params: { reviewer_id: currentUserId, role: currentUserRole } })

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

// 处理盖章操作
const handleApproveAndStamp = async (row) => {
  currentAuditRow.value = row
  showAuditDialog.value = true // 打开盖章大屏弹窗
  loading.pdfProcessing = true

  // 预加载印章图片URL
  currentSealUrl.value = getSealImageUrl(row.seal.id)
  // 重置印章位置
  sealX.value = 100
  sealY.value = 100
  // 重置印章大小
  sealWidth.value = 150
  sealHeight.value = 150

  try {
    // 1. 获取底图 PDF (ArrayBuffer)
    const response = await axios.get(`${API_BASE}/applications/${row.id}/preview_pdf`, {
      responseType: 'arraybuffer'
    })

    // 2. 加载 PDF.js
    const loadingTask = pdfjsLib.getDocument({ data: response.data })
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    currentPage.value = 1

    // 3. 渲染第一页
    await renderPage(1)

  } catch (err) {
    console.error(err)
    ElMessage.error('加载文件失败，请检查文件格式')
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
  const workspaceHeight = window.innerHeight - 60 - (20 * 2); // 窗口高度 - header高度 - 上下padding

  // 3. 计算动态缩放比例
  // 我们希望 PDF 视图略小于可用高度，留出一定边距 (例如 40px)
  dynamicPdfScale = (workspaceHeight - 40) / defaultViewport.height

  // 4. 应用动态缩放
  // 同时检查宽度，确保它不会导致水平滚动条 (如果PDF页面很宽)
  const availableWidth = window.innerWidth - 300 - (20 * 2) - 40; // 可用宽度
  const widthScale = availableWidth / defaultViewport.width;

  // 取高度和宽度缩放比例中较小的一个，确保 PDF 既能适应高度，又不会超过可用宽度
  dynamicPdfScale = Math.min(dynamicPdfScale, widthScale);

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
    viewport: viewport
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
    // 1. 获取原 PDF ArrayBuffer
    const pdfBytes = await axios.get(`${API_BASE}/applications/${currentAuditRow.value.id}/preview_pdf`, {
      responseType: 'arraybuffer'
    }).then(res => res.data)

    // 2. 获取印章图片 ArrayBuffer
    const sealBytes = await axios.get(currentSealUrl.value, {
      responseType: 'arraybuffer'
    }).then(res => res.data)

    // 3. 使用 pdf-lib 加载 PDF
    const pdfDocLib = await PDFDocument.load(pdfBytes)
    const sealImage = await pdfDocLib.embedPng(sealBytes)

    // 4. 获取当前页并计算坐标
    const pages = pdfDocLib.getPages()
    const page = pages[currentPage.value - 1]
    const { width, height } = page.getSize()

    const pdfX = (sealX.value / canvasWidth.value) * width
    // PDF Y 是从下往上，需要转换
    const pdfY = height - ((sealY.value + sealHeight.value) / canvasHeight.value) * height

    const pdfSealWidth = (sealWidth.value / canvasWidth.value) * width
    const pdfSealHeight = (sealHeight.value / canvasHeight.value) * height

    // 5. 绘制印章
    page.drawImage(sealImage, {
      x: pdfX,
      y: pdfY,
      width: pdfSealWidth,
      height: pdfSealHeight,
    })

    // 6. 保存生成新的 PDF
    const pdfDataUri = await pdfDocLib.save()
    const blob = new Blob([pdfDataUri], { type: 'application/pdf' })
    const file = new File([blob], `stamped_${currentAuditRow.value.original_file_name}.pdf`, { type: 'application/pdf' })

    // 7. 准备上传数据
    const fd = new FormData()
    fd.append('stamped_file', file)

    // 构造日志数据
    const logData = [{
      page_number: currentPage.value,
      x: pdfX,
      y: pdfY,
      width: pdfSealWidth,
      height: pdfSealHeight
    }]
    fd.append('log_data_json', JSON.stringify(logData))

    fd.append('reviewer_id', currentUserId)
    fd.append('role', currentUserRole)

    // 8. ⚠调用 POST /applications/{application_id}/confirm 接口
    //    该接口在后端应负责保存文件并更新状态为“已通过”
    await axios.post(`${API_BASE}/applications/${currentAuditRow.value.id}/confirm`, fd)

    ElMessage.success('盖章完成，申请状态已更新为“已通过”')
    showAuditDialog.value = false
    await fetchPendingApplications()

  } catch (err) {
    console.error(err)
    ElMessage.error('盖章合成或上传失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.stamping = false
  }
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
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
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
</style>
