/**
 * 鏍囨敞鐩稿叧 API
 */
import request from '../utils/request'

/**
 * 鍒涘缓鏍囨敞
 * @param {Object} data 鏍囨敞鏁版嵁
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
 * 鎵归噺鍒涘缓鏍囨敞
 * @param {Object} data 鎵归噺鏍囨敞鏁版嵁
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
 * 鑾峰彇鏂囦欢鐨勬墍鏈夋爣娉?
 * @param {number} fileId 鏂囦欢ID
 * @param {number} pageNumber 椤电爜锛堝彲閫夛級
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
 * 鑾峰彇鏍囨敞璇︽儏
 * @param {number} annotationId 鏍囨敞ID
 * @returns {Promise}
 */
export function getAnnotation(annotationId) {
  return request({
    url: `/annotations/${annotationId}`,
    method: 'get'
  })
}

/**
 * 鏇存柊鏍囨敞
 * @param {number} annotationId 鏍囨敞ID
 * @param {Object} data 鏇存柊鏁版嵁
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
 * 鍒犻櫎鏍囨敞
 * @param {number} annotationId 鏍囨敞ID
 * @returns {Promise}
 */
export function deleteAnnotation(annotationId) {
  return request({
    url: `/annotations/${annotationId}`,
    method: 'delete'
  })
}

/**
 * 鍒犻櫎鏂囦欢鐨勬墍鏈夋爣娉?
 * @param {number} fileId 鏂囦欢ID
 * @returns {Promise}
 */
export function deleteFileAnnotations(fileId) {
  return request({
    url: `/annotations/file/${fileId}`,
    method: 'delete'
  })
}

/**
 * 鍒涘缓妯℃澘
 * @param {Object} data 妯℃澘鏁版嵁
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
 * 鑾峰彇妯℃澘鍒楄〃
 * @param {string} documentType 鏂囨。绫诲瀷锛堝彲閫夛級
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
 * 鑾峰彇妯℃澘璇︽儏
 * @param {number} templateId 妯℃澘ID
 * @returns {Promise}
 */
export function getTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'get'
  })
}

/**
 * 鏇存柊妯℃澘
 * @param {number} templateId 妯℃澘ID
 * @param {Object} data 鏇存柊鏁版嵁
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
 * 鍒犻櫎妯℃澘
 * @param {number} templateId 妯℃澘ID
 * @returns {Promise}
 */
export function deleteTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'delete'
  })
}

/**
 * 搴旂敤妯℃澘鍒版枃浠?
 * @param {number} templateId 妯℃澘ID
 * @param {number} fileId 鏂囦欢ID
 * @returns {Promise}
 */
export function applyTemplate(templateId, fileId) {
  return request({
    url: `/templates/${templateId}/apply`,
    method: 'post',
    data: { file_id: fileId }
  })
}

export function applyTemplateMatching(templateId, fileId) {
  return request({
    url: `/templates/${templateId}/apply-matching`,
    method: 'post',
    data: { file_id: fileId }
  })
}

/**
 * 涓婁紶鏍囨敞鍥剧墖
 * @param {File} file 鍥剧墖鏂囦欢
 * @returns {Promise}
 */
export function uploadAnnotationImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/annotations/upload-image',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 鑾峰彇鏍囨敞鍥剧墖URL
 * @param {string} imagePath 鍥剧墖璺緞
 * @returns {string} 瀹屾暣鐨勫浘鐗嘦RL
 */
const getApiBaseUrl = () => {
  const envBase = import.meta.env.VITE_API_BASE_URL
  if (envBase) return envBase.replace(/\/+$/, '')

  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location
    const portPart = port ? `:${port}` : ''
    return `${protocol}//${hostname}${portPart}`
  }

  return ''
}

export function getAnnotationImageUrl(imagePath) {
  if (!imagePath) return ''
  // 浠?annotation_images/xxx.jpg 涓彁鍙栨枃浠跺悕
  const filename = imagePath.split('/').pop()
  return `${getApiBaseUrl()}/api/annotations/images/${filename}`
}

/**
 * 鍒犻櫎鏍囨敞鍥剧墖
 * @param {string} imagePath 鍥剧墖璺緞
 * @returns {Promise}
 */
export function deleteAnnotationImage(imagePath) {
  if (!imagePath) return Promise.resolve()
  const filename = imagePath.split('/').pop()
  return request({
    url: `/annotations/images/${filename}`,
    method: 'delete'
  })
}

/**
 * 鑾峰彇鐢荤瑪鏁版嵁
 * @param {number} fileId 鏂囦欢ID
 * @returns {Promise}
 */
export function getPaintData(fileId) {
  return request({
    url: `/annotations/paint/${fileId}`,
    method: 'get'
  })
}

/**
 * 淇濆瓨鐢荤瑪鏁版嵁
 * @param {number} fileId 鏂囦欢ID
 * @param {Array} strokes 鐢荤瑪杞ㄨ抗鍒楄〃
 * @returns {Promise}
 */
export function savePaintData(fileId, strokes = []) {
  return request({
    url: `/annotations/paint/${fileId}`,
    method: 'post',
    data: { strokes }
  })
}
// LLM 一键应用模板
export function applyTemplateLLM(templateId, fileId, payload = {}) {
  return request({
    url: `/templates/${templateId}/apply-llm`,
    method: 'post',
    data: { file_id: fileId, template_id: templateId, ...payload }
  })
}
