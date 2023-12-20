<template>
  <div>
    <h2 class="box__title">{{ $t('domainSettings.titleAddDomain') }}</h2>
    <Error :error="error"></Error>
    <FormElement class="control">
      <Dropdown
        v-model="selectedDomain"
        :show-search="false"
        class="domain-settings__domain-type"
      >
        <DropdownItem
          v-for="option in options"
          :key="option.value.domain"
          :name="option.name"
          :value="option.value"
        />
      </Dropdown>
    </FormElement>
    <component
      :is="currentDomainType.formComponent"
      ref="domainForm"
      :builder="builder"
      :domain="selectedDomain.domain"
      @submitted="createDomain($event)"
      @error="formHasError = $event"
    />
    <div class="actions">
      <Button
        type="link"
        prepend-icon="iconoir-nav-arrow-left"
        @click="hideForm"
      >
        {{ $t('action.back') }}
      </Button>
      <Button
        :disabled="createLoading || formHasError"
        size="large"
        :loading="createLoading"
        @click="onSubmit"
      >
        {{ $t('action.create') }}
      </Button>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'DomainsForm',
  mixins: [error],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    hideForm: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      selectedDomain: { type: 'custom', domain: 'custom' },
      createLoading: false,
      formHasError: false,
    }
  },
  computed: {
    domainTypes() {
      return Object.values(this.$registry.getAll('domain')) || []
    },
    selectedDomainType() {
      return this.selectedDomain.type
    },
    currentDomainType() {
      return this.$registry.get('domain', this.selectedDomainType)
    },
    options() {
      return this.domainTypes.map((domainType) => domainType.options).flat()
    },
  },
  watch: {
    selectedDomainType() {
      this.$refs?.domainForm?.reset()
    },
  },
  methods: {
    ...mapActions({
      actionCreateDomain: 'domain/create',
    }),
    onSubmit() {
      this.$refs.domainForm.submit()
    },
    async createDomain(data) {
      this.createLoading = true
      try {
        await this.actionCreateDomain({
          builderId: this.builder.id,
          ...data,
          type: this.selectedDomainType,
        })
        this.hideError()
        this.hideForm()
      } catch (error) {
        this.handleAnyError(error)
      }
      this.createLoading = false
    },
    handleAnyError(error) {
      if (
        !this.$refs.domainForm ||
        !this.$refs.domainForm.handleServerError ||
        !this.$refs.domainForm.handleServerError(error)
      ) {
        this.handleError(error)
      }
    },
  },
}
</script>
