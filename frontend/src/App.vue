<template>
  <div id="app">
    <!-- 顶部标题栏 -->
    <el-header class="app-header">
      <div class="header-bar">
        <div class="header-content">
          <h1>
            <el-icon><Star /></el-icon>
            OpenSource Daily Report
          </h1>
        </div>
        <el-button type="info" size="small" @click="showHelp = true">帮助</el-button>
      </div>
    </el-header>

    <!-- 主体布局：左侧菜单，右侧内容 -->
    <el-container class="app-body">
      <el-aside width="240px" class="app-aside">
        <el-menu router default-active="/" class="el-menu-vertical-demo">
          <el-menu-item index="/">
            <span>首页</span>
          </el-menu-item>
          <el-sub-menu index="pull">
            <template #title>
              <span>项目拉取</span>
            </template>
            <el-menu-item index="/pull/config">拉取配置</el-menu-item>
            <el-menu-item index="/pull/records">拉取记录</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="article">
            <template #title>
              <span>文章制作</span>
            </template>
            <el-menu-item index="/article/tasks">制作任务</el-menu-item>
            <el-menu-item index="/article/audit">文章审核</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="publish">
            <template #title>
              <span>文档发布</span>
            </template>
            <el-menu-item index="/publish/pending">待发文章池</el-menu-item>
            <el-menu-item index="/publish/config">发布配置（待开发）</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="system">
            <template #title>
              <span>系统配置</span>
            </template>
            <el-menu-item index="/system/model">模型配置</el-menu-item>
            <el-menu-item index="/system/prompt">提示词配置</el-menu-item>
            <el-menu-item index="/article/config">文章生成配置</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 底部标题栏 -->
    <el-footer class="app-footer">
      <div class="footer-content">
        <p>© 2025 OpenSource Daily Report | 数据来源: GitHub API | <span class="dt">2025-12-12T19:22:07.235Z</span></p>
      </div>
    </el-footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Star } from '@element-plus/icons-vue'
import HelpDialog from './components/HelpDialog.vue'

const showHelp = ref(false)
</script>

<HelpDialog v-model:visible="showHelp" />

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.app-header, .app-footer {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 16px 20px;
}

.app-header { position: fixed; top: 0; left: 0; right: 0; z-index: 1000; }

.header-bar { display: flex; justify-content: space-between; align-items: center; }
.header-content { text-align: center; }
.header-content h1 {
  color: #303133; font-size: 28px; margin-bottom: 6px;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}
.subtitle { color: #909399; font-size: 13px; }

.app-body { min-height: 100vh; padding-top: 80px; padding-bottom: 60px; box-sizing: border-box; }
.app-aside {
  background: rgba(255, 255, 255, 0.95);
  border-right: 1px solid rgba(0,0,0,0.06);
  height: 100%;
  overflow-y: auto;
}
.el-menu-vertical-demo {
  border-right: none;
  min-height: 100%;
}
.app-main {
  padding: 20px; max-width: 98%; margin: 0 auto; width: 100%;
}

.app-footer { text-align: center; color: #909399; font-size: 14px; position: fixed; bottom: 0; left: 0; right: 0; z-index: 1000; }
.footer-content { max-width: 98%; margin: 0 auto; }
.dt { font-family: monospace; }
</style>
