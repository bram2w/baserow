<template>
  <div>
    <ThemeConfigBlockSection>
      <template #default>
        <FormGroup horizontal :label="$t('imageThemeConfigBlock.alignment')">
          <div class="flex">
            <HorizontalAlignmentsSelector
              v-model="values.image_alignment"
              class="flex-grow-1"
            />
            <ResetButton
              v-model="values"
              :theme="theme"
              property="image_alignment"
            />
          </div>
        </FormGroup>
        <FormGroup
          horizontal
          :label="$t('imageThemeConfigBlock.maxWidthLabel')"
          :error="
            $v.values.image_max_width.$dirty &&
            !$v.values.image_max_width.integer
              ? $t('error.integerField')
              : !$v.values.image_max_width.minValue
              ? $t('error.minValueField', { min: 0 })
              : !$v.values.image_max_width.maxValue
              ? $t('error.maxValueField', { max: 100 })
              : ''
          "
        >
          <div class="flex">
            <FormInput
              v-model="values.image_max_width"
              class="flex-grow-1"
              no-control
              small
              type="number"
              icon-right="iconoir-percentage"
              :placeholder="$t('imageThemeConfigBlock.maxWidthPlaceholder')"
              :to-value="(value) => (value ? parseInt(value) : null)"
            ></FormInput>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="image_max_width"
            />
          </div>
        </FormGroup>
        <FormGroup
          horizontal
          :label="$t('imageThemeConfigBlock.maxHeightLabel')"
          :error="
            $v.values.image_max_height.$dirty &&
            !$v.values.image_max_height.integer
              ? $t('error.integerField')
              : !$v.values.image_max_height.minValue
              ? $t('error.minValueField', { min: 5 })
              : !$v.values.image_max_height.maxValue
              ? $t('error.maxValueField', { max: 3000 })
              : ''
          "
        >
          <div class="flex">
            <FormInput
              v-model="imageMaxHeight"
              class="flex-grow-1"
              no-control
              small
              type="number"
              iicon-right="iconoir-ruler-combine"
              :placeholder="$t('imageThemeConfigBlock.maxHeightPlaceholder')"
              :to-value="(value) => (value ? parseInt(value) : null)"
            >
              <template #suffix>
                <i>px</i>
              </template>
            </FormInput>
            <ResetButton
              v-model="imageMaxHeightForReset"
              :theme="theme"
              property="image_max_height"
            />
          </div>
        </FormGroup>
        <FormGroup
          horizontal
          :label="$t('imageThemeConfigBlock.imageConstraintsLabel')"
        >
          <div class="flex">
            <Dropdown
              v-model="values.image_constraint"
              small
              fixed-items
              :show-search="true"
              class="flex-grow-1"
            >
              <DropdownItem
                v-for="{ name, label } in imageConstraintChoices"
                :key="name"
                :disabled="constraintDisabled(name)"
                :description="
                  constraintDisabled(name)
                    ? $t(
                        `imageThemeConfigBlock.imageConstraint${label}Disabled`
                      )
                    : ''
                "
                :name="label"
                :value="name"
              >
              </DropdownItem>
            </Dropdown>
            <ResetButton
              v-model="imageConstraintForReset"
              :theme="theme"
              property="image_constraint"
            />
          </div>
        </FormGroup>
      </template>
      <template #preview>
        <ABImage src="/img/favicon_192.png" />
      </template>
    </ThemeConfigBlockSection>
  </div>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import ResetButton from '@baserow/modules/builder/components/theme/ResetButton'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/HorizontalAlignmentsSelector'
import { IMAGE_SOURCE_TYPES } from '@baserow/modules/builder/enums'
import { integer, maxValue, minValue } from 'vuelidate/lib/validators'

export default {
  name: 'ImageThemeConfigBlock',
  components: {
    ThemeConfigBlockSection,
    ResetButton,
    HorizontalAlignmentsSelector,
  },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: [
        'image_alignment',
        'image_max_width',
        'image_max_height',
        'image_constraint',
      ],
    }
  },
  computed: {
    imageMaxHeight: {
      get() {
        return this.values.image_max_height
      },
      set(newValue) {
        // If the `image_max_height` is emptied, and the
        // constraint is 'cover', then reset back to 'contain'.
        if (!newValue && this.values.image_constraint === 'cover') {
          this.values.image_constraint = 'contain'
        }
        // If the `image_max_height` is set, and the
        // constraint is 'contain', then reset back to 'cover'.
        if (newValue && this.values.image_constraint === 'contain') {
          this.values.image_constraint = 'cover'
        }
        this.values.image_max_height = newValue
      },
    },
    imageMaxHeightForReset: {
      get() {
        return { image_max_height: this.imageMaxHeight }
      },
      set(value) {
        this.imageMaxHeight = value.imageMaxHeight
      },
    },
    imageConstraintForReset: {
      get() {
        return { image_constraint: this.values.image_constraint }
      },
      set(value) {
        if (value.image_constraint === 'contain') {
          // Reset the height as we can't have a max height with contain
          this.values.image_max_height = null
        }
        if (value.image_constraint === 'cover') {
          // Set the height to what is defined in theme
          this.values.image_max_height = this.theme.image_max_height
        }
        this.values.image_constraint = value.image_constraint
      },
    },
    IMAGE_SOURCE_TYPES() {
      return IMAGE_SOURCE_TYPES
    },
    imageConstraintChoices() {
      return [
        {
          name: 'contain',
          label: this.$t('imageThemeConfigBlock.imageConstraintContain'),
        },
        {
          name: 'cover',
          label: this.$t('imageThemeConfigBlock.imageConstraintCover'),
        },
        {
          name: 'full-width',
          label: this.$t('imageThemeConfigBlock.imageConstraintFullWidth'),
        },
      ]
    },
  },
  methods: {
    constraintDisabled(name) {
      if (name === 'cover') {
        return !this.values.image_max_height
      } else if (name === 'contain') {
        return !!(
          this.values.image_max_height && this.values.image_max_height > 0
        )
      }
    },
  },
  validations: {
    values: {
      image_max_width: {
        integer,
        minValue: minValue(0),
        maxValue: maxValue(100),
      },
      image_max_height: {
        integer,
        minValue: minValue(5),
        maxValue: maxValue(3000),
      },
    },
  },
}
</script>
