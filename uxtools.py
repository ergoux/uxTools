import sublime, sublime_plugin
import re, json, urllib2
import threading

class GitApiGetAsync ( threading.Thread ):
    def __init__(self, url, callback, data = False):
        self.url = url
        self.callback = callback
        self.data = data
        self.token = sublime.load_settings("Preferences.sublime-settings").get("git_token")
        threading.Thread.__init__ ( self )

    def run ( self ):
        opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0))
        opener.addheaders = [('Authorization',('token %s' % self.token))]
        if self.url[:5] != 'https': self.url = "https://api.github.com/%s" % self.url
        if self.data: 
            resp = opener.open(self.url,json.dumps(self.data)).read()
        else:
            resp = opener.open(self.url).read()

        self.callback(json.loads(resp))

class ThreadProgress():
    def __init__(self, thread, message, success_message):
        self.thread = thread
        self.message = message
        self.success_message = success_message
        self.addend = 1
        self.size = 8
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if not self.thread.is_alive():
            if hasattr(self.thread, 'result') and not self.thread.result:
                sublime.status_message('')
                return
            sublime.status_message(self.success_message)
            return

        before = i % self.size
        after = (self.size - 1) - before
        sublime.status_message('%s [%s=%s]' % \
            (self.message, ' ' * before, ' ' * after))
        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend
        sublime.set_timeout(lambda: self.run(i), 100)


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
            "url": "repos/ergoux/kitukids/issues",
            "milestones": "repos/ergoux/kitukids/milestones"
        },
        "mine": {
            "display_str" : "your issues",
            "url": "issues"
        }
    }

    def dpm(self, obj):
        print "DPM: ", obj

    def render_milestones(self, milestones):
        for milestone in milestones:
            total_issues = int(milestone['closed_issues']) + int(milestone['open_issues'])
            percentage = (milestone['closed_issues'] * 100 / total_issues)  if total_issues > 0 else 100

            fill = percentage
            empt = 100 - fill

            percentage_meter = "[" + ("=" * fill) + ">" + (" " * empt) + "]"
            self.print_c("[%d] %s:\n %s %d/%d\t%d%%" % ( 
                milestone['number'],
                milestone['title'], 
                percentage_meter, 
                milestone['closed_issues'], 
                total_issues,
                percentage
            ), self.result_view.find('--- MILESTONES ---\n', 0).b)
        print milestones

    def run(self,edit,issues_to_display):
        self.regions, self.issues, self.issues_index  = [], {}, [0]

        self.result_view = get_window(self).new_file()
        self.result_view.set_scratch(True)

        thread = GitApiGetAsync(
            "user",
            lambda user:
                sublime.set_timeout(
                    lambda: self.print_c("Hello (%s) " % ( user['login']), self.result_view.find('\n--- MILESTONES ---', 0).a)
                , 100
                )
        )
        thread.start()
        #ThreadProgress(thread, 'Loading user data', '')

        self.print_c("Display : %s" % (self.display_options[issues_to_display]["display_str"]))

        self.print_c("")
        self.print_c("--- MILESTONES ---")
        print self.display_options[issues_to_display]["milestones"]
        thread = GitApiGetAsync(
            self.display_options[issues_to_display]["milestones"],
            lambda milestones:
                sublime.set_timeout(
                    lambda: self.render_milestones(milestones)
                , 100
                )
        )
        thread.start()

        self.print_c("")
        self.print_c("--- OPENED ---")

        self.get_issues(
            self.display_options[issues_to_display]["url"],
            "open",
            self.insert_issues,
            "--- OPENED ---\n"
        )

        self.print_c("")
        self.print_c("--- CLOSED ---")

        self.get_issues(
            self.display_options[issues_to_display]["url"],
            "closed",
            self.insert_issues,
            "--- CLOSED ---\n"
        )

        self.result_view.set_syntax_file('Packages/uxTools/issues_results.hidden-tmLanguage')
        self.result_view.settings().set('line_padding_bottom', 2)
        self.result_view.settings().set('line_padding_top', 2)
        self.result_view.settings().set('word_wrap', False)
        self.result_view.settings().set('command_mode', True)

    def insert_issues(self, issues,wildcard=False):
        insert_point = self.result_view.find(wildcard, 0).b
        base_point = insert_point

        if not insert_point: insert_point = 0

        for issue in issues:
            insert_point += self.insert_issue(issue, insert_point)

        total_len = insert_point - base_point

        # if the len of issues_index is 1 it means this is the first group so no check is needed
        if self.issues_index.__len__() is not 1:
            # We now get the index of the current issues group region
            curr_region = self.issues_index[-1]
            prepending_region = False

            # Checking how deep in the list of issues groups we need to prepend
            for issue_index in self.issues_index:
                # If the current region starts before the issue_index it means we are prepending before issue_index region
                if self.regions[curr_region].a < self.regions[issue_index].a:
                    prepending_region = issue_index
                    break

            if prepending_region is not False:
                # We need to add to the positions the total length of the current issues list
                for index in range(prepending_region, curr_region):
                    self.regions[index] = sublime.Region(self.regions[index].a + total_len, self.regions[index].b + total_len)

        # append the indexe of the next region (this index will start a group of issues)
        self.issues_index.append(self.regions.__len__())

        self.result_view.settings().set('issues_data', json.dumps(self.issues))
        self.result_view.add_regions('results', self.regions, '')

    def insert_issue(self, issue, insert_point=False):
        self.issues[issue['number']] = issue
        #self.print_c('#' + str(issue['number']) + ' - ' + issue['title'])
        if issue['assignee']:
            assignee = issue['assignee']['login']
        else:
            assignee = "UNASSIGNED"

        len1 = self.print_c('#%i - (%s)\t%s' % (issue['number'], assignee, issue['title']),insert_point)
        rgn = sublime.Region(insert_point, insert_point + len1)
        self.regions.append(rgn)
        return len1

    def print_c(self, str1, insert_point=False):
        if not insert_point: insert_point = self.result_view.size()
        edit = self.result_view.begin_edit()
        str1 += "\n"
        self.result_view.insert(edit, insert_point, str1)
        self.result_view.end_edit(edit)
        return str1.__len__()

    def get_issues(self, url, status, callback, wildcard):
        GitApiGetAsync(
            "%s?state=%s" % (url,status),
            lambda issues:
                sublime.set_timeout(
                    lambda: callback(issues, wildcard)
                , 100
                )
        ).start()
         
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

