import Vue from 'vue'

import Context from '@baserow/modules/core/components/Context'
import Modal from '@baserow/modules/core/components/Modal'
import Editable from '@baserow/modules/core/components/Editable'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Radio from '@baserow/modules/core/components/Radio'
import Scrollbars from '@baserow/modules/core/components/Scrollbars'
import Error from '@baserow/modules/core/components/Error'
import SwitchInput from '@baserow/modules/core/components/SwitchInput'
import Copied from '@baserow/modules/core/components/Copied'

import lowercase from '@baserow/modules/core/filters/lowercase'
import uppercase from '@baserow/modules/core/filters/uppercase'
import formatBytes from '@baserow/modules/core/filters/formatBytes'
import nameAbbreviation from '@baserow/modules/core/filters/nameAbbreviation'

import scroll from '@baserow/modules/core/directives/scroll'
import preventParentScroll from '@baserow/modules/core/directives/preventParentScroll'
import tooltip from '@baserow/modules/core/directives/tooltip'
import sortable from '@baserow/modules/core/directives/sortable'
import autoOverflowScroll from '@baserow/modules/core/directives/autoOverflowScroll'
import userFileUpload from '@baserow/modules/core/directives/userFileUpload'

Vue.component('Context', Context)
Vue.component('Modal', Modal)
Vue.component('Editable', Editable)
Vue.component('Dropdown', Dropdown)
Vue.component('DropdownItem', DropdownItem)
Vue.component('Checkbox', Checkbox)
Vue.component('Radio', Radio)
Vue.component('Scrollbars', Scrollbars)
Vue.component('Error', Error)
Vue.component('SwitchInput', SwitchInput)
Vue.component('Copied', Copied)

Vue.filter('lowercase', lowercase)
Vue.filter('uppercase', uppercase)
Vue.filter('formatBytes', formatBytes)
Vue.filter('nameAbbreviation', nameAbbreviation)

Vue.directive('scroll', scroll)
Vue.directive('preventParentScroll', preventParentScroll)
Vue.directive('tooltip', tooltip)
Vue.directive('sortable', sortable)
Vue.directive('autoOverflowScroll', autoOverflowScroll)
Vue.directive('userFileUpload', userFileUpload)
