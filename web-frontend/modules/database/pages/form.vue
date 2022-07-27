<template>
  <div>
    <Notifications></Notifications>
    <div class="form-view__page">
      <div
        v-if="coverImage !== null"
        class="form-view__cover"
        :style="{
          'background-image': `url(${coverImage.url})`,
        }"
      ></div>
      <form
        v-if="!submitted"
        class="form-view__body"
        @submit.prevent="submit(values)"
      >
        <div class="form-view__heading">
          <div v-if="logoImage !== null" class="form_view__logo">
            <img class="form_view__logo-img" :src="logoImage.url" width="200" />
          </div>
          <h1 v-if="title !== ''" class="form-view__title">{{ title }}</h1>
          <p v-if="description !== ''" class="form-view__description">
            {{ description }}
          </p>
        </div>
        <FormPageField
          v-for="field in visibleFields"
          :ref="'field-' + field.field.id"
          :key="field.field.id"
          v-model="values['field_' + field.field.id]"
          class="form-view__field"
          :slug="$route.params.slug"
          :field="field"
        ></FormPageField>
        <div class="form-view__actions">
          <FormViewPoweredBy></FormViewPoweredBy>
          <div class="form-view__submit">
            <button
              class="button button--primary button--large"
              :class="{ 'button--loading': loading }"
              :disabled="loading"
            >
              {{ submit_text }}
            </button>
          </div>
        </div>
      </form>
      <div v-else-if="submitted" class="form-view__submitted">
        <template v-if="isRedirect">
          <div class="form-view__submitted-message">
            Thanks for submitting the form!
          </div>
          <div class="form-view__redirecting-description">
            You're being redirected to {{ submitActionRedirectURL }}.
          </div>
          <div class="form-view__redirecting-loading">
            <div class="loading-absolute-center"></div>
          </div>
        </template>
        <div v-else class="form-view__submitted-message">
          {{ submitActionMessage || 'Thanks for submitting the form!' }}
        </div>
        <FormViewPoweredBy></FormViewPoweredBy>
      </div>
    </div>
  </div>
</template>

<script>
import { clone, isPromise } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'
import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import FormService from '@baserow/modules/database/services/view/form'
import FormPageField from '@baserow/modules/database/components/view/form/FormPageField'
import FormViewPoweredBy from '@baserow/modules/database/components/view/form/FormViewPoweredBy'
import { getPrefills } from '@baserow/modules/database/utils/form'
import { matchSearchFilters } from '@baserow/modules/database/utils/view'

