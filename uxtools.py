import sublime, sublime_plugin, re, subprocess, json

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

class uxtool_take_screenshot(sublime_plugin.TextCommand):
    def run(self, edit):
        resp, err = subprocess.Popen(["screencapture","-i","/tmp/imgur_upload.png"],stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if not err:
            resp, err = subprocess.Popen(["curl","-F","image=@/tmp/imgur_upload.png","-F","key=2bfe50a1bbc990e30d6062ecb9216096","http://api.imgur.com/2/upload.json"],stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            self.links = json.loads(resp)['upload']['links']
            sublime.set_clipboard(self.links["original"])
            sublime.status_message("Copied to clipboard %s" % self.links["original"])

class uxtool_kk_sync(sublime_plugin.TextCommand):
    def run(self, edit):
        self.options  = [
                            "Sync: Database",
                            "Sync: Pull in server",
                            "Sync: LS"
                        ]
        self.commands = [
                            "ssh bitnami@kitukids.com 'mysqldump -u root -pbitnami kitukids | bzip2 -c' | bunzip2 -c | mysql -u root kitukids",
                            "ssh","bitnami@kitukids.com 'cd /var/www/dev/ && git pull'",
                            "ls", "-lh"
                        ]
        self.quick_panel(self.options, self.selecion_done)

    def selecion_done(self, picked):
        print self.commands[picked]
        resp, err = subprocess.Popen(self.commands[picked], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print "--------------"
        print err
        sublime.status_message(resp);

    def quick_panel(self, *args, **kwargs):
        sublime.active_window().show_quick_panel(*args, **kwargs)
