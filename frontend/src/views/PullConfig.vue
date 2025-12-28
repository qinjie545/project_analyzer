<template>
  <div>
    <h2>项目拉取 - 配置</h2>
    <el-card class="box-card" shadow="hover">
      <el-form label-width="120px">
        <el-form-item label="来源仓库">
          <el-checkbox-group v-model="sources">
            <el-checkbox label="GitHub" />
            <el-checkbox label="Gitee" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="关键字">
          <div class="inline column">
            <el-input v-model="keywords" placeholder="例如: ai, data, devops" />
            <small class="help">支持英文逗号分隔多个关键字，例如：ai, data, devops</small>
          </div>
        </el-form-item>
        <el-form-item label="拉取规则">
          <el-select v-model="rule" placeholder="选择规则">
            <el-option label="最佳匹配" value="best_match" />
            <el-option label="最多 Star" value="most_stars" />
            <el-option label="最多 Fork" value="most_forks" />
            <el-option label="最近更新" value="recently_updated" />
            <el-option label="Help Wanted" value="help_wanted" />
            <el-option label="近期热门（Star/Fork 增长快）" value="trending" />
          </el-select>
        </el-form-item>
        <el-form-item label="拉取设置">
          <div class="inline">
            <el-input-number v-model="batch" :min="1" />
            <span class="suffix">每次拉取项目数</span>
          </div>
        </el-form-item>
        <el-form-item label="并发与间隔">
          <div class="inline">
            <el-input-number v-model="concurrency" :min="1" />
            <span class="suffix">拉取并发数</span>
            <el-input-number v-model="perProjectDelay" :min="0" />
            <span class="suffix">项目间隔(秒)</span>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="saveAndStart">开始拉取</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const sources = ref(['GitHub'])
const keywords = ref('')
const rule = ref('best_match')
const batch = ref(50)
const concurrency = ref(5)
const perProjectDelay = ref(1)

onMounted(async () => {
  try {
    const r = await api.getPullConfig()
    const cfg = (r.data && r.data.data) || {}
    if (cfg.sources) sources.value = cfg.sources
    if (cfg.keywords) {
      keywords.value = cfg.keywords
    } else if (Array.isArray(cfg.keywords_list)) {
      keywords.value = cfg.keywords_list.join(', ')
    }
    if (cfg.rule) rule.value = cfg.rule
    if (typeof cfg.concurrency === 'number') concurrency.value = cfg.concurrency
    if (typeof cfg.perProjectDelay === 'number') perProjectDelay.value = cfg.perProjectDelay
    if (typeof cfg.batch === 'number') batch.value = cfg.batch
  } catch (e) {
    // 忽略加载错误
  }
})

async function saveAndStart() {
  try {
    // 1. 保存配置
    await api.savePullConfig({
      sources: sources.value,
      keywords: keywords.value,
      rule: rule.value,
      concurrency: concurrency.value,
      perProjectDelay: perProjectDelay.value,
      batch: batch.value
    })
    
    // 2. 触发拉取
    await api.pullRunByConfig({})
    ElMessage.success('配置已保存并开始拉取')
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.message || '未知错误'))
  }
}
</script>

<style scoped>
.inline { display: flex; align-items: center; gap: 10px; }
.inline.column { flex-direction: column; align-items: flex-start; gap: 6px; }
.suffix { color: #909399; font-size: 12px; }
.help { color: #909399; }
</style>
