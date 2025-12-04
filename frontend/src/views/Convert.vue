<template>
  <div class="convert-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><DocumentCopy /></el-icon>
          <span>文档转换为 PDF</span>
        </div>
      </template>

      <el-alert
        title="功能说明"
        type="info"
        description="选择已上传的图片或 Word 文档，一键转换为 PDF 格式。支持 PNG、JPG、JPEG、GIF、BMP、DOC、DOCX"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- 文件列表 -->
      <div class="file-list-section">
        <div class="section-header">
          <h3>选择要转换的文件</h3>
          <el-button type="primary" size="small" @click="loadFileList">
            <el-icon><Refresh /></el-icon>
            刷新列表
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="imageFiles"
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="original_name" label="文件名" min-width="200" />
          <el-table-column prop="file_size" label="大小" width="120">
            <template #default="{ row }">
              {{ formatFileSize(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column prop="file_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click="convertSingle(row)"
                :disabled="row.status === 'converting' || row.status === 'converted'"
              >
                <el-icon><DocumentAdd /></el-icon>
                转换
              </el-button>
              <el-button
                v-if="row.conversion_id"
                link
                type="success"
                size="small"
                @click="downloadConverted(row.conversion_id)"
              >
                <el-icon><Download /></el-icon>
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="batch-actions" v-if="selectedFiles.length > 0">
          <el-alert
            :title="`已选择 ${selectedFiles.length} 个文件`"
            type="success"
            :closable="false"
          />
          <el-button type="primary" @click="convertBatch">
            <el-icon><DocumentAdd /></el-icon>
            批量转换
          </el-button>
        </div>
      </div>

      <el-divider />

      <!-- 转换进度 -->
      <div v-if="convertingTasks.length > 0" class="converting-section">
        <h3>转换进度</h3>
        <div v-for="task in convertingTasks" :key="task.file_id" class="convert-task">
          <div class="task-info">
            <span>{{ task.fileName }}</span>
            <span class="task-status">{{ task.statusText }}</span>
          </div>
          <el-progress
            :percentage="task.progress"
            :status="task.status === 'failed' ? 'exception' : task.status === 'completed' ? 'success' : ''"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DocumentCopy,
  DocumentAdd,
  Refresh,
  Download
} from '@element-plus/icons-vue'
import { getFileList } from '../api/upload'
import {
  convertToPDF,
  getConversionStatus,
  getConversionDownloadUrl
} from '../api/convert'

const fileList = ref([])
const selectedFiles = ref([])
const loading = ref(false)
const convertingTasks = ref([])

// 显示可转换的文件（图片和 Word 文档）
const imageFiles = computed(() => {
  return fileList.value.filter(file =>
    ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'doc', 'docx'].includes(file.file_type.toLowerCase())
  )
})

// 页面加载时获取文件列表
onMounted(() => {
  loadFileList()
})

// 加载文件列表
const loadFileList = async () => {
  loading.value = true
  try {
    const response = await getFileList()
    fileList.value = response.files || []
  } catch (error) {
    ElMessage.error('获取文件列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 处理文件选择
const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

// 转换单个文件
const convertSingle = async (file) => {
  try {
    // 添加到转换任务列表
    const task = {
      file_id: file.id,
      fileName: file.original_name,
      progress: 0,
      status: 'processing',
      statusText: '转换中...',
      conversion_id: null
    }
    convertingTasks.value.push(task)

    // 调用转换 API
    const result = await convertToPDF(file.id)
    task.conversion_id = result.conversion_id

    // 轮询转换状态
    await pollConversionStatus(task)

  } catch (error) {
    ElMessage.error(`转换失败：${error.message || '未知错误'}`)
    // 更新任务状态为失败
    const taskIndex = convertingTasks.value.findIndex(t => t.file_id === file.id)
    if (taskIndex > -1) {
      convertingTasks.value[taskIndex].status = 'failed'
      convertingTasks.value[taskIndex].statusText = '转换失败'
      convertingTasks.value[taskIndex].progress = 0
    }
  }
}

// 批量转换
const convertBatch = async () => {
  for (const file of selectedFiles.value) {
    await convertSingle(file)
    // 添加延迟避免并发过多
    await new Promise(resolve => setTimeout(resolve, 500))
  }
}

// 轮询转换状态
const pollConversionStatus = async (task) => {
  const maxAttempts = 30  // 最多轮询30次
  let attempts = 0

  const poll = async () => {
    try {
      const status = await getConversionStatus(task.conversion_id)

      task.progress = status.progress || 0
      task.statusText = getConversionStatusText(status.status)

      if (status.status === 'completed') {
        task.status = 'completed'
        task.progress = 100
        ElMessage.success(`${task.fileName} 转换成功`)

        // 更新文件列表中的状态
        const fileIndex = fileList.value.findIndex(f => f.id === task.file_id)
        if (fileIndex > -1) {
          fileList.value[fileIndex].status = 'converted'
          fileList.value[fileIndex].conversion_id = task.conversion_id
        }

        // 2秒后从转换任务列表中移除
        setTimeout(() => {
          const index = convertingTasks.value.findIndex(t => t.file_id === task.file_id)
          if (index > -1) {
            convertingTasks.value.splice(index, 1)
          }
        }, 2000)

        return
      }

      if (status.status === 'failed') {
        task.status = 'failed'
        task.statusText = status.error_message || '转换失败'
        ElMessage.error(`${task.fileName} 转换失败`)
        return
      }

      // 继续轮询
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(poll, 1000)
      } else {
        task.status = 'failed'
        task.statusText = '转换超时'
        ElMessage.error(`${task.fileName} 转换超时`)
      }

    } catch (error) {
      task.status = 'failed'
      task.statusText = '查询状态失败'
      console.error('查询转换状态失败:', error)
    }
  }

  await poll()
}

// 下载转换后的文件
const downloadConverted = (conversionId) => {
  const url = getConversionDownloadUrl(conversionId)
  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载文件')
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '0 B'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    'uploaded': 'info',
    'converting': 'warning',
    'converted': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'uploaded': '待转换',
    'converting': '转换中',
    'converted': '已转换',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取转换状态文本
const getConversionStatusText = (status) => {
  const statusMap = {
    'pending': '等待中...',
    'processing': '转换中...',
    'completed': '转换完成',
    'failed': '转换失败'
  }
  return statusMap[status] || status
}
</script>

<style scoped>
.convert-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.file-list-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
}

.batch-actions {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.converting-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.converting-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.convert-task {
  margin-bottom: 15px;
}

.convert-task:last-child {
  margin-bottom: 0;
}

.task-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
}

.task-status {
  color: #409eff;
  font-weight: bold;
}
</style>
