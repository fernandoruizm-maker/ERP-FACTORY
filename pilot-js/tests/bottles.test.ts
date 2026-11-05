import test from 'node:test';
import assert from 'node:assert/strict';
import { Bottles } from '../src/bottles.mjs';
type Actor = { id: string; role: string; areas: string[] };
const worker: Actor = { id: 'trabajador-ts-ficticio', role: 'operador', areas: ['bodega'] };
const boss: Actor = { id: 'responsable-ts-ficticio', role: 'gerente', areas: ['bodega'] };
test('TypeScript: contrato de diez botellas', () => {
  const app = new Bottles(); app.request('TS1', 10, worker); app.approve('TS1', boss);
  assert.equal(app.dispatch('TS1', worker).balance, 0);
});
test('TypeScript: rechaza autoaprobación', () => {
  const app = new Bottles(); app.request('TS1', 10, boss);
  assert.throws(() => app.approve('TS1', boss));
});
test('TypeScript: no permite stock negativo ni cantidad fraccionaria', () => {
  const app = new Bottles();
  for (const quantity of [-1, 0, 11, 1.5]) assert.throws(() => app.request('TS1', quantity, worker));
  assert.equal(app.stock, 10);
});
