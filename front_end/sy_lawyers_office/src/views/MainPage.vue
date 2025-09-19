<template>
  <div class="dashboard-container">
    <!-- 顶部栏 -->
    <header class="top-bar">
      <div class="logo-section">
        <img src="@/assets/img/logo.png" alt="湖南生元律师事务所Logo" class="logo-image">
      </div>
      <div class="user-section">
        <span>{{ currentUser }}</span>
        <el-button type="text" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="main-content">
      <!-- 左侧导航栏 -->
      <el-menu
        class="sidebar"
        :default-active="activeMenu"
        router
        background-color="#165DFF"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item index="cases" @click="switchTab('cases')">
          <i class="el-icon-document"></i>
          <span>案件管理</span>
        </el-menu-item>
        <el-menu-item index="lawyers" @click="switchTab('lawyers')">
          <i class="el-icon-user"></i>
          <span>律师管理</span>
        </el-menu-item>
        <el-menu-item index="statistics" @click="switchTab('statistics')">
          <i class="el-icon-data-analysis"></i>
          <span>统计分析</span>
        </el-menu-item>
      </el-menu>

      <!-- 右侧操作区 -->
      <div class="content-area">
        <!-- 案件管理 -->
        <div v-if="activeTab === 'cases'">
          <div class="content-header">
            <h2>案件管理</h2>
            <el-button type="primary" @click="showAddCaseDialog = true">新增案件</el-button>
          </div>
          <el-table :data="caseList" border style="width:100%">
            <el-table-column prop="id" label="案件编号" width="100"/>
            <el-table-column prop="type" label="案件类型" width="120"/>
            <el-table-column prop="client" label="委托人"/>
            <el-table-column prop="fee" label="收费(元)" width="120"/>
            <el-table-column prop="status" label="状态" width="120"/>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <el-button type="text" size="small" @click="editCase(scope.$index, scope.row)">编辑</el-button>
                <el-button type="text" size="small" @click="deleteCase(scope.$index, scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 新增案件弹窗 -->
          <el-dialog title="新增案件" v-model:visible="showAddCaseDialog" width="500px">
            <el-form :model="newCase" label-width="120px">
              <el-form-item label="案件类型">
                <el-select v-model="newCase.type" placeholder="选择案件类型">
                  <el-option label="民事" value="民事"></el-option>
                  <el-option label="刑事" value="刑事"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="委托人">
                <el-input v-model="newCase.client" placeholder="请输入委托人"></el-input>
              </el-form-item>
              <el-form-item label="收费">
                <el-input v-model="newCase.fee" type="number" placeholder="请输入收费金额"></el-input>
              </el-form-item>
              <el-form-item label="状态">
                <el-select v-model="newCase.status" placeholder="选择状态">
                  <el-option label="待审批" value="待审批"></el-option>
                  <el-option label="进行中" value="进行中"></el-option>
                  <el-option label="已结案" value="已结案"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
            <template v-slot:footer>
<span  class="dialog-footer">
              <el-button @click="showAddCaseDialog=false">取消</el-button>
              <el-button type="primary" @click="addCase">确认</el-button>
            </span>
</template>
          </el-dialog>
        </div>

        <!-- 律师管理 -->
        <div v-if="activeTab === 'lawyers'">
          <div class="content-header">
            <h2>律师管理</h2>
            <el-button type="primary" @click="showAddLawyerDialog = true">新增律师</el-button>
          </div>
          <el-table :data="lawyerList" border style="width:100%">
            <el-table-column prop="id" label="编号" width="100"/>
            <el-table-column prop="name" label="姓名"/>
            <el-table-column prop="username" label="账号"/>
            <el-table-column prop="role" label="角色" width="120"/>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <el-button type="text" size="small" @click="editLawyer(scope.$index, scope.row)">编辑</el-button>
                <el-button type="text" size="small" @click="deleteLawyer(scope.$index, scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 新增律师弹窗 -->
          <el-dialog title="新增律师" v-model:visible="showAddLawyerDialog" width="500px">
            <el-form :model="newLawyer" label-width="100px">
              <el-form-item label="姓名">
                <el-input v-model="newLawyer.name"></el-input>
              </el-form-item>
              <el-form-item label="账号">
                <el-input v-model="newLawyer.username"></el-input>
              </el-form-item>
              <el-form-item label="角色">
                <el-select v-model="newLawyer.role">
                  <el-option label="律师" value="律师"></el-option>
                  <el-option label="管理员" value="管理员"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
            <template v-slot:footer>
