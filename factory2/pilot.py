"""Dominio ficticio del piloto. No conecta con el ERP ni produce documentos fiscales."""
from copy import deepcopy
from html import escape
import threading

from .core import digest


class PilotError(ValueError):
    pass


class BottlePilot:
    def __init__(self):
        self.stock = 10
        self._requests = {}
        self.movements = []
        self._lock = threading.RLock()

    @staticmethod
    def access(actor, area, roles):
        if (not isinstance(actor, dict) or not isinstance(actor.get("id"), str) or
                not actor["id"].strip() or actor.get("role") not in roles or
                not isinstance(actor.get("areas"), list) or area not in actor["areas"]):
            raise PilotError("Usuario o área no autorizado.")

    def request(self, rid, quantity, area, actor):
        with self._lock:
            self.access(actor, area, {"operador", "gerente", "subgerente"})
            if area != "bodega" or not isinstance(rid, str) or not rid.strip():
                raise PilotError("Solicitud o área fuera del piloto.")
            if type(quantity) is not int or not 1 <= quantity <= self.stock:
                raise PilotError("Cantidad inválida o superior al stock.")
            if rid in self._requests:
                raise PilotError("Identificador utilizado; no se sobrescribe la solicitud.")
            self._requests[rid] = {"id": rid, "quantity": quantity, "area": area,
                "requester": actor["id"], "approver": None, "status": "PENDING"}

    def _get(self, rid):
        if rid not in self._requests:
            raise PilotError("Solicitud inexistente.")
        return self._requests[rid]

    def approve(self, rid, actor):
        with self._lock:
            request = self._get(rid)
            self.access(actor, request["area"], {"gerente", "subgerente"})
            if actor["id"] == request["requester"]:
                raise PilotError("Quien solicita no puede aprobar su propia salida.")
            if request["status"] != "PENDING":
                raise PilotError("La solicitud ya fue resuelta.")
            request.update(approver=actor["id"], status="APPROVED")

    def dispatch(self, rid, actor):
        with self._lock:
            request = self._get(rid)
            self.access(actor, request["area"], {"operador", "gerente", "subgerente"})
            if request["status"] == "DISPATCHED":
                return deepcopy(next(m for m in self.movements if m["request"] == rid))
            if request["status"] != "APPROVED":
                raise PilotError("Falta aprobación independiente.")
            if self.stock < request["quantity"]:
                raise PilotError("Stock insuficiente al ejecutar; no se produce salida parcial.")
            self.stock -= request["quantity"]
            movement = {"receipt": f"ENSAYO-{len(self.movements)+1:04d}", "request": rid,
                        "quantity": request["quantity"], "balance": self.stock,
                        "area": request["area"], "approver": request["approver"], "synthetic": True}
            self.movements.append(movement)
            request["status"] = "DISPATCHED"
            return deepcopy(movement)

    def receipt_html(self, rid, actor):
        with self._lock:
            request = self._get(rid)
            self.access(actor, request["area"], {"operador", "gerente", "subgerente"})
            if request["status"] != "DISPATCHED":
                raise PilotError("Aún no hay salida registrada para imprimir.")
            m = next(m for m in self.movements if m["request"] == rid)
            return ("<!doctype html><html lang='es'><meta charset='utf-8'><title>Comprobante de ensayo</title>"
                    "<style>body{font:17px system-ui;max-width:760px;margin:48px auto;padding:24px}"
                    "td,th{text-align:left;padding:12px;border-bottom:1px solid #ccc}"
                    "@media print{body{margin:0}}</style><h1>Salida de botellas · ensayo</h1>"
                    "<p>DATOS FICTICIOS · SIN VALIDEZ FISCAL</p><table>"
                    + "".join(f"<tr><th>{escape(k)}</th><td>{escape(str(v))}</td></tr>" for k,v in {
                        "Comprobante":m["receipt"], "Solicitud":rid, "Área":m["area"],
                        "Botellas entregadas":m["quantity"], "Saldo":m["balance"],
                        "Autorización ficticia":m["approver"]}.items())
                    + "</table><p>Consultar o imprimir este documento no genera movimientos.</p></html>")

    def snapshot(self):
        with self._lock:
            body = {"stock": self.stock, "requests": deepcopy(self._requests), "movements": deepcopy(self.movements)}
            return {**body, "sha256": digest(body)}

    @classmethod
    def restore(cls, snapshot):
        body = {k:v for k,v in snapshot.items() if k != "sha256"}
        if digest(body) != snapshot.get("sha256") or set(body) != {"stock", "requests", "movements"}:
            raise PilotError("Estado de ensayo alterado o incompleto.")
        try:
            moves = body["movements"]
            if (type(body["stock"]) is not int or not 0 <= body["stock"] <= 10 or
                    body["stock"] != 10 - sum(m["quantity"] for m in moves) or
                    len({m["request"] for m in moves}) != len(moves) or
                    any(type(m["quantity"]) is not int or m["quantity"] <= 0 for m in moves)):
                raise PilotError("Estado incoherente.")
        except (TypeError, KeyError):
            raise PilotError("Estado incoherente.") from None
        result = cls()
        result.stock, result._requests, result.movements = deepcopy((body["stock"], body["requests"], moves))
        return result
