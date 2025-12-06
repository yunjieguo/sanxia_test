<template>
  <div class="home">
    <!-- PDF 转换工具 -->
    <div class="tool-section">
      <div class="section-header">
        <el-icon :size="24" color="#409eff"><Refresh /></el-icon>
        <h2>PDF 转换</h2>
      </div>

      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" v-for="tool in convertTools" :key="tool.name">
          <el-card class="tool-card" shadow="hover" @click="goTo(tool.path)">
            <div class="tool-icon" :style="{ color: tool.color }">
              <component :is="tool.icon" :size="28" style="width: 40%" />
            </div>
            <h3>{{ tool.name }}</h3>
            <p>{{ tool.description }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 文档标注 -->
    <div class="tool-section">
      <div class="section-header">
        <el-icon :size="24" color="#e6a23c"><PriceTag /></el-icon>
        <h2>文档标注</h2>
      </div>

      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="tool-card" shadow="hover" @click="goTo('/edit/annotator')">
            <div class="tool-icon" style="color: #e6a23c">
              <PriceTag :size="28" style="width: 40%" />
            </div>
            <h3>文档标注</h3>
            <p>AI 辅助标注与信息提取</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Refresh, DocumentCopy, Picture, FolderOpened, Document, PriceTag } from '@element-plus/icons-vue'

const router = useRouter()
const backendStatus = ref(false)

const convertTools = [
  {
    name: 'Word 转 PDF',
    description: '将 Word 文档转换为 PDF 格式',
    icon: DocumentCopy,
    color: '#409eff',
    path: '/convert/word'
  },
  {
    name: '图片 转 PDF',
    description: '将图片文件转换为 PDF 格式',
    icon: Picture,
    color: '#67c23a',
    path: '/convert/image'
  },
  {
    name: '压缩包 转 PDF',
    description: '批量转换压缩包中的文件',
    icon: FolderOpened,
    color: '#e6a23c',
    path: '/convert/archive'
  },
  {
    name: 'OFD 转 PDF',
    description: '将 OFD 文档转换为 PDF 格式',
    icon: Document,
    color: '#f56c6c',
    path: '/convert/ofd'
  }
]

const goTo = (path) => {
  router.push(path)
}

const checkBackendStatus = async () => {
  try {
    await axios.get('/health')
    backendStatus.value = true
  } catch (error) {
    backendStatus.value = false
  }
}

onMounted(() => {
  checkBackendStatus()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.title-card {
  margin-bottom: 30px;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.page-title {
  margin: 0;
  font-size: 32px;
  font-weight: bold;
}

.page-desc {
  margin: 10px 0 0 0;
  font-size: 16px;
  opacity: 0.9;
}

.tool-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e4e7ed;
}

.section-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.tool-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  height: 200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.tool-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.tool-icon {
  margin-bottom: 12px;
}

.tool-card h3 {
  margin: 10px 0;
  font-size: 18px;
  color: #303133;
}

.tool-card p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.info-card {
  margin-top: 40px;
}

.info-card h3 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #303133;
}
</style>
