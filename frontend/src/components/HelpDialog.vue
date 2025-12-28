<template>
  <el-dialog v-model="visibleLocal" title="使用帮助" width="640px">
    <div class="help-content">
      <h3>概览</h3>
      <p>GitHub Daily Report 展示近期热门项目，并支持文章预审与模型配置。</p>

      <h3>功能入口</h3>
      <ul>
        <li>首页：查看统计与热门项目，支持搜索与项目解析。</li>
        <li>文章预审：查看并编辑最新文章内容。</li>
        <li>模型配置：设置外部大模型提供商、Base URL、模型名与 API Key。</li>
      </ul>

      <h3>数据获取</h3>
      <ul>
        <li>项目列表：/api/repos（无数据时返回空列表）。</li>
        <li>统计数据：/api/stats（包含总数、Stars/Forks 与语言分布）。</li>
        <li>健康检查：/api/health。</li>
        <li>文章：/api/article/latest、/api/article/save、/api/article/regenerate。</li>
      </ul>

      <h3>常见问题</h3>
      <ul>
        <li>404：确认后端在 5000 端口运行，前端在 3001 端口；生产构建使用 VITE_API_BASE 或自动指向 http://localhost:5000/api。</li>
        <li>跨域：开发环境通过 Vite 代理 /api 到后端。</li>
        <li>无数据：首次启动可能为空，接口会返回空数据而非错误。</li>
      </ul>

      <div class="timestamp">文档生成时间：2025-12-13T08:12:15.756Z</div>
    </div>
    <template #footer>
      <el-button @click="visibleLocal = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible'])

const visibleLocal = ref(props.visible)
watch(() => props.visible, v => (visibleLocal.value = v))
watch(visibleLocal, v => emit('update:visible', v))
</script>

<style scoped>
.help-content { line-height: 1.7; color: #303133; }
.help-content h3 { margin: 10px 0; }
.help-content ul { padding-left: 18px; }
.timestamp { margin-top: 12px; color: #909399; font-size: 12px; }
</style>
