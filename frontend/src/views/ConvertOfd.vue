<template>
  <div class="convert-ofd">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>OFD 转 PDF</span>
        </div>
      </template>

      <!-- 上传 -->
      <el-upload
        class="upload-demo"
        drag
        :multiple="true"
        :accept="acceptTypes"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
        :show-file-list="false"
        :auto-upload="true"
        style="margin-bottom: 20px"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            仅支持 OFD，单个文件不超过 50MB
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

      <!-- 列表 -->
      <div class="file-list-section">
        <div class="section-header">
          <h3>OFD 文件列表</h3>
          <el-button type="primary" size="small" @click="loadFileList">
            <el-icon><Refresh /></el-icon>
            刷新列表
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="ofdFiles"
          style="width: 100%"
          empty-text="暂无 OFD 文件"
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
          <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="downloadFile(row)">
                <el-icon><Download /></el-icon>
                下载原文件
              </el-button>
              <el-button link type="danger" size="small" @click="deleteOriginal(row)">
                <el-icon><Delete /></el-icon>
                删除原文件
              </el-button><br />
              <el-button
                v-if="row.status !== 'converted' && row.status !== 'converting'"
                link
                type="primary"
                size="small"
                @click="convertSingle(row)"
              >
                <el-icon><DocumentAdd /></el-icon>
                转换为PDF
              </el-button>
              <el-button
                v-if="row.conversion_id"
                link
                type="success"
                size="small"
                @click="downloadConverted(row.conversion_id)"
              >
                <el-icon><Download /></el-icon>
                下载PDF
              </el-button>
            </template>
          </el-table-column>
        </el-table>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, UploadFilled, Refresh, Download, DocumentAdd, Delete } from '@element-plus/icons-vue'
import { uploadFile, getFileList, getDownloadUrl, deleteFile } from '../api/upload'
import {
  convertToPDF,
  getConversionStatus,
  getConversionDownloadUrl
} from '../api/convert'

const STORAGE_KEY = 'conversion_map_ofd'
const acceptTypes = '.ofd'
const fileList = ref([])
const loading = ref(false)
const uploadingFiles = ref([])
const convertingTasks = ref([])
const conversionMap = ref(loadConversionMap())

const ofdFiles = computed(() =>
  fileList.value.filter(file =>
    ['ofd'].includes(file.file_type.toLowerCase())
  )
)

onMounted(() => {
  loadFileList()
})

const loadFileList = async () => {
  loading.value = true
  try {
    const response = await getFileList()
    const files = response.files || []
    fileList.value = files.map(f => ({
      ...f,
      conversion_id: conversionMap.value[f.id] || f.conversion_id
    }))
  } catch (error) {
    ElMessage.error('获取文件列表失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

const handleUpload = async (options) => {
  const { file } = options
  const uid = file.uid || Date.now()

  const uploadItem = {
    uid,
    name: file.name,
    percent: 0,
    status: ''
  }
  uploadingFiles.value.push(uploadItem)

  try {
    await uploadFile(file, (percent) => {
      const item = uploadingFiles.value.find(item => item.uid === uid)
      if (item) {
        item.percent = percent
      }
    })

    const item = uploadingFiles.value.find(item => item.uid === uid)
    if (item) {
      item.status = 'success'
    }

    ElMessage.success(`文件 ${file.name} 上传成功`)

    setTimeout(() => {
      const index = uploadingFiles.value.findIndex(item => item.uid === uid)
      if (index > -1) {
        uploadingFiles.value.splice(index, 1)
      }
    }, 2000)

    loadFileList()
  } catch (error) {
    const item = uploadingFiles.value.find(item => item.uid === uid)
    if (item) {
      item.status = 'exception'
    }
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  }
}

const convertSingle = async (file) => {
  try {
    const task = {
      file_id: file.id,
      fileName: file.original_name,
      progress: 0,
      status: 'processing',
      statusText: '转换中...',
      conversion_id: null
    }
    convertingTasks.value.push(task)

    const result = await convertToPDF(file.id)
    task.conversion_id = result.conversion_id

    await pollConversionStatus(task)

  } catch (error) {
    ElMessage.error(`转换失败: ${error.message || '未知错误'}`)
    const taskIndex = convertingTasks.value.findIndex(t => t.file_id === file.id)
    if (taskIndex > -1) {
      convertingTasks.value[taskIndex].status = 'failed'
      convertingTasks.value[taskIndex].statusText = '转换失败'
      convertingTasks.value[taskIndex].progress = 0
    }
  }
}

const pollConversionStatus = async (task) => {
  const maxAttempts = 30
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

        const fileIndex = fileList.value.findIndex(f => f.id === task.file_id)
        if (fileIndex > -1) {
          fileList.value[fileIndex].status = 'converted'
          fileList.value[fileIndex].conversion_id = task.conversion_id
        }
        saveConversionId(task.file_id, task.conversion_id)

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
      console.error('查询转换状态失败', error)
    }
  }

  await poll()
}

const downloadConverted = (conversionId) => {
  const url = getConversionDownloadUrl(conversionId)
  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载 PDF')
}

const downloadFile = (row) => {
  const url = getDownloadUrl(row.id)
  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载原文件')
}

const deleteOriginal = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除文件"${row.original_name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteFile(row.id)
    fileList.value = fileList.value.filter(f => f.id !== row.id)
    const map = { ...conversionMap.value }
    delete map[row.id]
    conversionMap.value = map
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversionMap.value))
    ElMessage.success('已删除原文件')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

const formatFileSize = (size) => {
  if (!size) return '0 B'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatDateTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

const getConversionStatusText = (status) => {
  const statusMap = {
    pending: '等待中...',
    processing: '转换中...',
    completed: '转换完成',
    failed: '转换失败'
  }
  return statusMap[status] || status
}

function loadConversionMap() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch (e) {
    console.error('加载本地 conversion_map 失败', e)
    return {}
  }
}

function saveConversionId(fileId, conversionId) {
  conversionMap.value = { ...conversionMap.value, [fileId]: conversionId }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversionMap.value))
}
</script>

<style scoped>
.convert-ofd {
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

.uploading-section {
  margin-bottom: 20px;
}

.upload-item {
  margin-bottom: 12px;
}

.upload-item-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.upload-percent {
  color: #409eff;
}

.converting-section {
  margin-top: 20px;
}

.convert-task {
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.task-status {
  color: #409eff;
}
</style>
