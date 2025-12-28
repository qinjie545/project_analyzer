<template>
  <div class="pending-articles">
    <h2>文档发布 - 待发文章池</h2>
    <el-card shadow="hover">
      <el-table :data="items" style="width:100%" v-loading="loading">
        <el-table-column prop="title" label="文章标题" min-width="240" />
        <el-table-column prop="repo_name" label="关联项目" width="180" />
        <el-table-column prop="approved_at" label="审核通过时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.approved_at) }}
          </template>
        </el-table-column>
        <el-table-column label="下载文档" width="300">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="primary" @click="download(row, 'pdf')">PDF</el-button>
              <el-button size="small" type="success" @click="download(row, 'docx')">Word</el-button>
              <el-button size="small" type="warning" @click="download(row, 'html')">HTML</el-button>
              <el-button size="small" type="info" @click="download(row, 'md')">MD</el-button>
            </el-button-group>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="preview(row)">预览</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Preview Dialog -->
    <el-dialog v-model="previewVisible" title="文章预览" width="80%" top="5vh">
      <div v-if="previewRow" class="preview-container">
        <v-md-preview :text="previewContent"></v-md-preview>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const items = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const previewRow = ref(null)
const previewContent = ref('')

const formatDate = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

const fetchItems = async () => {
  loading.value = true
  try {
    const res = await api.getPendingPublishArticles()
    if (res.data.success) {
      items.value = res.data.data
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('获取待发文章失败')
  } finally {
    loading.value = false
  }
}

const getDownloadUrl = (path) => {
    return path
}

const download = (row, type) => {
  const path = row.files[type]
  if (!path) {
    ElMessage.warning('文件未生成')
    return
  }
  
  const url = getDownloadUrl(path)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', '')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const preview = (row) => {
  previewRow.value = row
  previewContent.value = row.content || ''
  previewVisible.value = true
}

onMounted(fetchItems)
</script>

<style scoped>
.pending-articles { padding: 20px; }
.preview-container {
  height: 70vh;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}
</style>
