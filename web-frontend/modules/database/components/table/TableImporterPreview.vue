<template>
  <div class="control mt-3">
    <label class="control__label">Quick preview</label>
    <div class="control__elements">
      <div class="table-preview__container">
        <div class="table-preview">
          <div class="table-preview__row table-preview__head">
            <div
              v-for="(item, index) in preview.head"
              :key="index"
              class="table-preview__column"
            >
              {{ item }}
            </div>
          </div>
          <div
            v-for="(row, index) in preview.rows"
            :key="index"
            class="table-preview__row"
          >
            <div
              v-for="(column, rowIndex) in row"
              :key="rowIndex"
              class="table-preview__column"
            >
              {{ column }}
            </div>
          </div>
          <div v-if="preview.remaining > 0" class="table-preview__more">
            {{ preview.remaining }} other rows
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    preview: {
      type: Object,
      required: true,
    },
  },
}
</script>
