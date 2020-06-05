import Vue from 'vue'

import Context from '@baserow/modules/core/components/Context'
import Modal from '@baserow/modules/core/components/Modal'
import Editable from '@baserow/modules/core/components/Editable'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Scrollbars from '@baserow/modules/core/components/Scrollbars'
import Error from '@baserow/modules/core/components/Error'

import lowercase from '@baserow/modules/core/filters/lowercase'

import scroll from '@baserow/modules/core/directives/scroll'
import preventParentScroll from '@baserow/modules/core/directives/preventParentScroll'

Vue.component('Context', Context)
Vue.component('Modal', Modal)
Vue.component('Editable', Editable)
Vue.component('Dropdown', Dropdown)
Vue.component('DropdownItem', DropdownItem)
Vue.component('Checkbox', Checkbox)
Vue.component('Scrollbars', Scrollbars)
Vue.component('Error', Error)

Vue.filter('lowercase', lowercase)

Vue.directive('scroll', scroll)
Vue.directive('preventParentScroll', preventParentScroll)
