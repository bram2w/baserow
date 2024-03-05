<template>
  <div class="preview-navigation-bar">
    <div class="preview-navigation-bar__user-selector">
      <UserSelector />
    </div>
    <div class="preview-navigation-bar__address-bar">
      <template v-for="pathPart in splitPath">
        <PreviewNavigationBarInput
          v-if="pathPart.type === 'variable'"
          :key="pathPart.key"
          :class="`preview-navigation-bar__address-bar-parameter-input--${
            paramTypeMap[pathPart.value]
          }`"
          :validation-fn="pathPart.validationFn"
          :default-value="pageParameters[pathPart.value]"
          @change="
            actionSetParameter({
              page,
              name: pathPart.value,
              value: $event,
            })
          "
        />
        <div
          v-else
          :key="`else_${pathPart.key}`"
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
import { splitPath } from '@baserow/modules/builder/utils/path'
import PreviewNavigationBarInput from '@baserow/modules/builder/components/page/PreviewNavigationBarInput'
import UserSelector from '@baserow/modules/builder/components/page/UserSelector'
import { mapActions } from 'vuex'
import { PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS } from '@baserow/modules/builder/enums'

export default {
  components: { PreviewNavigationBarInput, UserSelector },
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
        key:
          pathPart.type === 'variable'
            ? `${this.paramTypeMap[pathPart.value]}-${pathPart.value}-${index}`
            : `${pathPart.value}-${index}`,
        validationFn:
          PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS[
            this.paramTypeMap[pathPart.value]
          ],
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
