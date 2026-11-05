import hashlib
import unittest
from factory.mvp.health_transition import transition, PATH, OLD, NEW
from factory.mvp.common import Blocked, checked_edits
from factory.mvp.health_transition import VERSION_REPLACEMENTS, VERSION_PATH

class HealthVersionTransitionTests(unittest.TestCase):
    def setUp(self):
        self.files={p:'\n'.join(old+'\n' for old,new,n in edits for _ in range(n))+'assert keep_security\n'
                    for p,edits in VERSION_REPLACEMENTS.items()}
        self.config={'repository':'fernandoruizm-maker/rdc','health_version_transition':{
            'issue':12,'base_sha':'base','file_hashes':{p:hashlib.sha256(v.encode()).hexdigest() for p,v in self.files.items()}}}
    def test_only_exact_literals_change(self):
        result=transition(self.config,12,'base',self.files)
        for p,edits in VERSION_REPLACEMENTS.items():
            restored=result[p]
            for old,new,n in reversed(edits):
                self.assertEqual(restored.count(new),n)
                restored=restored.replace(new,old)
            self.assertEqual(restored,self.files[p])
    def test_changed_file_base_and_wrong_issue_fail_closed(self):
        with self.assertRaises(Blocked): transition(self.config,12,'other',self.files)
        for path in self.files:
            with self.assertRaises(Blocked):
                transition(self.config,12,'base',{**self.files,path:self.files[path]+'# change'})
        self.assertEqual(transition(self.config,13,'base',self.files),{})
    def test_no_grant_no_test_changes(self):
        self.assertEqual(transition({'repository':'fernandoruizm-maker/rdc'},12,'base',self.files),{})
    def test_extra_path_in_grant_rejected(self):
        self.config['health_version_transition']['file_hashes']['tests/other.py']='x'
        with self.assertRaises(Blocked): transition(self.config,12,'base',self.files)

class HealthTransitionTests(unittest.TestCase):
    def setUp(self):
        self.source = '\n'.join([OLD] * 3) + '\nassert security_check\n'
        self.config = {'repository':'fernandoruizm-maker/rdc', 'health_text_transition':{
            'issue':11, 'base_sha':'base',
            'test_sha256':hashlib.sha256(self.source.encode()).hexdigest()}}
    def test_only_exact_expectations_change(self):
        result=transition(self.config,11,'base',{PATH:self.source})[PATH]
        self.assertEqual(result.replace(NEW,OLD),self.source)
        self.assertEqual(result.count(NEW),3)
    def test_default_and_other_issue_unchanged(self):
        self.assertEqual(transition({},11,'base',{}),{})
        self.assertEqual(transition(self.config,12,'base',{}),{})
    def test_changed_base_repository_or_file_rejected(self):
        for config,base,source in [(self.config,'other',self.source),
                ({**self.config,'repository':'other/repo'},'base',self.source),
                (self.config,'base',self.source+'# changed')]:
            with self.assertRaises(Blocked):
                transition(config,11,base,{PATH:source})
    def test_model_still_cannot_modify_existing_tests(self):
        for phase in ['test','build']:
            with self.assertRaises(Blocked):
                checked_edits([{'path':PATH,'content':self.source}],{PATH:self.source},
                              phase=phase,allowed_prefixes=['src/'])
