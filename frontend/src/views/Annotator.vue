<template>
  <div class="annotator-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><PriceTag /></el-icon>
          <span>智能标注</span>
        </div>
      </template>

      <el-alert
        title="功能说明"
        type="info"
        description="通过标注样本训练，实现文档关键信息的自动识别和抽取"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <div class="annotator-content">
        <el-empty description="标注功能开发中，敬请期待..." />
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 标注功能待实现
</script>

<style scoped>
.annotator-page {
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

.annotator-content {
  min-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
