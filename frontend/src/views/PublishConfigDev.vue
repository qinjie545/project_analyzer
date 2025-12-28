<template>
  <div>
    <h2>文档发布 - 发布配置（待开发）</h2>
    <el-card shadow="hover">
      <el-form label-width="120px">
        <el-form-item label="发布平台">
          <el-checkbox-group v-model="platforms">
            <el-checkbox label="微信公众号" />
            <el-checkbox label="知乎" />
            <el-checkbox label="掘金" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="发布时间">
          <el-time-picker v-model="publishTime" placeholder="选择时间" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="发布账号">
          <el-input v-model="account" placeholder="输入发布账号标识" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="apiKey" placeholder="输入平台 API Key" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="save">保存配置</el-button>
          <el-button @click="test">测试发布</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const platforms = ref(['微信公众号'])
const publishTime = ref('09:00')
const account = ref('')
const apiKey = ref('')

onMounted(async () => {
  try {
    const r = await api.getPublishConfig()
    const cfg = (r.data && r.data.data) || {}
    if (cfg.platforms) platforms.value = cfg.platforms
    if (cfg.publishTime) publishTime.value = cfg.publishTime
    if (cfg.account) account.value = cfg.account
    if (cfg.apiKey) apiKey.value = cfg.apiKey
  } catch (e) {
    // 忽略加载错误，仅在保存时提示
  }
})

async function save(){
  try {
    await api.savePublishConfig({
      platforms: platforms.value,
      publishTime: publishTime.value,
      account: account.value,
      apiKey: apiKey.value
    })
    ElMessage.success('发布配置已保存')
  } catch (e) {
    ElMessage.error('保存发布配置失败')
  }
}
async function test(){
  try {
    await api.publishTest({
      platform: platforms.value[0] || '微信公众号',
      title: '发布测试',
      url: '#'
    })
    ElMessage.info(`测试发布：平台=${platforms.value.join(',')}，账号=${account.value||'-'}，时间=${publishTime.value}`)
  } catch (e) {
    ElMessage.error('测试发布失败')
  }
}
</script>
