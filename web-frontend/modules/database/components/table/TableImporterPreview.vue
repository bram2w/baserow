<template>
  <div class="control mt-3">
    <label class="control__label">{{ title }}</label>
    <div class="control__elements">
      <div class="table-preview__container">
        <div class="table-preview">
          <div class="select-row-modal__head">
            <SimpleGrid :rows="rows" :fields="fields" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SimpleGrid from '@baserow/modules/database/components/view/grid/SimpleGrid'

export default {
  components: { SimpleGrid },
  props: {
    rows: {
      type: Array,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
  },
}
</script>
