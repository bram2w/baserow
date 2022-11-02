<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div v-if="orderedLicenses.length === 0" class="placeholder">
      <div class="placeholder__icon">
        <i class="fas fa-certificate"></i>
      </div>
      <h1 class="placeholder__title">
        {{ $t('licenses.titleNoLicenses') }}
      </h1>
      <p class="placeholder__content">
        {{ $t('licenses.noLicensesDescription') }}
      </p>
      <PremiumFeatures
        class="licenses__features margin-bottom-2"
      ></PremiumFeatures>
      <div class="placeholder__action">
        <a class="button button--large" @click="$refs.registerModal.show()">
          <i class="fas fa-plus"></i>
          {{ $t('licenses.registerLicense') }}
        </a>
        <RedirectToBaserowModal
          :href="'https://baserow.io/get-license/' + instanceId + '/'"
          class="button button--large button--ghost margin-left-2"
          target="_blank"
          >{{ $t('licenses.getLicense') }}</RedirectToBaserowModal
        >
      </div>
      <p>
        {{ $t('licenses.baserowInstanceId') }}
        <br />
        <span class="licenses__instance-id">{{ instanceId }}</span>
        <a
          class="licenses__instance-id-copy"
          @click.prevent="
            ;[copyToClipboard(instanceId), $refs.instanceIdCopied.show()]
          "
        >
          {{ $t('action.copy') }}
          <Copied ref="instanceIdCopied"></Copied>
        </a>
      </p>
    </div>
    <div v-else class="licenses">
      <div class="licenses__head">
        <h1 class="margin-bottom-0">
          {{ $t('licenses.titleLicenses') }}
        </h1>
        <div>
          <a
            class="button button--primary margin-right-1"
            @click="$refs.registerModal.show()"
          >
            <i class="fas fa-plus"></i>
            {{ $t('licenses.registerLicense') }}
          </a>
          <RedirectToBaserowModal
            :href="'https://baserow.io/get-license/' + instanceId + '/'"
            class="button button--ghost"
            target="_blank"
            >{{ $t('licenses.getLicense') }}</RedirectToBaserowModal
          >
        </div>
      </div>
      <div class="margin-bottom-3">
        {{ $t('licenses.baserowInstanceId') }}
        <span class="licenses__instance-id">{{ instanceId }}</span>
        <a
          class="licenses__instance-id-copy"
          @click.prevent="
            ;[copyToClipboard(instanceId), $refs.instanceIdCopied.show()]
          "
        >
          {{ $t('action.copy') }}
          <Copied ref="instanceIdCopied"></Copied>
        </a>
      </div>
      <div class="licenses__items">
        <nuxt-link
          v-for="license in orderedLicenses"
          :key="license.id"
          :to="{ name: 'admin-license', params: { id: license.id } }"
          class="licenses__item"
        >
          <div class="licenses__item-head">
            <div class="licenses__item-title">
              {{ $t('licenses.licenceId') }}
              <span class="licenses__item-title-license">{{
                license.license_id
              }}</span>
            </div>
            <div
              class="license-plan margin-right-1"
              :class="getLicenseType(license).getLicenseBadgeClass()"
            >
              {{ getLicenseType(license).getName() }}
            </div>
            <div
              v-if="!license.is_active"
              class="license-plan license-plan--expired"
            >
              {{ $t('licenses.expired') }}
            </div>
          </div>
          <div class="licenses__item-validity">
            {{
              $t('licenses.validity', {
                start: localDate(license.valid_from),
                end: localDate(license.valid_through),
              })
            }}
          </div>
          <ul class="licenses__item-details">
            <li>
              {{ license.seats_taken }} / {{ license.seats }}
              {{ $t('licenses.seats') }}
            </li>
            <li v-if="licenseFeatureDescription(license)">
              {{ licenseFeatureDescription(license) }}
              <i class="fas margin-left-1 fa-check license-yes"></i>
            </li>
          </ul>
        </nuxt-link>
      </div>
    </div>
    <RegisterLicenseModal ref="registerModal"></RegisterLicenseModal>
  </div>
</template>

<script>
import LicenseService from '@baserow_premium/services/license'
import RegisterLicenseModal from '@baserow_premium/components/license/RegisterLicenseModal'
import RedirectToBaserowModal from '@baserow_premium/components/RedirectToBaserowModal'
import PremiumFeatures from '@baserow_premium/components/PremiumFeatures'
import moment from '@baserow/modules/core/moment'
import SettingsService from '@baserow/modules/core/services/settings'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  components: { RedirectToBaserowModal, RegisterLicenseModal, PremiumFeatures },
  layout: 'app',
  middleware: 'staff',
  async asyncData({ app, error }) {
    try {
      const { data: instanceData } = await SettingsService(
        app.$client
      ).getInstanceID()
      const { data } = await LicenseService(app.$client).fetchAll()
      return {
        licenses: data,
        instanceId: instanceData.instance_id,
      }
    } catch {
      return error({
        statusCode: 400,
        message: 'Something went wrong while fetching the licenses.',
      })
    }
  },
  computed: {
    orderedLicenses() {
      return this.licenses
        .slice()
        .sort(
          (a, b) =>
            new Date(a.valid_from).getTime() - new Date(b.valid_from).getTime()
        )
        .sort((a, b) =>
          a.is_active === b.is_active ? 0 : a.is_active ? -1 : 1
        )
    },
  },
  methods: {
    localDate(date) {
      return moment.utc(date).local().format('ll')
    },
    copyToClipboard(value) {
      copyToClipboard(value)
    },
    getLicenseType(license) {
      return this.$registry.get('license', license.product_code)
    },
    licenseFeatureDescription(license) {
      return this.getLicenseType(license).getFeaturesDescription()
    },
    licenseSeatsInfo(license) {
      return this.getLicenseType(license).getFeaturesDescription()
    },
  },
}
</script>
