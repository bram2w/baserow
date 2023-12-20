<template>
  <div>
    <h2 class="box__title">{{ $t('pageSettings.title') }}</h2>
    <Error :error="error"></Error>
    <Alert v-if="success" type="success">
      <template #title>{{ $t('pageSettings.pageUpdatedTitle') }}</template>
      <p>{{ $t('pageSettings.pageUpdatedDescription') }}</p>
    </Alert>
    <PageSettingsForm
      :builder="builder"
      :page="page"
      :default-values="page"
      @submitted="updatePage"
    >
      <div class="actions actions--right">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          type="submit"
        >
          {{ $t('action.save') }}
        </button>
      </div>
    </PageSettingsForm>
  </div>
</template>

<script>
import error from '@baserow/modules/core/mixins/error'
import PageSettingsForm from '@baserow/modules/builder/components/page/settings/PageSettingsForm'
import { mapActions } from 'vuex'

export default {
  name: 'PageSettings',
  components: { PageSettingsForm },
  mixins: [error],
  inject: ['builder'],
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      success: false,
    }
  },
  methods: {
    ...mapActions({ actionUpdatePage: 'page/update' }),
    async updatePage({ name, path, path_params: pathPrams }) {
      this.success = false
      this.loading = true
      this.hideError()
      try {
        await this.actionUpdatePage({
          builder: this.builder,
          page: this.page,
          values: {
            name,
            path,
            path_params: pathPrams,
          },
        })
        this.success = true
      } catch (error) {
        this.handleError(error)
      }
      this.loading = false
    },
  },
}
</script>
