// Ejemplo ficticio independiente del ERP. Sin persistencia, red o credenciales.
export class Bottles {
  #stock = 10;
  #requests = new Map();
  get stock() { return this.#stock; }
  access(actor, roles) {
    if (!actor?.id || !roles.includes(actor.role) || !actor.areas?.includes('bodega'))
      throw new Error('Área o función no autorizada');
  }
  request(id, quantity, actor) {
    this.access(actor, ['operador', 'gerente', 'subgerente']);
    if (!id || this.#requests.has(id) || !Number.isInteger(quantity) || quantity <= 0 || quantity > this.#stock)
      throw new Error('Solicitud inválida');
    this.#requests.set(id, { quantity, requester: actor.id, approver: null, receipt: null });
  }
  approve(id, actor) {
    this.access(actor, ['gerente', 'subgerente']);
    const item = this.#requests.get(id);
    if (!item || item.requester === actor.id || item.approver) throw new Error('Aprobación inválida');
    item.approver = actor.id;
  }
  dispatch(id, actor) {
    this.access(actor, ['operador', 'gerente', 'subgerente']);
    const item = this.#requests.get(id);
    if (!item?.approver) throw new Error('Falta autorización');
    if (item.receipt) return { ...item.receipt };
    if (item.quantity > this.#stock) throw new Error('Stock insuficiente');
    this.#stock -= item.quantity;
    item.receipt = { id, quantity: item.quantity, balance: this.#stock, synthetic: true };
    return { ...item.receipt };
  }
}
