import sublime, sublime_plugin,re,subprocess

class uxtool_create_css(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        panel = window.get_output_panel("exec")
        panel.set_syntax_file('Packages/CSS/CSS.tmLanguage')
        window.run_command("show_panel", {
            "panel": "output.exec"
        });
        panel.set_read_only(False)
        for region in self.view.sel():
           panel.insert(edit, 0,
            '.' + self.view.substr(region) + ' {\n' + \
            '   top:0px;\n' + \
            '   left:0px;\n' + \
            '}\n'  \
            )

class uxtool_css_object(sublime_plugin.TextCommand):
    def run(self, edit):
        text = sublime.get_clipboard(); 
        resp = ''
        for line in text.split('\n'):
            tmp = line.split(':');
            resp += "'" + tmp[0] + "': '" + tmp[1][1:-1] + "',\n"
        self.view.insert(edit, self.view.sel()[0].a, resp[:-2])

class uxtool_upload_issues(sublime_plugin.TextCommand):
    def run(self, edit):
        resp = ""
        window = self.view.window()
        text = self.view.substr(self.view.sel()[0]); 
        panel = window.get_output_panel("exec")
        window.run_command("show_panel", {
            "panel": "output.exec"
        });
        panel.set_read_only(False)
        text = re.sub(r"\n\t", '<br>', text)
#        text = re.sub(r"'", "\\'", text)
        text = re.sub(r'"', '\\"', text)
        repo = re.search(r'\[\[(.+)\]\]\n',text).group(1)
        text = re.sub(r'\[\[.+\]\]\n', '', text)
        print text
        for issue in text.split('----\n'):
            obj = issue.split('\n')            
            json = '{"title":"%s","body":"%s","assignee":"%s","milestone":"%s","labels":["%s"]}\n' % (obj[0],obj[1],obj[2],obj[3],obj[4])
            print json
            resp, err = subprocess.Popen(["python","/Users/gizmo/dev/python/gitTest2.py",json,repo],stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            print resp
            print err
            panel.insert(edit, 0,resp)