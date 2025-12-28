<template>
  <div class="article-gen-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>⚙️ 制作配置</span>
        </div>
      </template>
      <el-form label-width="120px">
        <el-form-item label="生成引擎">
          <el-radio-group v-model="engineVersion">
            <el-radio label="v1">V1 (详细文档 -> 精简文章)</el-radio>
            <el-radio label="v2">V2 (直接生成文章)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="字数限制">
          <el-radio-group v-model="wordLimit">
            <el-radio :label="2000">2000字以内</el-radio>
            <el-radio :label="5000">5000字以内</el-radio>
            <el-radio :label="8000">8000字以内</el-radio>
          </el-radio-group>
        </el-form-item>
        <div class="actions">
          <el-button type="primary" @click="save">保存配置</el-button>
          <el-button @click="load">重置</el-button>
        </div>
        <el-divider />
        <el-alert type="info" title="说明" :closable="false">
          <template #default>
            <div>
              <p><strong>V1 引擎：</strong> 先生成约 20000 字的详细文档，再精简为 8000 字的文章。适合深度解析。</p>
              <p><strong>V2 引擎：</strong> 直接生成 8000 字的文章。速度更快，适合快速概览。</p>
            </div>
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

const engineVersion = ref('v1')
const wordLimit = ref(8000)

async function load() {
  try {
    const res = await api.getMakeConfig()
    if (res.data && res.data.data) {
      const d = res.data.data
      engineVersion.value = d.engine_version || 'v1'
      wordLimit.value = d.word_limit || 8000
    }
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

async function save() {
  try {
    const payload = {
      engine_version: engineVersion.value,
      word_limit: wordLimit.value
    }
    await api.saveMakeConfig(payload)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.article-gen-config { margin: 0 auto; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.actions { display: flex; align-items: center; gap: 10px; margin-top: 20px; }
</style>
