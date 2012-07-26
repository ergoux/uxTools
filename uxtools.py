import sublime, sublime_plugin, re, subprocess, json

def get_window(self):
    return self.view.window() or sublime.active_window()

def scratch(self, output, title=False, position=None, **kwargs):
    scratch_file = get_window(self).new_file()
    if title:
        scratch_file.set_name(title)
    scratch_file.set_scratch(True)
    _output_to_view(self,scratch_file, output, **kwargs)
    #scratch_file.set_read_only(True)
    if position:
        sublime.set_timeout(lambda: scratch_file.set_viewport_position(position), 0)
    return scratch_file

def quick_panel(self, *args, **kwargs):
    get_window(self).show_quick_panel(*args, **kwargs)

def _output_to_view(self, output_file, output, clear=False,
        syntax="Packages/Diff/Diff.tmLanguage", **kwargs):
    output_file.set_syntax_file(syntax)
    edit = output_file.begin_edit()
    if clear:
        region = sublime.Region(0, self.output_view.size())
        output_file.erase(edit, region)
    output_file.insert(edit, 0, output)
    output_file.end_edit(edit)

class uxtool_list_issues(sublime_plugin.TextCommand):
    def run(self,edit):
        self.edit = edit
        issues, load_info = subprocess.Popen(["curl",
            "-H","Authorization: token a061fe5e8fafc96c561093f44620e864d290b805",
            "https://api.github.com/issues"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        issues = json.loads(issues)
        self.options = []
        self.issues = issues
        for issue in issues:
            self.options.append(str(issue['number']) + ' - ' + issue['title'])
        quick_panel(self,self.options, self.issue_choosed)

    def issue_choosed(self, picked):
        if not picked == -1:
            self.picked = picked
            quick_panel(self,['view info','open url in browser','print number'], self.selection_done)

    def selection_done(self,opt):
        selected_issue = self.issues[self.picked]
        if opt == 0:
            scratch(self,
                "+ %s\n--- %s\n\n%s\n\n----------\n@@ %s @@" % (
                    selected_issue['title'],
                    selected_issue['repository']['full_name'] + " -> issue #" + str(selected_issue['number']),
                    selected_issue['body'],
                    selected_issue['updated_at']
                    ),self.issues[self.picked]['title'])
        elif opt == 1:
            sublime.active_window().run_command('open_url', {"url": selected_issue['html_url']})
        elif opt == 2:
            self.view.insert(self.edit, self.view.sel()[0].a, "#" + str(selected_issue['number']))

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
        repo = re.search(r'\[\[(.+)\]\]\n',text).group(1)
        text = re.sub(r'\[\[.+\]\]\n', '', text)
        for issue in text.split('----\n'):
            obj = issue.split("\n")
            issue_info = {
                "title"     : obj[0],
                "body"      : re.sub(r"<br>", '\n', obj[1]),
                "assignee"  : obj[2],
                "milestone" : obj[3],
                "labels"    : obj[4].split(",")
            }
            resp, load_info = subprocess.Popen([
                "curl",
                "-H","Authorization: token a1e2d5fc89820ae538c90662e6aadf21fc078ec5",
                "-d", json.dumps(issue_info),
                "-X","POST",
                'https://api.github.com/repos/%s/issues' % repo
            ],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
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
