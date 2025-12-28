<template>
  <div>
    <h2>信息查询 - 数据订正</h2>
    <el-card shadow="hover">
      <el-form label-width="120px">
        <el-form-item label="项目">
          <el-input v-model="repo" placeholder="owner/name" />
        </el-form-item>
        <el-form-item label="字段">
          <el-select v-model="field" placeholder="选择字段">
            <el-option label="描述" value="description" />
            <el-option label="语言" value="language" />
            <el-option label="标签" value="topics" />
          </el-select>
        </el-form-item>
        <el-form-item label="新值">
          <el-input v-model="value" type="textarea" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submit">提交订正</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const repo = ref('')
const field = ref('description')
const value = ref('')
function submit(){
  ElMessage.success('订正已提交（占位）')
}
</script>
