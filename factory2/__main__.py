"""Comandos locales. No existe comando de activar, publicar ni conectar al ERP."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from .core import Blocked, digest, file_digest
from .pilot import BottlePilot
from .runner import assess, bounded_process
from .state import Store
from .workflow import markdown_report, prepare, report

ROOT = Path(__file__).resolve().parent.parent


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def status():
    cfg = load(ROOT / "config.json")
    if any(cfg.get(k) is not False for k in ("enabled", "external_calls_enabled", "erp_access_enabled", "publication_enabled")):
        raise Blocked("Esta versión solo admite preparación local desactivada. Revisar configuración.")
    return {"installation": cfg["installation"], "enabled": False, "network_calls": False,
            "builder": "codex: adaptador preparado, llamada real pendiente",
            "reviewer": "claude: adaptador preparado, llamada real pendiente",
            "state": Store(ROOT / "state" / "factory2.sqlite3").summary(),
            "original_factory": "No gestionada desde esta instalación"}


def pilot():
    status()
    node = shutil.which("node")
    if not node:
        raise Blocked("Node no disponible. No se instala automáticamente.")
    artifact = {str(p.relative_to(ROOT)).replace("\\", "/"): file_digest(p)
                for directory in ("factory2", "tests", "pilot-js")
                for p in sorted((ROOT / directory).rglob("*"))
                if p.is_file() and p.suffix in (".py", ".mjs", ".ts")}
    worker = {"id": "operador-ficticio", "role": "operador", "areas": ["bodega"]}
    boss = {"id": "gerente-ficticio", "role": "gerente", "areas": ["bodega"]}
    app = BottlePilot()
    app.request("SAL-FICTICIA-001", 10, "bodega", worker)
    app.approve("SAL-FICTICIA-001", boss)
    first = app.dispatch("SAL-FICTICIA-001", worker)
    again = app.dispatch("SAL-FICTICIA-001", worker)
    recovered = BottlePilot.restore(app.snapshot())
    results = []
    commands = [
        ("python", [sys.executable, "-B", "-m", "unittest", "tests.test_pilot", "-v"]),
        ("javascript", [node, "--test", "--test-reporter=tap", "pilot-js/tests/bottles.test.mjs"]),
        ("typescript", [node, "--experimental-strip-types", "--test", "--test-reporter=tap", "pilot-js/tests/bottles.test.ts"])]
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    for profile, command in commands:
        code, log = bounded_process(command, cwd=ROOT)
        result = {**assess(profile, code, log), "profile": profile,
                  "artifact_digest": digest(artifact), "execution": "local trusted synthetic fixture"}
        results.append(result)
        (output / f"test-{profile}.txt").write_text(log, encoding="utf-8")
    data = report(prepare(load(ROOT / "fixtures" / "cliente.json")), results, artifact_digest=digest(artifact))
    data["pilot"] = {"initial_stock": 10, "final_stock": app.stock, "movements": len(app.movements),
                      "same_receipt_on_retry": first == again, "recovered_stock": recovered.stock,
                      "receipt": first}
    (output / "piloto.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (output / "comprobante-ensayo.html").write_text(app.receipt_html("SAL-FICTICIA-001", worker), encoding="utf-8")
    (output / "INFORME-PILOTO.md").write_text(markdown_report(data), encoding="utf-8")
    return {"results": results, "pilot": data["pilot"], "report": str(output / "INFORME-PILOTO.md"),
            "passed": all(r["status"] == "PASS" for r in results)}


def main():
    parser = argparse.ArgumentParser(description="Segunda fábrica desactivada · preparación local")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("pilot")
    sub.add_parser("recover")
    sub.add_parser("prepare-factory-review")
    discovery = sub.add_parser("discover")
    discovery.add_argument("brief", help="Ficha JSON autorizada por el usuario; no carpetas de ERP")
    args = parser.parse_args()
    try:
        if args.command == "status": result = status()
        elif args.command == "pilot": result = pilot()
        elif args.command == "recover":
            status()
            result = Store(ROOT / "state" / "factory2.sqlite3").recover()
        elif args.command == "prepare-factory-review":
            status()
            from .review_packet import packet
            manifest, packets = packet(ROOT)
            destination = ROOT / "outputs" / "revision-claude"
            destination.mkdir(parents=True, exist_ok=True)
            for p in packets:
                (destination / f"parte-{p['part']:02d}.json").write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            (destination / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            result = {"status":"NOT_RUN","files":len(manifest['files']),"parts":len(packets),
                      "factory_digest":manifest['factory_digest'],"transmitted":False,"destination":str(destination)}
        else:
            status()
            result = prepare(load(args.brief))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("passed") is False else 0
    except (Blocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
