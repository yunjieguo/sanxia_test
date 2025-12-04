import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    currentFile: null,
    fileList: [],
    loading: false
  }),

  actions: {
    setCurrentFile(file) {
      this.currentFile = file
    },

    addFile(file) {
      this.fileList.push(file)
    },

    removeFile(fileId) {
      const index = this.fileList.findIndex(f => f.id === fileId)
      if (index > -1) {
        this.fileList.splice(index, 1)
      }
    },

    clearFiles() {
      this.fileList = []
    },

    setLoading(status) {
      this.loading = status
    }
  }
})
