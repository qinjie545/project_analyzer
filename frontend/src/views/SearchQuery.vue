<template>
  <div>
    <h2>信息查询 - 搜索查询</h2>
    <el-card shadow="hover">
      <div class="toolbar">
        <el-input v-model="q" placeholder="输入关键字" clearable @keyup.enter="search" />
        <el-button type="primary" @click="search">搜索</el-button>
        <span class="hint">默认显示 {{limit}} 条</span>
      </div>
      <el-table :data="results" style="width:100%">
        <el-table-column prop="name" label="项目" min-width="220">
          <template #default="{ row }">
            <a :href="row.url" target="_blank">{{ row.name }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="stars" label="Stars" width="100" />
        <el-table-column prop="forks" label="Forks" width="100" />
        <el-table-column prop="desc" label="描述" min-width="240" />
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const q = ref('')
const limit = ref(50)
const results = ref([])

async function search(){
  try {
    const r = await api.getPullRecords({ page: 1, pageSize: limit.value, keyword: q.value })
    const rows = (r.data && r.data.data) || []
    results.value = rows.map(item => ({
      ...item,
      desc: item.summary || ''
    }))
  } catch (e) {
    ElMessage.error('搜索失败')
  }
}
</script>
<style scoped>
.toolbar{ display:flex; gap:10px; align-items:center; margin-bottom:12px; }
.hint{ color:#909399; font-size:12px; }
</style>
