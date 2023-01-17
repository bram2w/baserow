<template>
  <form @submit.prevent="submit">
    <div class="row">
      <div class="col col-7">
        <h3>{{ $t('manageTeamForm.nameTitle') }}</h3>
        <FormElement :error="fieldHasErrors('name')" class="control">
          <div class="control__elements">
            <input
              ref="name"
              v-model="values.name"
              :class="{ 'input--error': fieldHasErrors('name') }"
              type="text"
              class="input"
              @blur="$v.values.name.$touch()"
            />
            <div
              v-if="fieldHasErrors('name') && !$v.values.name.required"
              class="error"
            >
              {{ $t('error.requiredField') }}
            </div>
            <div v-if="$v.values.name.$dirty && hasMinMaxError" class="error">
              {{
                $t('error.minMaxLength', {
                  max: $v.values.name.$params.maxLength.max,
                  min: $v.values.name.$params.minLength.min,
                })
              }}
            </div>
          </div>
        </FormElement>
      </div>
      <div class="col col-5">
        <div class="manage-team-form__role-title">
          <h3>
            {{ $t('manageTeamForm.roleTitle') }}
            <HelpIcon
              class="margin-left-1"
              :tooltip="$t('manageTeamForm.roleHelpText')"
            />
          </h3>
        </div>
        <FormElement class="control">
          <div class="control__elements">
            <Dropdown v-model="values.default_role" :show-search="false">
              <DropdownItem
                v-for="role in roles"
                :key="role.uid"
                :name="role.name"
                :value="role.uid"
                :description="role.description"
              >
                {{ role.name }}
                <Badge
                  v-if="!role.isBillable && atLeastOneBillableRole"
                  primary
                  class="margin-left-1"
                  >{{ $t('common.free') }}
                </Badge>
              </DropdownItem>
            </Dropdown>
          </div>
        </FormElement>
      </div>
    </div>
    <div class="row">
      <div class="col col-12">
        <h3>{{ $t('manageTeamForm.membersTitle') }}</h3>
        <div v-if="subjectsLoading" class="loading"></div>
        <p v-if="!invitedUserSubjects.length">
          {{
            $t('manageTeamForm.noSubjectsSelected', {
              buttonLabel: $t('manageTeamForm.inviteMembers'),
            })
          }}
        </p>
        <List
          v-if="invitedUserSubjects.length && !subjectsLoading"
          class="select-members-list__items"
          :items="invitedUserSubjects"
          :attributes="[]"
        >
          <template #left-side="{ item }">
            <div class="select-members-list__user-initials margin-left-1">
              {{ item.name | nameAbbreviation }}
            </div>
            <span class="margin-left-1">
              {{ item.name }}
            </span>
          </template>
          <template #right-side="{ item }">
            <div class="margin-right-1">
              {{ item.email }}
              <a class="color-error" @click="$emit('remove-subject', item)"
                ><i class="fas fa-fw fa-trash"></i
              ></a>
            </div>
          </template>
        </List>
      </div>
    </div>
    <div class="row margin-top-2">
      <div class="col col-6">
        <a
          class="button button--ghost"
          :disabled="loading"
          @click="$emit('invite')"
          >{{ $t('manageTeamForm.inviteMembers') }}
        </a>
      </div>
      <div class="col col-6 align-right">
        <button
          :class="{ 'button--loading': loading }"
          class="button"
          :disabled="loading"
        >
          {{ $t('manageTeamForm.submit') }}
        </button>
      </div>
    </div>
  </form>
</template>

<script>
import { required, maxLength, minLength } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import { filterRoles } from '@baserow_enterprise/utils/roles'

export default {
  name: 'ManageTeamForm',
  mixins: [form],
  props: {
    group: {
      type: Object,
      required: true,
    },
    invitedUserSubjects: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    subjectsLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      values: {
        name: '',
        default_role: 'VIEWER',
        subjects: [],
      },
    }
  },
  computed: {
    roles() {
      return filterRoles(this.group._.roles, {
        scopeType: 'group',
        subjectType: 'baserow_enterprise.Team',
      })
    },
    defaultRole() {
      return this.roles.length > 0 ? this.roles[this.roles.length - 1] : null
    },
    hasMinMaxError() {
      return !this.$v.values.name.maxLength || !this.$v.values.name.minLength
    },
    atLeastOneBillableRole() {
      return this.roles.some((role) => role.isBillable)
    },
  },
  watch: {
    invitedUserSubjects(newValue) {
      this.values.subjects = []
      for (let s = 0; s < this.invitedUserSubjects.length; s++) {
        this.values.subjects.push({
          subject_id: this.invitedUserSubjects[s].user_id,
          subject_type: 'auth.User',
        })
      }
    },
  },
  validations: {
    values: {
      name: {
        required,
        minLength: minLength(2),
        maxLength: maxLength(160),
      },
    },
  },
  mounted() {
    this.$refs.name.focus()
  },
}
</script>
