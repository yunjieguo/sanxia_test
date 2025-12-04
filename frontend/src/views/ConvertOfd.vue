<template>
  <div class="convert-ofd">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>OFD 转 PDF</span>
        </div>
      </template>

      <el-empty description="功能开发中，敬请期待">
        <el-button type="primary" @click="goBack">返回工具列表</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'

const router = useRouter()

const goBack = () => {
  router.push('/pdf-tools')
}
</script>

<style scoped>
.convert-ofd {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}
</style>
