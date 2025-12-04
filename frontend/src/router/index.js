import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/pdf-tools',
    name: 'PdfTools',
    component: () => import('../views/PdfTools.vue')
  },
  // PDF转换工具
  {
    path: '/convert/word',
    name: 'ConvertWord',
    component: () => import('../views/Convert.vue')
  },
  {
    path: '/convert/image',
    name: 'ConvertImage',
    component: () => import('../views/ConvertImage.vue')
  },
  {
    path: '/convert/archive',
    name: 'ConvertArchive',
    component: () => import('../views/ConvertArchive.vue')
  },
  {
    path: '/convert/ofd',
    name: 'ConvertOfd',
    component: () => import('../views/ConvertOfd.vue')
  },
  // PDF编辑工具
  {
    path: '/edit/editor',
    name: 'PdfEditor',
    component: () => import('../views/Editor.vue')
  },
  {
    path: '/edit/annotator',
    name: 'Annotator',
    component: () => import('../views/Annotator.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
