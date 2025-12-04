/**
 * 文件转换相关 API
 */
import request from '../utils/request'

/**
 * 转换为 PDF
 * @param {Number} fileId - 文件ID
 * @returns {Promise}
 */
export function convertToPDF(fileId) {
  return request({
    url: '/convert/to-pdf',
    method: 'post',
    data: { file_id: fileId }
  })
}

/**
 * 查询转换状态
 * @param {Number} conversionId - 转换任务ID
 * @returns {Promise}
 */
export function getConversionStatus(conversionId) {
  return request({
    url: `/convert/status/${conversionId}`,
    method: 'get'
  })
}

/**
 * 获取转换结果
 * @param {Number} conversionId - 转换任务ID
 * @returns {Promise}
 */
export function getConversionResult(conversionId) {
  return request({
    url: `/convert/result/${conversionId}`,
    method: 'get'
  })
}

/**
 * 下载转换结果
 * @param {Number} conversionId - 转换任务ID
 * @returns {String} - 下载链接
 */
export function getConversionDownloadUrl(conversionId) {
  return `/api/convert/download/${conversionId}`
}

/**
 * 删除转换任务
 * @param {Number} conversionId - 转换任务ID
 * @returns {Promise}
 */
export function deleteConversion(conversionId) {
  return request({
    url: `/convert/${conversionId}`,
    method: 'delete'
  })
}
