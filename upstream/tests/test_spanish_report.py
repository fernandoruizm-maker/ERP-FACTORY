import unittest
from factory.mvp.common import Blocked
from factory.mvp.pipeline import Pipeline
from factory.mvp.spanish_report import render, role_form, verify_created_report
from factory.mvp.common import digest


class SpanishReportTests(unittest.TestCase):
    def report(self, roles, accounting=None):
        metric={'tests_run':2,'failures':0,'errors':0,'skipped':0}
        checkpoint={'classification':{'level':'alto','roles':roles,'reasons':['Ejemplo']},
            'tdd':{k:metric for k in ('baseline','red','green','regression')},
            'business_change':'Ejemplo inventado','test_changes':'Añadidas 2; modificadas 0; eliminadas 0',
            'reviews':{'tests':{'verdict':'PASS','rationale':'Cobertura conservada','findings':[]}},
            'changes':{'tecnico/demo.py':'example'},'limitations':'Sin datos reales'}
        return render(checkpoint,owner='owner',specialist='expert',requested='Ensayo',
                      manual_steps='Leer los resultados',accounting=accounting,trial=True)

    def test_accounting_evidence_cannot_be_omitted(self):
        with self.assertRaises(Blocked):self.report(['CONTADOR'])

    def test_accounting_report_shows_obtained_not_only_expected(self):
        text=self.report(['CONTADOR'],[{'operation':'Cobro ficticio','expected':'100',
            'actual':'99','balances':'Caja y clientes','difference':'1'}])
        self.assertIn('| Cobro ficticio | 100 | 99 | Caja y clientes | 1 |',text)
        self.assertIn('NO INTEGRAR',text)

    def test_mixed_roles_are_shown_without_mandatory_comment(self):
        text=role_form(['CONTADOR','TECNICO'])
        for phrase in ['CONTADOR','TECNICO','sin escribir un comentario','ambos roles','Request changes','NO PUEDO EVALUAR']:
            self.assertIn(phrase,text)
        self.assertNotIn('FACTORY-VERSION:',text)
        self.assertNotIn('FACTORY-ROL ',text)

    def test_technical_report_has_evidence_limitations_and_steps(self):
        text=self.report(['TECNICO'])
        for phrase in ['Pruebas antes y después','Hallazgos','Riesgos','en pantalla',
                       'tecnico/demo.py','modificadas 0; eliminadas 0','Sin datos reales']:
            self.assertIn(phrase,text)

    def test_app_pipeline_rejects_missing_policy_before_any_action(self):
        with self.assertRaises(Blocked):
            Pipeline({'github_app':{'app_id':1}},None,None,None,None).execute({})

    def test_created_report_binds_expected_evidence(self):
        pr={'state':'open','draft':True,'title':'Informe','body':'head: abc','head':{'sha':'abc'}}
        self.assertEqual(verify_created_report(pr,title='Informe',body='head: {{FACTORY_HEAD}}',head='abc'),
                         digest({'title':'Informe','body':'head: abc'}))

    def test_edited_or_incomplete_report_cannot_be_adopted_on_retry(self):
        pr={'state':'open','draft':True,'title':'Informe','body':'evidencia','head':{'sha':'abc'}}
        for key,value in [('title','otro'),('body','sustituido'),('draft',False),('head',{'sha':'otro'})]:
            with self.subTest(field=key),self.assertRaises(Blocked):
                verify_created_report({**pr,key:value},title='Informe',body='evidencia',head='abc')
