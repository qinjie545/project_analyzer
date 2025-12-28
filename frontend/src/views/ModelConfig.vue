<template>
  <div class="model-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>⚙️ 模型配置</span>
          <span class="ts">2025-12-16T12:56:54.866Z</span>
        </div>
      </template>
      <el-form label-width="120px">
        <el-form-item label="模型提供方">
          <el-select v-model="provider" placeholder="选择模型提供方" style="max-width: 320px">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Qwen (DashScope)" value="qwen" />
            <el-option label="Other (OpenAI Compatible)" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="baseUrl" placeholder="如 https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="Model Name">
          <el-input v-model="model" placeholder="如 gpt-3.5-turbo, claude-3-opus, deepseek-chat" />
        </el-form-item>
        <el-form-item label="外部 API Key">
          <el-input v-model="apiKey" placeholder="输入外部模型 API Key" show-password />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" @click="save">保存配置</el-button>
          <el-button type="success" @click="test" :loading="testing">测试配置</el-button>
          <el-button @click="reset">重置</el-button>
        </div>
        <el-divider />
        <el-alert type="info" title="说明" :closable="false">
          <template #default>
            <div>配置将保存到后端，用于文章生成等任务。测试配置会发送一条简单的“你好！”消息来验证连通性。</div>
          </template>
        </el-alert>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const provider = ref('openai')
const baseUrl = ref('')
const model = ref('')
const apiKey = ref('')
const testing = ref(false)

async function load() {
  try {
    const res = await api.getMakeConfig()
    if (res.data && res.data.data) {
      const d = res.data.data
      provider.value = d.provider || 'openai'
      baseUrl.value = d.base_url || ''
      model.value = d.model || ''
      apiKey.value = d.external_api_key || ''
    }
  } catch (e) {
    // ignore
  }
}

async function save() {
  try {
    const payload = {
      provider: provider.value,
      base_url: baseUrl.value,
      model: model.value,
      external_api_key: apiKey.value
    }
    await api.saveMakeConfig(payload)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function test() {
  if (!apiKey.value) {
    ElMessage.warning('请先填写 API Key')
    return
  }
  testing.value = true
  try {
    const payload = {
      provider: provider.value,
      apiKey: apiKey.value,
      baseUrl: baseUrl.value,
      modelName: model.value
    }
    const res = await api.testModelConfig(payload)
    if (res.data && res.data.success) {
      ElMessage.success(`测试成功！回复：${res.data.reply}`)
    } else {
      ElMessage.error(res.data.message || '测试失败')
    }
  } catch (e) {
    ElMessage.error('测试请求失败: ' + (e.response?.data?.message || e.message))
  } finally {
    testing.value = false
  }
}

const reset = () => {
  provider.value = 'openai'
  baseUrl.value = ''
  model.value = ''
  apiKey.value = ''
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.model-config { margin: 0 auto; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.ts { font-family: monospace; color: #909399; }
.actions { display: flex; align-items: center; gap: 10px; }
</style>
