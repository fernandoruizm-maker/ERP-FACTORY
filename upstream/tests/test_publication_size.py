import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from factory.memory import Brain
from factory.mvp.common import Blocked, digest, load_config
from factory.mvp.pipeline import Pipeline


class PublicationSizeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        config = load_config(Path(__file__).resolve().parents[1] / 'config.app.example.json')
        config['state_dir'] = tmp.name
        self.github = Mock()
        self.github.issue.return_value = {'updated_at': 'now', 'labels': [{'name': config['trigger_label']}]}
        self.github.base.return_value = 'base'
        self.github.status.return_value = {'created_at': 'now'}
        self.github.changed_paths.return_value = ['src/api.py']
        self.github.publish.return_value = {'number': 1, 'head_sha': 'head'}
        self.github.get.side_effect = lambda _: {
            **self.github.publish.call_args.kwargs, 'state': 'open', 'draft': True, 'head': {'sha': 'head'}}
        self.pipeline = Pipeline(config, self.github, None, None, Mock())
        metric = dict(tests_run=72, failures=0, errors=0, skipped=0, output='LOCAL_LOG' * 20000)
        self.cp = dict(issue_number=1, issue_updated_at='now', requester=config['allowed_requesters'][0],
            base_sha='base', candidate_id='abc', brain_sha=Brain.load(config['brain_dir']).fingerprint,
            config_sha=digest(config), spec={'title':'Ensayo'}, changes={'src/api.py':'# fixture'},
            classification={'roles':['TECNICO'], 'level':'alto', 'reasons':['Backend']},
            business_change='Demostración', test_changes='Pruebas conservadas', limitations='Ejemplo',
            reviews={'tests':{'verdict':'PASS','rationale':'Cobertura revisada','findings':[]}},
            tdd={phase:dict(metric) for phase in ('baseline','red','green','regression')})
        self.cp['tdd']['red']['failures'] = 2

    def test_large_logs_publish_without_changing_evidence_or_approvals(self):
        result = self.pipeline.publish('job', self.cp)
        body = self.github.publish.call_args.kwargs['body']
        self.assertEqual(result['state'], 'WAITING_APPROVAL')
        self.assertNotIn('LOCAL_LOG', body)
        self.assertIn('Cobertura revisada', body)
        self.assertIn('| 72 | 2 | 0 | 0 |', body)
        self.assertLessEqual(len(body.encode()), 60000)
        archive = self.root / 'evidence/job/publication-evidence.json'
        self.assertEqual(json.loads(archive.read_text())['tdd'], self.cp['tdd'])
        self.assertIn(('head','factory/human-approval','pending'),
                      [call.args[:3] for call in self.github.status.call_args_list])

    def test_report_without_app_is_in_spanish_and_preserves_evidence(self):
        del self.pipeline.config['github_app']
        self.cp['config_sha'] = digest(self.pipeline.config)
        self.cp['reviews']['tests']['findings'] = ['Observación de muestra']
        result = self.pipeline.publish('job', self.cp)
        body = self.github.publish.call_args.kwargs['body']
        for phrase in ('Aprobación humana obligatoria', 'Especificación', 'Revisiones independientes',
                       'Cobertura revisada', 'Observación de muestra', '| 72 | 2 | 0 | 0 |'):
            self.assertIn(phrase, body)
        self.assertNotIn('Human approval required', body)
        self.assertNotIn('LOCAL_LOG', body)
        self.assertEqual(result['state'], 'WAITING_APPROVAL')

    def test_oversized_human_findings_block_before_publication(self):
        self.cp['reviews']['tests']['rationale'] = 'á' * 31000
        with self.assertRaises(Blocked):
            self.pipeline.publish('job', self.cp)
        self.github.publish.assert_not_called()
