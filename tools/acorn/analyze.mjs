// Traverses an Acorn AST, never evaluates candidate code. Not a security sandbox.
export function importsFromAst(tree) {
  const imports = [];
  const pending = [[tree, null, null]];
  let count = 0;
  function literal(node) {
    if (!node || node.type !== 'Literal' || typeof node.value !== 'string' ||
        !node.value || node.value.length > 1000) throw new Error('BLOCKED');
    imports.push(node.value);
  }
  while (pending.length) {
    const [node, parent, key] = pending.pop();
    if (!node || typeof node !== 'object') continue;
    if (++count > 100000) throw new Error('BLOCKED');
    if (node.type === 'ImportDeclaration' || node.type === 'ExportAllDeclaration' ||
        (node.type === 'ExportNamedDeclaration' && node.source)) literal(node.source);
    if (node.type === 'ImportExpression') {
      if (node.options) throw new Error('BLOCKED');
      literal(node.source);
    }
    if (node.type === 'MetaProperty') throw new Error('BLOCKED');
    if (node.type === 'Identifier') {
      if (['eval', 'Function', 'createRequire', '_load'].includes(node.name)) throw new Error('BLOCKED');
      if (node.name === 'require') {
        if (!parent || parent.type !== 'CallExpression' || key !== 'callee' ||
            parent.optional || parent.arguments.length !== 1) throw new Error('BLOCKED');
        literal(parent.arguments[0]);
      }
    }
    if (node.type === 'MemberExpression' && node.computed) throw new Error('BLOCKED');
    for (const [childKey, child] of Object.entries(node)) {
      if (Array.isArray(child)) for (const item of child) pending.push([item, node, childKey]);
      else if (child && typeof child === 'object') pending.push([child, node, childKey]);
    }
  }
  return imports;
}
