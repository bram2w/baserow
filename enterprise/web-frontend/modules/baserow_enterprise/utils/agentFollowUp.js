import moment from '@baserow/modules/core/moment'

export const ACTIVE_FOLLOW_UP_STATUS = 'active'

/**
 * When the checks of a follow-up run, in words: "Every hour", "When row 12 in
 * Issues changes".
 */
export function describeWatch(watch, t) {
  if (!watch?.type) {
    return ''
  }
  if (watch.type === 'schedule') {
    return t(`agentFollowUps.every_${watch.every}`)
  }
  const rowIds = watch.row_ids || []
  return t(`agentFollowUps.watch_${watch.type}`, {
    table: watch.table_name || '',
    rows: rowIds.join(', '),
    count: rowIds.length,
  })
}

/**
 * The details of a follow-up, or of a proposed one, as key-value rows: what
 * it is for, when it checks, what it looks at and who hears about it.
 */
export function followUpFields(followUp, t, { notify = '' } = {}) {
  const fields = [
    { key: t('agentFollowUps.goal'), value: followUp.goal },
    { key: t('agentFollowUps.when'), value: describeWatch(followUp.watch, t) },
    {
      key: t('agentFollowUps.check'),
      value: followUp.check_instructions,
    },
    { key: t('agentFollowUps.doneWhen'), value: followUp.done_when },
    { key: t('agentFollowUps.state'), value: followUp.state },
  ]
  if (followUp.watch?.table_name) {
    fields.splice(2, 0, {
      key: t('agentFollowUps.table'),
      value: followUp.watch.table_name,
      kind: 'table',
    })
  }
  const notified = notify || followUp.created_by?.name
  if (notified) {
    fields.push({
      key: t('agentFollowUps.notifies'),
      value: notified,
      kind: 'member',
    })
  }
  if ('expires_on' in followUp) {
    fields.push({
      key: t('agentFollowUps.until'),
      value: followUp.expires_on
        ? moment(followUp.expires_on).format('LL')
        : t('agentFollowUps.noEndDate'),
    })
  }
  return fields.filter((field) => field.value)
}
