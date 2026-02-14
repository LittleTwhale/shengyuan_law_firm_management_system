<template>
  <el-dialog
    :title="isEdit ? '编辑资料' : '发布新资料'"
    :model-value="visible"
    width="900px"
    @close="handleClose"
    :close-on-click-modal="false"
    destroy-on-close
    top="5vh"
    append-to-body
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入文章标题" />
      </el-form-item>

      <el-row>
        <el-col :span="12">
          <el-form-item label="所属分类" prop="category_id">
            <el-select v-model="form.category_id" placeholder="请选择" style="width: 100%">
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="文号" prop="document_number">
            <el-input v-model="form.document_number" placeholder="例如：湘生律党[2023]1号" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="发文单位" prop="issuing_authority">
        <el-input v-model="form.issuing_authority" placeholder="例如：中共湖南省律师行业委员会" />
      </el-form-item>

      <el-form-item label="正文内容" prop="content">
        <div style="border: 1px solid #ccc; width: 100%;z-index: 1000">
          <Toolbar
            style="border-bottom: 1px solid #ccc"
            :editor="editorRef"
            :defaultConfig="toolbarConfig"
            mode="default"
          />
          <Editor
            style="height: 400px; overflow-y: hidden"
            v-model="form.content"
            :defaultConfig="editorConfig"
            mode="default"
            @onCreated="handleEditorCreated"
          />
        </div>
      </el-form-item>

      <el-divider content-position="left">附件管理</el-divider>

      <el-upload
        class="upload-demo"
        drag
        action="#"
        :auto-upload="false"
        multiple
        v-model:file-list="rawFiles"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持 doc, pdf, 图片 等文件格式。选择文件后，点击底部的“保存”按钮会自动上传。
          </div>
        </template>
      </el-upload>

      <div v-if="attachmentList && attachmentList.length > 0" style="margin-top: 20px">
        <p style="font-weight: bold; margin-bottom: 10px; font-size: 14px; color: #606266">
          已归档附件:
        </p>
        <el-table :data="attachmentList" border style="width: 100%" size="small">
          <el-table-column prop="file_name" label="文件名" />
          <el-table-column prop="file_size" label="大小" width="120">
            <template #default="{ row }">{{ (row.file_size / 1024).toFixed(1) }} KB</template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="downloadAttachment(row)">
                下载
              </el-button>
              <el-button link type="danger" size="small" @click="removeAttachment(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        {{ materialId ? '保存修改' : '立即创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, shallowRef, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import request from '@/utils/request'

// 引入 WangEditor
import '@wangeditor/editor/dist/css/style.css'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'

const props = defineProps({
  visible: Boolean,
  editData: Object,
  categories: Array,
})
const emit = defineEmits(['update:visible', 'refresh'])

const formRef = ref(null)
const submitting = ref(false)
const materialId = ref(null)
const attachmentList = ref([]) // 已保存的附件
const rawFiles = ref([]) // 待上传的新文件

// 编辑器实例，必须用 shallowRef
const editorRef = shallowRef()
const toolbarConfig = {}
const editorConfig = {
  placeholder: '请输入内容...',
  MENU_CONF: {
    uploadImage: {
      // 1. 上传图片接口地址
      server: request.defaults.baseURL + '/party_building/upload_image',

      // 2. 后端接收的字段名 (对应 fastapi 的 file: UploadFile = File(...))
      fieldName: 'file',

      // 3. 限制文件大小 (例如 5M)
      maxFileSize: 5 * 1024 * 1024,

      // 4. 请求头 (鉴权)
      headers: {
        Authorization: 'Bearer ' + localStorage.getItem('token'), // 务必带上 Token
      },

      // 5. 自定义插入图片 (可选，如果你后端返回格式符合 WangEditor 标准则不需要此项)
      // WangEditor 默认支持的格式就是你后端返回的 { errno: 0, data: { url: '...' } }
      // 所以这里通常不需要 customInsert

      // 错误处理
      onFailed(file, res) {
        ElMessage.error(`${file.name} 上传失败`)
        console.error(res)
      },
      onError(file, err) {
        ElMessage.error(`${file.name} 上传出错`)
        console.error(err)
      },
    },
  },
}

