<template>
  <div class="grid-view__row" :style="{ width: width + 'px' }">
    <div class="grid-view__column" :style="{ width: width + 'px' }">
      <a
        class="grid-view__add-row"
        :class="{ hover: addHover }"
        @mouseover="setHover(true)"
        @mouseleave="setHover(false)"
        @click="$emit('add-row')"
      >
        <i v-if="includeRowDetails" class="fas fa-plus"></i>
      </a>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

export default {
  name: 'GridViewRowAdd',
  mixins: [gridViewHelpers],
  props: {
    fields: {
      type: Array,
      required: true,
    },
    includeRowDetails: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    width() {
      let width = this.fields.reduce(
        (value, field) => this.getFieldWidth(field.id) + value,
        0
      )
      if (this.includeRowDetails) {
        width += this.gridViewRowDetailsWidth
      }
      return width
    },
    ...mapGetters({
      addHover: 'view/grid/getAddRowHover',
    }),
  },
  methods: {
    setHover(value) {
      this.$store.dispatch('view/grid/setAddRowHover', value)
    },
  },
}
</script>
