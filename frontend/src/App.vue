<template>
  <el-config-provider :locale="locale">
    <div id="app">
      <el-container style="height: 100vh">
        <!-- 顶部导航栏 -->
        <el-header style="background-color: #409eff; color: #fff">
          <div class="header-content">
            <div class="logo">
              <el-icon :size="24"><Document /></el-icon>
              <span class="title">PDF文档处理系统</span>
            </div>
            <el-button type="primary" plain size="small" @click="goHome">首页</el-button>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { Document } from '@element-plus/icons-vue'

const locale = zhCn
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => {
  const path = route.path
  // 若在 PDF 工具相关页面，高亮 PDF 工具菜单
  if (path.startsWith('/pdf-tools') || path.startsWith('/convert') || path.startsWith('/edit')) {
    return '/pdf-tools'
  }
  return path
})

const goHome = () => {
  router.push('/')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.el-header {
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}
</style>
