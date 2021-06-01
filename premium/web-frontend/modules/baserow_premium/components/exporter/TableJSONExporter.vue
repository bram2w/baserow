<template>
  <div>
    <div class="row">
      <div class="col col-12">
        <div class="control">
          <label class="control__label">Encoding</label>
          <div class="control__elements">
            <CharsetDropdown
              v-model="values.export_charset"
              :disabled="loading"
            >
            </CharsetDropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CharsetDropdown from '@baserow/modules/core/components/helpers/CharsetDropdown'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'TableJSONExporter',
  components: { CharsetDropdown },
  mixins: [form],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      values: {
        export_charset: 'utf-8',
      },
    }
  },
}
</script>
