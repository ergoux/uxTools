import sublime, sublime_plugin, re, subprocess, json, urllib2

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
    output_file.insert(edit, output_file.size(), output)
    output_file.end_edit(edit)

def git_api_get(url,data=False):
    token = sublime.load_settings("Preferences.sublime-settings").get("git_token")
    opener = urllib2.build_opener(
        urllib2.HTTPRedirectHandler(),
        urllib2.HTTPHandler(debuglevel=0),
        urllib2.HTTPSHandler(debuglevel=0))
    opener.addheaders = [('Authorization',('token %s' % token))]
    if url[:5] != 'https': url = "https://api.github.com/%s" % url
    if data: 
        resp = opener.open(url,json.dumps(data)).read()
    else:
        resp = opener.open(url).read()
    return json.loads(resp)


class uxtool_list_issues(sublime_plugin.TextCommand):
    display_options = {
        "all": {
            "display_str": "all issues",
            "url": "repos/ergoux/kitukids/issues"
        },
        "mine": {
            "display_str" : "your issues",
            "url": "issues"
        }
    }

    def run(self,edit,issues_to_display):
        self.regions, self.issues = {}, {}

        self.result_view = get_window(self).new_file()
        self.result_view.set_scratch(True)
        self.edit = self.result_view.begin_edit()
        
        self.print_c("Display : " + self.display_options[issues_to_display]["display_str"])
        self.print_c("")
        self.print_c("--- OPENED ---")

        for issue in self.get_issues(self.display_options[issues_to_display]["url"],"open"):
            self.insert_issue(issue)

        self.print_c("")
        self.print_c("--- CLOSED ---")

        for issue in self.get_issues(self.display_options[issues_to_display]["url"],"closed"):
            self.insert_issue(issue);

        self.result_view.end_edit(self.edit)
        self.result_view.settings().set('issues_data', json.dumps(self.issues))

        self.result_view.add_regions('results', self.regions.keys(), '')
        self.result_view.set_syntax_file('Packages/uxTools/issues_results.hidden-tmLanguage')
        self.result_view.settings().set('line_padding_bottom', 2)
        self.result_view.settings().set('line_padding_top', 2)
        self.result_view.settings().set('word_wrap', False)
        self.result_view.settings().set('command_mode', True)

    def insert_issue(self, issue):
        self.issues[issue['number']] = issue

        insert_point = self.result_view.size()
        #self.print_c('#' + str(issue['number']) + ' - ' + issue['title'])
        if issue['assignee']:
            assignee = issue['assignee']['login']
        else:
            assignee = "UNASSIGNED"

        self.print_c('#%i - (%s)\t%s' % (issue['number'], assignee, issue['title']))
        rgn = sublime.Region(insert_point, self.result_view.size())
        self.regions[rgn] = issue

    def print_c(self, str):
        self.result_view.insert(self.edit, self.result_view.size(), str + "\n")

    def get_issues(self, url,status):
        return git_api_get("%s?state=%s" % (url,status))
         
class navigate_results(sublime_plugin.TextCommand):
    DIRECTION = {'forward': 1, 'backward': -1}
    STARTING_POINT = {'forward': -1, 'backward': 0}
    OPTS = ("View Info  ->  ","Open in Browser  ->  ","Copy #  ->  ")
    currOpt = 0
    prevSelection = None
    diff = 0

    def __init__(self, view):
        super(navigate_results, self).__init__(view)

    def run(self, edit,direction):
        view = self.view
        settings = view.settings()

        if self.prevSelection is not None:
            self.diff = self.prevSelection["region"].b - self.prevSelection["region"].a
            self.view.erase(edit, self.prevSelection["region"])

        
        results = self.view.get_regions('results')
        if not results:
            sublime.status_message('No results to navigate')
            return        

        selection = int(settings.get('selected_result', 0))
        if direction in self.DIRECTION: selection = selection + self.DIRECTION[direction]

        try:
            target = results[selection]
        except IndexError:
            target = results[0]
            selection = 0
    
        settings.set('selected_result', selection)
        target = target.cover(target)

        if not direction in self.DIRECTION:     
            if direction == 'left': self.currOpt = self.currOpt - 1
            if direction == 'right': self.currOpt = self.currOpt + 1
            if self.currOpt > 2 : self.currOpt = 0
            if self.currOpt < 0 : self.currOpt = 2
            
            opt_len = self.OPTS[self.currOpt].__len__()
            self.view.insert(edit, target.a, self.OPTS[self.currOpt])
            self.prevSelection = {"region":sublime.Region(target.a, target.a + opt_len)}

        else:
            view.add_regions('selection', [target], 'selected', 'dot')
            view.show(target)
            self.prevSelection = None
            self.currOpt = 0
        settings.set('selected_result_opt', self.currOpt)


class clear_selection(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_regions('selection')
        self.view.settings().erase('selected_result')

class goto_issue(sublime_plugin.TextCommand):
    def __init__(self, *args):
        super(goto_issue, self).__init__(*args)
    
    def render_issue(self,edit,selected_issue):
        scratch_file = scratch(self,
            "+ %s\n--- %s\n\n%s\n\n----------\n@@ %s @@" % (
                selected_issue['title'],
                "ergoux/kitukids -> issue #" + str(selected_issue['number']),
                selected_issue['body'],
                selected_issue['updated_at']
                ),selected_issue['title'])

        issue_comments = git_api_get(selected_issue['url'] + "/comments")

        for issue_comment in issue_comments:
            _output_to_view(
                self,
                scratch_file,
                "\n+comment by %s\n%s\n----\n" % (
                    issue_comment['user']['login'],
                    issue_comment['body']
                    )
            )
        #os.system("say %s"% (selected_issue['title']))


    def open_in_browser(self,edit,selected_issue):
        sublime.active_window().run_command('open_url', {"url": selected_issue['html_url']})

    def copy_number(self,edit,selected_issue):
        sublime.set_clipboard('#' + str(selected_issue['number']))

    def run(self, edit):
        iss = json.loads(self.view.settings().get('issues_data', 0))
        opt = self.view.settings().get('selected_result_opt', 0)
        ## Get the idx of selected result region
        selection = int(self.view.settings().get('selected_result', -1))
        ## Get the region
        selected_region = self.view.get_regions('results')[selection]
        
        data = self.view.substr(selected_region)
        issue_num = re.search(r'#(.+) -',data).group(1)
        selected_issue = iss[issue_num]
        (
            self.render_issue,
            self.open_in_browser,
            self.copy_number
        )[opt](edit,selected_issue)

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
            resp = git_api_get('repos/%s/issues' % repo,issue_info)
            panel.insert(edit, 0, json.dumps(resp))

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
