<template>
  <div
    class="card"
    :class="{ 'card--loading': loading }"
    @mousedown="$emit('mousedown', $event)"
    @mousemove="$emit('mousemove', $event)"
    @mouseenter="$emit('mouseenter', $event)"
  >
    <RecursiveWrapper
      :components="
        wrapperDecorations.map((comp) => ({
          ...comp,
          props: comp.propsFn(row),
        }))
      "
    >
      <div v-if="coverImageField !== null" class="card__cover">
        <i
          v-if="!coverImageUrl"
          class="card__cover-empty-image iconoir-media-image"
        ></i>
        <div
          v-if="coverImageUrl !== null"
          class="card__cover-image"
          :style="{
            'background-image': 'url(' + coverImageUrl + ')',
          }"
        ></div>
      </div>
      <div class="card__content">
        <component
          :is="dec.component"
          v-for="dec in firstCellDecorations"
          :key="dec.decoration.id"
          v-bind="dec.propsFn(row)"
        />
        <div class="card__fields">
          <div v-for="field in fields" :key="field.id" class="card__field">
            <div class="card__field-name">{{ field.name }}</div>
            <div class="card__field-value">
              <component
                :is="getCardComponent(field)"
                v-if="!loading"
                :field="field"
                :value="row['field_' + field.id]"
              />
            </div>
          </div>
        </div>
      </div>
    </RecursiveWrapper>
  </div>
</template>

<script>
import { FileFieldType } from '@baserow/modules/database/fieldTypes'
import RecursiveWrapper from '@baserow/modules/database/components/RecursiveWrapper'

export default {
  name: 'RowCard',
  components: { RecursiveWrapper },
  props: {
    fields: {
      type: Array,
      required: true,
    },
    decorationsByPlace: {
      type: Object,
      required: false,
      default: () => {},
    },
    row: {
      type: Object,
      required: false,
      default: () => {},
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    coverImageField: {
      required: false,
      default: null,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  computed: {
    coverImageUrl() {
      if (
        this.coverImageField === null ||
        this.coverImageField.type !== FileFieldType.getType()
      ) {
        return null
      }

      const value = this.row[`field_${this.coverImageField.id}`]

      if (!Array.isArray(value)) {
        return null
      }

      const image = value.find((file) => file.is_image)

      if (image === undefined) {
        return null
      }

      return image.thumbnails.card_cover.url
    },
    firstCellDecorations() {
      return this.decorationsByPlace?.first_cell || []
    },
    wrapperDecorations() {
      return this.decorationsByPlace?.wrapper || []
    },
  },
  methods: {
    getCardComponent(field) {
      return this.$registry.get('field', field.type).getCardComponent(field)
    },
  },
}
</script>
