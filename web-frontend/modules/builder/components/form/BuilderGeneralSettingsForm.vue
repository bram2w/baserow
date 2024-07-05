<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('generalSettings.labelForm')" required>
      <ImageInput
        v-model="values.favicon_file"
        :default-image="defaultFavicon"
        :allowed-image-types="FAVICON_IMAGE_FILE_TYPES"
        :label-description="$t('generalSettings.labelDescription')"
        :label-button="$t('generalSettings.labelButton')"
      />
    </FormGroup>
  </form>
</template>

<script>
import { FAVICON_IMAGE_FILE_TYPES } from '@baserow/modules/core/enums'
import DefaultFavicon from '@baserow/modules/core/static/img/favicon_192.png'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'BuilderGeneralSettingsForm',
  mixins: [form],
  props: {},
  data() {
    return {
      values: { favicon_file: null },
      allowedValues: ['favicon_file'],
    }
  },
  computed: {
    defaultFavicon() {
      return DefaultFavicon
    },
    FAVICON_IMAGE_FILE_TYPES() {
      return FAVICON_IMAGE_FILE_TYPES
    },
  },
}
</script>
