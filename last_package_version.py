import sublime
import sublime_plugin
import os
import json

from subprocess import Popen, PIPE

CREATE_NO_WINDOW = 0x08000000
pkg_path = os.path.abspath(os.path.dirname(__file__))


class SublimeNodeRequireReplaceCommand(sublime_plugin.TextCommand):
  def run( self, edit, chrs, region=None ):
    if region :
      self.view.replace(edit, region, chrs)
    else :
      for sel in self.view.sel() :
        self.view.replace(edit, sel, chrs)

class GetLastPackageVersionCommand(sublime_plugin.TextCommand):

  def run( self, edit, name ):
    check_thread = Popen(['node', os.path.join(pkg_path,'node_scripts/get_target_repo_installed_version.js'), str(name)], stdout=PIPE,stderr=PIPE, creationflags=CREATE_NO_WINDOW)
    jsresult = check_thread.stdout.read()
    check_err = check_thread.stderr.read()
    if check_err : 
      print(check_err)
      return False
    res = jsresult[:-1]

    if res :
      for sel in self.view.sel() :
        self.view.replace(edit, sel, str(res, encoding='utf8'))

class LastPackageVersionCommand(sublime_plugin.TextCommand):
  def run(self, edit):

    def on_done( name ):
      self.view.run_command('get_last_package_version', { 'name' : name })

    self.view.window().show_input_panel('Enter lib name', '', on_done, None, None)
