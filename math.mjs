const constants = new Map([
  ['pi', Math.PI], ['π', Math.PI], ['e', Math.E], ['tau', 2 * Math.PI], ['τ', 2 * Math.PI]
]);
const variables = new Set(['x', 'a', 'b', 'c', 'd', 'ans']);
const juxtaposedNames = /^(?:ans|tau|pi|[xab cde])+$/x;
