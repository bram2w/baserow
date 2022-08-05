/**
 * This decorator helps to group multiple function calls into one during the
 * given graceDelay.
 * It's a little bit like a debounce but all the arguments are stacked and given to the
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
 * const getName = groupCalls(async (argList) => {
 *   const result = await (
 *     await fetch('some/url', doSomethingWithArgList(argList))
 *   ).json()
 *   return (id)=>{
 *     return result[id]
 *   }
 * }, 50)
 *
 * // Somewhere in the code
 * const name = await getName(42)
 * // Somewhere else
 * const name = await getName(4)
 *
 * ```
 *
 * If the two calls are triggered whithin the 50ms the `groupCalls` callback
 * function will be called with `[42, 4]`.
 *
 * @param {function} callback the function called after the grace delay which receive an
 *   array of arguments and must return a function that return the original result for
 *   the provided args
 * @param {int} graceDelay the grace delay in ms before the provide function is called
 * @returns A function you can call with your arguments.
 */
export const groupCalls = (callback, graceDelay) => {
  let argsList, delay, currentResolve, currentPromise

  const init = () => {
    argsList = []
    delay = null
    currentResolve = null
    currentPromise = null
  }
  init()

  return async (...args) => {
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
