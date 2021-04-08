/**
 * This error can be raised when trying to find an item within a store that doesn't
 * exist. For example when a certain application is expected in a store, but can't
 * be found.
 */
export class StoreItemLookupError extends Error {}

/**
 * This error can be raised when a view receives multiple refresh events and wishes to
 * cancel the older ones which could still be running some async slow query. It
 * indicates to the top level refresh event handler that it should abort this particular
 * refresh event but keep the "refreshing" state in progress as a new refresh event is
 * still being processed.
 */
export class RefreshCancelledError extends Error {}
