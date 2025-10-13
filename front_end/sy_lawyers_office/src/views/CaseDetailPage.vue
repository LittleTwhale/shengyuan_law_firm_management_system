<template>
  <div class="case-detail">
    <!-- 顶部返回栏 -->
    <el-page-header @back="goBack" title="返回" />

    <!-- 居中标题 -->
    <h2 class="page-title">案件详情</h2>

    <el-card class="detail-card" v-loading="loading">
      <!-- 案件基本信息 -->
      <el-descriptions title="案件基本信息" :column="2" border>
        <el-descriptions-item label="案件号">{{ caseData.case_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件类别">{{ caseData.case_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="委托日期">{{ formatDate(caseData.commission_date) }}</el-descriptions-item>
        <el-descriptions-item label="委托人">{{ caseData.client_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="身份证号/单位税号">{{ caseData.client_id_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ caseData.client_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件来源">{{ caseData.case_source || '-' }}</el-descriptions-item>
        <el-descriptions-item label="介入阶段">{{ caseData.stage || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案由">{{ caseData.cause || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 收费信息 -->
      <el-descriptions title="费用信息" :column="2" border>
        <el-descriptions-item label="收费方式">{{ caseData.fee_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件收入">
          {{ caseData.case_income ? `${caseData.case_income} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="风险比例">{{ caseData.risk_ratio || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 律师信息 -->
      <el-descriptions title="律师信息" :column="2" border>
        <el-descriptions-item label="主办律师">{{ caseData.main_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="助理律师">{{ caseData.assistant_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行律师">{{ caseData.execution_lawyer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行助理">{{ caseData.execution_assistant?.real_name || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 系统信息 -->
      <el-descriptions title="系统信息" :column="2" border>
        <el-descriptions-item label="创建时间">{{ formatDateTime(caseData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(caseData.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 诉讼信息 -->
      <el-descriptions title="诉讼信息" :column="2" border>
        <el-descriptions-item label="原告">{{ caseData.plaintiff || '-' }}</el-descriptions-item>
        <el-descriptions-item label="被告">{{ caseData.defendant || '-' }}</el-descriptions-item>
        <el-descriptions-item label="代理权限">{{ caseData.agency_power || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审理法院">{{ caseData.court || '-' }}</el-descriptions-item>
        <el-descriptions-item label="立案日">{{ formatDate(caseData.filing_date) }}</el-descriptions-item>
        <el-descriptions-item label="开庭时间">{{ formatDate(caseData.hearing_date) }}</el-descriptions-item>
        <el-descriptions-item label="结案时间">{{ formatDate(caseData.closing_date) }}</el-descriptions-item>
        <el-descriptions-item label="结案状态">{{ caseData.closing_status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结案方式">{{ caseData.closing_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件地点">{{ caseData.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="案件详情">
          <div class="case-detail-content" v-text="caseData.details || '-'"></div>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 保全与状态 -->
      <el-descriptions title="案件状态" :column="2" border>
        <el-descriptions-item label="审核状态">{{ caseData.review_status }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ caseData.reviewer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否重大">{{ caseData.is_major ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否解除">{{ caseData.is_dismissed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否纸质卷宗">{{ caseData.has_paper_file ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否笔录">{{ caseData.has_record ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否保全">{{ caseData.has_preservation ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="保全开始日">{{ formatDate(caseData.preservation_start) }}</el-descriptions-item>
        <el-descriptions-item label="保全终止日">{{ formatDate(caseData.preservation_end) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 费用与执行 -->
      <el-descriptions title="费用与执行信息" :column="2" border>
        <el-descriptions-item label="诉讼费缴费时间">{{ formatDate(caseData.litigation_fee_payment_date) }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费缴费金额">
          {{ caseData.litigation_fee_payment_amount ? `${caseData.litigation_fee_payment_amount} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="诉讼费退费时间">{{ formatDate(caseData.litigation_fee_refund_date) }}</el-descriptions-item>
        <el-descriptions-item label="诉讼费退费金额">
          {{ caseData.litigation_fee_refund_amount ? `${caseData.litigation_fee_refund_amount} 元` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="申请执行日">{{ formatDate(caseData.execution_application_date) }}</el-descriptions-item>
        <el-descriptions-item label="调解到期日">{{ formatDate(caseData.mediation_due_date) }}</el-descriptions-item>
        <el-descriptions-item label="执行到期日">{{ formatDate(caseData.execution_due_date) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 附件信息区域 -->
      <el-descriptions title="案件附件" border>
        <el-descriptions-item label="附件列表" :column="1">
          <div class="attachment-list">


            <div v-if="attachments.length === 0 && !loadingAttachments" class="no-attachments">
              暂无附件
            </div>

            <el-table
              v-if="attachments.length > 0"
              :data="attachments"
              border
              style="width: 100%; margin-top: 10px"
            >
              <el-table-column prop="file_name" label="文件名" />
              <el-table-column
                prop="uploader"
                label="上传人"
                :formatter= "(row) => row.uploader?.real_name || '-' "
              />
              <el-table-column
                prop="file_size"
                label="文件大小(KB)"
                :formatter="formatFileSize"
              />
              <el-table-column
                prop="uploaded_at"
                label="上传时间"
                :formatter="(row, column, cellValue) => formatDateTime(cellValue)"
              />
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button
                    size="small"
                    @click="previewAttachment(scope.row)"
                  >
                    预览
                  </el-button>
                  <el-button
                    size="small"
                    @click="downloadAttachment(scope.row.attachment_id)"
                  >
                    下载
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-descriptions-item>
      </el-descriptions>

    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const caseData = ref({})
const loading = ref(false)
const caseId = route.params.id

// 附件相关变量
const attachments = ref([])
const attachmentFileList = ref([])
const loadingAttachments = ref(false)

const goBack = () => {
  // 从路由状态中获取来源页面路径，默认返回案件管理页面
  const fromPath = route.query.from || '/main/cases'
  router.push(fromPath)
}

const loadCaseDetail = async () => {
  loading.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:8002/cases/${caseId}`)
    caseData.value = res.data || {}

    // 权限判断逻辑
    const role = sessionStorage.getItem('role')
    const currentUserId = sessionStorage.getItem('user_id')
    const mainLawyerId = caseData.value.main_lawyer?.id

    if (role === 'user' && mainLawyerId && String(mainLawyerId) !== String(currentUserId)) {
      ElMessage.error('您没有权限查看此案件')
      await router.push('/main/cases')
    } else {
      // 加载案件附件
      await loadAttachments()
    }
  } catch (err) {
    console.error('加载案件详情失败:', err)
    ElMessage.error('加载案件详情失败')
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
    const res = await axios.get(`http://127.0.0.1:8002/attachments/case/${caseId}`)
    attachments.value = res.data
    // 转换为上传组件需要的格式
    attachmentFileList.value = res.data.map(item => ({
      name: item.file_name,
      url: `/attachments/${item.attachment_id}/download`,
      uid: item.attachment_id
    }))
  } catch (err) {
    console.error('加载附件失败:', err)
    ElMessage.error('加载附件失败')
  } finally {
    loadingAttachments.value = false
  }
}

// 文件大小转换为MB的方法
const formatFileSize = (row) => {
  // 假设file_size单位是字节，转换为MB并保留两位小数
  if (!row.file_size) return '0 MB';
  const mbSize = row.file_size / (1024 * 1024);
  return mbSize.toFixed(2) + ' MB';
};

// 下载附件
const downloadAttachment = (attachmentId) => {
  window.open(`http://127.0.0.1:8002/attachments/${attachmentId}/download`, '_blank')
}

// 预览附件
const previewAttachment = (attachment) => {
  // 根据文件类型决定预览方式
  const fileType = attachment.file_type || '';

  // 对于图片类型，可以直接在新窗口打开
  if (fileType.startsWith('image/')) {
    window.open(`http://127.0.0.1:8002/attachments/${attachment.attachment_id}/preview`, '_blank');
    return;
  }

  // 对于PDF文件，可以使用浏览器内置预览
  if (fileType === 'application/pdf') {
    window.open(`http://127.0.0.1:8002/attachments/${attachment.attachment_id}/preview`, '_blank');
    return;
  }

  // 对于Office文档，可以提示无法直接预览或使用第三方服务
  ElMessage.info('该文件类型不支持直接预览，建议下载查看');
};

onMounted(() => {
  loadCaseDetail()
})

const formatDate = (dateVal) => {
  if (!dateVal) return '-'
  const date = new Date(dateVal)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const formatDateTime = (dateVal) => {
  if (!dateVal) return '';

  let timestamp;

  // 处理时间戳（数字类型）
  if (typeof dateVal === 'number') {
    // 处理秒级时间戳（如果是10位数字）
    if (dateVal.toString().length === 10) {
      dateVal *= 1000;
    }
    timestamp = dateVal;
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
      dateVal
    ];

    // 尝试各种格式，找到能正确解析的
    for (const fmt of formats) {
      const tempDate = new Date(fmt);
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime();
        break;
      }
    }
  }
  // 处理Date对象
  else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime();
  }

  // 验证时间戳是否有效
  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal);
    return '无效日期';
  }

  const date = new Date(timestamp);

  // 使用toLocaleString()同时显示日期和时间
  // 可以通过参数自定义格式，例如：
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false // 24小时制
  });
}
</script>

<style scoped>
.case-detail {
  padding: 20px;
}
.detail-card {
  margin-top: 10px;
}
/* 居中标题样式 */
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
/* 案件详情文本换行样式 */
.case-detail-content {
  white-space: pre-line; /* 保留换行符，自动处理空格和宽度 */
  line-height: 1.8; /* 增加行高，提升长文本可读性 */
  color: #444; /* 可选：调整文本颜色，区分于标签 */
  padding: 5px 0; /* 可选：增加上下内边距，避免与其他内容拥挤 */
}
/* 附件列表样式 */
.attachment-list {
  margin-top: 10px;
}
.no-attachments {
  color: #999;
  padding: 10px;
  text-align: center;
}
</style>
