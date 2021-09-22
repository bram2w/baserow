<template>
  <div>
    <h2 class="box__title">{{ $t('uploadViaURLUserFileUpload.title') }}</h2>
    <Error :error="error"></Error>
    <form @submit.prevent="upload(values.url)">
      <div class="control">
        <label class="control__label">{{
          $t('uploadViaURLUserFileUpload.urlLabel')
        }}</label>
        <div class="control__elements">
          <input
            v-model="values.url"
            :class="{ 'input--error': $v.values.url.$error }"
            type="text"
            class="input input--large"
            @blur="$v.values.url.$touch()"
          />
          <div v-if="$v.values.url.$error" class="error">
            {{ $t('uploadViaURLUserFileUpload.urlError') }}
          </div>
        </div>
      </div>
      <div class="actions actions--right">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
        >
          {{ $t('action.upload') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, url } from 'vuelidate/lib/validators'

import error from '@baserow/modules/core/mixins/error'
import UserFileService from '@baserow/modules/core/services/userFile'

export default {
  name: 'UploadViaURLUserFileUpload',
  mixins: [error],
  data() {
    return {
      loading: false,
      values: {
        url: '',
      },
    }
  },
  methods: {
    async upload(url) {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const { data } = await UserFileService(this.$client).uploadViaURL(url)
        this.$emit('uploaded', [data])
      } catch (error) {
        this.handleError(error, 'userFile')
      }

      this.loading = false
    },
  },
  validations: {
    values: {
      url: { required, url },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "uploadViaURLUserFileUpload": {
      "title": "Upload from a URL",
      "urlLabel": "URL",
      "urlError": "A valid URL is required."
    }
  },
  "fr": {
    "uploadViaURLUserFileUpload": {
      "title": "À partir d'une URL",
      "urlLabel": "URL",
      "urlError": "Une URL valide doit être renseignée."
    }
  }
}
</i18n>
