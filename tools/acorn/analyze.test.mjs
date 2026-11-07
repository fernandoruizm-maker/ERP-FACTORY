// Handwritten AST doubles. These tests do NOT load or exercise the Acorn package.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {importsFromAst} from './analyze.mjs';
const literal = value => ({type: 'Literal', value});
const id = name => ({type: 'Identifier', name});
const call = argument => ({type: 'CallExpression', callee: id('require'), arguments: [argument]});

test('static imports and reexports use literal decoded module names', () => {
  for (const type of ['ImportDeclaration', 'ExportAllDeclaration', 'ExportNamedDeclaration']) {
    assert.deepEqual(importsFromAst({type, source: literal('zod')}), ['zod']);
  }
});
test('literal require and import expressions are inventoried', () => {
  assert.deepEqual(importsFromAst(call(literal('node:fs'))), ['node:fs']);
  assert.deepEqual(importsFromAst({type: 'ImportExpression', source: literal('zod')}), ['zod']);
});
test('dynamic import and require names block', () => {
  assert.throws(() => importsFromAst(call(id('name'))), /BLOCKED/);
  assert.throws(() => importsFromAst({type: 'ImportExpression', source: id('name')}), /BLOCKED/);
});
test('aliases and member require block', () => {
  assert.throws(() => importsFromAst({type: 'VariableDeclarator', init: id('require')}), /BLOCKED/);
  assert.throws(() => importsFromAst({type: 'MemberExpression', property: id('require')}), /BLOCKED/);
});
test('computed members and known alternative loaders block', () => {
  assert.throws(() => importsFromAst({type: 'MemberExpression', computed: true, property: literal('require')}), /BLOCKED/);
  for (const name of ['eval', 'Function', 'createRequire', '_load']) {
    assert.throws(() => importsFromAst(id(name)), /BLOCKED/);
  }
});
test('meta imports and import options block', () => {
  assert.throws(() => importsFromAst({type: 'MetaProperty'}), /BLOCKED/);
  assert.throws(() => importsFromAst({type: 'ImportExpression', source: literal('zod'), options: {}}), /BLOCKED/);
});
test('invalid module literals block', () => {
  for (const value of ['', null, 9, 'a'.repeat(1001)]) {
    assert.throws(() => importsFromAst(call(literal(value))), /BLOCKED/);
  }
});
test('division and regex AST nodes do not hide nested imports', () => {
  const ast = {type: 'Program', body: [{type: 'Literal', regex: {pattern: "'"}},
    {type: 'BinaryExpression', operator: '/', left: literal(10), right: literal(2)},
    {type: 'ImportDeclaration', source: literal('unapproved')}]};
  assert.deepEqual(importsFromAst(ast), ['unapproved']);
});
test('oversize AST fails closed', () => {
  assert.throws(() => importsFromAst({type: 'Program', body: Array.from({length: 100001}, () => literal(1))}), /BLOCKED/);
});