<span  class="dialog-footer">
              <el-button @click="showAddLawyerDialog=false">取消</el-button>
              <el-button type="primary" @click="addLawyer">确认</el-button>
            </span>
</template>
          </el-dialog>
        </div>

        <!-- 统计分析 -->
        <div v-if="activeTab==='statistics'">
          <h2>统计分析</h2>
          <el-card>
            <p>案件总数: {{caseList.length}}</p>
            <p>总收费: {{totalFee}}</p>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

const router = useRouter();
const currentUser = ref('张律师');
const activeMenu = ref('cases');
const activeTab = ref('cases');

const switchTab = (tab) => { activeTab.value = tab; activeMenu.value = tab; };

// 案件管理
const showAddCaseDialog = ref(false);
const newCase = reactive({ type:'', client:'', fee:0, status:'待审批' });
const caseList = ref([
  { id:1, type:'民事', client:'王小明', fee:5000, status:'进行中' },
  { id:2, type:'刑事', client:'李四', fee:8000, status:'待审批' }
]);
const addCase = () => {
  if(!newCase.type||!newCase.client){ElMessage.warning('请完整填写案件信息');return;}
  const id = caseList.value.length?caseList.value[caseList.value.length-1].id+1:1;
  caseList.value.push({id,...newCase});
  ElMessage.success('案件添加成功');
  showAddCaseDialog.value=false;
  newCase.type=''; newCase.client=''; newCase.fee=0; newCase.status='待审批';
};
const editCase=(i,row)=>{ElMessage.info(`编辑案件 ${row.id} 功能待实现`);};
const deleteCase=(i,row)=>{caseList.value.splice(i,1);ElMessage.success(`案件 ${row.id} 已删除`);};

// 律师管理
const showAddLawyerDialog = ref(false);
const newLawyer = reactive({name:'',username:'',role:'律师'});
const lawyerList = ref([
  {id:1,name:'张律师',username:'zhang',role:'律师'},
  {id:2,name:'李律师',username:'li',role:'律师'}
]);
const addLawyer=()=>{
  if(!newLawyer.name||!newLawyer.username){ElMessage.warning('请完整填写律师信息');return;}
  const id = lawyerList.value.length?lawyerList.value[lawyerList.value.length-1].id+1:1;
  lawyerList.value.push({id,...newLawyer});
  ElMessage.success('律师添加成功'); showAddLawyerDialog.value=false;
  newLawyer.name=''; newLawyer.username=''; newLawyer.role='律师';
};
const editLawyer=(i,row)=>{ElMessage.info(`编辑律师 ${row.name} 功能待实现`);};
const deleteLawyer=(i,row)=>{lawyerList.value.splice(i,1);ElMessage.success(`律师 ${row.name} 已删除`);};

// 统计
const totalFee = computed(()=>caseList.value.reduce((sum,c)=>sum+c.fee,0));

// 登出
const handleLogout=()=>{router.push('/'); ElMessage.info('已退出登录');};
</script>

<style scoped>
.dashboard-container {
  display:flex;
  flex-direction:column;
  height:100vh;
}
.top-bar{
  display:flex;
  justify-content:space-between;
  align-items:center;height:60px;
  background-color:#165DFF;
  color:#fff;padding:0 20px;
}
.logo-section{
  display:flex;
  align-items:center;
}
.logo-image{
  width:200px;
  height:50px;
  margin-right:10px;
  object-fit:contain;
}
.firm-name{
  font-size:18px;
  font-weight:600;
}
.user-section span{
  margin-right:10px;
}
.main-content{
  display:flex;
  flex:1;
  overflow:hidden;
}
.sidebar{
  width:200px;
  min-width:200px;
  height:100%;
}
.content-area{
  flex:1;
  padding:20px;
  overflow-y:auto;
}
.content-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}
</style>
