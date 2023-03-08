<template>
  <div>
    <!--
    This is a temporary page that just holds the static html code. It can later be used
    to copy parts out off when building the real thing. When we don't need it anymore,
    we should delete it. Note that when this page component is deleted, we must also
    delete `builder/components/TemporaryPreview.vue`.
    -->
    <header class="layout__col-2-1 header header--space-between">
      <ul class="header__filter">
        <li class="header__filter-item">
          <div>
            <a class="header__filter-link"
              ><i class="header__filter-icon fas fa-stream"></i>
              <span class="header__filter-name">Elements</span></a
            >
          </div>
        </li>
        <li class="header__filter-item">
          <div>
            <a class="header__filter-link"
              ><i class="header__filter-icon fas fa-table"></i>
              <span class="header__filter-name">Data</span></a
            >
          </div>
        </li>
        <li class="header__filter-item">
          <div>
            <a class="header__filter-link"
              ><i class="header__filter-icon fas fa-square-root-alt"></i>
              <span class="header__filter-name">Variables</span></a
            >
          </div>
        </li>
        <li class="header__filter-item">
          <div>
            <a class="header__filter-link"
              ><i class="header__filter-icon fas fa-cogs"></i>
              <span class="header__filter-name">Page settings</span></a
            >
          </div>
        </li>
      </ul>
      <ul class="header__filter">
        <li class="header__filter-item header__filter-item--no-margin-left">
          <div>
            <a
              class="header__filter-link"
              :class="{ 'active active--primary': device === 'desktop' }"
              @click="setDevice('desktop')"
              ><i class="header__filter-icon fas fa-laptop"></i
            ></a>
          </div>
        </li>
        <li class="header__filter-item">
          <div>
            <a
              class="header__filter-link"
              :class="{ 'active active--primary': device == 'tablet' }"
              @click="setDevice('tablet')"
              ><i class="header__filter-icon fas fa-tablet"></i
            ></a>
          </div>
        </li>
        <li class="header__filter-item">
          <div>
            <a
              class="header__filter-link"
              :class="{ 'active active--primary': device == 'smartphone' }"
              @click="setDevice('smartphone')"
              ><i class="header__filter-icon fas fa-mobile"></i
            ></a>
          </div>
        </li>
      </ul>
      <ul class="header__filter">
        <li class="header__filter-item">
          <div>
            <a class="header__filter-link">
              <span class="header__filter-name">Preview</span></a
            >
          </div>
        </li>
        <li class="header__filter-item header__filter-item--right">
          <div>
            <a class="header__filter-link"
              ><i class="header__filter-icon fas fa-upload"></i>
              <span class="header__filter-name">Publish</span></a
            >
          </div>
        </li>
      </ul>
    </header>
    <div class="layout__col-2-2 content">
      <div class="page-builder">
        <div class="page-builder__preview-wrapper">
          <div
            ref="preview"
            class="page-builder__preview"
            :class="{
              'page-builder__preview--tablet': device == 'tablet',
              'page-builder__preview--smartphone': device == 'smartphone',
            }"
          >
            <div ref="previewScaled" class="page-builder__preview-scaled">
              <TemporaryPreview>
                <div
                  v-for="(i, index) in new Array(3)"
                  :key="index"
                  class="page-builder__preview-element"
                  :class="{
                    'page-builder__preview-element--active':
                      selectedElementIndex === index,
                  }"
                  @click="selectedElementIndex = index"
                >
                  <a
                    v-if="selectedElementIndex + 1 !== index"
                    href="#"
                    class="
                      page-builder__preview-add
                      page-builder__preview-element-add
                      page-builder__preview-element-add-first
                    "
                  >
                    <i class="fas fa-plus"></i>
                  </a>
                  <a
                    v-if="selectedElementIndex - 1 !== index"
                    href="#"
                    class="
                      page-builder__preview-add
                      page-builder__preview-element-add
                      page-builder__preview-element-add-last
                    "
                  >
                    <i class="fas fa-plus"></i>
                  </a>
                  <div
                    class="
                      page-builder__preview-menu
                      page-builder__preview-element-menu
                    "
                  >
                    <a href="#" class="page-builder__preview-menu-item">
                      <i class="fas fa-copy"></i>
                      <div class="page-builder__preview-menu-item-description">
                        Copy
                      </div>
                    </a>
                    <a href="#" class="page-builder__preview-menu-item">
                      <i class="fas fa-arrow-up"></i>
                      <div class="page-builder__preview-menu-item-description">
                        Move up
                      </div>
                    </a>
                    <a href="#" class="page-builder__preview-menu-item">
                      <i class="fas fa-arrow-down"></i>
                      <div class="page-builder__preview-menu-item-description">
                        Move down
                      </div>
                    </a>
                    <a href="#" class="page-builder__preview-menu-item">
                      <i class="fas fa-trash"></i>
                      <div class="page-builder__preview-menu-item-description">
                        Delete
                      </div>
                    </a>
                  </div>
                  <p style="font-size: 20px; line-height: 180%; margin: 0">
                    1Are your projects, ideas or business processes unorganized
                    or unclear? With Baserow you decide how you want to
                    structure everything. Whether you’re managing customers,
                    products or airplanes. If you know how a spreadsheet works,
                    you know how Baserow works.
                  </p>
                </div>
              </TemporaryPreview>
            </div>
          </div>
        </div>
        <div class="page-builder__sidebar">
          <ul class="page-builder__sidebar-tabs">
            <li class="page-builder__sidebar-tab">
              <a href="#" class="page-builder__sidebar-tab-link">General</a>
            </li>
            <li class="page-builder__sidebar-tab">
              <a href="#" class="page-builder__sidebar-tab-link">Style</a>
            </li>
            <li class="page-builder__sidebar-tab">
              <a
                href="#"
                class="
                  page-builder__sidebar-tab-link
                  page-builder__sidebar-tab-link--active
                "
                >Visibility</a
              >
            </li>
            <li class="page-builder__sidebar-tab">
              <a href="#" class="page-builder__sidebar-tab-link">Events</a>
            </li>
          </ul>
          <div class="page-builder__sidebar-content">
            content
            <br />
            content
            <br />
            content
            <br />
            content
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ResizeObserver from 'resize-observer-polyfill'

