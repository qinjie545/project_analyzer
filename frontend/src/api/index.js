import axios from 'axios'

const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('API 请求错误:', error)
    return Promise.reject(error)
  }
)

export default {
  // 获取项目列表
  getRepos(limit = null) {
    const url = limit ? `/repos/${limit}` : '/repos'
    return api.get(url)
  },
  
  // 获取统计数据
  getStats() {
    return api.get('/stats')
  },
  
  // 健康检查
  healthCheck() {
    return api.get('/health')
  },

  // 触发后端分析
  analyzeRepo(fullName, apiKey = null, provider = null, baseUrl = null, model = null) {
    const payload = { repo_full_name: fullName }
    if (apiKey) payload.external_api_key = apiKey
    if (provider) payload.model_provider = provider
    if (baseUrl) payload.model_base_url = baseUrl
    if (model) payload.model_name = model
    return api.post('/analyze', payload)
  },

  // 文章预审接口
  getLatestArticle() {
    return api.get('/article/latest')
  },
  saveArticle(content) {
    return api.post('/article/save', { content })
  },
  regenerateArticle(suggestions) {
    return api.post('/article/regenerate', { suggestions })
  },

  // 拉取：运行与记录
  pullRun({ keyword = 'GPT', limit = 10, sort = 'stars', simulate = false, task_id = null } = {}) {
    const payload = { keyword, limit, sort, simulate }
    if (task_id) payload.task_id = task_id
    return api.post('/pull/run', payload)
  },
  getPullRecords(params) {
    return api.get('/pull/records', { params })
  },
  rePull(data) {
    return api.post('/pull/repull', data)
  },
  getPullConfig() {
    return api.get('/pull/config')
  },
  savePullConfig(data) {
    return api.post('/pull/config', data)
  },
  pullTest(data) {
    return api.post('/pull/test', data)
  },
  createArticleTask(data) {
    return api.post('/article/create_task', data)
  },
  getRepoReadme(path) {
    return api.get('/repo/readme', { params: { path } })
  },
  pullRunByConfig(params = {}) {
    return api.post('/pull/run/config', params)
  },
  testModelConfig(config) {
    return api.post('/config/model/test', config)
  },
  getMakeConfig() {
    return api.get('/config/model')
  },
  saveMakeConfig(data) {
    return api.post('/config/model', data)
  },
  getMakeTasks() {
    return api.get('/make/tasks')
  },
  getMakeLogs(taskId) {
    return api.get(`/make/logs/${taskId}`)
  },
  enqueueMakeTask(data) {
    return api.post('/make/enqueue', data)
  },
  getPendingPublishArticles() {
    return api.get('/publish/pending')
  },
  getPublishConfig() {
    return api.get('/publish/config')
  },
  savePublishConfig(data) {
    return api.post('/publish/config', data)
  },
  publishTest(data) {
    return api.post('/publish/test', data)
  },
  getPublishHistory() {
    return api.get('/publish/history')
  },
  getPublishLinks() {
    return api.get('/publish/links')
  },
  getPendingReviewTasks() {
    return api.get('/article/tasks/pending_review')
  },
  auditArticle(data) {
    return api.post('/article/audit', data)
  },
  getPrompts() {
    return api.get('/prompts')
  },
  savePrompt(data) {
    return api.post('/prompts', data)
  },
  setDefaultPrompt(data) {
    return api.post('/prompts/default', data)
  }
}
