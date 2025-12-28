<template>
  <div>
    <h2>文档发布 - 外网链接</h2>
    <el-card shadow="hover">
      <el-table :data="items" style="width:100%">
        <el-table-column prop="platform" label="平台" width="140" />
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="url" label="链接" min-width="280">
          <template #default="{ row }">
            <a :href="row.url" target="_blank">{{ row.url }}</a>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="open(row)">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'

const items = ref([])

async function loadLinks() {
  try {
    const r = await api.getPublishLinks()
    items.value = (r.data && r.data.data) || []
  } catch (e) {
    items.value = []
  }
}

onMounted(()=>{
  loadLinks()
})
function open(row){ window.open(row.url, '_blank') }
</script>
