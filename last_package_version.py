import sublime
import sublime_plugin
import os
import json
import threading

from subprocess import Popen, PIPE, STDOUT

CREATE_NO_WINDOW = 0x08000000
pkg_path = os.path.abspath(os.path.dirname(__file__))


def get_module_last_version( name ):
  check_thread = Popen(['node', os.path.join(pkg_path,'node_scripts/get_target_repo_installed_version.js'), str(name)], stdout=PIPE,stderr=PIPE, creationflags=CREATE_NO_WINDOW)
  jsresult = check_thread.stdout.read()
  check_err = check_thread.stderr.read()
  if check_err : 
    print check_err
    return False
  return jsresult[:-1]

class LastPackageVersionCommand(sublime_plugin.TextCommand):
  def run(self, edit):

    def on_done( name ):
      res = get_module_last_version(name)

      if res :
        res_len = len(res)
        for sel in self.view.sel() :

          self.view.replace(edit, sel, res)

    def idol(name):
      pass

    self.view.window().show_input_panel('Enter lib name', '', on_done, idol, idol)