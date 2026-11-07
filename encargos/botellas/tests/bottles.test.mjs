import test from 'node:test';
import assert from 'node:assert/strict';
import { Bottles } from '../src/bottles.mjs';
const operator = { id: 'operador-ficticio', role: 'operador', areas: ['bodega'] };
const manager = { id: 'gerente-ficticio', role: 'gerente', areas: ['bodega'] };
test('diez botellas, saldo cero y respuesta repetida sin otra salida', () => {
  const app = new Bottles(); app.request('S1', 10, operator); app.approve('S1', manager);
  const first = app.dispatch('S1', operator);
  assert.equal(app.stock, 0); assert.deepEqual(app.dispatch('S1', operator), first);
});
test('no autoriza otra área', () => {
  const app = new Bottles(); app.request('S1', 10, operator);
  assert.throws(() => app.approve('S1', { ...manager, areas: ['ventas'] }));
  assert.equal(app.stock, 10);
});
test('sin aprobación no hay movimiento', () => {
  const app = new Bottles(); app.request('S1', 10, operator);
  assert.throws(() => app.dispatch('S1', operator)); assert.equal(app.stock, 10);
});
test('subgerente independiente puede aprobar', () => {
  const app = new Bottles(); app.request('S1', 2, operator);
  app.approve('S1', { ...manager, role: 'subgerente' }); assert.equal(app.dispatch('S1', operator).balance, 8);
});
test('revalida saldo entre dos solicitudes aprobadas', () => {
  const app = new Bottles(); for (const id of ['A', 'B']) {app.request(id, 6, operator); app.approve(id, manager);}
  app.dispatch('A', operator); assert.throws(() => app.dispatch('B', operator)); assert.equal(app.stock, 4);
});

test('un ID duplicado no reemplaza la solicitud original', () => {
  const app = new Bottles(); app.request('S1', 2, operator);
  assert.throws(() => app.request('S1', 9, operator));
  app.approve('S1', manager);
  assert.equal(app.dispatch('S1', operator).quantity, 2);
  assert.equal(app.stock, 8);
});

test('otra area no puede despachar ni recuperar un comprobante', () => {
  const app = new Bottles(); app.request('S1', 2, operator); app.approve('S1', manager);
  const outsider = { ...operator, areas: ['ventas'] };
  assert.throws(() => app.dispatch('S1', outsider)); assert.equal(app.stock, 10);
  const receipt = app.dispatch('S1', operator);
  assert.throws(() => app.dispatch('S1', outsider)); assert.equal(app.stock, 8);
  assert.deepEqual(app.dispatch('S1', operator), receipt);
});
