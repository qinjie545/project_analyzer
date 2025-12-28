<template>
  <div>
    <h2>文章制作 - 制作任务</h2>
    <el-card shadow="hover">
      <el-table :data="tasks" style="width:100%">
        <el-table-column prop="id" label="任务ID" width="220" />
        <el-table-column prop="repo_name" label="项目名称" min-width="180">
          <template #default="{ row }">
            {{ row.repo_name || row.input_ref || '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="createdAt" label="创建时间" width="200" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="viewLog(row)">查看日志</el-button>
            <el-button size="small" type="primary" @click="retry(row)">重新制作</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="logVisible" title="制作日志" width="60%">
      <pre class="log">{{ currentLog }}</pre>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

import api from '@/api'

const tasks = ref([])
const logVisible = ref(false)
const currentLog = ref('')

async function refresh() {
  const r = await api.getMakeTasks()
  tasks.value = (r.data && r.data.data) || []
}

onMounted(()=>{
  refresh()
})
async function viewLog(row){
  try {
    const res = await api.getMakeLogs(row.id)
    currentLog.value = (res.data && res.data.data && res.data.data.log) || '暂无日志'
  } catch (e) {
    currentLog.value = '获取日志失败'
  }
  logVisible.value = true
}
async function retry(row){
  try {
    // Use input_ref as pull_record_id if it's numeric, else repo_name
    const payload = {}
    if (/^\d+$/.test(row.input_ref)) {
      payload.pull_record_id = row.input_ref
    } else {
      payload.repo_name = row.repo_name || row.input_ref
    }
    
    await api.createArticleTask(payload)
    ElMessage.success(`已触发重新制作：${row.repo_name}`)
    refresh()
  } catch (e) {
    ElMessage.error('重新制作失败')
  }
}
</script>
<style scoped>
.log{ background:#0b1020; color:#c6e2ff; padding:12px; border-radius:8px; white-space:pre-wrap; }
</style>
