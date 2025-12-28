import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ModelConfig from '../views/ModelConfig.vue'
import PullConfig from '../views/PullConfig.vue'
import PullRecords from '../views/PullRecords.vue'
import ArticleTasks from '../views/ArticleTasks.vue'
import ArticleAudit from '../views/ArticleAudit.vue'
import ArticleGenConfig from '../views/ArticleGenConfig.vue'
import PublishConfigDev from '../views/PublishConfigDev.vue'
import PendingArticles from '../views/PendingArticles.vue'
import PromptConfig from '../views/PromptConfig.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/system/model', name: 'ModelConfig', component: ModelConfig },
  { path: '/system/prompt', name: 'PromptConfig', component: PromptConfig },
  { path: '/pull/config', name: 'PullConfig', component: PullConfig },
  { path: '/pull/records', name: 'PullRecords', component: PullRecords },
  { path: '/article/tasks', name: 'ArticleTasks', component: ArticleTasks },
  { path: '/article/audit', name: 'ArticleAudit', component: ArticleAudit },
  { path: '/article/config', name: 'ArticleGenConfig', component: ArticleGenConfig },
  { path: '/publish/pending', name: 'PendingArticles', component: PendingArticles },
  { path: '/publish/config', name: 'PublishConfig', component: PublishConfigDev }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
