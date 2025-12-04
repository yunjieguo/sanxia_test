/**
 * 文件上传相关 API
 */
import request from '../utils/request'

/**
 * 上传文件
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 上传进度回调
 * @returns {Promise}
 */
export function uploadFile(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    }
  })
}

/**
 * 获取文件列表
 * @param {Number} skip - 跳过的记录数
 * @param {Number} limit - 返回的最大记录数
 * @returns {Promise}
 */
export function getFileList(skip = 0, limit = 100) {
  return request({
    url: '/files',
    method: 'get',
    params: { skip, limit }
  })
}

/**
 * 获取文件详情
 * @param {Number} fileId - 文件ID
 * @returns {Promise}
 */
export function getFileInfo(fileId) {
  return request({
    url: `/files/${fileId}`,
    method: 'get'
  })
}

/**
 * 删除文件
 * @param {Number} fileId - 文件ID
 * @returns {Promise}
 */
export function deleteFile(fileId) {
  return request({
    url: `/files/${fileId}`,
    method: 'delete'
  })
}

/**
 * 下载文件
 * @param {Number} fileId - 文件ID
 * @returns {String} - 下载链接
 */
export function getDownloadUrl(fileId) {
  return `/api/files/${fileId}/download`
}

/**
 * 批量上传文件
 * @param {Array<File>} files - 文件数组
 * @param {Function} onProgress - 进度回调
 * @returns {Promise}
 */
export async function uploadMultipleFiles(files, onProgress) {
  const results = []
  const total = files.length

  for (let i = 0; i < files.length; i++) {
    try {
      const result = await uploadFile(files[i], (percent) => {
        if (onProgress) {
          const overallPercent = Math.round(((i + percent / 100) / total) * 100)
          onProgress({
            current: i + 1,
            total,
            percent: overallPercent,
            currentFile: files[i].name,
            currentFilePercent: percent
          })
        }
      })
      results.push({ success: true, data: result })
    } catch (error) {
      results.push({ success: false, error, fileName: files[i].name })
    }
  }

  return results
}
