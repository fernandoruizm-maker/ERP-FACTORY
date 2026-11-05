from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from .common import Blocked, SPEC_SCHEMA, EDITS_SCHEMA, REVIEW_SCHEMA, checked_edits, digest
from .polling import validate_poll_request
from ..memory import Brain


def informe_sin_app(number, checkpoint):
    spec_labels = {"title": "Título", "problem": "Problema", "acceptance": "Criterios de aceptación",
                   "design": "Diseño", "test_plan": "Plan de pruebas", "open_questions": "Preguntas pendientes"}
    phases = {"baseline": "Antes", "red": "Prueba nueva antes del cambio",
              "green": "Prueba nueva después del cambio", "regression": "Conjunto completo"}
    roles = {"security": "Seguridad", "architecture": "Arquitectura", "ux": "Interfaz", "tests": "Pruebas"}
    lines = [f"Solicitud #{number}", f"<!-- Closes #{number} -->", "## Aprobación humana obligatoria",
             "Cambio crítico. Revisa los resultados antes de aprobar. Si tienes dudas, solicita cambios.",
             f"Versión evaluada: `{checkpoint['candidate_id']}` · Base: `{checkpoint['base_sha']}`",
             "## Especificación"]
    for key, value in checkpoint["spec"].items():
        if isinstance(value, list):
            value = "\n".join("- " + item for item in value) or "Ninguna"
        lines.append(f"**{spec_labels.get(key, key)}**\n{value}")
    rows = ["| Fase | Pruebas | Fallos | Errores | Omitidas |", "|---|---:|---:|---:|---:|"]
    for phase, value in checkpoint["tdd"].items():
        rows.append(f"| {phases.get(phase, phase)} | {value['tests_run']} | {value['failures']} | "
                    f"{value['errors']} | {value['skipped']} |")
    lines.extend(["## Resultados de las pruebas", "\n".join(rows), "## Revisiones independientes"])
    for role, review in checkpoint["reviews"].items():
        verdict = "Conforme" if review["verdict"] == "PASS" else "Bloqueado"
        lines.append(f"**{roles.get(role, role)}** · {verdict}. {review['rationale']}")
        lines.extend("Hallazgo: " + finding for finding in review["findings"])
    return "\n\n".join(lines)


