<template>
  <div class="party-container">
    <el-container style="height: 100%">
      <el-aside width="240px" class="category-aside">
        <div class="aside-header">
          <span>资料分类</span>
          <el-button
            v-if="isAdmin"
            type="primary"
            link
            icon="Plus"
            size="small"
            @click="openCategoryDialog()"
          >
            管理
          </el-button>
        </div>
        <el-menu
          :default-active="String(activeCategoryId)"
          class="category-menu"
          @select="handleCategorySelect"
        >
          <el-menu-item index="0">
            <el-icon><Menu /></el-icon>
            <span>全部资料</span>
          </el-menu-item>
          <el-menu-item v-for="cat in categories" :key="cat.id" :index="String(cat.id)">
            <el-icon><Document /></el-icon>
            <span>{{ cat.name }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-content">
        <div class="header">
          <h2>党建资料库</h2>
          <div class="action-buttons">
            <el-button v-if="isAdmin" type="primary" icon="Plus" @click="openMaterialDialog()">
              发布资料
            </el-button>
          </div>
        </div>

        <div class="toolbar">
          <div class="toolbar-left">
            <div class="mobile-category-select">
              <div style="display: flex; gap: 10px; margin-bottom: 10px; width: 100%">
                <el-select
                  v-model="activeCategoryId"
                  @change="handleCategorySelect"
                  placeholder="选择分类"
                  style="flex: 1"
                >
                  <el-option label="全部资料" :value="0" />
                  <el-option
                    v-for="cat in categories"
                    :key="cat.id"
                    :label="cat.name"
                    :value="cat.id"
                  />
                </el-select>
                <el-button
                  v-if="isAdmin"
                  type="primary"
                  plain
                  icon="Setting"
                  @click="openCategoryDialog()"
                >
                  管理
                </el-button>
              </div>
            </div>

            <el-input
              v-model="queryParams.search"
              placeholder="搜索标题或文号"
              prefix-icon="Search"
              clearable
              class="responsive-search"
              @clear="fetchMaterials"
              @keyup.enter="fetchMaterials"
            />
          </div>
        </div>

        <el-table :data="materials" v-loading="loading" stripe border style="width: 100%">
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="link-text" @click="viewDetail(row)">{{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="document_number"
            label="文号"
            width="220"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="category.name" label="分类" width="180" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.category?.name || '无' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="publisher_name" label="发布人" width="150" align="center" />
          <el-table-column prop="view_count" label="阅读量" width="100" align="center" />
          <el-table-column prop="created_at" label="发布时间" width="200" align="center">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right" align="center" v-if="isAdmin">
            <template #default="{ row }">
              <el-button link type="primary" @click="openMaterialDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteMaterial(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.limit"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="fetchMaterials"
          />
        </div>
      </el-main>
    </el-container>

    <PartyMaterialForm
      v-model:visible="showMaterialDialog"
      :edit-data="currentMaterial"
      :categories="categories"
      @refresh="fetchMaterials"
    />

    <el-dialog title="分类管理" v-model="showCategoryDialog" width="min(95%, 500px)">
      <div class="category-manage-body">
        <el-table :data="categories" border size="small">
          <el-table-column prop="name" label="名称">
            <template #default="{ row }">
              <el-input v-if="row.isEdit" v-model="row.editName" size="small" />
              <span v-else>{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="权重" width="80">
            <template #default="{ row }">
              <el-input-number
                v-if="row.isEdit"
                v-model="row.editSort"
                size="small"
                :controls="false"
                style="width: 100%"
              />
              <span v-else>{{ row.sort_order }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <div v-if="row.isEdit">
                <el-button link type="success" @click="saveCategory(row)">保存</el-button>
                <el-button link type="info" @click="row.isEdit = false">取消</el-button>
              </div>
              <div v-else>
                <el-button link type="primary" @click="startEditCategory(row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteCategory(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div class="add-cat-row">
          <el-input
            v-model="newCategory.name"
            placeholder="新分类名称"
            style="width: 200px; margin-right: 10px"
          />
          <span>权重：</span>
          <el-input-number
            v-model="newCategory.sort_order"
            placeholder="请输入"
            :min="0"
            style="width: 100px; margin-right: 10px"
          />
          <el-button type="primary" @click="handleAddCategory">添加新分类</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Menu, Document } from '@element-plus/icons-vue'
import request from '@/utils/request' // 直接引入 request 工具
import PartyMaterialForm from './PartyMaterialForm.vue'

const router = useRouter()
const currentUserId = localStorage.getItem('user_id')
const isAdmin = ref(false)

// 状态
const categories = ref([])
const activeCategoryId = ref(0)
const materials = ref([])
const loading = ref(false)
const total = ref(0)

const queryParams = reactive({
  page: 1,
  limit: 15,
  search: '',
})

// 弹窗控制
const showMaterialDialog = ref(false)
const currentMaterial = ref(null)
const showCategoryDialog = ref(false)
const newCategory = reactive({ name: '', sort_order: 0 })

// 初始化
onMounted(async () => {
  await fetchUserProfile()
  await fetchCategories()
  await fetchMaterials()
})

// 获取用户详情并判断细粒度权限
const fetchUserProfile = async () => {
  try {
    const res = await request.get(`/user/profile/info?user_id=${currentUserId}`)
    const user = res.data
    // 逻辑：如果是拥有者(owner) 或者 权限列表里 party_admin 为 true
    isAdmin.value =
      user.role === 'owner' || (user.permissions && user.permissions.party_admin === true)
  } catch (err) {
    console.error('获取用户信息失败', err)
    // 失败时保持默认 false，或者根据业务需求处理
  }
}

// 获取分类
const fetchCategories = async () => {
  try {
    const res = await request.get('/party_building/categories', {
      params: { active_only: !isAdmin.value },
    })
    categories.value = res.data
  } catch (error) {
    console.error(error)
  }
}

// 获取资料列表
const fetchMaterials = async () => {
  loading.value = true
  try {
    const params = {
      skip: (queryParams.page - 1) * queryParams.limit,
      limit: queryParams.limit,
      search: queryParams.search,
      category_id: activeCategoryId.value === 0 ? null : activeCategoryId.value,
    }
    const res = await request.get('/party_building/materials', { params })
    materials.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error(error)
    ElMessage.error('获取资料列表失败')
  } finally {
    loading.value = false
  }
}

// 切换分类
const handleCategorySelect = (index) => {
  activeCategoryId.value = Number(index)
  queryParams.page = 1
  fetchMaterials()
}

// 打开文章编辑/新增
const openMaterialDialog = (row = null) => {
  currentMaterial.value = row
  showMaterialDialog.value = true
}

// 查看详情 (跳转新页面)
const viewDetail = (row) => {
  const routeUrl = router.resolve({
    path: `/main/party_building/detail/${row.id}`,
  })
  window.open(routeUrl.href, '_blank')
}

// 删除文章
const handleDeleteMaterial = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该资料及其附件吗？', '警告', { type: 'warning' })
    await request.delete(`/party_building/materials/${row.id}`)
    ElMessage.success('删除成功')
    await fetchMaterials()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// ============= 分类管理逻辑 =============
const openCategoryDialog = () => {
  showCategoryDialog.value = true
  newCategory.name = ''
  newCategory.sort_order = 0
}

const handleAddCategory = async () => {
  if (!newCategory.name) return ElMessage.warning('请输入名称')
  try {
    await request.post('/party_building/categories', {
      ...newCategory,
      is_active: true,
    })
    ElMessage.success('添加成功')
    newCategory.name = ''
    await fetchCategories()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

const startEditCategory = (row) => {
  row.isEdit = true
  row.editName = row.name
  row.editSort = row.sort_order
}

const saveCategory = async (row) => {
  try {
    await request.put(`/party_building/categories/${row.id}`, {
      name: row.editName,
      sort_order: row.editSort,
    })
    ElMessage.success('更新成功')
    row.isEdit = false
    await fetchCategories()
  } catch (e) {
    console.error(e)
    ElMessage.error('更新失败')
  }
}

const handleDeleteCategory = async (row) => {
  try {
    await ElMessageBox.confirm('删除分类前请确保该分类下无文章。确定删除？', '提示', {
      type: 'warning',
    })
    await request.delete(`/party_building/categories/${row.id}`)
    ElMessage.success('删除成功')
    await fetchCategories()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const formatDate = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleString()
}
</script>

<style scoped>
.party-container {
  height: calc(100vh - 80px);
  background: #fff;
}
.category-aside {
  background-color: #f8f9fa;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
}
.aside-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  font-weight: bold;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fff;
}
.category-menu {
  border-right: none;
  background-color: transparent;
}
.main-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
}

/* 新增：头部样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.link-text {
  color: #409eff;
  cursor: pointer;
}
.link-text:hover {
  text-decoration: underline;
}
.pagination-container {
  margin-top: 20px;
  text-align: right;
}
.add-cat-row {
  margin-top: 15px;
  border-top: 1px dashed #eee;
  padding-top: 15px;
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* 让内部元素在空间不足时换行 */
  gap: 10px;
}

/* 移动端专属样式隐藏与显示 */
.mobile-category-select {
  display: none;
}
.responsive-search {
  width: 300px;
}

/* ============= 响应式/移动端适配 ============= */
@media (max-width: 768px) {
  /* 隐藏左侧边栏 */
  .category-aside {
    display: none !important;
  }

  /* 显示移动端下拉分类 */
  .mobile-category-select {
    display: block;
    width: 100%;
  }

  /* 调整工具栏布局 */
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left {
    display: flex;
    flex-direction: column;
    width: 100%;
  }

  /* 搜索框撑满屏幕 */
  .responsive-search {
    width: 100% !important;
  }

  /* 调整主区域边距 */
  .main-content {
    padding: 10px;
  }

  /* 调整头部字体和布局 */
  .header h2 {
    font-size: 20px;
  }

  /* 分类管理的输入框在移动端占满行 */
  .add-cat-row .el-input,
  .add-cat-row .el-input-number {
    width: 100% !important;
    margin-right: 0 !important;
  }
}
</style>
