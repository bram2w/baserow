<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div class="license-detail">
      <h1>
        {{ $t('license.title', license) }}
      </h1>
      <div class="license-detail__users">
        <h2>{{ $t('license.users') }}</h2>
        <p>
          {{ $t('license.description', license) }}
        </p>
        <div class="license-detail__add">
          <div
            v-show="license.seats - license.seats_taken > 0"
            class="license-detail__add-dropdown"
          >
            <div v-if="addUserLoading" class="loading-overlay"></div>
            <PaginatedDropdown
              ref="add"
              :value="null"
              :fetch-page="fetchUsers"
              :not-selected-text="$t('license.addUser')"
              :add-empty-item="false"
              @input="addUser"
            ></PaginatedDropdown>
          </div>
          {{
            $tc('license.seatLeft', leftSeats, {
              count: leftSeats,
            })
          }}
        </div>
        <div
          v-for="(licenseUser, index) in license.users"
          :key="licenseUser.email"
          class="license-detail__user"
        >
          <div class="license-detail__user-number">{{ index + 1 }}</div>
          <div class="license-detail__user-name">
            {{ licenseUser.first_name }}
          </div>
          <div class="license-detail__user-email">{{ licenseUser.email }}</div>
          <div>
            <div v-if="removingUser === licenseUser.id" class="loading"></div>
            <a
              v-else
              class="license-detail__user-delete"
              @click="removeUser(licenseUser)"
            >
              <i class="fas fa-trash"></i>
            </a>
          </div>
        </div>
        <div class="license-detail__actions">
          <div v-if="actionLoading" class="loading"></div>
          <template v-else>
            <a
              v-show="license.seats - license.seats_taken > 0"
              class="margin-right-2"
              @click="fillSeats()"
              >{{ $t('license.fillSeats') }}</a
            >
            <a
              v-show="license.seats - license.seats_taken < license.seats"
              class="color-error"
              @click="removeAllUsers()"
              >{{ $t('license.removeAll') }}</a
            >
          </template>
        </div>
      </div>
      <div class="license-detail__body">
        <div class="license-detail__body-left">
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.licenseId') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ license.license_id }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.plan') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              <div
                class="license-plan license-plan--inline"
                :class="{
                  'license-plan--premium': license.product_code === 'premium',
                }"
              >
                <template v-if="license.product_code === 'premium'">{{
                  $t('license.premium')
                }}</template>
              </div>
              <div
                v-if="!license.is_active"
                class="license-plan license-plan--inline license-plan--expired"
              >
                {{ $t('license.expired') }}
              </div>
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.validFrom') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ localDateTime(license.valid_from) }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.validThrough') }}
              </div>
              <div class="license-detail__item-description">
                {{ $t('license.validThroughDescription') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ localDateTime(license.valid_through) }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.lastCheck') }}
              </div>
              <div class="license-detail__item-description">
                {{ $t('license.lastCheckDescription') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              <div v-if="checkLoading" class="loading"></div>
              <template v-else>
                {{ localDateTime(license.last_check) }}
                <a @click="check()">{{ $t('license.checkNow') }}</a>
              </template>
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.seats') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ license.seats_taken }} / {{ license.seats }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.licensedTo') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ license.issued_to_name }} ({{ license.issued_to_email }})
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.premiumFeatures') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              <i
                class="fas fa-check"
                :class="
                  license.product_code === 'premium'
                    ? 'license-yes'
                    : 'license-no'
                "
              ></i>
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.applications') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ $t('license.unlimited') }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.rowUsage') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ $t('license.unlimited') }}
            </div>
          </div>
          <div class="license-detail__item">
            <div class="license-detail__item-label">
              <div class="license-detail__item-name">
                {{ $t('license.storeUsage') }}
              </div>
            </div>
            <div class="license-detail__item-value">
              {{ $t('license.unlimited') }}
            </div>
          </div>
        </div>
        <div class="license-body__body-right">
          <div class="delete-section">
            <div class="delete-section__label">
              <div class="delete-section__label-icon">
                <i class="fas fa-exclamation"></i>
              </div>
              {{ $t('license.disconnectLicense') }}
            </div>
            <i18n path="license.disconnectDescription" tag="p">
              <template #contact>
                <a href="https://baserow.io/contact" target="_blank"
                  >baserow.io/contact</a
                >
              </template>
            </i18n>
            <a
              class="button button--error"
              @click="$refs.disconnectModal.show()"
              >{{ $t('license.disconnectLicense') }}</a
            >
            <DisconnectLicenseModal
              ref="disconnectModal"
              :license="license"
            ></DisconnectLicenseModal>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'
