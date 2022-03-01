<template>
  <a
    v-if="!downloadXHR"
    :href="`${url}?dl=${filename}`"
    target="_blank"
    :download="filename"
  >
    <slot></slot>
  </a>
  <a
    v-else
    :href="`${url}`"
    target="_blank"
    :download="filename"
    :class="{ [loadingClass]: loading }"
    @click="onClick($event)"
  >
    <slot></slot>
  </a>
</template>

<script>
export default {
  name: 'DownloadLink',
  props: {
    url: {
      type: String,
      required: true,
    },
    filename: {
      type: String,
      required: true,
    },
    onError: {
      type: Function,
      required: false,
      default: null,
    },
    loadingClass: {
      type: String,
      required: true,
    },
  },
  data() {
    return { loading: false }
  },
  computed: {
    downloadXHR() {
      return this.$env.DOWNLOAD_FILE_VIA_XHR === '1'
    },
  },
  methods: {
    async download() {
      this.loading = true
      // We are using fetch here to avoid extra header
      // as we need to add them to CORS later
      const response = await fetch(this.url)
      const blob = await response.blob()
      const data = window.URL.createObjectURL(blob)

      this.loading = false

      // Create temporary anchor element to trigger the download
      const a = document.createElement('a')
      a.style = 'display: none'
      a.href = data
      a.target = '_blank'
      a.download = this.filename
      document.body.appendChild(a)
      a.onclick = (e) => {
        // prevent modal/whatever closing
        e.stopPropagation()
      }
      a.click()

      setTimeout(function () {
        // Remove the element
        document.body.removeChild(a)
        // Release resource on after triggering the download
        window.URL.revokeObjectURL(data)
      }, 500)
    },
    onClick(event) {
      if (this.downloadXHR) {
        event.preventDefault()
        this.download().catch((error) => {
          // In any case, to be sure the loading animation will not last
          this.loading = false
          if (this.onError) {
            this.onError(error)
          } else {
            throw error
          }
        })
      }
    },
  },
}
</script>
