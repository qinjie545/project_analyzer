<template>
  <div class="home">
    <el-card class="stats-card" v-if="stats">
      <template #header>
        <div class="card-header">
          <span>📊 数据统计</span>
          <span class="fetch-date" v-if="stats.fetch_date">
            {{ formatDate(stats.fetch_date) }}
          </span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8" :md="8">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_repos }}</div>
            <div class="stat-label">项目总数</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8" :md="8">
          <div class="stat-item">
            <div class="stat-value">{{ formatNumber(stats.total_stars) }}</div>
            <div class="stat-label">总 Stars</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8" :md="8">
          <div class="stat-item">
            <div class="stat-value">{{ formatNumber(stats.total_forks) }}</div>
            <div class="stat-label">总 Forks</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="language-card" v-if="stats && stats.language_distribution">
      <template #header>
        <span>💻 编程语言分布</span>
      </template>
      <div class="language-tags">
        <el-tag
          v-for="(count, lang) in stats.language_distribution"
          :key="lang"
          :type="getTagType(lang)"
          size="large"
          class="language-tag"
        >
          {{ lang }} ({{ count }})
        </el-tag>
      </div>
    </el-card>

    <el-card class="repos-card">
      <template #header>
        <div class="card-header">
          <span>🚀 热门项目</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索项目..."
            style="width: 300px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-loading v-loading="loading" element-loading-text="加载中...">
        <div v-if="filteredRepos.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无数据" />
        </div>
        <div v-else class="repos-list">
          <el-card
            v-for="(repo, index) in filteredRepos"
            :key="repo.full_name"
            class="repo-card"
            shadow="hover"
          >
            <div class="repo-header">
              <div class="repo-rank">#{{ index + 1 }}</div>
              <div class="repo-info">
                <h3 class="repo-name">
                  <a :href="repo.url" target="_blank" rel="noopener noreferrer">
                    {{ repo.full_name }}
                  </a>
                </h3>
                <p class="repo-description">{{ repo.description || '暂无描述' }}</p>
              </div>
            </div>
            <div class="repo-meta">
              <div class="meta-item">
                <el-icon><Star /></el-icon>
                <span>{{ formatNumber(repo.stars) }}</span>
              </div>
              <div class="meta-item">
                <el-icon><ForkSpoon /></el-icon>
                <span>{{ formatNumber(repo.forks) }}</span>
              </div>
              <div class="meta-item" v-if="repo.language">
                <el-tag :type="getTagType(repo.language)" size="small">
                  {{ repo.language }}
                </el-tag>
              </div>
            </div>
            <div class="repo-topics" v-if="repo.topics && repo.topics.length > 0">
              <el-tag
                v-for="topic in repo.topics.slice(0, 5)"
                :key="topic"
                size="small"
                class="topic-tag"
              >
                {{ topic }}
              </el-tag>
            </div>
            <div class="repo-actions">
              <el-button type="primary" size="small" @click="triggerAnalyze(repo)">解析项目</el-button>
              <el-tag v-if="analyzeStatus[repo.full_name]" :type="analyzeStatus[repo.full_name].success ? 'success' : 'danger'" size="small">
                {{ analyzeStatus[repo.full_name].success ? '成功' : '失败' }}
              </el-tag>
            </div>
            <div v-if="logs[repo.full_name] && logs[repo.full_name].length" class="repo-logs">
              <el-timeline>
                <el-timeline-item v-for="(log, idx) in logs[repo.full_name]" :key="idx" :timestamp="formatLogTime(log.time)">
                  {{ log.message }}
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-card>
        </div>
      </el-loading>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Star, ForkSpoon, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const repos = ref([])
const stats = ref(null)
const loading = ref(false)
const searchKeyword = ref('')

// 分析日志与状态
const logs = ref({})
const analyzeStatus = ref({})

const filteredRepos = computed(() => {
  if (!searchKeyword.value) {
    return repos.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return repos.value.filter(repo => 
    repo.name.toLowerCase().includes(keyword) ||
    repo.full_name.toLowerCase().includes(keyword) ||
    (repo.description && repo.description.toLowerCase().includes(keyword)) ||
    (repo.language && repo.language.toLowerCase().includes(keyword))
  )
})

const addLog = (fullName, message) => {
  const time = new Date().toISOString()
  logs.value[fullName] = [...(logs.value[fullName] || []), { time, message }]
}
const formatLogTime = (iso) => new Date(iso).toLocaleString('zh-CN')

const triggerAnalyze = async (repo) => {
  const fullName = repo.full_name
  addLog(fullName, '开始解析...')
  try {
    const provider = localStorage.getItem('model_provider') || null
    const baseUrl = localStorage.getItem('model_base_url') || null
    const model = localStorage.getItem('model_name') || null
    const apiKey = localStorage.getItem('external_api_key') || null
    const response = await api.analyzeRepo(fullName, apiKey, provider, baseUrl, model)
    if (response.data && response.data.success) {
      analyzeStatus.value[fullName] = { success: true }
      addLog(fullName, `解析成功：${response.data.data.analysis.summary}`)
    } else {
      analyzeStatus.value[fullName] = { success: false }
      addLog(fullName, `解析失败：${(response.data && response.data.message) || '未知错误'}`)
    }
  } catch (e) {
    analyzeStatus.value[fullName] = { success: false }
    addLog(fullName, `解析异常：${e.message}`)
  }
}

const fetchRepos = async () => {
  loading.value = true
  try {
    const response = await api.getRepos()
    if (response.data.success) {
      repos.value = response.data.data
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败，请检查后端服务是否运行')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await api.getStats()
    if (response.data.success) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const formatNumber = (num) => {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

const formatDate = (dateString) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateString
  }
}

const getTagType = (lang) => {
  const types = ['', 'success', 'info', 'warning', 'danger']
  const hash = lang.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return types[hash % types.length]
}

onMounted(() => {
  fetchRepos()
  fetchStats()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-card,
.language-card,
.repos-card {
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fetch-date {
  font-size: 14px;
  color: #909399;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.language-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.language-tag {
  margin: 5px 0;
}

.repos-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.repo-card {
  transition: transform 0.2s;
}

.repo-card:hover {
  transform: translateY(-2px);
}

.repo-header {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.repo-rank {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  min-width: 40px;
}

.repo-info {
  flex: 1;
}

.repo-name {
  margin-bottom: 8px;
}

.repo-name a {
  color: #303133;
  text-decoration: none;
  font-size: 18px;
  font-weight: 600;
}

.repo-name a:hover {
  color: #409eff;
}

.repo-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.repo-meta {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
  font-size: 14px;
}

.repo-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-tag {
  margin: 0;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.repo-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.repo-logs {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .repo-header {
    flex-direction: column;
  }

  .repo-rank {
    display: none;
  }
}
</style>
