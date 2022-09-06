/**
 * This helper groups multiple function calls into one during the given graceDelay.
 * It's similar to a debounce but all the arguments are stacked and given to the
 * callback function a the end of the delay.
 * It's useful, for example, if you want to group many calls of a
 * function that query the server into one to have only one server call.
 * The callback function receives the array of args of all calls during the grace
 * time and must return a function that return the right value given the originally
 * specified args.
 *
 * Example:
 *
 * ```js
 * const groupGetNameCalls = callGrouper(50)
 *
 * const getName = groupGetNameCalls(async (argList) => {
 *   const result = await (
 *     await fetch('some/url', doSomethingWithArgList(argList))
 *   ).json()
 *   return (id) => {
 *     return result[id]
 *   }
 * })
 *
 * // Somewhere in the code
 * const name = await getName(42)
 * // Somewhere else
 * const name = await getName(4)
 *
 * ```
 *
 * If the two calls are triggered within the 50ms the `groupCalls` callback
 * function will be called with `[42, 4]`.
 *
 * @param {int} graceDelay the grace delay in ms during which the calls are grouped
 * @returns A function you can call with a callback to create the final function that
 *  behave like the original function. The callback will receive an array of all the
 *  arguments and must return a function that returns the original result given the
 *  provided args.
 */
export const callGrouper = (graceDelay) => {
  let argsList, delay, currentResolve, currentPromise

  const init = () => {
    argsList = []
    delay = null
    currentResolve = null
    currentPromise = null
  }
  init()

  return (callback) =>
    async (...args) => {
      clearTimeout(delay)

      argsList.push(args)

      if (currentPromise === null) {
        currentPromise = new Promise((resolve) => (currentResolve = resolve))
      }

      delay = setTimeout(async () => {
        currentResolve(await callback(argsList))
        init()
      }, graceDelay)

      return (await currentPromise)(...args)
    }
}
