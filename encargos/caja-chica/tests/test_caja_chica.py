"""Fixed fictional acceptance contract; the trial builder cannot edit this file."""
import unittest
from src.caja_chica import CajaChica


class CajaChicaTests(unittest.TestCase):
    def setUp(self):
        self.caja = CajaChica(limite_diario_centavos=10000, responsable_id='responsable-ficticio')
        self.dia = '2026-01-15'

    def solicitud(self, ident='A', monto=4000, persona='persona-ficticia', dia=None):
        self.caja.solicitar(ident, persona, dia or self.dia, monto)

    def aprobado(self, ident='A', monto=4000, persona='persona-ficticia', dia=None):
        self.solicitud(ident, monto, persona, dia)
        self.caja.aprobar(ident, 'responsable-ficticio')

    def test_comprobante_y_pago_idempotente(self):
        self.aprobado()
        recibo = self.caja.pagar('A')
        self.assertEqual(recibo, {'id':'A', 'persona':'persona-ficticia', 'dia':self.dia,
                                 'monto_centavos':4000, 'aprobador':'responsable-ficticio'})
        self.assertEqual(self.caja.pagar('A'), recibo)
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 4000)

    def test_sin_aprobacion_no_paga(self):
        self.solicitud()
        with self.assertRaises(ValueError): self.caja.pagar('A')
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 0)

    def test_solo_responsable(self):
        self.solicitud()
        with self.assertRaises(ValueError): self.caja.aprobar('A', 'intruso-ficticio')
        with self.assertRaises(ValueError): self.caja.pagar('A')

    def test_sin_autoaprobacion(self):
        self.solicitud(persona='responsable-ficticio')
        with self.assertRaises(ValueError): self.caja.aprobar('A', 'responsable-ficticio')
        with self.assertRaises(ValueError): self.caja.pagar('A')

    def test_revalida_tope_al_pagar(self):
        self.aprobado('A', 6000)
        self.aprobado('B', 6000)
        self.caja.pagar('A')
        with self.assertRaises(ValueError): self.caja.pagar('B')
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 6000)
        self.aprobado('C', 4000)
        self.caja.pagar('C')
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 10000)

    def test_tope_separado_por_persona_y_dia(self):
        self.aprobado('A', 10000)
        self.aprobado('B', 10000, persona='otra-persona-ficticia')
        self.aprobado('C', 10000, dia='2026-01-16')
        for ident in ('A', 'B', 'C'): self.caja.pagar(ident)
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 10000)
        self.assertEqual(self.caja.consumo('otra-persona-ficticia', self.dia), 10000)
        self.assertEqual(self.caja.consumo('persona-ficticia', '2026-01-16'), 10000)

    def test_importes_invalidos(self):
        for i, monto in enumerate((0, -1, 1.5, True, '100')):
            with self.subTest(monto=monto), self.assertRaises(ValueError):
                self.solicitud(str(i), monto)
        self.assertEqual(self.caja.consumo('persona-ficticia', self.dia), 0)

    def test_id_duplicado_no_sustituye_solicitud(self):
        self.solicitud()
        with self.assertRaises(ValueError): self.solicitud(monto=1)
        self.caja.aprobar('A', 'responsable-ficticio')
        self.assertEqual(self.caja.pagar('A')['monto_centavos'], 4000)
