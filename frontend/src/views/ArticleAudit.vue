<template>
  <div class="article-audit">
    <h2>文章制作 - 文章审核</h2>
    
    <!-- 列表视图 -->
    <el-card v-if="!currentTask" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>待审核文章列表</span>
          <el-button type="primary" @click="fetchTasks" :icon="Refresh">刷新</el-button>
        </div>
      </template>
      <el-table :data="tasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="repo_name" label="项目名称">
          <template #default="scope">
            {{ scope.row.repo_name }}
            <el-tag v-if="scope.row.feedback" size="small" type="warning" style="margin-left: 5px">已修改</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="article_type" label="文章类型" width="150" />
        <el-table-column prop="created_at" label="生成时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="startAudit(scope.row)">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 审核视图 -->
    <el-card v-else shadow="hover">
      <template #header>
        <div class="card-header">
          <span>审核文章: {{ currentTask.repo_name }}</span>
          <div>
            <el-button @click="showThinkingDialog = true" type="warning" plain style="margin-right: 10px" v-if="thinkingContent">查看思考过程</el-button>
            <el-button @click="cancelAudit">返回列表</el-button>
          </div>
        </div>
      </template>
      
      <div class="audit-container">
        <div class="preview-section">
          <h3>文章内容编辑</h3>
          <el-alert v-if="currentTask.feedback" :title="'上次反馈: ' + currentTask.feedback" type="warning" :closable="false" style="margin-bottom: 10px" />
          <el-input
            v-model="currentContent"
            type="textarea"
            :rows="20"
            placeholder="文章内容"
          />
        </div>
        <div class="preview-render">
           <h3>预览</h3>
           <v-md-preview :text="currentContent"></v-md-preview>
        </div>
      </div>
      
      <div class="actions-section">
        <el-input v-model="auditOpinion" type="textarea" :rows="3" placeholder="填写审批意见" />
        <div class="btns">
          <el-button type="success" @click="submitAudit('approve')">审批通过</el-button>
          <el-button type="primary" @click="submitAudit('revise')">提交修改 (重新生成)</el-button>
          <el-button type="warning" @click="submitAudit('reject')">不通过（回入制作任务池）</el-button>
        </div>
      </div>
    </el-card>

    <!-- 详细版本预览弹窗 -->
    <el-dialog v-model="showDetailDialog" title="详细版本预览" width="80%">
      <v-md-preview :text="detailContent"></v-md-preview>
    </el-dialog>

    <!-- 思考过程弹窗 -->
    <el-dialog v-model="showThinkingDialog" title="思考过程" width="80%">
      <div class="thinking-content">
        <pre>{{ thinkingContent }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import api from '../api'

const tasks = ref([])
const loading = ref(false)
const currentTask = ref(null)
const currentContent = ref('')
const auditOpinion = ref('')
const showDetailDialog = ref(false)
const detailContent = ref('')
const showThinkingDialog = ref(false)
const thinkingContent = ref('')

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await api.getPendingReviewTasks()
    if (res.data.success) {
      tasks.value = res.data.data
    }
  } catch (e) {
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const startAudit = (task) => {
  currentTask.value = task
  currentContent.value = task.content || ''
  detailContent.value = task.detailed_content || ''
  thinkingContent.value = task.thinking_content || ''
  auditOpinion.value = ''
}

const cancelAudit = () => {
  currentTask.value = null
  currentContent.value = ''
}

const submitAudit = async (action) => {
  if (!currentTask.value) return
  
  try {
    const res = await api.auditArticle({
      id: currentTask.value.id,
      action: action,
      content: currentContent.value,
      opinion: auditOpinion.value
    })
    
    if (res.data.success) {
      let msg = '操作成功'
      if (action === 'approve') msg = '已审批通过'
      else if (action === 'revise') msg = '已提交修改并开始重新生成'
      else if (action === 'reject') msg = '已回入任务池'
      
      ElMessage.success(msg)
      currentTask.value = null
      fetchTasks()
    } else {
      ElMessage.error(res.data.message || '操作失败')
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.audit-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.actions-section { border-top: 1px solid #eee; padding-top: 20px; }
.btns { margin-top: 10px; }
.markdown-body { border: 1px solid #dcdfe6; padding: 10px; border-radius: 4px; min-height: 400px; max-height: 600px; overflow-y: auto; background-color: #fff; }
.thinking-content pre { white-space: pre-wrap; word-wrap: break-word; background: #f5f7fa; padding: 15px; border-radius: 4px; }
</style>
