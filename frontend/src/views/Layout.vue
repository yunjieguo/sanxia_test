<template>
  <div class="layout">
    <!-- 顶部导航栏 -->
    <el-menu
      :default-active="activeMenu"
      class="el-menu-demo"
      mode="horizontal"
      @select="handleSelect"
      router
    >
      <div class="logo">
        <el-icon :size="24"><Document /></el-icon>
        <span class="logo-text">PDF处理系统</span>
      </div>

      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/pdf-tools">PDF工具</el-menu-item>

      <div class="flex-grow"></div>
    </el-menu>

    <!-- 页面内容 -->
    <div class="main-content">
      <router-view />
    </div>

    <!-- 底部 -->
    <el-footer class="footer">
      <p>PDF 文档处理系统 v1.0.0 © 2024</p>
    </el-footer>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Document } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = ref('/')

watch(() => route.path, (newPath) => {
  if (newPath.startsWith('/pdf-tools') || newPath.startsWith('/convert') || newPath.startsWith('/edit')) {
    activeMenu.value = '/pdf-tools'
  } else {
    activeMenu.value = newPath
  }
}, { immediate: true })

const handleSelect = (key) => {
  console.log('Selected menu:', key)
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-menu-demo {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.logo-text {
  white-space: nowrap;
}

.flex-grow {
  flex-grow: 1;
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.footer {
  text-align: center;
  background-color: #fff;
  border-top: 1px solid #e4e7ed;
  line-height: 60px;
}

.footer p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
</style>