class Pipeline:
    def __init__(self, config, github, agent, runner, queue):
        self.config, self.github, self.agent = config, github, agent
        self.runner, self.queue = runner, queue

    def execute(self, job):
        """Recoverable publication; earlier pure computation restarts after a worker crash."""
        if self.config.get('github_app'):
            from .dual_approval import validate_policy
            try:
                validate_policy(self.config['approval_policy'])
            except (KeyError, ValueError, TypeError):
                raise Blocked('Configurar propietario y especialista antes de ejecutar la factoría') from None
        payload = json.loads(job["payload"])
        checkpoint = json.loads(job["checkpoint"])
        if checkpoint.get("ready_to_publish"):
            return self.publish(job["id"], checkpoint)
        if payload["requester"] not in self.config["allowed_requesters"]:
            raise Blocked("Requester not allowed")
        if not self.github.can_write(payload["requester"]):
            raise Blocked("Requester no longer has write permission")
        issue = self.github.issue(payload["issue_number"])
        if issue["updated_at"] != payload["issue_updated_at"]:
            raise Blocked("Issue changed; enqueue its latest revision")
        if self.config["trigger_label"] not in [label["name"] for label in issue["labels"]]:
            raise Blocked("Issue is not opted into the factory")
        validate_poll_request(self.config, self.github, issue, payload)
        self.github.governance(self.config["base_branch"])
        self.runner.preflight()
        base = self.github.base(self.config["base_branch"])
        files = self.github.snapshot(base, self.config["context_prefixes"])
        from . import coverage_only
        coverage_mode = coverage_only.enabled(self.config, payload['issue_number'], base, files)
        from .health_transition import transition, transition_details
        test_updates = transition(self.config, payload['issue_number'], base, files)
        transition_count, transition_reason = transition_details(payload['issue_number'])
        brain = Brain.load(self.config["brain_dir"])
        context = {"repository": self.config["repository"], "base_sha": base,
                   "issue": {"title": issue["title"], "body": issue.get("body") or ""},
                   "brain": dict(brain.documents), "files": files,
                   "test_framework": "stdlib unittest; tests/; imports from repository root",
                   "execution_constraints": {
                       "tests": "Add exactly one NEW tests/test_factory_<name>.py. Never modify existing tests.",
                       "product": "Only edit files inside product_prefixes. Do not edit test or runner configuration.",
                       "approval": "Controller always requires independent human approval for Python/backend changes."
                   },
                   "product_prefixes": self.config["product_prefixes"]}
        if test_updates:
            context['operator_test_transition'] = {
                'reason': transition_reason,
                'before': {p:files[p] for p in test_updates}, 'after':test_updates}
            context['files'] = {**files, **test_updates}
            context['execution_constraints']['tests'] += ' The controller already applies the exact operator-authorized expectation transition shown separately. Do not edit it. Add your NEW test normally.'
        if coverage_mode:
            context['execution_constraints'].update(
                tests='Add exactly one NEW tests/test_factory_ping_http.py. Existing tests and product code are frozen. The endpoint already works: the new coverage MUST pass initially. Never invent RED or introduce a defect.',
                product='Only add NEW src/PING.md in Spanish. Do not change src/api.py or any other existing file.')
            context['validation_mode']='Coverage of existing behavior, explicitly authorized for Issue 13. No RED expected; report initial PASS honestly.'
        if len(json.dumps(context)) > 500_000:
            raise Blocked("Combined task context exceeds budget")
        spec = self.agent.ask("spec_writer", "Produce a complete SDD compatible with execution_constraints. "
                              "Tests must go in a NEW tests/test_factory_<name>.py; existing tests remain unchanged. "
                              "Use open_questions only for blocking unknowns. Write all human-facing explanations in simple Spanish.",
                              context, SPEC_SCHEMA)
        self.record(job["id"], "spec", spec)
        if spec["open_questions"] or not spec["acceptance"]:
            raise Blocked("Specification needs clarification")
        self.record(job["id"], "spec", spec)
        baseline = self.runner.run(files)
        self.record(job["id"], "baseline", asdict(baseline))
        if not baseline.green or baseline.skipped:
            raise Blocked("Baseline must contain passing tests with no skips before automated changes")
        if test_updates:
            transition_red = self.runner.run({**files, **test_updates})
            self.record(job['id'], 'transition-red', asdict(transition_red))
            if (transition_red.exit_code == 0 or transition_red.failures != transition_count
                    or transition_red.errors or transition_red.skipped
                    or set(transition_red.ids) != set(baseline.ids)):
                raise Blocked('Exact expectation transition must fail exactly the authorized count of unchanged tests before implementation')
        context["spec"] = spec
        proposed = self.agent.ask("test_writer",
            "Add exactly one NEW tests/test_factory_<name>.py with focused unittest regression tests for the acceptance criteria. "
            "Use real assertions. Do not change product code, existing tests or import setup. " +
            ("The new HTTP coverage must pass on existing behavior. No RED expected. Use local loopback only, ephemeral port, timeout and guaranteed server shutdown."
             if coverage_mode else "The test must fail with AssertionError on current behavior, not an import, syntax or environment error."),
            context, EDITS_SCHEMA)
        tests = checked_edits(proposed["edits"], files, phase="test", allowed_prefixes=())
        self.record(job["id"], "test-proposal", proposed)
        if len(tests) != 1:
            raise Blocked("MVP requires one new regression test file")
        if coverage_mode:
            coverage_only.validate_tests(tests)
        test_pattern = next(iter(tests)).split("/")[-1]
        frozen = {**files, **test_updates, **tests}
        red = self.runner.run(frozen, test_pattern)
        self.record(job["id"], "red", asdict(red))
        if coverage_mode:
            coverage_only.require_passing(red)
        elif (red.exit_code == 0 or red.tests_run < 1 or red.failures < 1
                or red.errors or red.skipped or not red.ids or "AssertionError" not in red.output):
            raise Blocked("RED must demonstrate an assertion failure in the new test")
        full_red = None
        if test_updates or coverage_mode:
            full_red = self.runner.run(frozen)
            self.record(job['id'], 'full-red', asdict(full_red))
            if coverage_mode:
                coverage_only.require_passing(full_red)
            if ((not coverage_mode and full_red.exit_code == 0) or full_red.errors or full_red.skipped
                    or not set(baseline.ids).issubset(full_red.ids)
                    or not set(red.ids).issubset(full_red.ids)):
                raise Blocked('Full RED suite must preserve all baseline and new tests without errors or skips')
        context["files"], context["red_evidence"] = frozen, asdict(red)
        changes = {}
        green = regression = None
        for attempt in range(3):
            proposal = self.agent.ask("builder",
                "Implement the SDD using complete file edits inside product_prefixes. "
                "Never modify tests, test framework, CI, Brain or governance. Tests are frozen. "
                "Use supplied failure evidence; preserve other behavior.", context, EDITS_SCHEMA)
            edits = checked_edits(proposal["edits"], frozen, phase="build",
                                  allowed_prefixes=self.config["product_prefixes"])
            if coverage_mode:
                coverage_only.validate_docs(edits)
            self.record(job["id"], f"implementation-{attempt}", proposal)
            changes.update(edits)
            candidate_files = {**frozen, **changes}
            green = self.runner.run(candidate_files, test_pattern)
            regression = self.runner.run(candidate_files)
            self.record(job["id"], f"green-{attempt}", asdict(green))
            self.record(job["id"], f"regression-{attempt}", asdict(regression))
            if (green.green and not green.skipped and set(green.ids) == set(red.ids)
                    and regression.green and not regression.skipped
                    and set(baseline.ids).issubset(regression.ids)
                    and set(green.ids).issubset(regression.ids)):
                break
            context["files"] = candidate_files
            context["failure_evidence"] = {"focused": asdict(green), "regression": asdict(regression)}
        else:
            raise Blocked("TDD repair budget exhausted")
        # Bind all audit inputs to exact data, not the agent's self-reported success.
        candidate_id = digest({"base": base, "files": candidate_files,
                               "brain": brain.fingerprint, "spec": spec, "config": self.config})
        review_context = {**context, "files": candidate_files, "changes": {**test_updates, **tests, **changes},
                          "candidate_id": candidate_id, "green": asdict(green),
                          "regression": asdict(regression), 'baseline':asdict(baseline)}
        if full_red:
            if set(full_red.ids) != set(regression.ids):
                raise Blocked('Full RED and final regression must run the identical set of tests')
            review_context.update(full_red=asdict(full_red))
            if test_updates:
                review_context['transition_red']=asdict(transition_red)
        focus = {
            "security": "Review auth, injection, secrets, data exposure and test tampering. Any blocking finding => BLOCK.",
            "architecture": "Review SDD acceptance, Brain conventions, architecture and quality of assertions. Any violation => BLOCK.",
            "ux": "Review API behavior and interface coherence. Backend-only changes: assess API consumer impact; explain visual N/A. Do not claim browser testing."}
        if self.config.get('github_app'):
            focus['tests'] = ('Independently review coverage of business acceptance, lost or weakened assertions, '
                'removed tests, skips and test bypasses. Any lost coverage or tampering => BLOCK.')
        with ThreadPoolExecutor(max_workers=len(focus)) as pool:
            review_contract = (" Return findings ONLY for blocking defects; PASS requires findings=[]. "
                               "Put positive observations and non-applicability in rationale. "
                               "Never omit a genuine defect to return PASS. Write rationale and findings in simple Spanish.")
            futures = {role: pool.submit(self.agent.ask, role, instruction + review_contract,
                                       review_context, REVIEW_SCHEMA) for role, instruction in focus.items()}
            reviews = {role: future.result() for role, future in futures.items()}
        self.record(job["id"], "reviews", reviews)
        if any(r["verdict"] != "PASS" or r["findings"] for r in reviews.values()):
            raise Blocked("Independent quality review blocked publication")
        # Python product changes are always critical in this MVP. No LLM risk downgrade.
        checkpoint = {"ready_to_publish": True, "base_sha": base,
                      "candidate_id": candidate_id, "brain_sha": brain.fingerprint,
                      "config_sha": digest(self.config), "issue_number": payload["issue_number"],
                      "issue_updated_at": payload["issue_updated_at"], "requester": payload["requester"],
                      "spec": spec, "changes": {**test_updates, **tests, **changes}, "reviews": reviews,
                      "tdd": {"baseline": asdict(baseline), "red": asdict(red),
                              "green": asdict(green), "regression": asdict(regression)},
                      "risk": "CRITICAL", "created_at": datetime.now(timezone.utc).isoformat()}
        if payload.get('ingress') == 'poll':
            checkpoint.update(ingress='poll', label_event_id=payload['label_event_id'])
        if coverage_mode:
            checkpoint['validation_mode']='coverage_only'
            checkpoint['tdd']['coverage_before']=asdict(full_red)
        if self.config.get('github_app'):
            from .dual_approval import classify
            checkpoint['classification'] = classify(checkpoint['changes'])
            checkpoint['business_change'] = spec['problem'] + '\n\n' + '\n'.join(spec['acceptance'])
            checkpoint['test_changes'] = ('Añadido: '+', '.join(tests)+'. Pruebas existentes modificadas: 0; eliminadas: 0.')
            if test_updates:
                checkpoint['test_changes'] = ('Archivo de pruebas añadido: '+', '.join(tests)+
                    f'. Pruebas existentes modificadas: {transition_count}. Eliminadas: 0. '+transition_reason+
                    ' Fallaron antes del cambio de producto; se conservan todos los identificadores y comprobaciones de seguridad.')
                checkpoint['operator_test_transition'] = context['operator_test_transition']
                checkpoint['tdd']['transition_red'] = asdict(transition_red)
                checkpoint['tdd']['full_red'] = asdict(full_red)
            checkpoint['limitations'] = ('Verificados los tests y las revisiones indicadas. No se han probado datos '
                'reales ni operaciones del ERP. Esta versión no acredita pruebas visuales ni revisión fiscal.')
        self.queue.set(job["id"], "PUBLISHING", checkpoint)
        return self.publish(job["id"], checkpoint)

    def record(self, job_id, phase, value):
        root = Path(self.config["state_dir"]) / "evidence" / job_id
        root.mkdir(parents=True, exist_ok=True)
        (root / (phase + ".json")).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def publish(self, job_id, checkpoint):
        issue = self.github.issue(checkpoint["issue_number"])
        if (issue["updated_at"] != checkpoint["issue_updated_at"]
                or self.config["trigger_label"] not in [v["name"] for v in issue["labels"]]
                or checkpoint["requester"] not in self.config["allowed_requesters"]
                or not self.github.can_write(checkpoint["requester"])):
            raise Blocked("Task changed or requester is no longer authorized")
        validate_poll_request(self.config, self.github, issue, checkpoint)
        if checkpoint["config_sha"] != digest(self.config):
            raise Blocked("Configuration changed after generation")
        if Brain.load(self.config["brain_dir"]).fingerprint != checkpoint["brain_sha"]:
            raise Blocked("Brain changed after generation")
        if self.github.base(self.config["base_branch"]) != checkpoint["base_sha"]:
            raise Blocked("Base branch changed; regenerate and revalidate")
        self.github.governance(self.config["base_branch"])
        number = checkpoint["issue_number"]
        title = f"Factory #{number}: {checkpoint['spec']['title']}"
        evidence = {key: checkpoint[key] for key in ("candidate_id", "base_sha", "spec", "tdd", "reviews")}
        self.record(job_id, "publication-evidence", evidence)
        reference = f"Registro completo en Ubuntu: evidence/{job_id}/publication-evidence.json"
        if self.config.get('github_app'):
            from .spanish_report import render
            policy = self.config['approval_policy']
            body = render(checkpoint, owner=policy['owner']['login'], specialist=policy['specialist']['login'],
                requested=checkpoint['spec']['title'],
                manual_steps=('1. Leer src/PING.md en esta rama y seguir la guía dentro de Ubuntu.\n'
                    '2. Consultar http://127.0.0.1:8080/ping desde el mismo entorno: respuesta esperada {"message":"pong"}.\n'
                    '3. Detener la demostración según la guía. No se verificó un navegador; no es el ERP ni producción.'
                    if checkpoint.get('validation_mode')=='coverage_only' else
                    '1. Iniciar la demostración de esta rama en el entorno aislado con python -m src.api.\n'
                    '2. En ese mismo entorno, consultar http://127.0.0.1:8080/health y comparar con los criterios de aceptación. '
                    'Si se añadió version, comparar también con http://127.0.0.1:8080/version.\n'
                    '3. Comparar las pruebas y los hallazgos. Si no puede evaluar el resultado, no aprobar. No se ha verificado un navegador.'
                    if checkpoint.get('operator_test_transition') else
                    '1. Leer los criterios de aceptación.\n2. Comparar la tabla de pruebas y los hallazgos.\n'
                    '3. Si no puede evaluar el resultado, no aprobar. Este cambio no incluye una vista previa visual.'),
                accounting=checkpoint.get('accounting_evidence'))
        else:
            body = informe_sin_app(number, checkpoint)
        body += "\n\n" + reference
        if len(body.encode("utf-8")) > 60_000:
            raise Blocked("Informe de revisión demasiado grande; evidencia completa conservada en Ubuntu")
        pr = self.github.publish(base_sha=checkpoint["base_sha"], base_branch=self.config["base_branch"],
                                 branch=f"factory/issue-{number}-{job_id[:12]}",
                                 changes=checkpoint["changes"], title=title, body=body)
        if self.config.get('github_app'):
            from .spanish_report import verify_created_report
            report_fingerprint=verify_created_report(self.github.get('/pulls/'+str(pr['number'])),
                title=title,body=body,head=pr['head_sha'])
        checkpoint["pr"] = pr
        self.queue.set(job_id, "PUBLISHING", checkpoint)
        quality = self.github.status(pr["head_sha"], "factory/quality", "success", "Pruebas y revisiones independientes completadas")
        self.github.status(pr["head_sha"], "factory/human-approval", "pending", "Pendiente de las aprobaciones humanas requeridas")
        reviewers = [r for r in self.config["human_reviewers"] if r != pr.get("author_login")]
        if self.config.get('github_app'):
            from .dual_approval import classify
            checkpoint.update(report_sha=report_fingerprint,
                approval_ready_at=quality['created_at'],changed_paths=self.github.changed_paths(pr['number']))
            checkpoint['classification']=classify(checkpoint['changed_paths'])
            self.queue.set(job_id,'PUBLISHING',checkpoint)
            expert=self.config['approval_policy']['specialist']['login']
            if checkpoint['classification']['roles'] and self.github.can_write(expert):
                reviewers.append(expert)
        if not reviewers:
            raise Blocked("An independent human reviewer is required; use a GitHub App as PR author")
        if self.config.get('github_app'):
            checkpoint['review_request_note']='PR en borrador: las personas designadas revisan mediante el enlace y formulario del informe.'
        else:
            self.github.request_reviewers(pr["number"], list(dict.fromkeys(reviewers)))
        self.queue.set(job_id, "WAITING_APPROVAL", checkpoint)
        return {"state": "WAITING_APPROVAL", "pr": pr, "deployment_attempted": False}
