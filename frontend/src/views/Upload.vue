<template>
  <div class="upload-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Upload /></el-icon>
          <span>文件上传</span>
        </div>
      </template>

      <el-upload
        class="upload-demo"
        drag
        :multiple="true"
        :accept="acceptTypes"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
        :show-file-list="false"
        :auto-upload="true"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF, PNG, JPG, JPEG, DOC, DOCX, OFD, ZIP, RAR 格式，
            单个文件不超过 50MB
          </div>
        </template>
      </el-upload>

      <!-- 上传进度 -->
      <div v-if="uploadingFiles.length > 0" class="uploading-section">
        <h3>正在上传</h3>
        <div v-for="item in uploadingFiles" :key="item.uid" class="upload-item">
          <div class="upload-item-info">
            <span>{{ item.name }}</span>
            <span class="upload-percent">{{ item.percent }}%</span>
          </div>
          <el-progress :percentage="item.percent" :status="item.status" />
        </div>
      </div>

      <el-divider />

      <!-- 已上传文件列表 -->
      <div class="file-list">
        <div class="file-list-header">
          <h3>已上传文件 ({{ fileList.length }})</h3>
          <el-button type="primary" size="small" @click="loadFileList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="fileList"
          style="width: 100%"
          empty-text="暂无文件"
        >
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
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="getStatusType(row.status)"
                size="small"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="downloadFile(row)">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button link type="primary" size="small" @click="viewFile(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Refresh,
  Download,
  View,
  Delete
} from '@element-plus/icons-vue'
import {
  uploadFile,
  getFileList,
  deleteFile,
  getDownloadUrl
} from '../api/upload'

const acceptTypes = '.pdf,.png,.jpg,.jpeg,.doc,.docx,.ofd,.zip,.rar'
const fileList = ref([])
const uploadingFiles = ref([])
const loading = ref(false)

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

// 上传前验证
const beforeUpload = (file) => {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

// 自定义上传方法
const handleUpload = async (options) => {
  const { file } = options
  const uid = file.uid || Date.now()

  // 添加到上传列表
  const uploadItem = {
    uid,
    name: file.name,
    percent: 0,
    status: ''
  }
  uploadingFiles.value.push(uploadItem)

  try {
    // 调用上传 API
    const response = await uploadFile(file, (percent) => {
      // 更新进度
      const item = uploadingFiles.value.find(item => item.uid === uid)
      if (item) {
        item.percent = percent
      }
    })

    // 上传成功
    const item = uploadingFiles.value.find(item => item.uid === uid)
    if (item) {
      item.status = 'success'
    }

    ElMessage.success(`文件 ${file.name} 上传成功`)

    // 延迟后从上传列表中移除
    setTimeout(() => {
      const index = uploadingFiles.value.findIndex(item => item.uid === uid)
      if (index > -1) {
        uploadingFiles.value.splice(index, 1)
      }
    }, 2000)

    // 刷新文件列表
    loadFileList()

    return response
  } catch (error) {
    // 上传失败
    const item = uploadingFiles.value.find(item => item.uid === uid)
    if (item) {
      item.status = 'exception'
    }

    ElMessage.error(`文件 ${file.name} 上传失败：` + (error.message || '未知错误'))

    // 延迟后从上传列表中移除
    setTimeout(() => {
      const index = uploadingFiles.value.findIndex(item => item.uid === uid)
      if (index > -1) {
        uploadingFiles.value.splice(index, 1)
      }
    }, 2000)

    throw error
  }
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '0 B'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    'uploaded': 'success',
    'converting': 'warning',
    'converted': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'uploaded': '已上传',
    'converting': '转换中',
    'converted': '已转换',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 下载文件
const downloadFile = (file) => {
  const url = getDownloadUrl(file.id)
  const link = document.createElement('a')
  link.href = url
  link.download = file.original_name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载文件')
}

// 查看文件
const viewFile = (file) => {
  const url = getDownloadUrl(file.id)
  window.open(url, '_blank')
}

// 删除文件
const handleDelete = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.original_name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteFile(file.id)
    ElMessage.success('文件删除成功')

    // 刷新列表
    loadFileList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error.message || '未知错误'))
    }
  }
}
</script>

<style scoped>
.upload-page {
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

.upload-demo {
  width: 100%;
}

.uploading-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.uploading-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.upload-item {
  margin-bottom: 15px;
}

.upload-item:last-child {
  margin-bottom: 0;
}

.upload-item-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
}

.upload-percent {
  color: #409eff;
  font-weight: bold;
}

.file-list {
  margin-top: 20px;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.file-list-header h3 {
  margin: 0;
  font-size: 16px;
}
</style>
