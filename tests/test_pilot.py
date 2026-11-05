import unittest
from factory2.pilot import BottlePilot, PilotError


class BottleTests(unittest.TestCase):
    def setUp(self):
        self.pilot = BottlePilot()
        self.worker = {"id": "operador-ficticio", "role": "operador", "areas": ["bodega"]}
        self.manager = {"id": "gerente-ficticio", "role": "gerente", "areas": ["bodega"]}

    def test_ten_bottles_receipt_and_idempotent_dispatch(self):
        self.pilot.request("SAL-1", 10, "bodega", self.worker)
        self.pilot.approve("SAL-1", self.manager)
        first = self.pilot.dispatch("SAL-1", self.worker)
        second = self.pilot.dispatch("SAL-1", self.worker)
        self.assertEqual(self.pilot.stock, 0)
        self.assertEqual(first, second)
        self.assertEqual(first["quantity"], 10)
        self.assertEqual(len(self.pilot.movements), 1)
        before = self.pilot.snapshot()
        self.assertIn("SIN VALIDEZ FISCAL", self.pilot.receipt_html("SAL-1", self.worker))
        self.assertEqual(before, self.pilot.snapshot())

    def test_submanager_can_approve(self):
        self.pilot.request("SAL-1", 1, "bodega", self.worker)
        self.pilot.approve("SAL-1", {**self.manager, "role": "subgerente"})
        self.assertEqual(self.pilot.dispatch("SAL-1", self.worker)["balance"], 9)

    def test_wrong_area_cannot_approve_dispatch_or_print(self):
        self.pilot.request("SAL-1", 1, "bodega", self.worker)
        outsider = {**self.manager, "areas": ["ventas"]}
        with self.assertRaises(PilotError): self.pilot.approve("SAL-1", outsider)
        self.pilot.approve("SAL-1", self.manager)
        with self.assertRaises(PilotError): self.pilot.dispatch("SAL-1", outsider)
        self.pilot.dispatch("SAL-1", self.worker)
        with self.assertRaises(PilotError): self.pilot.receipt_html("SAL-1", outsider)

    def test_self_approval_and_unapproved_dispatch_denied(self):
        self.pilot.request("SAL-1", 10, "bodega", self.manager)
        with self.assertRaises(PilotError): self.pilot.approve("SAL-1", self.manager)
        with self.assertRaises(PilotError): self.pilot.dispatch("SAL-1", self.worker)
        self.assertEqual(self.pilot.stock, 10)

    def test_stock_rechecked_after_other_dispatch(self):
        for rid in ("SAL-1", "SAL-2"):
            self.pilot.request(rid, 6, "bodega", self.worker)
            self.pilot.approve(rid, self.manager)
        self.pilot.dispatch("SAL-1", self.worker)
        with self.assertRaises(PilotError): self.pilot.dispatch("SAL-2", self.worker)
        self.assertEqual(self.pilot.stock, 4)

    def test_invalid_quantities_and_duplicate_requests(self):
        for q in (0, -1, 11, True, 1.5, "10"):
            with self.assertRaises(PilotError): self.pilot.request("BAD", q, "bodega", self.worker)
        self.pilot.request("SAL-1", 1, "bodega", self.worker)
        with self.assertRaises(PilotError): self.pilot.request("SAL-1", 2, "bodega", self.worker)

    def test_snapshot_recovery_preserves_dispatch_identity(self):
        self.pilot.request("SAL-1", 10, "bodega", self.worker)
        self.pilot.approve("SAL-1", self.manager)
        receipt = self.pilot.dispatch("SAL-1", self.worker)
        restored = BottlePilot.restore(self.pilot.snapshot())
        self.assertEqual(restored.dispatch("SAL-1", self.worker), receipt)
        self.assertEqual(restored.stock, 0)
        damaged = self.pilot.snapshot()
        damaged["stock"] = 99
        with self.assertRaises(PilotError): BottlePilot.restore(damaged)


if __name__ == "__main__": unittest.main()
