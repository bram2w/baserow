<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div v-if="orderedLicenses.length === 0" class="placeholder">
      <div class="placeholder__icon">
        <i class="fas fa-certificate"></i>
      </div>
      <h1 class="placeholder__title">No licenses found</h1>
      <p class="placeholder__content">
        Your Baserow instance doesn’t have any licenses registered. A premium
        license gives you immediate access to all of the additional features. If
        you already have a license, you can register it here. Alternatively you
        can get one by clicking on the button below.
      </p>
      <ul class="licenses__features">
        <li class="licenses__feature">
          <i class="fas fa-fw fa-check licenses__feature-icon"></i>
          Row comments
        </li>
        <li class="licenses__feature">
          <i class="fas fa-fw fa-check licenses__feature-icon"></i>
          JSON and XML export
        </li>
        <li class="licenses__feature">
          <i class="fas fa-fw fa-check licenses__feature-icon"></i>
          Admin functionality
        </li>
      </ul>
      <div class="placeholder__action">
        <a class="button button--large" @click="$refs.registerModal.show()">
          <i class="fas fa-plus"></i>
          Register license
        </a>
        <a
          :href="'https://baserow.io/get-license/' + instanceId + '/'"
          class="button button--large button--ghost margin-left-2"
          target="_blank"
          >Get a license</a
        >
      </div>
      <p>
        Your Baserow instance ID is:
        <br />
        <span class="licenses__instance-id">{{ instanceId }}</span>
        <a
          class="licenses__instance-id-copy"
          @click.prevent="
            ;[copyToClipboard(instanceId), $refs.instanceIdCopied.show()]
          "
        >
          Copy
          <Copied ref="instanceIdCopied"></Copied>
        </a>
      </p>
    </div>
    <div v-else class="licenses">
      <div class="licenses__head">
        <h1 class="margin-bottom-0">Licenses</h1>
        <div>
          <a
            class="button button--primary margin-right-1"
            @click="$refs.registerModal.show()"
          >
            <i class="fas fa-plus"></i>
            Register a license
          </a>
          <a
            :href="'https://baserow.io/get-license/' + instanceId + '/'"
            class="button button--ghost"
            target="_blank"
            >Get a license</a
          >
        </div>
      </div>
      <p>
        Your Baserow instance ID is:
        <span class="licenses__instance-id">{{ instanceId }}</span>
        <a
          class="licenses__instance-id-copy"
          @click.prevent="
            ;[copyToClipboard(instanceId), $refs.instanceIdCopied.show()]
          "
        >
          Copy
          <Copied ref="instanceIdCopied"></Copied>
        </a>
      </p>
      <div class="licenses__items">
        <nuxt-link
          v-for="license in orderedLicenses"
          :key="license.id"
          :to="{ name: 'admin-license', params: { id: license.id } }"
          class="licenses__item"
        >
          <div class="licenses__item-head">
            <div class="licenses__item-title">
              License ID
              <span class="licenses__item-title-license">{{
                license.license_id
              }}</span>
            </div>
            <div
              class="license-plan margin-right-1"
              :class="{
                'license-plan--premium': license.product_code === 'premium',
              }"
            >
              <template v-if="license.product_code === 'premium'"
                >Premium</template
              >
            </div>
            <div
              v-if="!license.is_active"
              class="license-plan license-plan--expired"
            >
              Expired
            </div>
          </div>
          <div class="licenses__item-validity">
            Valid from {{ localDate(license.valid_from) }} through
            {{ localDate(license.valid_through) }}
          </div>
          <ul class="licenses__item-details">
            <li>{{ license.seats_taken }} / {{ license.seats }} seats</li>
            <li>
              Premium features
              <i
                class="fas margin-left-1"
                :class="
                  license.product_code === 'premium'
                    ? 'fa-check license-yes'
                    : 'fa-times license-no'
                "
              ></i>
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
import moment from '@baserow/modules/core/moment'
import SettingsService from '@baserow/modules/core/services/settings'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  components: { RegisterLicenseModal },
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
  },
}
</script>
