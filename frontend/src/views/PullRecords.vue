<template>
  <div>
    <h2>项目拉取 - 拉取记录</h2>
    <el-card class="box-card" shadow="hover">
      <div style="margin-bottom:10px;">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索项目名称或简述"
          size="small"
          style="width: 100%;"
          clearable
          @keyup.enter="refresh"
          @clear="refresh"
        >
          <template #append>
            <el-button @click="refresh">搜索</el-button>
          </template>
        </el-input>
      </div>
      <el-table :data="items" style="width: 100%">
        <el-table-column prop="name" label="项目" min-width="220">
          <template #default="{ row }">
            <a :href="row.url" target="_blank">{{ row.name }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="pullTime" label="拉取时间" width="200" />
        <el-table-column prop="stars" label="Stars" width="100" />
        <el-table-column prop="forks" label="Forks" width="100" />
        <el-table-column label="Token 规模" width="120">
          <template #default="{ row }">
            {{ formatTokenCount(row.token_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="简述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span 
              v-if="row.summary" 
              style="cursor:pointer;color:#409EFF" 
              @click="showDetail(row)"
            >
              {{ row.summary }}
            </span>
            <span v-else style="color:#909399">暂无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button size="small" @click="rePull(row)">重新拉取</el-button>
            <el-button size="small" type="primary" @click="openDir(row)">打开目录</el-button>
            <el-button 
              size="small" 
              :type="row.task_id ? 'warning' : 'success'" 
              @click="generateArticle(row)"
            >
              {{ row.task_id ? '继续生成' : '生成文章' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 30, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="项目详情" width="70%">
      <div v-loading="detailLoading">
        <h3>{{ currentDetail.name }}</h3>
        <p><strong>URL:</strong> <a :href="currentDetail.url" target="_blank">{{ currentDetail.url }}</a></p>
        <el-divider content-position="left">详细介绍</el-divider>
        <div style="max-height: 500px; overflow-y: auto; background: #f5f7fa; padding: 15px; border-radius: 4px;">
          <v-md-preview :text="readmeContent || '暂无详细内容'"></v-md-preview>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const items = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const detailVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref({})
const readmeContent = ref('')

function formatTokenCount(count) {
  if (!count) return '0';
  if (count < 1000) return count + '';
  if (count < 1000000) return (count / 1000).toFixed(1) + 'k';
  return (count / 1000000).toFixed(1) + 'M';
}

async function refresh() {
  const r = await api.getPullRecords({ 
    page: currentPage.value, 
    pageSize: pageSize.value,
    keyword: searchKeyword.value 
  })
  items.value = (r.data && r.data.data) || []
  total.value = (r.data && r.data.total) || 0
}

function handleSizeChange(val) {
  pageSize.value = val
  refresh()
}

function handleCurrentChange(val) {
  currentPage.value = val
  refresh()
}

onMounted(() => {
  refresh()
})

async function rePull(row) {
  try {
    await api.rePull({ id: row.id })
    ElMessage.success(`已触发重新拉取：${row.name}`)
    refresh()
  } catch (e) {
    ElMessage.error('重新拉取失败')
  }
}
function openDir(row) {
  ElMessage.success(`项目目录：${row.path}`)
}
async function generateArticle(row) {
  if (row.task_id) {
    router.push('/articles/tasks')
    return
  }
  try {
    await api.createArticleTask({
      pull_record_id: row.id,
      repo_name: row.name
    })
    ElMessage.success(`已创建制作任务：${row.name}`)
    refresh()
  } catch (e) {
    ElMessage.error('创建任务失败')
  }
}
async function showDetail(row) {
  currentDetail.value = row
  detailVisible.value = true
  
  // 优先显示已生成的详细内容
  if (row.detail) {
    readmeContent.value = row.detail
    return
  }
  
  // 否则加载 README
  detailLoading.value = true
  readmeContent.value = ''
  try {
    const res = await api.getRepoReadme(row.path)
    readmeContent.value = (res.data && res.data.data) || '未找到 README 文件'
  } catch (e) {
    readmeContent.value = '获取详情失败'
  } finally {
    detailLoading.value = false
  }
}
</script>
