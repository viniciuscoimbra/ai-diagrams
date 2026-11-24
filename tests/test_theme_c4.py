import json, os, sys, tempfile, unittest

SK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'skills', 'ai-diagrams')
sys.path.insert(0, os.path.join(SK, 'scripts'))
import theme  # noqa: E402

C4_KEYS = ('c4_focus', 'c4_focus_border', 'c4_internal', 'c4_internal_border')


class C4ThemeColors(unittest.TestCase):
    def _theme_without_c4_colors(self):
        t = json.load(open(os.path.join(SK, 'themes', 'ai-diagrams.json')))
        for k in C4_KEYS:
            del t['derived'][k]
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
        json.dump(t, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_skill_themes_have_role_colors(self):
        for nome in ('ai-diagrams', 'paper'):
            t = theme.carregar(theme.caminho(nome))
            for k in C4_KEYS:
                self.assertRegex(t['derived'][k], r'^#[0-9A-Fa-f]{6}$')

    def test_old_theme_keeps_the_gray_look(self):
        t = theme.carregar(self._theme_without_c4_colors())
        d, c = t['derived'], t['colors']
        self.assertEqual((d['c4_focus'], d['c4_focus_border'], d['c4_internal'], d['c4_internal_border']),
                         (c['paper'], c['ink'], c['zone'], c['muted']))
        css = theme.css_root(t)
        self.assertIn('--c4-internal:%s;' % c['zone'].upper(), css)


if __name__ == '__main__':
    unittest.main()
