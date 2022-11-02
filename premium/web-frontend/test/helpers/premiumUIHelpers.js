/**
 * Various helper functions which interact with premium baserow components.
 */
export class PremiumUIHelpers {
  static sidebarShowsPremiumEnabled(sidebarComponent) {
    return sidebarComponent.find('.instance-wide-license').exists()
  }
}
