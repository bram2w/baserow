<template>
  <div>
    <h2 class="box__title">{{ $t('domainSettings.titleAddDomain') }}</h2>
    <Error :error="error"></Error>
    <FormElement class="control">
      <Dropdown
        v-model="selectedDomainType"
        :show-search="false"
        class="domain-settings__domain-type"
      >
        <DropdownItem
          v-for="domainType in domainTypes"
          :key="domainType.getType()"
          :name="domainType.name"
          :value="domainType.getType()"
        />
      </Dropdown>
    </FormElement>
    <component
      :is="currentDomainType.formComponent"
      ref="domainForm"
      :builder="builder"
      @submitted="createDomain($event)"
    />
    <div class="actions">
      <a @click="hideForm">
        <i class="fas fa-chevron-left margin-right-1"></i>
        {{ $t('action.back') }}
      </a>
      <button
        class="button button--large"
        :disabled="createLoading || formHasError()"
        :class="{ 'button--loading': createLoading }"
        @click="onSubmit"
      >
        {{ $t('domainSettings.addDomain') }}
      </button>
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
      selectedDomainType: 'custom',
      createLoading: false,
    }
  },
  computed: {
    domainTypes() {
      return this.$registry.getAll('domain')
    },
    currentDomainType() {
      return this.$registry.get('domain', this.selectedDomainType)
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
    formHasError() {
      if (this.$refs.domainForm) {
        return this.$refs.domainForm.hasError()
      } else {
        return false
      }
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
