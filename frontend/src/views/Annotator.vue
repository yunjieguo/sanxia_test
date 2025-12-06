<template>
  <div class="annotator-page">
    <!-- 顶部工具栏 -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-icon><PriceTag /></el-icon>
          <span class="toolbar-title">文档标注</span>
        </div>
        <div class="toolbar-center">
          <el-input
            v-model="searchKeyword"
            placeholder="按文件名搜索 PDF"
            clearable
            size="small"
            style="width: 240px; margin-right: 10px"
          />
          <el-select
            v-model="selectedFileId"
            placeholder="选择要标注的文件"
            style="width: 300px"
            @change="loadFile"
            clearable
          >
            <el-option
              v-for="file in filteredFiles"
              :key="file.id"
              :label="file.original_name"
              :value="file.id"
            />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" :disabled="!selectedFileId" @click="saveAnnotations">
            <el-icon><DocumentChecked /></el-icon>
            保存标注
          </el-button>
          <el-button :disabled="!selectedFileId" @click="loadAnnotations">
            <el-icon><FolderOpened /></el-icon>
            加载标注
          </el-button>
          <el-button :disabled="!selectedFileId || exportingPdf" @click="exportAnnotatedPdf">
            <el-icon><Document /></el-icon>
            导出标注 PDF
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <div class="main-content" v-if="selectedFileId">
      <!-- 左侧：PDF 预览和标注画布 -->
      <el-card class="pdf-container" shadow="never">
        <template #header>
          <div class="pdf-header">
            <span>PDF 预览</span>
            <div class="pdf-controls">
              <el-button-group>
                <el-button size="small" :disabled="currentPage <= 1" @click="prevPage">
                  <el-icon><ArrowLeft /></el-icon>
                  上一页
                </el-button>
                <el-button size="small" disabled>
                  {{ currentPage }} / {{ totalPages }}
                </el-button>
                <el-button size="small" :disabled="currentPage >= totalPages" @click="nextPage">
                  下一页
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </el-button-group>
              <el-button-group style="margin-left: 10px">
                <el-button size="small" @click="zoomOut">
                  <el-icon><ZoomOut /></el-icon>
                </el-button>
                <el-button size="small" disabled>
                  {{ Math.round(scale * 100) }}%
                </el-button>
                <el-button size="small" @click="zoomIn">
                  <el-icon><ZoomIn /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>
        </template>

        <div class="paint-toolbar">
          <el-button-group size="small">
            <el-button :type="paintingMode ? 'primary' : 'default'" @click="togglePainting">
              <el-icon><Edit /></el-icon>
              画笔
            </el-button>
            <el-button :type="paintTool === 'free' ? 'primary' : 'default'" @click="selectPaintTool('free')">
              曲线
            </el-button>
            <el-button :type="paintTool === 'line' ? 'primary' : 'default'" @click="selectPaintTool('line')">
              直线
            </el-button>
            <el-button :type="paintTool === 'rect' ? 'primary' : 'default'" @click="selectPaintTool('rect')">
              矩形
            </el-button>
            <el-button :type="paintTool === 'eraser' ? 'primary' : 'default'" @click="selectPaintTool('eraser')">
              橡皮
            </el-button>
          </el-button-group>
          <div class="paint-controls">
            <span class="label">粗细</span>
            <el-slider v-model="paintWidth" :min="1" :max="10" :step="1" style="width: 120px" />
            <span class="label">颜色</span>
            <el-color-picker v-model="paintColor" show-alpha />
            <el-button size="small" @click="undoPaint">回退</el-button>
            <el-button size="small" @click="clearPaint">清空</el-button>
          </div>
        </div>

        <div class="pdf-viewer-wrapper" ref="pdfViewerWrapper">
          <div class="pdf-viewer" :style="{ transform: `scale(${scale})`, transformOrigin: 'top center' }">
            <vue-pdf-embed
              ref="pdfEmbed"
              :source="pdfSource"
              :page="currentPage"
              @loaded="onPdfLoaded"
              @error="onPdfError"
            />
            <!-- Canvas 标注层 -->
            <canvas
              ref="annotationCanvas"
              class="annotation-canvas"
              @mousedown="startDrawing"
              @mousemove="drawing"
              @mouseup="stopDrawing"
              @mouseleave="onCanvasLeave"
            ></canvas>
          </div>
        </div>
      </el-card>

      <!-- 右侧：工具面板和标注列表 -->
      <el-card class="tools-container" shadow="never">
        <el-tabs v-model="activeTab">
          <!-- 标注工具 -->
          <el-tab-pane label="标注工具" name="tools">
            <div class="tools-panel">
              <el-form label-width="80px">
                <el-form-item label="标注类型">
                  <el-select v-model="currentTool.type" placeholder="选择标注类型">
                    <el-option label="文本" value="text" />
                    <!-- <el-option label="长文本" value="long_text" /> -->
                    <el-option label="图片" value="image" />
                  </el-select>
                </el-form-item>

                <el-form-item label="字段名称">
                  <template v-if="currentTool.type === 'image'">
                    <el-input value="图片" disabled />
                  </template>
                  <el-select
                    v-else
                    v-model="currentTool.fieldName"
                    placeholder="选择或输入字段名"
                    allow-create
                    filterable
                  >
                    <el-option label="合同名称" value="contract_name" />
                    <el-option label="合同日期" value="contract_date" />
                    <el-option label="合同编号" value="contract_number" />
                    <el-option label="合同金额" value="contract_amount" />
                    <el-option label="甲方名称" value="party_a" />
                    <el-option label="乙方名称" value="party_b" />
                  </el-select>
                </el-form-item>

                <el-form-item label="字段值" v-if="currentTool.type !== 'image'">
                  <el-input
                    v-model="currentTool.fieldValue"
                    placeholder="可选，提取后自动填充"
                    type="textarea"
                    :rows="2"
                  />
                </el-form-item>

                <el-form-item label="文字颜色" v-if="currentTool.type !== 'image'">
                  <el-color-picker
                    v-model="currentTool.fontColor"
                    show-alpha
                    :predefine="['#303133', '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']"
                  />
                </el-form-item>

                <el-form-item label="字体" v-if="currentTool.type !== 'image'">
                  <el-select v-model="currentTool.fontFamily" filterable allow-create placeholder="选择或输入字体">
                    <el-option label="微软雅黑" value="Microsoft YaHei" />
                    <el-option label="黑体" value="SimHei" />
                    <el-option label="宋体" value="SimSun" />
                  </el-select>
                </el-form-item>

                <!-- 图片上传组件（当标注类型为图片时显示） -->
                <el-form-item label="上传图片" v-if="currentTool.type === 'image'">
                  <el-upload
                    class="image-uploader"
                    :auto-upload="false"
                    :show-file-list="false"
                    :on-change="handleImageChange"
                    accept="image/*"
                  >
                    <img v-if="currentTool.imagePreview" :src="currentTool.imagePreview" class="uploaded-image" />
                    <el-icon v-else class="image-uploader-icon"><Plus /></el-icon>
                  </el-upload>
                  <div class="upload-tip">点击上传图片（支持 JPG、PNG 等格式）</div>
                  <el-button
                    v-if="currentTool.imageFile"
                    size="small"
                    type="danger"
                    text
                    @click="clearUploadedImage"
                    style="margin-top: 8px"
                  >
                    清除图片
                  </el-button>
                </el-form-item>

                <el-form-item label="文字大小" v-if="currentTool.type !== 'image'">
                  <el-slider
                    v-model="currentTool.fontSize"
                    :min="8"
                    :max="32"
                    :step="1"
                    style="width: 200px"
                    show-input
                    :show-input-controls="false"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" :disabled="!canAnnotate" @click="enableDrawMode">
                    <el-icon><Edit /></el-icon>
                    开始标注
                  </el-button>
                  <el-button @click="cancelDrawMode" v-if="isDrawing">
                    取消
                  </el-button>
                  <el-button
                    type="success"
                    :disabled="!selectedAnnotation"
                    @click="updateSelectedAnnotation"
                  >
                    更新选中
                  </el-button>
                </el-form-item>
              </el-form>

              <el-divider />

              <div class="tool-tips">
                <el-alert
                  title="使用提示"
                  type="info"
                  :closable="false"
                  v-html="`
                  <div>1. 选择标注类型和字段名称; <br />
                  2. 点击“开始标注”; <br />
                  3. 在 PDF 上拖动鼠标框选区域; <br />
                  4. 完成后点击“保存标注”; <br />
                  </div>
                  `"
                />
              </div>
            </div>
          </el-tab-pane>

          <!-- 标注列表 -->
          <el-tab-pane
            :label="`标注列表${totalAnnotationCount ? '（' + totalAnnotationCount + '）' : ''}`"
            name="annotations"
          >
            <div class="annotations-header">
              <div>
                <strong>标注列表</strong>
                <span v-if="pageAnnotations.length">（{{ pageAnnotations.length }} 条）</span>
              </div>
              <el-button
                class="annotations-clear"
                type="danger"
                size="small"
                link
                :disabled="annotations.length === 0"
                @click="clearAnnotations"
              >
                清空
              </el-button>
            </div>
            <div class="annotations-list">
              <div v-if="annotations.length === 0" class="empty-annotations">
                <el-empty description="暂无标注" />
              </div>
              <div v-else>
                <div
                  v-for="(annotation, index) in pageAnnotations"
                  :key="annotation.id || index"
                  class="annotation-item"
                  :class="{ 'active': selectedAnnotation === annotation }"
                  @click="selectAnnotation(annotation)"
                >
                  <div class="annotation-header">
                    <el-tag :type="getAnnotationTypeColor(annotation.annotation_type)" size="small">
                      {{ getAnnotationTypeName(annotation.annotation_type) }}
                    </el-tag>
                    <span class="field-name">{{ getFieldNameCN(annotation.field_name) }}</span>
                    <el-tag size="small" type="info" style="margin-left: 6px;">
                      {{ (annotation.coordinates?.font_size || 12) }}px
                    </el-tag>
                    <el-button
                      type="danger"
                      size="small"
                      text
                      @click.stop="deleteAnnotation(annotation)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <div
                    class="annotation-value"
                    v-if="annotation.field_value"
                    :style="getAnnotationTextStyle(annotation)"
                  >
                    {{ annotation.field_value }}
                  </div>
                  <!-- 显示图片缩略图 -->
                  <div class="annotation-image" v-if="annotation.annotation_type === 'image' && annotation.image_path">
                    <img :src="getAnnotationImageUrl(annotation.image_path)" alt="标注图片" class="annotation-thumbnail" />
                  </div>
                  <div class="annotation-coords">
                    页码: {{ annotation.page_number }} |
                    坐标: ({{ Math.round(annotation.coordinates.x) }}, {{ Math.round(annotation.coordinates.y) }})
                  </div>
                </div>
              </div>

              <el-divider content-position="left">
                画笔/橡皮 <span v-if="pagePaintStrokes.length">（{{ pagePaintStrokes.length }} 条）</span>
              </el-divider>
              <div v-if="pagePaintStrokes.length === 0" class="empty-annotations">
                <el-empty description="当前页暂无画笔" />
              </div>
              <div v-else>
                <div
                  v-for="(stroke, idx) in pagePaintStrokes"
                  :key="idx"
                  class="annotation-item"
                >
                  <div class="annotation-header">
                    <el-tag size="small" type="warning">{{ stroke.type === 'eraser' ? '橡皮' : '画笔' }}</el-tag>
                    <span class="field-name">宽度 {{ stroke.width }}</span>
                    <span
                      v-if="stroke.type !== 'eraser'"
                      class="color-dot"
                      :style="{ background: stroke.color || '#f56c6c' }"
                      title="颜色"
                    ></span>
                    <el-button
                      type="danger"
                      size="small"
                      text
                      @click.stop="deletePaintStroke(stroke)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <div class="annotation-coords">
                    <template v-if="getStrokeBounds(stroke)">
                      范围: {{ Math.round(getStrokeBounds(stroke).x) }}, {{ Math.round(getStrokeBounds(stroke).y) }} -
                      {{ Math.round(getStrokeBounds(stroke).width) }} × {{ Math.round(getStrokeBounds(stroke).height) }}
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 模板 -->
          <el-tab-pane label="模板" name="templates">
            <div class="templates-panel">
              <el-button type="primary" @click="showCreateTemplateDialog = true" style="margin-bottom: 10px">
                <el-icon><Plus /></el-icon>
                创建模板
              </el-button>
              <div v-if="templates.length === 0">
                <el-empty description="暂无模板" />
              </div>
              <div v-else>
                <div
                  v-for="template in templates"
                  :key="template.id"
                  class="template-item"
                >
                  <div class="template-header">
                    <span class="template-name">{{ template.template_name }}</span>
                    <div>
                      <el-button size="small" @click="viewTemplate(template)" style="margin-right: 6px">
                        查看
                      </el-button>
                      <el-button size="small" @click="applyTemplateToFile(template.id)">
                        应用
                      </el-button>
                      <el-button type="danger" size="small" text @click="deleteTemplateById(template.id)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="template-info">
                    <el-tag size="small">{{ template.document_type }}</el-tag>
                    <span v-if="template.description">{{ template.description }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 未选择文件时的提示 -->
    <el-card v-else class="empty-state">
      <el-empty description="请先选择要标注的 PDF 文件">
        <div class="empty-actions">
          <el-button type="primary" @click="goToConvert">
            <el-icon><Upload /></el-icon>
            转换文件为 PDF
          </el-button>
          <div class="upload-stack">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,application/pdf"
              :on-change="handlePdfUpload"
            >
              <el-button class="upload-pdf-btn">
                <el-icon><Upload /></el-icon>
                上传 PDF
              </el-button>
            </el-upload>
            <el-button class="history-btn" @click="openUploadHistory">
              历史上传记录
            </el-button>
          </div>
        </div>
        <div v-if="uploadingPdf" class="upload-progress">上传中 {{ uploadPercent }}%</div>
      </el-empty>
    </el-card>

    <!-- 创建模板对话框 -->
    <el-dialog v-model="showCreateTemplateDialog" title="创建标注模板" width="600px">
      <el-form :model="newTemplate" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="newTemplate.template_name" placeholder="例如：标准采购合同" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-input v-model="newTemplate.document_type" placeholder="例如：contract" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="newTemplate.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="createNewTemplate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="showTemplatePreviewDialog"
      title="模板标注点"
      width="1070px"
      top="8vh"
    >
      <div v-if="previewTemplate" class="template-preview-body">
        <p style="margin-bottom: 10px;">
          <strong>模板名称：</strong>{{ previewTemplate.template_name }}
          <span v-if="previewTemplate.document_type">（{{ previewTemplate.document_type }}）</span>
        </p>
        <el-table
          :data="(previewTemplate.template_data && previewTemplate.template_data.fields) || []"
          size="small"
          border
        >
          <el-table-column label="字段名称" min-width="140">
            <template #default="{ row }">
              {{ getFieldNameCN(row.field_name) }}
            </template>
          </el-table-column>
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              {{ getFieldTypeName(row.field_type) }}
            </template>
          </el-table-column>
        <el-table-column label="字段值" min-width="220">
          <template #default="{ row }">
            <template v-if="row.field_type === 'image' && (row.image_path || row.field_value)">
              <div class="template-image" @click="openTemplateImage(row.image_path || row.field_value)">
                <img :src="getAnnotationImageUrl(row.image_path || row.field_value)" alt="模板图片" />
              </div>
            </template>
            <template v-else-if="row.field_type !== 'image'">
              <span
                class="template-text"
                :style="{
                  color: row.coordinates?.font_color || '#333',
                  fontFamily: sanitizeFontFamily(row.coordinates?.font_family) || 'SimHei'
                }"
              >
                {{ row.field_value || '—' }}
              </span>
            </template>
            <template v-else>
              {{ row.field_value || '—' }}
            </template>
          </template>
        </el-table-column>
          <el-table-column label="字体大小" width="90">
            <template #default="{ row }">
              {{ (row.coordinates?.font_size || row.coordinates?.fontSize || 12) }}px
            </template>
          </el-table-column>
          <el-table-column prop="page_number" label="页码" width="80">
            <template #default="{ row }">
              {{ row.page_number || 1 }}
            </template>
          </el-table-column>
          <el-table-column label="坐标" min-width="340">
            <template #default="{ row }">
              <span v-if="row.coordinates">
                宽约 {{ (row.coordinates.width || 0).toFixed(2) }}、高约 {{ (row.coordinates.height || 0).toFixed(2) }}，
                左上角位于 (X:{{ (row.coordinates.x || 0).toFixed(2) }} Y:{{ (row.coordinates.y || 0).toFixed(2) }})
              </span>
              <span v-else>未设置</span>
            </template>
          </el-table-column>
        </el-table>

        <el-divider content-position="left">画笔/橡皮</el-divider>
        <el-table
          :data="(previewTemplate.template_data && previewTemplate.template_data.paint_data) || []"
          size="small"
          border
          v-if="previewTemplate.template_data && previewTemplate.template_data.paint_data && previewTemplate.template_data.paint_data.length"
        >
          <el-table-column label="类型" width="90">
            <template #default="{ row }">
              {{ row.type === 'eraser' ? '橡皮' : '画笔' }}
            </template>
          </el-table-column>
          <el-table-column label="颜色" width="120">
            <template #default="{ row }">
              <span v-if="row.type !== 'eraser'" class="color-dot" :style="{ background: row.color || '#f56c6c' }"></span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="宽度" width="80">
            <template #default="{ row }">
              {{ row.width || 0 }}
            </template>
          </el-table-column>
          <el-table-column label="页码" width="80">
            <template #default="{ row }">
              {{ row.page_number || 1 }}
            </template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-annotations">
          <el-empty description="暂无画笔数据" />
        </div>
      </div>
      <template #footer>
        <el-button @click="showTemplatePreviewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 模板图片大图预览 -->
    <el-dialog
      v-model="showTemplateImageDialog"
      width="60vw"
      top="6vh"
      :show-close="true"
      destroy-on-close
    >
      <div class="template-image-large" v-if="templateImagePreviewUrl">
        <img :src="templateImagePreviewUrl" alt="模板图片预览" />
      </div>
    </el-dialog>

    <!-- 历史上传列表 -->
    <el-dialog
      v-model="showUploadHistoryDialog"
      title="历史上传 PDF"
      width="800px"
      top="8vh"
      @open="loadUploadHistory"
    >
      <el-table :data="uploadHistory" size="small" v-loading="historyLoading" style="width: 100%">
        <el-table-column prop="original_name" label="文件名" min-width="220" />
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="selectHistoryFile(row)">选择</el-button>
            <el-button size="small" type="danger" text @click="deleteHistoryFile(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  PriceTag, DocumentChecked, FolderOpened, Document, ArrowLeft, ArrowRight,
  ZoomIn, ZoomOut, Edit, Delete, Upload, Plus
} from '@element-plus/icons-vue'
import VuePdfEmbed from 'vue-pdf-embed'
import { getFileList, getDownloadUrl, uploadFile, deleteFile } from '../api/upload'
import {
  createAnnotation,
  createAnnotationsBatch,
  getFileAnnotations,
  deleteAnnotation as deleteAnnotationApi,
  deleteFileAnnotations,
  getTemplates,
  createTemplate,
  deleteTemplate,
  applyTemplate,
  updateAnnotation,
  uploadAnnotationImage,
  getAnnotationImageUrl,
  deleteAnnotationImage,
  getPaintData,
  savePaintData
} from '../api/annotate'
import { getConversionDownloadUrl } from '../api/convert'

const router = useRouter()

// 文件列表
const fileList = ref([])
const selectedFileId = ref(null)
const pdfSource = ref(null)
const searchKeyword = ref('')
const conversionMap = ref(loadConversionMaps())

// PDF 相关
const pdfEmbed = ref(null)
const pdfViewerWrapper = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)

// 标注画布
const annotationCanvas = ref(null)
const canvasDpr = ref(1)
const canvasContext = ref(null)
const isDrawing = ref(false)
const drawMode = ref(false)
const isMoving = ref(false)
const movingAnnotation = ref(null)
const moveOffset = ref({ x: 0, y: 0 })
const startPoint = ref({ x: 0, y: 0 })
const currentRect = ref(null)
const imageCache = new Map()
// 画笔工具
const paintingMode = ref(false)
const paintTool = ref('free') // free | line | rect | eraser
const paintColor = ref('#f56c6c')
const paintWidth = ref(2)
const paintHistory = ref([]) // {type,color,width,points?,rect?,page_number}
const tempPaint = ref(null)

const getCanvasPoint = (clientX, clientY) => {
  const canvas = annotationCanvas.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  return {
    x: (clientX - rect.left) / scale.value,
    y: (clientY - rect.top) / scale.value
  }
}

// 标注数据
const annotations = ref([])
const selectedAnnotation = ref(null)
const currentTool = ref({
  type: 'text',
  fieldName: '',
  fieldValue: '',
  fontSize: 12,
  fontColor: '#333333',
  fontFamily: 'SimHei',
  imageFile: null,
  imagePreview: null,
  imagePath: null
})

// UI 状态
const activeTab = ref('tools')
const showTemplateDialog = ref(false)
const showCreateTemplateDialog = ref(false)
const showTemplatePreviewDialog = ref(false)
const previewTemplate = ref(null)

// 模板
const templates = ref([])
const newTemplate = ref({
  template_name: '',
  document_type: '',
  description: ''
})

// 计算属性
const pdfFiles = computed(() => {
  return fileList.value.filter(file =>
    file.file_type.toLowerCase() === 'pdf' || file.status === 'converted'
  )
})

const filteredFiles = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return pdfFiles.value
  return pdfFiles.value.filter(file => file.original_name.toLowerCase().includes(keyword))
})

const pageAnnotations = computed(() => {
  return annotations.value.filter(ann => ann.page_number === currentPage.value)
})

const pagePaintStrokes = computed(() => {
  return (paintHistory.value || []).filter(stroke => (stroke.page_number || 1) === currentPage.value)
})

const totalAnnotationCount = computed(() => {
  return (annotations.value?.length || 0) + (paintHistory.value?.length || 0)
})

const getStrokeBounds = (stroke) => {
  if (!stroke) return null
  if (stroke.type === 'rect' && stroke.rect) {
    return {
      x: stroke.rect.x,
      y: stroke.rect.y,
      width: stroke.rect.width,
      height: stroke.rect.height
    }
  }
  const pts = stroke.points || []
  if (pts.length === 0) return null
  const xs = pts.map(p => p.x)
  const ys = pts.map(p => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  }
}

const canAnnotate = computed(() => {
  if (!currentTool.value.type) return false
  if (currentTool.value.type === 'image') return true
  return !!currentTool.value.fieldName
})

// 生命周期
onMounted(() => {
  loadFileList()
  loadTemplates()
})

// 监听文件选择
watch(selectedFileId, (newId) => {
  if (newId) {
    loadFile()
  } else {
    pdfSource.value = null
    annotations.value = []
  }
})

// 监听页面变化
watch(currentPage, () => {
  redrawAnnotations()
})

// 监听缩放变化，保持画布同步
watch(scale, () => {
  nextTick(setupCanvas)
})

// 切换标注类型时的默认值处理
watch(
  () => currentTool.value.type,
  (newType, oldType) => {
    if (newType === 'image') {
      currentTool.value.fieldName = 'image'
      currentTool.value.fieldValue = ''
      currentTool.value.fontSize = 12
      currentTool.value.fontColor = '#333333'
      currentTool.value.fontFamily = 'SimHei'
    } else if (oldType === 'image') {
      currentTool.value.imageFile = null
      currentTool.value.imagePreview = null
      currentTool.value.imagePath = null
      currentTool.value.fieldName = ''
    }
  }
)

// 加载文件列表
const loadFileList = async () => {
  try {
    const response = await getFileList()
    const files = response.files || []
    fileList.value = files.map(f => ({
      ...f,
      conversion_id: conversionMap.value[f.id] || f.conversion_id
    }))
  } catch (error) {
    ElMessage.error('获取文件列表失败: ' + (error.message || '未知错误'))
  }
}

// 加载文件
const loadFile = async () => {
  if (!selectedFileId.value) return

  const file = fileList.value.find(f => f.id === selectedFileId.value)
  if (!file) {
    ElMessage.error('文件不存在')
    return
  }

  // 设置 PDF 源
  const conversionId = file.conversion_id || resolveConversionId(file.id)

  if (file.file_type.toLowerCase() === 'pdf') {
    pdfSource.value = getDownloadUrl(file.id)
  } else if (file.status === 'converted' && conversionId) {
    pdfSource.value = getConversionDownloadUrl(conversionId)
  } else {
    pdfSource.value = null
    ElMessage.warning('该文件尚未转换为可预览的 PDF，请先去转换页面完成转换')
  }

  currentPage.value = 1
  annotations.value = []

  // 加载已有标注
  await loadAnnotations()
}

// PDF 加载完成
const onPdfLoaded = ({ numPages }) => {
  totalPages.value = numPages
  nextTick(() => {
    setupCanvas()
    updateScaleToFit()
  })
}

// PDF 加载错误
const onPdfError = (error) => {
  ElMessage.error('PDF 加载失败: ' + error.message)
}

// 设置画布
const setupCanvas = () => {
  const canvas = annotationCanvas.value
  const pdfElement = pdfEmbed.value?.$el?.querySelector('canvas')

  if (canvas && pdfElement) {
    const dpr = window.devicePixelRatio || 1
    const extraHeight = 90
    // 使用 scroll 尺寸，确保画布覆盖滚动后区域
    const displayWidth = pdfElement.scrollWidth || pdfElement.offsetWidth
    const displayHeight = pdfElement.scrollHeight || pdfElement.offsetHeight
    canvasDpr.value = dpr
    canvas.width = displayWidth * dpr
    canvas.height = (displayHeight + extraHeight) * dpr
    canvas.style.width = `${displayWidth}px`
    canvas.style.height = `${displayHeight + extraHeight}px`
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.scale(dpr, dpr)
    canvasContext.value = ctx
    redrawAnnotations()
  }
}

// 页面导航
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 缩放
const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.1, 3.0)
  nextTick(setupCanvas)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.1, 0.3)
  nextTick(setupCanvas)
}

// 监听窗口尺寸变化
window.addEventListener('resize', () => nextTick(setupCanvas))
// 根据容器宽度自适应 PDF 宽度
const updateScaleToFit = () => {
  nextTick(() => {
    const wrapper = pdfViewerWrapper.value
    const pdfCanvas = pdfEmbed.value?.$el?.querySelector('canvas')
    if (!wrapper || !pdfCanvas) return

    // 预留一些左右间距，避免滚动条遮挡
    const wrapperWidth = Math.max(wrapper.clientWidth - 24, 0)
    const pdfWidth = pdfCanvas.width || pdfCanvas.offsetWidth
    if (wrapperWidth && pdfWidth) {
      const fitScale = wrapperWidth / pdfWidth
      scale.value = Math.min(Math.max(fitScale, 0.5), 3.0)
      nextTick(setupCanvas)
    }
  })
}

// 窗口或滚动时同步画布
const onWrapperScroll = () => {
  setupCanvas()
}

onMounted(() => {
  if (pdfViewerWrapper.value) {
    pdfViewerWrapper.value.addEventListener('scroll', onWrapperScroll)
  }
  window.addEventListener('resize', () => nextTick(setupCanvas))
})

// 清理监听
onUnmounted(() => {
  if (pdfViewerWrapper.value) {
    pdfViewerWrapper.value.removeEventListener('scroll', onWrapperScroll)
  }
})

// 启用绘制模式
const enableDrawMode = () => {
  if (!canAnnotate.value) {
    ElMessage.warning('请先选择标注类型和字段名称')
    return
  }
  // 关闭画笔模式
  if (paintingMode.value) {
    paintingMode.value = false
    tempPaint.value = null
    setCanvasCursor('crosshair')
  }
  drawMode.value = true
  ElMessage.info('请在 PDF 上拖动鼠标框选区域')
}

// 取消绘制模式
const cancelDrawMode = () => {
  drawMode.value = false
  isDrawing.value = false
  currentRect.value = null
  redrawAnnotations()
}

// 开始绘制
const startDrawing = (e) => {
  const canvas = annotationCanvas.value
  if (!canvas) return

  const point = getCanvasPoint(e.clientX, e.clientY)

  // 移动模式：未开启绘制时，允许拖动已有标注
  if (!drawMode.value && !paintingMode.value) {
    const hit = findAnnotationAtPoint(point.x, point.y)
    if (hit) {
      selectAnnotation(hit)
      movingAnnotation.value = hit
      moveOffset.value = {
        x: point.x - (hit.coordinates?.x || 0),
        y: point.y - (hit.coordinates?.y || 0)
      }
      isMoving.value = true
      setCanvasCursor('grabbing')
    }
    return
  }

  // 画笔绘制
  if (paintingMode.value) {
    isDrawing.value = true
    if (paintTool.value === 'free') {
      tempPaint.value = {
        type: 'free',
        color: paintColor.value,
        width: paintWidth.value,
        points: [{ x: point.x, y: point.y }],
        page_number: currentPage.value
      }
    } else if (paintTool.value === 'eraser') {
      tempPaint.value = {
        type: 'eraser',
        color: '#ffffff',
        width: paintWidth.value,
        points: [{ x: point.x, y: point.y }],
        page_number: currentPage.value
      }
    } else if (paintTool.value === 'line') {
      tempPaint.value = {
        type: 'line',
        color: paintColor.value,
        width: paintWidth.value,
        points: [{ x: point.x, y: point.y }],
        page_number: currentPage.value
      }
    } else if (paintTool.value === 'rect') {
      tempPaint.value = {
        type: 'rect',
        color: paintColor.value,
        width: paintWidth.value,
        rect: { x: point.x, y: point.y, width: 0, height: 0 },
        page_number: currentPage.value
      }
    }
    return
  }

  startPoint.value = {
    x: point.x,
    y: point.y
  }
  isDrawing.value = true
}

// 绘制中
const drawing = (e) => {
  const canvas = annotationCanvas.value
  const point = getCanvasPoint(e.clientX, e.clientY)
  const currentX = point.x
  const currentY = point.y

  // hover 状态下提示可拖动
  if (!drawMode.value && !isMoving.value && !paintingMode.value) {
    const hit = findAnnotationAtPoint(currentX, currentY)
    setCanvasCursor(hit ? 'grab' : 'crosshair')
  }

  // 画笔绘制
  if (paintingMode.value && isDrawing.value && tempPaint.value) {
    if (tempPaint.value.type === 'free' || tempPaint.value.type === 'eraser') {
      tempPaint.value.points.push({ x: currentX, y: currentY })
    } else if (tempPaint.value.type === 'line') {
      tempPaint.value.points[1] = { x: currentX, y: currentY }
    } else if (tempPaint.value.type === 'rect') {
      const r = tempPaint.value.rect
      tempPaint.value.rect = {
        ...r,
        width: currentX - r.x,
        height: currentY - r.y
      }
    }
    redrawAnnotations()
    return
  }

  // 拖动已有标注
  if (isMoving.value && movingAnnotation.value) {
    const ann = movingAnnotation.value
    const coords = ann.coordinates || {}
    const newCoords = {
      ...coords,
      x: currentX - moveOffset.value.x,
      y: currentY - moveOffset.value.y
    }
    ann.coordinates = newCoords
    redrawAnnotations()
    return
  }

  if (!isDrawing.value || !drawMode.value) return

  currentRect.value = {
    x: Math.min(startPoint.value.x, currentX),
    y: Math.min(startPoint.value.y, currentY),
    width: Math.abs(currentX - startPoint.value.x),
    height: Math.abs(currentY - startPoint.value.y)
  }

  redrawAnnotations()
  drawCurrentRect()
}

// 停止绘制
const stopDrawing = async () => {
  // 停止拖动已有标注
  if (isMoving.value && movingAnnotation.value) {
    const ann = movingAnnotation.value
    isMoving.value = false
    movingAnnotation.value = null
    setCanvasCursor('grab')

    // 如果已保存，则同步更新后端坐标
    if (ann.id) {
      try {
        const payload = {
          file_id: selectedFileId.value,
          page_number: ann.page_number || currentPage.value,
          annotation_type: ann.annotation_type,
          field_name: ann.field_name,
          field_value: ann.field_value,
          image_path: ann.image_path,
          coordinates: {
            ...(ann.coordinates || {}),
            font_size: ann.coordinates?.font_size || ann.coordinates?.fontSize || currentTool.value.fontSize,
            font_color: ann.coordinates?.font_color || currentTool.value.fontColor,
            font_family: ann.coordinates?.font_family || currentTool.value.fontFamily
          }
        }
        const resp = await updateAnnotation(ann.id, payload)
        ann.coordinates = resp.coordinates || payload.coordinates
      } catch (error) {
        ElMessage.error('更新标注位置失败: ' + (error.message || '未知错误'))
      }
    }
    redrawAnnotations()
    return
  }

  // 结束画笔绘制
  if (paintingMode.value && isDrawing.value && tempPaint.value) {
    if ((tempPaint.value.type === 'free' || tempPaint.value.type === 'eraser') && tempPaint.value.points.length < 2) {
      tempPaint.value = null
    } else {
      paintHistory.value.push(tempPaint.value)
      tempPaint.value = null
    }
    isDrawing.value = false
    redrawAnnotations()
    return
  }

  if (!isDrawing.value || !drawMode.value || !currentRect.value) return

  // 如果是图片标注，先确保有图片并上传/复用路径
  let imagePath = null
  if (currentTool.value.type === 'image') {
    if (currentTool.value.imageFile) {
      try {
        const uploadResult = await uploadAnnotationImage(currentTool.value.imageFile)
        imagePath = uploadResult.image_path
        // 释放旧的本地预览，切换为后端可访问地址
        if (currentTool.value.imagePreview?.startsWith('blob:')) {
          URL.revokeObjectURL(currentTool.value.imagePreview)
        }
        currentTool.value.imagePreview = getAnnotationImageUrl(imagePath)
        currentTool.value.imagePath = imagePath
        ElMessage.success('图片上传成功')
      } catch (error) {
        ElMessage.error('图片上传失败: ' + (error.message || '未知错误'))
        isDrawing.value = false
        drawMode.value = false
        currentRect.value = null
        redrawAnnotations()
        return
      }
    } else if (currentTool.value.imagePath) {
      imagePath = currentTool.value.imagePath
    } else {
      ElMessage.warning('请先上传标注图片')
      isDrawing.value = false
      drawMode.value = false
      currentRect.value = null
      redrawAnnotations()
      return
    }
  }

  // 创建标注
  const annotation = {
    page_number: currentPage.value,
    annotation_type: currentTool.value.type,
    field_name: currentTool.value.fieldName,
    field_value: currentTool.value.fieldValue || '',
    image_path: imagePath,
    coordinates: {
      ...currentRect.value,
      font_size: currentTool.value.fontSize,
      font_color: currentTool.value.fontColor,
      font_family: currentTool.value.fontFamily
    }
  }

  annotations.value.push(annotation)
  ElMessage.success('标注已添加')

  // 重置状态
  isDrawing.value = false
  drawMode.value = false
  currentRect.value = null

  // 清理文件选择，但保留可复用的线上预览
  if (currentTool.value.type === 'image') {
    currentTool.value.imageFile = null
  }

  redrawAnnotations()
}

// 绘制当前矩形
const drawCurrentRect = () => {
  if (!currentRect.value || !canvasContext.value) return

  const ctx = canvasContext.value
  ctx.strokeStyle = '#409EFF'
  ctx.lineWidth = 2
  ctx.strokeRect(
    currentRect.value.x,
    currentRect.value.y,
    currentRect.value.width,
    currentRect.value.height
  )
}

// 重绘所有标注
const redrawAnnotations = () => {
  const canvas = annotationCanvas.value
  const ctx = canvasContext.value

  if (!canvas || !ctx) return

  // 清空画布
  const dpr = canvasDpr.value || 1
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  // 绘制画笔
  drawPaintStrokes(ctx)

  // 绘制当前页面的标注
  pageAnnotations.value.forEach(annotation => {
    const coords = annotation.coordinates
    const fontSize = coords.font_size || coords.fontSize || 12
    const fontColor = coords.font_color || '#333'
    const fontFamily = formatFontFamily(sanitizeFontFamily(coords.font_family || 'SimHei'))
    const isActive = selectedAnnotation.value === annotation
    ctx.strokeStyle = isActive ? '#f56c6c' : getAnnotationColor(annotation.annotation_type)
    ctx.lineWidth = isActive ? 3 : 2
    ctx.strokeRect(coords.x, coords.y, coords.width, coords.height)

    if (isActive) {
      ctx.fillStyle = 'rgba(245, 108, 108, 0.12)'
      ctx.fillRect(coords.x, coords.y, coords.width, coords.height)
    }

    // 绘制字段名与字段值
    const label = getFieldNameCN(annotation.field_name)
    const value = annotation.field_value || ''
    const padding = 4
    const textX = coords.x + padding
    const textY = coords.y - 4 // 字段名放在选框上方
    const valueY = coords.y + padding + fontSize

    ctx.fillStyle = fontColor
    ctx.font = `${fontSize}px ${fontFamily}`
    ctx.fillText(label, textX, textY)

    if (value) {
      ctx.fillStyle = fontColor
      ctx.font = `${fontSize}px ${fontFamily}`
      ctx.fillText(value, textX, valueY)
    }

    // 如果是图片标注，在选框内绘制图片
    if (annotation.annotation_type === 'image' && annotation.image_path) {
      const url = getAnnotationImageUrl(annotation.image_path)
      const drawImageToCanvas = (img) => {
        const targetW = coords.width
        const targetH = coords.height
        const ratio = Math.min(targetW / img.width, targetH / img.height)
        const drawW = img.width * ratio
        const drawH = img.height * ratio
        const offsetX = coords.x + (targetW - drawW) / 2
        const offsetY = coords.y + (targetH - drawH) / 2
        const currentCtx = canvasContext.value
        if (!currentCtx) return
        currentCtx.drawImage(img, offsetX, offsetY, drawW, drawH)
      }

      const cached = imageCache.get(url)
      if (cached) {
        drawImageToCanvas(cached)
      } else {
        loadImage(url)
          .then(() => redrawAnnotations())
          .catch(() => {
            /* ignore load error */
          })
      }
    }
  })
}

const findAnnotationAtPoint = (x, y) => {
  // 倒序遍历，优先选中后绘制的标注
  for (let i = pageAnnotations.value.length - 1; i >= 0; i -= 1) {
    const ann = pageAnnotations.value[i]
    const c = ann.coordinates || {}
    if (x >= c.x && x <= c.x + c.width && y >= c.y && y <= c.y + c.height) {
      return ann
    }
  }
  return null
}

const setCanvasCursor = (cursor) => {
  const canvas = annotationCanvas.value
  if (canvas) {
    canvas.style.cursor = cursor
  }
}

const togglePainting = () => {
  paintingMode.value = !paintingMode.value
  if (paintingMode.value) {
    drawMode.value = false
    setCanvasCursor('crosshair')
  }
}

const selectPaintTool = (tool) => {
  paintTool.value = tool
  if (!paintingMode.value) paintingMode.value = true
}

const undoPaint = () => {
  if (paintHistory.value.length > 0) {
    paintHistory.value.pop()
    redrawAnnotations()
  }
}

const clearPaint = () => {
  paintHistory.value = []
  tempPaint.value = null
  redrawAnnotations()
}

// 画笔保存/加载
const normalizePaintStrokes = (strokes = []) => {
  return (strokes || []).map(stroke => ({
    ...stroke,
    page_number: stroke.page_number || 1
  }))
}

const loadPaint = async () => {
  if (!selectedFileId.value) return { total: 0, eraser: 0 }
  try {
    const resp = await getPaintData(selectedFileId.value)
    const strokes = normalizePaintStrokes(resp.strokes || [])
    paintHistory.value = strokes
    tempPaint.value = null
    redrawAnnotations()
    return { total: strokes.length, eraser: strokes.filter(s => s.type === 'eraser').length }
  } catch (error) {
    console.error('加载画笔失败:', error)
    return { total: 0, eraser: 0 }
  }
}

const savePaint = async () => {
  if (!selectedFileId.value) return
  try {
    await savePaintData(selectedFileId.value, paintHistory.value || [])
  } catch (error) {
    console.error('保存画笔失败:', error)
  }
}

const deletePaintStroke = async (stroke) => {
  const idx = paintHistory.value.indexOf(stroke)
  if (idx > -1) {
    paintHistory.value.splice(idx, 1)
    tempPaint.value = null
    redrawAnnotations()
    try {
      await savePaint()
      ElMessage.success('画笔已删除')
    } catch (error) {
      ElMessage.error('画笔删除后保存失败: ' + (error.message || '未知错误'))
    }
  }
}

const drawPaintStrokes = (ctx) => {
  const drawStroke = (stroke) => {
    ctx.save()
    ctx.strokeStyle = stroke.color
    ctx.lineWidth = stroke.width
    ctx.lineJoin = 'round'
    ctx.lineCap = 'round'
    if (stroke.type === 'free' || stroke.type === 'eraser') {
      const pts = stroke.points || []
      if (pts.length < 2) return
      ctx.beginPath()
      ctx.moveTo(pts[0].x, pts[0].y)
      for (let i = 1; i < pts.length; i++) {
        ctx.lineTo(pts[i].x, pts[i].y)
      }
      ctx.stroke()
    } else if (stroke.type === 'line') {
      const p1 = stroke.points?.[0]
      const p2 = stroke.points?.[1]
      if (!p1 || !p2) return
      ctx.beginPath()
      ctx.moveTo(p1.x, p1.y)
      ctx.lineTo(p2.x, p2.y)
      ctx.stroke()
    } else if (stroke.type === 'rect') {
      const rect = stroke.rect
      if (!rect) return
      ctx.strokeRect(rect.x, rect.y, rect.width, rect.height)
    }
    ctx.restore()
  }

  paintHistory.value.forEach(drawStroke)
  if (tempPaint.value) {
    drawStroke(tempPaint.value)
  }
}

// 获取标注颜色
const getAnnotationColor = (type) => {
  const colors = {
    text: '#409EFF',
    long_text: '#67C23A',
    image: '#E6A23C'
  }
  return colors[type] || '#909399'
}

// 获取标注类型名称
const getAnnotationTypeName = (type) => {
  const names = {
    text: '文本',
    long_text: '长文本',
    image: '图片'
  }
  return names[type] || type
}

// 模板字段类型中文
const getFieldTypeName = (type) => {
  const names = {
    text: '文本',
    long_text: '长文本',
    image: '图片'
  }
  return names[type] || type || '-'
}

// 模板字段名称中文
const getFieldNameCN = (fieldName) => {
  const map = {
    contract_name: '合同名称',
    contract_date: '合同日期',
    contract_number: '合同编号',
    contract_amount: '合同金额',
    party_a: '甲方名称',
    party_b: '乙方名称',
    image: '图片'
  }
  return map[fieldName] || fieldName || '-'
}

// 获取标注类型颜色
const getAnnotationTypeColor = (type) => {
  const colors = {
    text: 'primary',
    long_text: 'success',
    image: 'warning'
  }
  return colors[type] || 'info'
}

const formatFontFamily = (family) => {
  if (!family) return 'Arial'
  // 如果包含空格或中文，使用引号包裹，避免 canvas 字体解析失败
  if (family.includes(' ') || /[\u4e00-\u9fa5]/.test(family)) {
    return `'${family}'`
  }
  return family
}

const sanitizeFontFamily = (family) => {
  if (!family) return 'SimHei'
  // 去除外层引号，避免重复包裹
  const trimmed = family.trim().replace(/^['"]+|['"]+$/g, '')
  return trimmed || 'SimHei'
}

const getAnnotationTextStyle = (annotation) => {
  const coords = annotation.coordinates || {}
  const color = coords.font_color || '#333'
  const family = sanitizeFontFamily(coords.font_family) || 'SimHei'
  return {
    color,
    fontFamily: family
  }
}

// 加载图片并缓存，避免重复请求
const loadImage = (url) => {
  if (imageCache.has(url)) {
    return Promise.resolve(imageCache.get(url))
  }
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      imageCache.set(url, img)
      resolve(img)
    }
    img.onerror = reject
    img.src = url
  })
}

// 选择标注
const selectAnnotation = (annotation) => {
  selectedAnnotation.value = annotation
  currentTool.value.fieldName = annotation.field_name
  currentTool.value.fieldValue = annotation.field_value || ''
  currentTool.value.type = annotation.annotation_type
  currentTool.value.fontSize = annotation.coordinates?.font_size || annotation.coordinates?.fontSize || 12
  currentTool.value.fontColor = annotation.coordinates?.font_color || '#333333'
  currentTool.value.fontFamily = sanitizeFontFamily(annotation.coordinates?.font_family) || 'SimHei'
  if (annotation.annotation_type === 'image') {
    currentTool.value.imagePath = annotation.image_path || null
    currentTool.value.imageFile = null
    currentTool.value.imagePreview = annotation.image_path ? getAnnotationImageUrl(annotation.image_path) : null
  } else {
    currentTool.value.imagePath = null
    currentTool.value.imageFile = null
    currentTool.value.imagePreview = null
  }
  redrawAnnotations()
}

// 删除标注
const deleteAnnotation = async (annotation) => {
  try {
    await ElMessageBox.confirm(
      `确认删除此标注吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (annotation.id) {
      // 已保存的标注，从服务器删除
      await deleteAnnotationApi(annotation.id)
    }

    // 从本地列表删除
    const index = annotations.value.indexOf(annotation)
    if (index > -1) {
      annotations.value.splice(index, 1)
    }

    redrawAnnotations()
    ElMessage.success('标注已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 更新选中的标注（字段名、字段值、字体大小）
const updateSelectedAnnotation = async () => {
  if (!selectedAnnotation.value) {
    ElMessage.warning('请先选择一个标注')
    return
  }

  try {
    let imagePath = currentTool.value.type === 'image'
      ? (currentTool.value.imagePath || selectedAnnotation.value.image_path || null)
      : null

    // 处理图片替换或新增
    if (currentTool.value.type === 'image') {
      if (currentTool.value.imageFile) {
        const uploadResult = await uploadAnnotationImage(currentTool.value.imageFile)
        imagePath = uploadResult.image_path
        if (currentTool.value.imagePreview?.startsWith('blob:')) {
          URL.revokeObjectURL(currentTool.value.imagePreview)
        }
        currentTool.value.imagePreview = getAnnotationImageUrl(imagePath)
        currentTool.value.imagePath = imagePath
        ElMessage.success('标注图片已更新')
      } else if (!imagePath) {
        ElMessage.warning('请先上传标注图片')
        return
      }
    } else {
      // 切换到非图片类型时清空图片数据
      imagePath = null
      currentTool.value.imageFile = null
      currentTool.value.imagePreview = null
      currentTool.value.imagePath = null
    }

    const payload = {
      file_id: selectedFileId.value,
      page_number: selectedAnnotation.value.page_number || currentPage.value,
      annotation_type: currentTool.value.type,
      field_name: currentTool.value.fieldName,
      field_value: currentTool.value.fieldValue,
      image_path: imagePath,
      coordinates: {
        ...(selectedAnnotation.value.coordinates || currentRect.value || {}),
        font_size: currentTool.value.fontSize,
        font_color: currentTool.value.fontColor,
        font_family: currentTool.value.fontFamily
      }
    }

    // 已保存的标注走更新，未保存的直接创建
    let resp
    if (selectedAnnotation.value.id) {
      resp = await updateAnnotation(selectedAnnotation.value.id, payload)
    } else {
      resp = await createAnnotation(payload)
    }

    const updated = {
      ...selectedAnnotation.value,
      ...resp,
      image_path: resp?.image_path ?? imagePath,
      coordinates: resp.coordinates || payload.coordinates
    }
    selectedAnnotation.value = updated

    const idx = annotations.value.findIndex(a => a.id === updated.id || a === selectedAnnotation.value || a.field_name === updated.field_name && a.page_number === updated.page_number)
    if (idx > -1) {
      annotations.value[idx] = updated
    } else {
      annotations.value.push(updated)
    }

    redrawAnnotations()
    ElMessage.success('标注已更新并保存')
  } catch (error) {
    ElMessage.error('更新失败: ' + (error.message || '未知错误'))
  }
}

// 清空标注：支持清空本页或全部
const clearAnnotations = async () => {
  if (!selectedFileId.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  try {
    const action = await ElMessageBox.confirm(
      '请选择清空范围：',
      '清空标注',
      {
        confirmButtonText: '清空本页',
        cancelButtonText: '清空全部',
        type: 'warning',
        distinguishCancelAndClose: true
      }
    )

    // 确认：清空当前页
    if (action === 'confirm') {
      const current = [...pageAnnotations.value]
      for (const ann of current) {
        if (ann.id) {
          await deleteAnnotationApi(ann.id)
        }
        const idx = annotations.value.indexOf(ann)
        if (idx > -1) annotations.value.splice(idx, 1)
      }
      // 清空当前页画笔
      const remaining = paintHistory.value.filter(stroke => (stroke.page_number || 1) !== currentPage.value)
      paintHistory.value = remaining
      await savePaint()
      selectedAnnotation.value = null
      redrawAnnotations()
      ElMessage.success('已清空当前页标注')
      return
    }
  } catch (error) {
    // cancel => 清空全部；close/其他则忽略
    if (error === 'cancel') {
      try {
        await deleteFileAnnotations(selectedFileId.value)
        annotations.value = []
        paintHistory.value = []
        await savePaint()
        selectedAnnotation.value = null
        redrawAnnotations()
        ElMessage.success('已清空全部标注')
      } catch (err) {
        ElMessage.error('清空失败: ' + (err.message || '未知错误'))
      }
    } else if (error !== 'close') {
      ElMessage.error('清空失败: ' + (error.message || '未知错误'))
    }
  }
}

// 保存标注
const saveAnnotations = async () => {
  if (annotations.value.length === 0) {
    ElMessage.warning('没有可保存的标注')
    return
  }

  try {
    const unsavedAnnotations = annotations.value.filter(ann => !ann.id)

    if (unsavedAnnotations.length === 0) {
      ElMessage.info('所有标注已保存')
      await savePaint()
      return
    }

    await createAnnotationsBatch({
      file_id: selectedFileId.value,
      annotations: unsavedAnnotations
    })

    ElMessage.success(`成功保存 ${unsavedAnnotations.length} 个标注`)

    await savePaint()

    // 重新加载标注
    await loadAnnotations()
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  }
}

// 加载标注
const loadAnnotations = async () => {
  if (!selectedFileId.value) return

  try {
    const response = await getFileAnnotations(selectedFileId.value)
    annotations.value = response.annotations || []
    const paintStat = await loadPaint()
    redrawAnnotations()

    if (annotations.value.length > 0 || paintStat.total > 0) {
      const paintMsg = paintStat.total > 0
        ? `，${paintStat.total} 条画笔/橡皮${paintStat.eraser ? `（橡皮 ${paintStat.eraser} 条）` : ''}`
        : ''
      ElMessage.success(`加载了 ${annotations.value.length} 条标注${paintMsg}`)
    }
  } catch (error) {
    console.error('加载标注失败:', error)
  }
}

// 加载模板列表
const loadTemplates = async () => {
  try {
    const response = await getTemplates()
    templates.value = response.templates || []
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

// ======= 工具函数 =======
function loadConversionMaps() {
  const keys = [
    'conversion_map_word',
    'conversion_map_image',
    'conversion_map_ofd',
    'conversion_map_archive'
  ]
  const map = {}
  keys.forEach(key => {
    try {
      const stored = localStorage.getItem(key)
      if (stored) {
        Object.assign(map, JSON.parse(stored))
      }
    } catch (e) {
      console.error(`读取本地转换映射失败: ${key}`, e)
    }
  })
  return map
}

function resolveConversionId(fileId) {
  return conversionMap.value[fileId] || null
}

// 创建新模板
const createNewTemplate = async () => {
  try {
    // 从当前标注生成字段定义
    const fields = annotations.value.map((ann, idx) => ({
      field_name: ann.field_name || `field_${idx + 1}`,
      field_type: ann.annotation_type,
      required: false,
      description: '',
      field_value: ann.field_value || '',
      image_path: ann.image_path || null,
      page_number: ann.page_number || 1,
      coordinates: ann.coordinates || null
    }))

    if (fields.length === 0) {
      ElMessage.warning('请先添加一些标注作为模板字段')
      return
    }

    await createTemplate({
      ...newTemplate.value,
      fields,
      paint_data: paintHistory.value || []
    })

    ElMessage.success('模板创建成功')
    showCreateTemplateDialog.value = false
    newTemplate.value = {
      template_name: '',
      document_type: '',
      description: ''
    }
    loadTemplates()
  } catch (error) {
    ElMessage.error('创建模板失败: ' + (error.message || '未知错误'))
  }
}

// 删除模板
const deleteTemplateById = async (templateId) => {
  try {
    await ElMessageBox.confirm(
      '确认删除此模板吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteTemplate(templateId)
    ElMessage.success('模板删除成功')
    loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 应用模板
const applyTemplateToFile = async (templateId) => {
  if (!selectedFileId.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  try {
    const response = await applyTemplate(templateId, selectedFileId.value)
    ElMessage.info(response.message)
    if (response.paint_data) {
      paintHistory.value = normalizePaintStrokes(response.paint_data)
      tempPaint.value = null
      redrawAnnotations()
    } else {
      await loadPaint()
    }
    await loadAnnotations()
    activeTab.value = 'annotations'
  } catch (error) {
    ElMessage.error('应用模板失败: ' + (error.message || '未知错误'))
  }
}

// 查看模板详情
const showTemplateImageDialog = ref(false)
const templateImagePreviewUrl = ref('')
const uploadingPdf = ref(false)
const uploadPercent = ref(0)
const exportingPdf = ref(false)
const showUploadHistoryDialog = ref(false)
const uploadHistory = ref([])
const historyLoading = ref(false)

const viewTemplate = (template) => {
  previewTemplate.value = template
  showTemplatePreviewDialog.value = true
}

const openTemplateImage = (path) => {
  if (!path) return
  const url = getAnnotationImageUrl(path)
  templateImagePreviewUrl.value = url
  showTemplateImageDialog.value = true
}

// 跳转到转换页面
const goToConvert = () => {
  router.push('/')
}

// 处理图片选择
const handleImageChange = (file) => {
  const rawFile = file.raw
  if (!rawFile) return

  // 验证文件类型
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
  if (!validTypes.includes(rawFile.type)) {
    ElMessage.error('只支持 JPG、PNG、GIF、BMP、WEBP 格式的图片')
    return
  }

  // 验证文件大小（5MB）
  const maxSize = 5 * 1024 * 1024
  if (rawFile.size > maxSize) {
    ElMessage.error('图片大小不能超过 5MB')
    return
  }

  // 保存文件和预览
  currentTool.value.imageFile = rawFile
  currentTool.value.imagePreview = URL.createObjectURL(rawFile)
  // 选择了新图片，清空旧的远程路径，等待重新上传
  currentTool.value.imagePath = null
}

// 清除上传的图片
const clearUploadedImage = () => {
  if (currentTool.value.imagePreview && currentTool.value.imagePreview.startsWith('blob:')) {
    URL.revokeObjectURL(currentTool.value.imagePreview)
  }
  currentTool.value.imageFile = null
  currentTool.value.imagePreview = null
  currentTool.value.imagePath = null
}

// 鼠标移出时重置指针
const onCanvasLeave = () => {
  if (!drawMode.value && !isMoving.value) {
    setCanvasCursor('crosshair')
  }
}

// 处理 PDF 上传
const handlePdfUpload = async (file) => {
  const rawFile = file.raw
  if (!rawFile) return
  if (rawFile.type !== 'application/pdf' && !rawFile.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('仅支持 PDF 文件')
    return
  }
  uploadingPdf.value = true
  uploadPercent.value = 0
  try {
    const resp = await uploadFile(rawFile, (percent) => {
      uploadPercent.value = percent
    })
    ElMessage.success('PDF 上传成功')
    await loadFileList()
    // 自动选中新文件
    if (resp?.id) {
      selectedFileId.value = resp.id
      await loadFile()
    }
  } catch (error) {
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploadingPdf.value = false
    uploadPercent.value = 0
  }
}

// 导出标注后的 PDF（截取当前预览区域）
const exportAnnotatedPdf = async () => {
  if (!pdfViewerWrapper.value) return
  exportingPdf.value = true
  ElMessage.info('正在导出 PDF，请稍候...')
  try {
    const html2canvas = await loadHtml2Canvas()
    const jsPDF = await loadJspdf()
    if (!html2canvas || !jsPDF) {
      throw new Error('缺少导出依赖')
    }

    const element = pdfViewerWrapper.value
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()

    const originalPage = currentPage.value
    const total = Number(totalPages.value) > 0 ? Number(totalPages.value) : 1
    const wrapper = pdfViewerWrapper.value
    const prevHeight = wrapper.style.height
    const prevOverflow = wrapper.style.overflow
    for (let p = 1; p <= total; p += 1) {
      currentPage.value = p
      await nextTick()
      await sleep(150)
      // 取消滚动限制，截取整页
      wrapper.style.height = `${wrapper.scrollHeight}px`
      wrapper.style.overflow = 'visible'
      await nextTick()
      const canvas = await html2canvas(wrapper, { scale: 2, useCORS: true })
      const imgData = canvas.toDataURL('image/png')
      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      if (p > 1) pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
      // 恢复滚动
      wrapper.style.height = prevHeight
      wrapper.style.overflow = prevOverflow
    }
    currentPage.value = originalPage
    await nextTick()

    pdf.save('annotated.pdf')
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请确认依赖已安装：html2canvas、jspdf')
  } finally {
    exportingPdf.value = false
  }
}

// 懒加载 html2canvas（CDN 回退）
const loadHtml2Canvas = async () => {
  if (window.html2canvas) return window.html2canvas
  try {
    const mod = await import(/* @vite-ignore */ 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js')
    return mod.default || window.html2canvas || mod
  } catch (e) {
    console.error('加载 html2canvas 失败', e)
    return null
  }
}

// 懒加载 jsPDF（CDN 回退）
const loadJspdf = async () => {
  if (window.jspdf?.jsPDF) return window.jspdf.jsPDF
  try {
    const mod = await import(/* @vite-ignore */ 'https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js')
    return mod.jsPDF || window.jspdf?.jsPDF || mod.default?.jsPDF
  } catch (e) {
    console.error('加载 jsPDF 失败', e)
    return null
  }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// 历史上传
const openUploadHistory = () => {
  showUploadHistoryDialog.value = true
}

const loadUploadHistory = async () => {
  historyLoading.value = true
  try {
    const resp = await getFileList(0, 200)
    const files = (resp.files || []).filter(f => (f.file_type || '').toLowerCase() === 'pdf')
    uploadHistory.value = files
  } catch (e) {
    ElMessage.error('加载历史上传失败')
  } finally {
    historyLoading.value = false
  }
}

const deleteHistoryFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确认删除 ${file.original_name} 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteFile(file.id)
    // 更新列表和下拉
    uploadHistory.value = uploadHistory.value.filter(f => f.id !== file.id)
    fileList.value = fileList.value.filter(f => f.id !== file.id)
    if (selectedFileId.value === file.id) {
      selectedFileId.value = null
      pdfSource.value = null
    }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const selectHistoryFile = async (file) => {
  selectedFileId.value = file.id
  showUploadHistoryDialog.value = false
  await loadFile()
}

const formatFileSize = (size) => {
  if (!size && size !== 0) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.annotator-page {
  height: calc(104vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.toolbar-card {
  flex-shrink: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-title {
  font-size: 18px;
  font-weight: bold;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.empty-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 10px;
}

.upload-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-pdf-btn {
  background: linear-gradient(135deg, #4dabf7 0%, #228be6 100%);
  color: #fff;
}

.history-btn {
  align-self: flex-start;
}

.upload-progress {
  font-size: 12px;
  color: #666;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 15px;
  min-height: 0;
}

.pdf-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pdf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pdf-controls {
  display: flex;
  gap: 10px;
}

.pdf-viewer-wrapper {
  flex: 1;
  overflow: auto;
  position: relative;
  background: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  height: calc(90vh - 190px);
  max-height: none;
  padding: 8px 0;
}

.pdf-viewer {
  position: relative;
  display: inline-block;
  transform-origin: top center;
  padding-bottom: 84px; /* 为画布预留额外高度 */
}

.paint-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: -15px 0 8px 0;
  flex-wrap: nowrap;
}

.paint-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.paint-controls .label {
  color: #666;
  font-size: 13px;
}

.annotation-canvas {
  position: absolute;
  top: 0;
  left: 0;
  cursor: crosshair;
  pointer-events: auto;
}

.tools-container {
  width: 350px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.tools-panel {
  padding: 10px 0;
}

.tool-tips {
  margin-top: 20px;
}

.annotations-list {
  max-height: 500px;
  overflow-y: auto;
}

.annotations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.annotations-clear {
  padding: 0 6px;
}

.annotation-item {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.annotation-item:hover {
  background: #f5f5f5;
}

.annotation-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.annotation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.field-name {
  flex: 1;
  font-weight: bold;
}

.annotation-value {
  margin: 5px 0;
  color: #666;
  font-size: 13px;
}

.annotation-coords {
  font-size: 12px;
  color: #999;
}

.color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid #e0e0e0;
  margin-left: 8px;
}

.annotation-image {
  width: 120px;
  height: 80px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  margin-top: 6px;
}

.annotation-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.templates-panel {
  padding: 10px 0;
}

.template-item {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 10px;
}

.template-preview-body {
  max-height: 70vh;
  overflow-y: auto;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-name {
  font-weight: bold;
}

.template-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #666;
}

.template-image {
  width: 140px;
  height: 100px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  cursor: pointer;
}

.template-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.template-image-large {
  width: 100%;
  height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.template-image-large img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.template-text {
  white-space: pre-wrap;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-annotations {
  padding: 40px 0;
}

/* 图片上传组件样式 */
.image-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 178px;
  height: 178px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.3s;
}

.image-uploader:hover {
  border-color: #409EFF;
}

.image-uploader-icon {
  font-size: 28px;
  color: #8c939d;
}

.uploaded-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>
