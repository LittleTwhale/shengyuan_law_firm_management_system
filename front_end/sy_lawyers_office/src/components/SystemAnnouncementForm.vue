<template>
  <el-dialog
    :title="isEdit ? '编辑系统公告' : '发布新公告'"
    :model-value="visible"
    width="min(95%, 900px)"
    @close="handleClose"
    :close-on-click-modal="false"
    destroy-on-close
    top="5vh"
    append-to-body
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12">
          <el-form-item label="公告类型" prop="type">
            <el-select v-model="form.type" placeholder="请选择类型" style="width: 100%">
              <el-option label="系统更新日志" value="update_log" />
              <el-option label="常规系统公告" value="general_notice" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-form-item label="关联版本号" prop="version">
            <el-input v-model="form.version" placeholder="例如：1.2.0 (常规公告可不填)" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="公告标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入核心标题，例如：v1.2.0 上线啦" />
      </el-form-item>

      <el-form-item label="正文内容" prop="content">
        <div style="border: 1px solid #ccc; width: 100%; z-index: 1000">
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

      <el-form-item label="是否立即发布" prop="is_active">
        <el-switch v-model="form.is_active" active-text="发布" inactive-text="草稿" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        {{ isEdit ? '保存修改' : '立即发布' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, shallowRef, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

import '@wangeditor/editor/dist/css/style.css'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'

const props = defineProps({
  visible: Boolean,
  editData: Object,
})
const emit = defineEmits(['update:visible', 'refresh'])

const formRef = ref(null)
const submitting = ref(false)
const noticeId = ref(null)

// --- WangEditor 配置 ---
const editorRef = shallowRef()
const toolbarConfig = {}
const editorConfig = ref({
  placeholder: '请输入公告正文...',
  MENU_CONF: {
    uploadImage: {
      // 复用党建模块的图片上传接口即可，或者你后端新建一个公共的 /upload_image 接口
      server: request.defaults.baseURL + '/party_building/upload_image',
      fieldName: 'file',
      maxFileSize: 5 * 1024 * 1024,
      headers: {
        Authorization: 'Bearer ' + localStorage.getItem('token'),
      },
      onFailed(file, res) {
        console.error(res)
        ElMessage.error(`${file.name} 上传失败`)
      },
      onError(file, err) {
        console.error(err)
        ElMessage.error(`${file.name} 上传出错`)
      },
    },
  },
})

onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})

const handleEditorCreated = (editor) => {
  editorRef.value = editor
}
// --- 结束 WangEditor 配置 ---

const form = reactive({
  type: 'update_log',
  title: '',
  version: '',
  content: '',
  is_active: true,
})

const rules = {
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

const isEdit = computed(() => !!props.editData)

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.editData) {
        noticeId.value = props.editData.id
        form.type = props.editData.type
        form.title = props.editData.title
        form.version = props.editData.version || ''
        form.content = props.editData.content || ''
        form.is_active = props.editData.is_active
      } else {
        noticeId.value = null
        form.type = 'update_log'
        form.title = ''
        form.version = ''
        form.content = ''
        form.is_active = true
      }
    }
  },
)

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (noticeId.value) {
        await request.put(`/system/announcements/${noticeId.value}`, form)
        ElMessage.success('公告已更新')
      } else {
        await request.post('/system/announcements', form)
        ElMessage.success('公告已发布')
      }
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
</script>

<style scoped>
.w-e-modal {
  z-index: 9999 !important;
}
</style>