# class uxtool_take_screenshot(sublime_plugin.TextCommand):
#     def run(self, edit):
#         resp, err = subprocess.Popen(["screencapture","-i","/tmp/imgur_upload.png"],stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
#         if not err:
#             resp, err = subprocess.Popen(["curl","-F","image=@/tmp/imgur_upload.png","-F","key=2bfe50a1bbc990e30d6062ecb9216096","http://api.imgur.com/2/upload.json"],stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
#             self.links = json.loads(resp)['upload']['links']
#             sublime.set_clipboard(self.links["original"])
#             sublime.status_message("Copied to clipboard %s" % self.links["original"])

# class uxtool_kk_sync(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.options  = [
#                             "Sync: Database",
#                             "Sync: Pull in server",
#                             "Sync: LS"
#                         ]
#         self.commands = [
#                             "ssh bitnami@kitukids.com 'mysqldump -u root -pbitnami kitukids | bzip2 -c' | bunzip2 -c | mysql -u root kitukids",
#                             "ssh","bitnami@kitukids.com 'cd /var/www/dev/ && git pull'",
#                             "ls", "-lh"
#                         ]
#         self.quick_panel(self.options, self.selecion_done)

#     def selecion_done(self, picked):
#         print self.commands[picked]
#         resp, err = subprocess.Popen(self.commands[picked], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
#         print "--------------"
#         print err
#         sublime.status_message(resp);

#     def quick_panel(self, *args, **kwargs):
#         sublime.active_window().show_quick_panel(*args, **kwargs)
