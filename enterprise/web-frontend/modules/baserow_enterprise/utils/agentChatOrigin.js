/**
 * How a conversation was started, as the key the conversation list filters
 * on (the backend's `origin` query parameter): `manual`, `service`,
 * `trigger:<trigger type>` or `channel:<channel type>`.
 */
export function getChatOrigin(chat) {
  if (chat.source === 'trigger') {
    return `trigger:${chat.trigger_type || ''}`
  }
  if (chat.source === 'channel') {
    return `channel:${chat.channel_type || ''}`
  }
  if (chat.source === 'service') {
    return 'service'
  }
  // Conversations from the old setup assistant were started by hand too.
  return 'manual'
}

// Not an origin of a conversation but a filter next to them: the ones the
// current user started.
export const ORIGIN_MINE = 'mine'

/**
 * Whether a conversation belongs in the list filtered on `origin`.
 */
export function chatMatchesOrigin(chat, origin, userId) {
  if (origin === null) {
    return true
  }
  if (origin === ORIGIN_MINE) {
    return chat.user_id !== null && chat.user_id === userId
  }
  return getChatOrigin(chat) === origin
}

const TRIGGER_ICONS = {
  periodic: 'iconoir-timer',
  http_trigger: 'iconoir-globe',
  email_trigger: 'iconoir-mail',
  row_comment_created: 'iconoir-chat-bubble-empty',
}

/**
 * The node type of an agent trigger type; table triggers are registered as
 * their `local_baserow_` service.
 */
export function getTriggerNodeType(registry, triggerType) {
  for (const candidate of [triggerType, `local_baserow_${triggerType}`]) {
    try {
      return registry.get('node', candidate)
    } catch {
      // Not a node type; try the next candidate.
    }
  }
  return null
}

/**
 * The label and icon (or image) that show where a conversation came from.
 */
export function describeChatOrigin(origin, { registry, t }) {
  if (origin === ORIGIN_MINE) {
    return {
      label: t('agentChatOrigin.mine'),
      icon: 'iconoir-profile-circle',
      image: '',
    }
  }
  const [kind, type = ''] = origin.split(':')
  if (kind === 'trigger') {
    const nodeType = getTriggerNodeType(registry, type)
    return {
      label: nodeType?.name || t('agentChatOrigin.trigger'),
      icon: TRIGGER_ICONS[type] || nodeType?.iconClass || 'iconoir-flash',
      image: '',
    }
  }
  if (kind === 'channel') {
    let channelType = null
    try {
      channelType = registry.get('agentChatChannel', type)
    } catch {
      // A channel type that is no longer available.
    }
    return {
      label: channelType?.name || t('agentChatOrigin.channel'),
      icon: channelType?.icon || 'iconoir-chat-bubble',
      image: channelType?.image || '',
    }
  }
  if (kind === 'service') {
    return {
      label: t('agentChatOrigin.service'),
      icon: 'iconoir-play',
      image: '',
    }
  }
  return {
    label: t('agentChatOrigin.manual'),
    icon: 'iconoir-user',
    image: '',
  }
}
