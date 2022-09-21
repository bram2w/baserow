<template>
  <div
    v-scroll="scroll"
    class="simple-grid"
    :class="{
      'simple-grid--full-height': fullHeight,
      'simple-grid--with-footer': withFooter,
    }"
  >
    <div
      v-if="fixedFields.length > 0 || showRowId"
      ref="left"
      class="simple-grid__left"
    >
      <div class="simple-grid__head">
        <div
          v-if="showRowId"
          class="simple-grid__field simple-grid__field--first"
        ></div>
        <div
          v-for="field in fixedFields"
          :key="field.id"
          class="simple-grid__field"
        >
          <i
            class="fas simple-grid__field-icon"
            :class="'fa-' + fieldTypes[field.type].iconClass"
          ></i>
          {{ field.name }}
        </div>
      </div>
      <div class="simple-grid__body">
        <div
          v-for="row in rows"
          :key="row.id"
          class="simple-grid__row"
          :class="{
            'simple-grid__row--hover':
              showHoveredRow && currentHoveredRow === row.id,
            'simple-grid__row--selected': selectedRows.includes(row.id),
          }"
          @click="$emit('row-click', row)"
          @mouseover="currentHoveredRow = row.id"
          @mouseleave="currentHoveredRow = null"
        >
          <div
            v-if="showRowId"
            class="simple-grid__cell simple-grid__cell--first"
          >
            {{ row.id }}
          </div>
          <div
            v-for="field in fixedFields"
            :key="field.id"
            class="simple-grid__cell"
          >
            <SimpleGridField :field="field" :row="row" />
          </div>
        </div>
        <div
          v-if="canAddRow"
          class="simple-grid__row"
          :class="{ 'simple-grid__row--hover': showHoveredRow && addRowHover }"
          @mouseover="addRowHover = true"
          @mouseleave="addRowHover = false"
          @click="$emit('add-row')"
        >
          <a
            class="
              simple-grid__cell simple-grid__cell--single simple-grid__add-row
            "
          >
            <i class="fas fa-plus" />
          </a>
        </div>
        <div v-if="withFooter" class="simple-grid__foot">
          <slot name="footLeft"></slot>
        </div>
      </div>
    </div>
    <div class="simple-grid__right-scrollbar-wrapper">
      <Scrollbars
        ref="scrollbars"
        horizontal="getHorizontalScrollbarElement"
        @horizontal="horizontalScroll"
      ></Scrollbars>
      <div ref="right" class="simple-grid__right-wrapper">
        <div class="simple-grid__right">
          <div class="simple-grid__head">
            <div
              v-for="field in fields"
              :key="field.id"
              class="simple-grid__field"
            >
              <i
                class="fas simple-grid__field-icon"
                :class="'fa-' + fieldTypes[field.type].iconClass"
              ></i>
              {{ field.name }}
            </div>
          </div>
          <div class="simple-grid__body">
            <div
              v-for="row in rows"
              :key="row.id"
              class="simple-grid__row"
              :class="{
                'simple-grid__row--hover':
                  showHoveredRow && currentHoveredRow === row.id,
                'simple-grid__row--selected': selectedRows.includes(row.id),
              }"
              @click="$emit('row-click', row)"
              @mouseover="currentHoveredRow = row.id"
              @mouseleave="currentHoveredRow = null"
            >
              <div
                v-for="field in fields"
                :key="field.id"
                class="simple-grid__cell"
              >
                <SimpleGridField :field="field" :row="row" />
              </div>
            </div>
            <div
              v-if="canAddRow"
              class="simple-grid__row"
              :class="{
                'simple-grid__row--hover': showHoveredRow && addRowHover,
              }"
              @mouseover="addRowHover = true"
              @mouseleave="addRowHover = false"
              @click="$emit('add-row')"
            >
              <div class="simple-grid__cell simple-grid__cell--single"></div>
            </div>
            <div v-if="withFooter" class="simple-grid__foot"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SimpleGridField from './SimpleGridField'
export default {
  name: 'SimpleGrid',
  components: { SimpleGridField },
  props: {
    rows: {
      type: Array,
      required: true,
    },
    fixedFields: {
      type: Array,
      required: false,
      default: () => [],
    },
    fields: {
      type: Array,
      required: true,
    },
    selectedRows: {
      type: Array,
      required: false,
      default: () => [],
    },
    showHoveredRow: {
      type: Boolean,
      required: false,
      default: false,
    },
    canAddRow: {
      type: Boolean,
      required: false,
      default: false,
    },
    showRowId: {
      type: Boolean,
      required: false,
      default: false,
    },
    fullHeight: {
      type: Boolean,
      required: false,
      default: false,
    },
    withFooter: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return { addRowHover: false, currentHoveredRow: null }
  },
  computed: {
    fieldTypes() {
      return this.$registry.getAll('field')
    },
  },
  methods: {
    getHorizontalScrollbarElement() {
      return this.$refs.right
    },
    /**
     * Event that is called when the users does any form of scrolling on the whole grid
     * surface.
     */
    scroll(pixelY, pixelX) {
      const left = this.$refs.right.scrollLeft + pixelX
      this.horizontalScroll(left)
      this.$refs.scrollbars.update()
      return pixelY !== 0
    },
    horizontalScroll(left) {
      this.$refs.right.scrollLeft = left
    },
  },
}
</script>