import { notifyIf } from '@baserow/modules/core/utils/error'
import PaginatedDropdown from '@baserow/modules/core/components/PaginatedDropdown'
import LicenseService from '@baserow_premium/services/license'
import DisconnectLicenseModal from '@baserow_premium/components/license/DisconnectLicenseModal'

export default {
  components: { DisconnectLicenseModal, PaginatedDropdown },
  layout: 'app',
  middleware: 'staff',
  async asyncData({ params, app, error }) {
    try {
      const { data } = await LicenseService(app.$client).fetch(params.id)
      return { license: data }
    } catch {
      return error({
        statusCode: 404,
        message: 'The license was not found.',
      })
    }
  },
  data() {
    return {
      user: null,
      addUserLoading: false,
      actionLoading: false,
      checkLoading: false,
      removingUser: -1,
    }
  },
  computed: {
    leftSeats() {
      return this.license.seats - this.license.seats_taken
    },
  },
  methods: {
    localDateTime(timestamp) {
      if (timestamp === null) {
        return ''
      }

      return moment.utc(timestamp).local().format('ll LT')
    },
    fetchUsers(page, search) {
      return LicenseService(this.$client).lookupUsers(
        this.license.id,
        page,
        search
      )
    },
    async addUser(event) {
      this.addUserLoading = true
      try {
        const { data } = await LicenseService(this.$client).addUser(
          this.license.id,
          event.id
        )
        this.license.users.push(data)
        this.license.seats_taken += 1
      } catch (error) {
        notifyIf(error)
      }

      this.addUserLoading = false
      this.$nextTick(() => {
        this.user = null
        this.$refs.add.reset()
      })
    },
    async removeUser(user) {
      this.removingUser = user.id

      try {
        await LicenseService(this.$client).removeUser(this.license.id, user.id)
        const index = this.license.users.findIndex((u) => u.id === user.id)
        if (index !== undefined) {
          this.license.seats_taken -= 1
          this.license.users.splice(index, 1)
        }
        this.$refs.add.reset()
      } catch (error) {
        notifyIf(error)
      } finally {
        this.removingUser = -1
      }
    },
    async fillSeats() {
      this.actionLoading = true

      try {
        const { data } = await LicenseService(this.$client).fillSeats(
          this.license.id
        )
        this.license.seats_taken += data.length
        this.license.users.push(...data)
        this.$refs.add.reset()
      } catch (error) {
        notifyIf(error)
      }

      this.actionLoading = false
    },
    async removeAllUsers() {
      this.actionLoading = true

      try {
        await LicenseService(this.$client).removeAllUsers(this.license.id)
        this.license.seats_taken = 0
        this.license.users = []
        this.$refs.add.reset()
      } catch (error) {
        notifyIf(error)
      }

      this.actionLoading = false
    },
    async check() {
      this.checkLoading = true

      try {
        const { data, status } = await LicenseService(this.$client).check(
          this.license.id
        )
        if (status === 204) {
          this.$router.push({ name: 'admin-licenses' })
        } else {
          this.license = data
        }
      } catch (error) {
        notifyIf(error)
      }

      this.checkLoading = false
    },
  },
}
</script>
