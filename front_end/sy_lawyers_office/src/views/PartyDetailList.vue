<template>
  <div v-if="parties && parties.length > 0">
    <div v-for="(p, index) in parties" :key="p.id" class="party-item">
      <span class="party-index">{{ index + 1 }}.</span>

      <template v-if="showBadge && p.party_type">
        <span v-if="theme === 'primary'" class="party-role-badge">{{ p.party_type }}</span>
        <span v-else-if="theme === 'warning'" class="party-role-badge warning">{{
          p.party_type
        }}</span>
        <el-tag
          v-else-if="theme === 'purple'"
          size="small"
          color="#ebdcfc"
          style="color: #6d14d7; border-color: #6d14d7; margin-right: 5px"
        >
          {{ p.party_type }}
        </el-tag>
        <span v-else-if="theme === 'info'" class="party-role-badge info">{{ p.party_type }}</span>
      </template>

      <span class="party-name">{{ p.name }}</span>

      <span class="party-tag" v-if="p.phone">
        <el-icon><Phone /></el-icon> {{ p.phone }}
      </span>
      <span class="party-tag" v-if="p.id_number">
        <el-icon><Postcard /></el-icon> {{ p.id_number }}
      </span>
      <span class="party-address" v-if="p.address"> (地址: {{ p.address }}) </span>
      <span class="party-address" v-if="p.legal_representative">
        [法人: {{ p.legal_representative }}]
      </span>
    </div>
  </div>
  <span v-else>{{ emptyText }}</span>
</template>

<script setup>
import { Phone, Postcard } from '@element-plus/icons-vue' // 引入图标

defineProps({
  parties: {
    type: Array,
    default: () => [],
  },
  showBadge: {
    type: Boolean,
    default: true,
  },
  // 主题：primary (蓝), warning (黄), purple (紫), info (灰)
  theme: {
    type: String,
    default: 'primary',
  },
  // 当数组为空时显示的占位文本
  emptyText: {
    type: String,
    default: '-',
  },
})
</script>

<style scoped>
/* 新增当事人列表样式 (从原页面抽离) */
.party-item {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #eee;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.party-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}
.party-index {
  color: #999;
  font-weight: bold;
}
.party-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
}
.party-tag {
  font-size: 13px;
  color: #666;
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.party-role-badge {
  font-size: 12px;
  background-color: #ecf5ff;
  color: #409eff;
  border: 1px solid #d9ecff;
  padding: 0 5px;
  border-radius: 4px;
}
.party-role-badge.warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border-color: #faecd8;
}
.party-role-badge.info {
  background-color: #f4f4f5;
  color: #909399;
  border-color: #e9e9eb;
}
.party-address {
  font-size: 12px;
  color: #999;
}
</style>
