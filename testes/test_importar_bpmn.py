"""BPMN boundaries that must never lose source semantics silently."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/ai-diagrams/scripts'))
from importar_dados import bpmn
from importar_mermaid import ImportError, lines

BASE = {'h1': 'Process', 'sub': 'Imported process.', 'idioma': 'en', 'cabecalho': ['Process', 'BPMN'], 'rodape': ['Process']}
SOURCE = '''<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="defs" targetNamespace="urn:test">
<process id="process" name="Process" isExecutable="false">
<startEvent id="start"><outgoing>f1</outgoing></startEvent>
<task id="task" name="Review"><incoming>f1</incoming><outgoing>f2</outgoing></task>
<endEvent id="end"><incoming>f2</incoming></endEvent>
<sequenceFlow id="f1" sourceRef="start" targetRef="task"/>
<sequenceFlow id="f2" sourceRef="task" targetRef="end"/>
</process>
</definitions>'''


class BPMNBoundaryTest(unittest.TestCase):
    def rejects(self, source, pattern='BPMN-NAO-SUPORTADO'):
        with self.assertRaisesRegex(ImportError, pattern):
            bpmn(source, dict(BASE))

    def test_single_pool_and_geometry_are_supported(self):
        source = SOURCE.replace('</definitions>', '''
<collaboration id="c"><participant id="pool" name="Process" processRef="process"/></collaboration>
<BPMNDiagram xmlns="http://www.omg.org/spec/BPMN/20100524/DI" id="diagram"><BPMNPlane id="plane" bpmnElement="c"/></BPMNDiagram>
</definitions>''')
        kind, model = bpmn(source, dict(BASE))
        self.assertEqual(kind, 'bpmn')
        self.assertEqual([node['type'] for node in model['nodes']], ['startEvent', 'task', 'endEvent'])
        self.assertEqual(len(model['flows']), 2)
        self.assertEqual(model['title'], 'Process')

    def test_preserves_all_task_documentation(self):
        source = SOURCE.replace('<incoming>f1</incoming>', '<documentation>First</documentation><documentation>Second</documentation><incoming>f1</incoming>')
        self.assertEqual(bpmn(source, dict(BASE))[1]['nodes'][1]['doc'], 'First\nSecond')

    def test_reports_source_line_of_unknown_element(self):
        self.rejects(SOURCE.replace('<startEvent id="start">', '<startEvent id="start"><extensionElements/>'), r'linha 3: startEvent/extensionElements')

    def test_entity_and_processing_instructions_are_rejected(self):
        self.rejects('<!DOCTYPE definitions [<!ENTITY x "expanded">]>' + SOURCE)
        self.rejects('<?external value?>' + SOURCE)
        self.rejects(SOURCE.replace('name="Process"', 'name="&undefined;"'))

    def test_lane_documentation_is_rejected_instead_of_dropped(self):
        self.rejects(SOURCE.replace('<startEvent', '<laneSet id="ls"><lane id="l"><documentation>Owner rule</documentation></lane></laneSet><startEvent', 1))

    def test_semantics_cannot_hide_inside_di(self):
        self.rejects(SOURCE.replace('</definitions>', '<BPMNDiagram xmlns="http://www.omg.org/spec/BPMN/20100524/DI"><task xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="hidden"/></BPMNDiagram></definitions>'))

    def test_reference_and_namespace_validation(self):
        self.rejects(SOURCE.replace('targetRef="task"', 'targetRef="missing"'))
        self.rejects(SOURCE.replace('<incoming>f1</incoming>', '<incoming>f2</incoming>'))
        self.rejects(SOURCE.replace('http://www.omg.org/spec/BPMN/20100524/MODEL', 'urn:fake'))

    def test_unknown_attributes_and_task_types(self):
        self.rejects(SOURCE.replace('name="Review"', 'name="Review" default="f2"'))
        self.rejects(SOURCE.replace('<task ', '<userTask ').replace('</task>', '</userTask>'))
        self.rejects(SOURCE.replace('isExecutable="false"', 'isExecutable="true"'))

    def test_empty_lanes_do_not_assign_nodes_silently(self):
        self.rejects(SOURCE.replace('<startEvent', '<laneSet id="ls"><lane id="lane" name="Ops"/></laneSet><startEvent', 1))

    def test_mermaid_directives_are_not_comments(self):
        with self.assertRaisesRegex(ImportError, 'MERMAID-NAO-SUPORTADO: linha 2'):
            lines('%% ordinary comment\n%%{init: {}}%%\nflowchart LR')
        self.assertEqual(lines('%% comment\nflowchart LR'), [(2, 'flowchart LR')])


if __name__ == '__main__':
    unittest.main()