// 组件销毁时，也及时销毁编辑器
onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})

const handleEditorCreated = (editor) => {
  editorRef.value = editor // 记录 editor 实例，重要！
}

const form = reactive({
  title: '',
  category_id: null,
  document_number: '',
  issuing_authority: '',
  content: '', // 绑定富文本内容
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

const isEdit = computed(() => !!props.editData)

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.editData) {
        // 编辑模式回填
        materialId.value = props.editData.id
        form.title = props.editData.title
        form.category_id = props.editData.category_id
        form.document_number = props.editData.document_number
        form.issuing_authority = props.editData.issuing_authority
        form.content = props.editData.content
        attachmentList.value = props.editData.attachments || []
      } else {
        // 新增模式重置
        materialId.value = null
        Object.keys(form).forEach((k) => (form[k] = ''))
        if (props.categories.length > 0) form.category_id = props.categories[0].id
        attachmentList.value = []
      }
      // 每次打开清空待上传列表
      rawFiles.value = []
    }
  },
)

const handleClose = () => {
  emit('update:visible', false)
  rawFiles.value = []
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      let targetId = materialId.value

      // 1. 保存/更新资料基础信息
      if (targetId) {
        // 更新资料
        await request.put(`/party_building/materials/${targetId}`, form)
        ElMessage.success('基础信息已保存')
      } else {
        // 创建资料
        const res = await request.post('/party_building/materials', form)
        targetId = res.data.id
        materialId.value = targetId // 更新当前ID
      }

      // 2. 处理附件上传 (仿 CaseForm 逻辑)
      if (rawFiles.value.length > 0 && targetId) {
        const uploadPromises = rawFiles.value.map((fileItem) => {
          const fd = new FormData()
          // Element Plus 的 file-list 中，真实文件在 .raw 属性
          const file = fileItem.raw || fileItem

          fd.append('file', file)
          fd.append('material_id', targetId)
          // 假设后端接口不需要 uploaded_by，如果需要可自行添加

          // 使用 request 实例发送上传请求
          return request.post('/party_building/attachments', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
        })

        try {
          await Promise.all(uploadPromises)
          ElMessage.success(`成功上传 ${rawFiles.value.length} 个附件`)
        } catch (uploadErr) {
          console.error('部分附件上传失败', uploadErr)
          ElMessage.warning('资料已保存，但部分附件上传失败，请检查')
        }
      }

      // 3. 完成流程
      emit('refresh')
      handleClose()
    } catch (e) {
      console.error(e)
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 附件相关操作
const downloadAttachment = async (row) => {
  try {
    ElMessage.info('正在请求下载...')

    // 1. 请求二进制流 (注意 responseType: 'blob')
    const res = await request.get(`/party_building/attachments/${row.id}/download`, {
      responseType: 'blob',
    })

    // 2. 创建 Blob 对象
    const blob = new Blob([res.data])

    // 3. 创建下载链接
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = row.file_name // 使用后端返回的文件名或数据库保存的文件名
    link.style.display = 'none'

    // 4. 触发点击并清理
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href) // 释放内存

    ElMessage.success('下载开始')
  } catch (error) {
    console.error('下载失败', error)
    ElMessage.error('下载失败')
  }
}

const removeAttachment = async (row) => {
  try {
    await ElMessageBox.confirm('确定要永久删除该附件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    // 调用删除附件 API
    await request.delete(`/party_building/attachments/${row.id}`)
    attachmentList.value = attachmentList.value.filter((item) => item.id !== row.id)
    ElMessage.success('附件已删除')
  } catch (e) {
    if (e !== 'cancel') {
      console.log(e)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.upload-demo {
  margin-top: 10px;
}
/* 强制提升 WangEditor 弹窗 (Modal) 的层级。
  Element Plus 的 Dialog z-index 通常是 2000+，所以这里设置一个很高的值（如 9999）。
*/
.w-e-modal {
  z-index: 9999 !important;
}
</style>
