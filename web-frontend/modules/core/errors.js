/**
 * This error can be raised when trying to find an item within a store that doesn't
 * exist. For example when a certain application is expected in a store, but can't
 * be found.
 */
export class StoreItemLookupError extends Error {}