export default {
  components: {
    Notifications,
    FormPageField,
    FormViewPoweredBy,
  },
  async asyncData({ params, error, app, route, redirect, store }) {
    const slug = params.slug
    const publicAuthToken = await store.dispatch(
      'page/view/public/setAuthTokenFromCookies',
      { slug }
    )

    let data = null
    try {
      const { data: responseData } = await FormService(
        app.$client
      ).getMetaInformation(slug, publicAuthToken)
      data = responseData
    } catch (e) {
      const statusCode = e.response?.status
      // password protect forms require authentication
      if (statusCode === 401) {
        return redirect({
          name: 'database-public-view-auth',
          query: { original: route.path },
        })
      } else {
        return error({ statusCode: 404, message: 'Form not found.' })
      }
    }

    // After the form field meta data has been fetched, we need to make the values
    // object with the empty field value as initial form value.
    const values = {}
    const prefills = getPrefills(route.query)
    const promises = []
    data.fields.forEach((field) => {
      field._ = { touched: false }
      const fieldType = app.$registry.get('field', field.field.type)
      const setValue = (value) => {
        values[`field_${field.field.id}`] = value
      }

      const prefill = prefills[field.name]
      values[`field_${field.field.id}`] = fieldType.getEmptyValue(field.field) // Default value
      if (prefill !== undefined && fieldType.canParseQueryParameter()) {
        const result = fieldType.parseQueryParameter(field, prefill, {
          slug,
          client: app.$client,
        })

        if (isPromise(result)) {
          result.then(setValue)
          promises.push(result)
        } else {
          setValue(result)
        }
      }
    })

    await Promise.all(promises)

    // Order the fields directly after fetching the results to make sure the form is
    // serverside rendered in the right order.
    data.fields = data.fields.sort((a, b) => {
      // First by order.
      if (a.order > b.order) {
        return 1
      } else if (a.order < b.order) {
        return -1
      }

      // Then by id.
      if (a.field.id < b.field.id) {
        return -1
      } else if (a.field.id > b.field.id) {
        return 1
      } else {
        return 0
      }
    })

    return {
      title: data.title,
      description: data.description,
      coverImage: data.cover_image,
      logoImage: data.logo_image,
      submit_text: data.submit_text,
      fields: data.fields,
      values,
      publicAuthToken,
    }
  },
  data() {
    return {
      loading: false,
      submitted: false,
      submitAction: 'MESSAGE',
      submitActionMessage: '',
      submitActionRedirectURL: '',
    }
  },
  head() {
    return {
      title: this.title || 'Form',
      bodyAttrs: {
        class: ['background-white'],
      },
    }
  },
  computed: {
    isRedirect() {
      return (
        this.submitAction === 'REDIRECT' && this.submitActionRedirectURL !== ''
      )
    },
    /**
     * Returns all the fields that should be visible to the visitor. They can change
     * depending on the values because some fields have conditions whether they
     * should be visible.
     */
    visibleFields() {
      return this.fields.reduce((visibleFields, field, index, tmp) => {
        // If the conditional visibility is disabled, we must always show the field.
        if (!field.show_when_matching_conditions) {
          return [...visibleFields, field]
        }

        // A condition is only valid if the filter field is before this field because
        // you can only filter fields before. Therefore, we check which fields are
        // before.
        const fieldsBefore = this.fields.slice(0, index).map((f) => f.field)
        // Find the valid filters by checking if the filter field is before this field
        // and if the filter type is compatible with the field.
        const conditions = field.conditions.filter((condition) => {
          const filterType = this.$registry.get('viewFilter', condition.type)
          const filterField = fieldsBefore.find((f) => f.id === condition.field)
          return (
            filterField !== undefined &&
            filterType.fieldIsCompatible(filterField)
          )
        })
        const conditionType = field.condition_type

        // If there aren't any conditions, we must always show the field.
        if (conditions.length === 0) {
          return [...visibleFields, field]
        }

        // We only want to work with the values of fields that are actually visible.
        // This to avoid matching the conditions on values of fields that aren't
        // visible, but were filled out in the past and are still remembered in memory.
        const visibleFieldIds = visibleFields.map((f) => f.field.id)
        const visibleValues = clone(this.values)
        this.fields
          .filter(
            (f) =>
              !visibleFieldIds.includes(f.field.id) &&
              f.field.id !== field.field.id
          )
          .forEach((f) => {
            visibleValues['field_' + f.field.id] = this.$registry
              .get('field', f.field.type)
              .getEmptyValue(f.field)
          })

        if (
          matchSearchFilters(
            this.$registry,
            conditionType,
            conditions,
            fieldsBefore,
            visibleValues
          )
        ) {
          return [...visibleFields, field]
        }

        return visibleFields
      }, [])
    },
  },
  methods: {
    async submit() {
      if (this.loading) {
        return
      }

      this.touch()
      this.loading = true
      const values = clone(this.values)
      const submitValues = {}

      // Loop over the visible fields, because we only want to submit those values.
      for (let i = 0; i < this.visibleFields.length; i++) {
        const field = this.visibleFields[i]
        const fieldType = this.$registry.get('field', field.field.type)
        const valueName = `field_${field.field.id}`
        const value = values[valueName]
        const ref = this.$refs['field-' + field.field.id][0]

        // If the field required and empty or if the value has a validation error, then
        // we don't want to submit the form, focus on the field and top the loading.
        if (
          (field.required && fieldType.isEmpty(field.field, value)) ||
          fieldType.getValidationError(field.field, value) !== null ||
          // It could be that the field component is in an invalid state and hasn't
          // update the value yet. In that case, we also don't want to submit the form.
          !ref.isValid()
        ) {
          ref.focus()
          this.loading = false
          return
        }

        submitValues[valueName] = fieldType.prepareValueForUpdate(
          field.field,
          values[valueName]
        )
      }

      try {
        const slug = this.$route.params.slug
        const { data } = await FormService(this.$client).submit(
          slug,
          submitValues,
          this.publicAuthToken
        )

        this.submitted = true
        this.submitAction = data.submit_action
        this.submitActionMessage = data.submit_action_message
        this.submitActionRedirectURL = data.submit_action_redirect_url.replace(
          `{row_id}`,
          data.row_id
        )

        // If the submit action is a redirect, then we need to redirect safely to the
        // provided URL.
        if (this.isRedirect) {
          setTimeout(() => {
            window.location.assign(this.submitActionRedirectURL)
          }, 4000)
        }
      } catch (error) {
        notifyIf(error, 'view')
      }
      this.loading = false
    },
    /**
     * Marks all the fields are touched. This will show any validation error messages
     * if there are any.
     */
    touch() {
      this.visibleFields.forEach((field) => {
        field._.touched = true
      })
    },
  },
}
</script>
