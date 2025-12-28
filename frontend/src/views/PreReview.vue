<template>
  <div class="pre-review">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📝 文章预审与编辑</span>
          <el-button type="primary" size="small" @click="loadLatest">加载最新文章</el-button>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :md="16">
          <el-input
            v-model="content"
            type="textarea"
            :rows="20"
            placeholder="文章内容将在此显示，可直接编辑"
          />
          <div class="actions">
            <el-button type="success" @click="saveEdits" :disabled="!content">保存编辑</el-button>
            <el-tag v-if="saveStatus" :type="saveStatus === 'success' ? 'success' : 'danger'" size="small">
              {{ saveStatus === 'success' ? '保存成功' : '保存失败' }}
            </el-tag>
          </div>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card>
            <template #header>
              <span>🔧 修改意见与重新生成</span>
            </template>
            <el-input v-model="suggestions" type="textarea" :rows="8" placeholder="填写修改意见，重新生成将依据此意见" />
            <div class="actions">
              <el-button type="warning" @click="regenerate" :disabled="!suggestions">重新生成</el-button>
              <el-tag v-if="regenStatus" :type="regenStatus === 'queued' ? 'warning' : (regenStatus === 'success' ? 'success' : 'danger')" size="small">
                {{ regenStatus === 'queued' ? '已提交重新生成' : (regenStatus === 'success' ? '生成成功' : '生成失败') }}
              </el-tag>
            </div>
            <div v-if="logs.length" class="logs">
              <el-timeline>
                <el-timeline-item v-for="(log, idx) in logs" :key="idx" :timestamp="formatLogTime(log.time)">
                  {{ log.message }}
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const content = ref('')
const suggestions = ref('')
const saveStatus = ref('')
const regenStatus = ref('')
const logs = ref([])

const addLog = (message) => {
  logs.value = [...logs.value, { time: new Date().toISOString(), message }]
}
const formatLogTime = (iso) => new Date(iso).toLocaleString('zh-CN')

const loadLatest = async () => {
  try {
    const resp = await api.getLatestArticle()
    if (resp.data && resp.data.success) {
      content.value = resp.data.data.content
      addLog('加载最新文章成功')
    } else {
      ElMessage.error(resp.data.message || '加载失败')
    }
  } catch (e) {
    ElMessage.error('加载最新文章异常')
  }
}

const saveEdits = async () => {
  try {
    const resp = await api.saveArticle(content.value)
    if (resp.data && resp.data.success) {
      saveStatus.value = 'success'
      addLog('保存编辑成功')
    } else {
      saveStatus.value = 'fail'
      ElMessage.error(resp.data.message || '保存失败')
    }
  } catch (e) {
    saveStatus.value = 'fail'
    ElMessage.error('保存异常')
  } finally {
    setTimeout(() => (saveStatus.value = ''), 2000)
  }
}

const regenerate = async () => {
  try {
    const resp = await api.regenerateArticle(suggestions.value)
    if (resp.data && resp.data.success) {
      regenStatus.value = resp.data.data.status || 'queued'
      addLog('重新生成任务已提交')
    } else {
      regenStatus.value = 'fail'
      ElMessage.error(resp.data.message || '提交失败')
    }
  } catch (e) {
    regenStatus.value = 'fail'
    ElMessage.error('提交异常')
  } finally {
    setTimeout(() => (regenStatus.value = ''), 3000)
  }
}

// 自动加载一次
loadLatest()
</script>

<style scoped>
.pre-review {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.logs {
  margin-top: 10px;
}
</style>
