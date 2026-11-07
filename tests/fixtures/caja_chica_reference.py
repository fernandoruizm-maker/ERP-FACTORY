"""Fixed fictional test double; proposed by Codex, pending human review, not a deliverable."""


class CajaChica:
    def __init__(self, limite_diario_centavos, responsable_id):
        self.limite, self.responsable = limite_diario_centavos, responsable_id
        self.solicitudes, self.pagos = {}, {}

    def solicitar(self, ident, persona, dia, monto):
        if ident in self.solicitudes or type(monto) is not int or monto <= 0:
            raise ValueError('Solicitud ficticia invalida')
        self.solicitudes[ident] = {'id': ident, 'persona': persona, 'dia': dia, 'monto_centavos': monto}

    def aprobar(self, ident, responsable):
        item = self.solicitudes[ident]
        if responsable != self.responsable or responsable == item['persona']:
            raise ValueError('Aprobador ficticio invalido')
        item['aprobador'] = responsable

    def consumo(self, persona, dia):
        return sum(p['monto_centavos'] for p in self.pagos.values() if p['persona'] == persona and p['dia'] == dia)

    def pagar(self, ident):
        if ident in self.pagos:
            return dict(self.pagos[ident])
        item = self.solicitudes[ident]
        if ('aprobador' not in item or self.consumo(item['persona'], item['dia']) + item['monto_centavos'] > self.limite):
            raise ValueError('Pago ficticio bloqueado')
        self.pagos[ident] = dict(item)
        return dict(item)
