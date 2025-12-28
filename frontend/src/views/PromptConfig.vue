<template>
  <div class="prompt-config">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>提示词配置</span>
        </div>
      </template>

      <el-container style="height: 600px; border: 1px solid #eee">
        <el-aside width="200px" style="background-color: rgb(238, 241, 246)">
          <el-menu :default-active="activeScene" @select="handleSceneSelect">
            <el-menu-item index="article_generation">
              <span>文章生成</span>
            </el-menu-item>
            <el-menu-item index="repo_detail">
              <span>项目详情解析</span>
            </el-menu-item>
            <el-menu-item index="repo_summary">
              <span>项目简述生成</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main>
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else>
            <div class="scene-header">
              <h3>{{ sceneNameMap[activeScene] || activeScene }}</h3>
              <el-button type="primary" size="small" @click="addTemplate">新增模板</el-button>
            </div>

            <el-tabs v-model="activeTab" type="card" editable @edit="handleTabsEdit">
              <el-tab-pane
                v-for="item in currentTemplates"
                :key="item.id"
                :label="item.name + (item.is_default ? ' (默认)' : '')"
                :name="String(item.id)"
              >
                <el-form label-position="top">
                  <el-form-item label="模板名称">
                    <el-input v-model="item.name" placeholder="请输入模板名称" />
                  </el-form-item>
                  
                  <el-form-item label="提示词内容">
                    <el-input
                      v-model="item.content"
                      type="textarea"
                      :rows="15"
                      placeholder="请输入提示词内容"
                    />
                  </el-form-item>
                  
                  <el-form-item>
                    <div class="actions">
                      <el-button type="primary" @click="saveTemplate(item)">保存</el-button>
                      <el-button 
                        v-if="!item.is_default && item.id" 
                        type="success" 
                        @click="setDefault(item)"
                      >设为默认</el-button>
                      <el-tag v-if="item.is_default" type="success">当前默认模板</el-tag>
                    </div>
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>
            
            <el-empty v-if="currentTemplates.length === 0" description="暂无模板，请新增" />
          </div>
        </el-main>
      </el-container>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeScene = ref('article_generation')
const activeTab = ref('')
const allPrompts = ref([])
const loading = ref(false)

const sceneNameMap = {
  'article_generation': '文章生成',
  'repo_detail': '项目详情解析',
  'repo_summary': '项目简述生成'
}

const currentTemplates = computed(() => {
  return allPrompts.value.filter(p => p.scene === activeScene.value)
})

const fetchPrompts = async () => {
  loading.value = true
  try {
    const res = await api.getPrompts()
    if (res.data.success) {
      allPrompts.value = res.data.data
      // Set active tab to default or first
      const current = currentTemplates.value
      if (current.length > 0) {
        const def = current.find(p => p.is_default)
        activeTab.value = def ? String(def.id) : String(current[0].id)
      }
    }
  } catch (error) {
    ElMessage.error('获取提示词失败')
  } finally {
    loading.value = false
  }
}

const handleSceneSelect = (index) => {
  activeScene.value = index
  const current = allPrompts.value.filter(p => p.scene === index)
  if (current.length > 0) {
    const def = current.find(p => p.is_default)
    activeTab.value = def ? String(def.id) : String(current[0].id)
  } else {
    activeTab.value = ''
  }
}

const addTemplate = () => {
  const newTemp = {
    id: 'new_' + Date.now(),
    scene: activeScene.value,
    name: '新模板',
    content: '',
    is_default: false
  }
  allPrompts.value.push(newTemp)
  activeTab.value = newTemp.id
}

const handleTabsEdit = (targetName, action) => {
  if (action === 'remove') {
    // Only allow removing new unsaved templates for now in UI, or implement delete API
    // For simplicity, just remove from list if it's new
    const idx = allPrompts.value.findIndex(p => String(p.id) === targetName)
    if (idx !== -1) {
      if (String(targetName).startsWith('new_')) {
        allPrompts.value.splice(idx, 1)
        if (activeTab.value === targetName) {
          activeTab.value = currentTemplates.value.length ? String(currentTemplates.value[0].id) : ''
        }
      } else {
        ElMessage.warning('暂不支持删除已保存的模板')
      }
    }
  }
}

const saveTemplate = async (item) => {
  try {
    const payload = {
      id: String(item.id).startsWith('new_') ? null : item.id,
      scene: item.scene,
      name: item.name,
      content: item.content
    }
    const res = await api.savePrompt(payload)
    if (res.data.success) {
      ElMessage.success('保存成功')
      await fetchPrompts() // Refresh to get real ID
    } else {
      ElMessage.error(res.data.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const setDefault = async (item) => {
  if (String(item.id).startsWith('new_')) {
    ElMessage.warning('请先保存模板')
    return
  }
  try {
    const res = await api.setDefaultPrompt({ id: item.id })
    if (res.data.success) {
      ElMessage.success('设置成功')
      await fetchPrompts()
    } else {
      ElMessage.error(res.data.message || '设置失败')
    }
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

onMounted(() => {
  fetchPrompts()
})
</script>

<style scoped>
.prompt-config { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.scene-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.actions { display: flex; gap: 10px; align-items: center; }
.loading-container { padding: 20px; }
</style>