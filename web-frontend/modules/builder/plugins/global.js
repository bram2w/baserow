import Vue from 'vue'

import ABButton from '@baserow/modules/builder/components/elements/baseComponents/ABButton'
import ABInput from '@baserow/modules/builder/components/elements/baseComponents/ABInput'
import ABFormGroup from '@baserow/modules/builder/components/elements/baseComponents/ABFormGroup'
import ABLink from '@baserow/modules/builder/components/elements/baseComponents/ABLink'
import ABHeading from '@baserow/modules/builder/components/elements/baseComponents/ABHeading'
import ABDropdown from '@baserow/modules/builder/components/elements/baseComponents/ABDropdown'
import ABDropdownItem from '@baserow/modules/builder/components/elements/baseComponents/ABDropdownItem'
import ABCheckbox from '@baserow/modules/builder/components/elements/baseComponents/ABCheckbox.vue'
import ABRadio from '@baserow/modules/builder/components/elements/baseComponents/ABRadio.vue'
import ABImage from '@baserow/modules/builder/components/elements/baseComponents/ABImage.vue'
import ABParagraph from '@baserow/modules/builder/components/elements/baseComponents/ABParagraph.vue'
import ABTag from '@baserow/modules/builder/components/elements/baseComponents/ABTag.vue'
import ABTable from '@baserow/modules/builder/components/elements/baseComponents/ABTable.vue'

function setupVueForAB(Vue) {
  Vue.component('ABButton', ABButton)
  Vue.component('ABInput', ABInput)
  Vue.component('ABFormGroup', ABFormGroup)
  Vue.component('ABLink', ABLink)
  Vue.component('ABHeading', ABHeading)
  Vue.component('ABDropdown', ABDropdown)
  Vue.component('ABDropdownItem', ABDropdownItem)
  Vue.component('ABCheckbox', ABCheckbox)
  Vue.component('ABRadio', ABRadio)
  Vue.component('ABImage', ABImage)
  Vue.component('ABParagraph', ABParagraph)
  Vue.component('ABTag', ABTag)
  Vue.component('ABTable', ABTable)
}

setupVueForAB(Vue)

export { setupVueForAB }
