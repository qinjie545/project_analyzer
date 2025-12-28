<template>
  <div>
    <h2>信息查询 - 数据审核</h2>
    <el-card shadow="hover">
      <el-table :data="items" style="width:100%">
        <el-table-column prop="name" label="项目" min-width="220" />
        <el-table-column prop="issue" label="问题描述" min-width="260" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="approve(row)">通过</el-button>
            <el-button size="small" type="danger" @click="reject(row)">驳回</el-button>
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

async function loadTasks() {
  try {
    const r = await api.getPendingReviewTasks()
    const rows = (r.data && r.data.data) || []
    items.value = rows.map(t => ({
      id: t.id,
      name: t.repo_name,
      issue: t.feedback || '待审核'
    }))
  } catch (e) {
    ElMessage.error('加载待审核任务失败')
  }
}

onMounted(()=>{
  loadTasks()
})

async function approve(row){
  try {
    await api.auditArticle({ id: row.id, action: 'approve' })
    ElMessage.success(`审核通过：${row.name}`)
    loadTasks()
  } catch (e) {
    ElMessage.error('审核通过失败')
  }
}
async function reject(row){
  try {
    await api.auditArticle({ id: row.id, action: 'reject' })
    ElMessage.error(`已驳回：${row.name}`)
    loadTasks()
  } catch (e) {
    ElMessage.error('驳回失败')
  }
}
</script>
