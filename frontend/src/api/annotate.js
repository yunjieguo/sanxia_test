/**
 * 标注相关 API
 */
import request from '../utils/request'

/**
 * 创建标注
 * @param {Object} data 标注数据
 * @returns {Promise}
 */
export function createAnnotation(data) {
  return request({
    url: '/annotations',
    method: 'post',
    data
  })
}

/**
 * 批量创建标注
 * @param {Object} data 批量标注数据
 * @returns {Promise}
 */
export function createAnnotationsBatch(data) {
  return request({
    url: '/annotations/batch',
    method: 'post',
    data
  })
}

/**
 * 获取文件的所有标注
 * @param {number} fileId 文件ID
 * @param {number} pageNumber 页码（可选）
 * @returns {Promise}
 */
export function getFileAnnotations(fileId, pageNumber = null) {
  const params = pageNumber !== null ? { page_number: pageNumber } : {}
  return request({
    url: `/annotations/file/${fileId}`,
    method: 'get',
    params
  })
}

/**
 * 获取标注详情
 * @param {number} annotationId 标注ID
 * @returns {Promise}
 */
export function getAnnotation(annotationId) {
  return request({
    url: `/annotations/${annotationId}`,
    method: 'get'
  })
}

/**
 * 更新标注
 * @param {number} annotationId 标注ID
 * @param {Object} data 更新数据
 * @returns {Promise}
 */
export function updateAnnotation(annotationId, data) {
  return request({
    url: `/annotations/${annotationId}`,
    method: 'put',
    data
  })
}

/**
 * 删除标注
 * @param {number} annotationId 标注ID
 * @returns {Promise}
 */
export function deleteAnnotation(annotationId) {
  return request({
    url: `/annotations/${annotationId}`,
    method: 'delete'
  })
}

/**
 * 删除文件的所有标注
 * @param {number} fileId 文件ID
 * @returns {Promise}
 */
export function deleteFileAnnotations(fileId) {
  return request({
    url: `/annotations/file/${fileId}`,
    method: 'delete'
  })
}

/**
 * 创建模板
 * @param {Object} data 模板数据
 * @returns {Promise}
 */
export function createTemplate(data) {
  return request({
    url: '/templates',
    method: 'post',
    data
  })
}

/**
 * 获取模板列表
 * @param {string} documentType 文档类型（可选）
 * @returns {Promise}
 */
export function getTemplates(documentType = null) {
  const params = documentType ? { document_type: documentType } : {}
  return request({
    url: '/templates',
    method: 'get',
    params
  })
}

/**
 * 获取模板详情
 * @param {number} templateId 模板ID
 * @returns {Promise}
 */
export function getTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'get'
  })
}

/**
 * 更新模板
 * @param {number} templateId 模板ID
 * @param {Object} data 更新数据
 * @returns {Promise}
 */
export function updateTemplate(templateId, data) {
  return request({
    url: `/templates/${templateId}`,
    method: 'put',
    data
  })
}

/**
 * 删除模板
 * @param {number} templateId 模板ID
 * @returns {Promise}
 */
export function deleteTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'delete'
  })
}

/**
 * 应用模板到文件
 * @param {number} templateId 模板ID
 * @param {number} fileId 文件ID
 * @returns {Promise}
 */
export function applyTemplate(templateId, fileId) {
  return request({
    url: `/templates/${templateId}/apply`,
    method: 'post',
    data: { file_id: fileId }
  })
}
