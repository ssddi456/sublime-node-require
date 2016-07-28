
export * from "OK";

export var z = 3;
export default 5;
export const y = 1;
export let {a, b, c: {d, e: {f = 4}}} = { c : { e : { f : 3 }}};
export function inc() {
  i++;
}
export class foo8 {}
export { a as x, c as w } from "hello"
