<template>
  <div class="editor-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Edit /></el-icon>
          <span>PDF 编辑器</span>
        </div>
      </template>

      <el-alert
        title="功能说明"
        type="info"
        description="提供文本编辑、表单编辑、注释批注、页面管理等 PDF 编辑功能"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <div class="editor-content">
        <el-empty description="编辑功能开发中，敬请期待..." />
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 编辑功能待实现
</script>

<style scoped>
.editor-page {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.editor-content {
  min-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