import TemporaryPreview from '@baserow/modules/builder/components/TemporaryPreview'

export default {
  name: 'Page',
  components: { TemporaryPreview },
  layout: 'app',
  data() {
    return {
      device: 'desktop', // desktop, tablet or smartphone
      selectedElementIndex: 1,
    }
  },
  mounted() {
    this.resizeObserver = new ResizeObserver(() => {
      this.resized()
    })
    this.resizeObserver.observe(this.$el)
    this.$nextTick(() => {
      this.resized()
    })
  },
  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el)
  },
  methods: {
    setDevice(value) {
      this.device = value
      this.$nextTick(() => {
        this.resized()
      })
    },
    resized() {
      // The widths are the minimum width the preview must have. If the preview dom
      // element becomes smaller than the target, it will be scaled down so that the
      // actual width remains the same, and it will preview the correct device.
      const minimumWidths = {
        desktop: 1100,
        tablet: 768,
        smartphone: 420,
      }
      const preview = this.$refs.preview
      const previewScaled = this.$refs.previewScaled

      const currentWidth = preview.clientWidth
      const currentHeight = preview.clientHeight
      const targetWidth = minimumWidths[this.device]
      let scale = 1
      let horizontal = 0
      let vertical = 0

      if (currentWidth < targetWidth) {
        scale = Math.round((currentWidth / targetWidth) * 100) / 100
        horizontal = (currentWidth - currentWidth * scale) / 2 / scale
        vertical = (currentHeight - currentHeight * scale) / 2 / scale
      }

      previewScaled.style.transform = `scale(${scale})`
      previewScaled.style.transformOrigin = `0 0`
      previewScaled.style.width = `${horizontal * 2 + currentWidth}px`
      previewScaled.style.height = `${vertical * 2 + currentHeight}px`
    },
  },
}
</script>
