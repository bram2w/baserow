<template>
  <div class="preview-navigation-bar">
    <div />
    <div class="preview-navigation-bar__address-bar">
      <template v-for="pathPart in splitPath">
        <input
          v-if="pathPart.type === 'variable'"
          :key="pathPart.key"
          class="preview-navigation-bar__address-bar-parameter"
          :class="`preview-navigation-bar__address-bar-parameter--${
            paramTypeMap[pathPart.value]
          }`"
          :value="pageParameters[pathPart.value]"
          @input="
            actionSetParameter({
              page,
              name: pathPart.value,
              value: $event.target.value,
            })
          "
        />
        <div
          v-else
          :key="pathPart.key"
          class="preview-navigation-bar__address-bar-path"
        >
          {{ pathPart.value }}
        </div>
      </template>
    </div>
    <div />
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { splitPath } from '@baserow/modules/builder/utils/path'

export default {
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  computed: {
    pageParameters() {
      return this.$store.getters['pageParameter/getParameters'](this.page)
    },
    splitPath() {
      return splitPath(this.page.path).map((pathPart, index) => ({
        ...pathPart,
        key: `${pathPart.value}-${index}`,
      }))
    },
    paramTypeMap() {
      return Object.fromEntries(
        this.page.path_params.map(({ name, type }) => [name, type])
      )
    },
  },
  methods: {
    ...mapActions({ actionSetParameter: 'pageParameter/setParameter' }),
  },
}
</script>
