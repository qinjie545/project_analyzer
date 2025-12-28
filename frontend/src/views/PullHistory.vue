<template>
  <div>
    <h2>项目拉取 - 历史</h2>
    <el-card class="box-card" shadow="hover">
      <el-table :data="items" style="width: 100%">
        <el-table-column prop="name" label="项目" min-width="220">
          <template #default="{ row }">
            <a :href="row.url" target="_blank">{{ row.name }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="pullTime" label="拉取时间" width="180" />
        <el-table-column prop="stars" label="Stars" width="100" />
        <el-table-column prop="forks" label="Forks" width="100" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="rePull(row)">重新拉取</el-button>
            <el-button size="small" type="primary" @click="openDir(row)">打开目录</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const items = ref([])

async function loadHistory() {
  try {
    const r = await api.getPullRecords({ page: 1, pageSize: 100 })
    items.value = (r.data && r.data.data) || []
  } catch (e) {
    ElMessage.error('加载历史记录失败')
  }
}

onMounted(() => {
  loadHistory()
})

async function rePull(row) {
  try {
    await api.rePull({ id: row.id })
    ElMessage.success(`已触发重新拉取：${row.name}`)
    loadHistory()
  } catch (e) {
    ElMessage.error('重新拉取失败')
  }
}
function openDir(row) {
  // 前端无法直接打开本地目录，这里提示路径，实际可通过后端打开或返回静态浏览链接
  ElMessage.success(`项目目录：${row.path}`)
}
</script>
