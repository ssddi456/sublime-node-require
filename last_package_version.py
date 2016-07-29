import sublime
import sublime_plugin
import os
import json
import sys

python_version = sys.version_info[0]

if python_version == 3 :
  from . import last_package_version
  from . import suggestion_from_folder
  from . import popen
else:
  import popen
  import last_package_version
  import suggestion_from_folder

pkg_path = os.path.abspath(os.path.dirname(__file__))


class SublimeNodeRequireReplaceCommand(sublime_plugin.TextCommand):
  def run( self, edit, chrs, region=None ):
    if region :
      self.view.replace(edit, region, chrs)
    else :
      for sel in self.view.sel() :
        self.view.replace(edit, sel, chrs)

def get_module_last_version(name):
  res = popen.get_node_output(['node', os.path.join(pkg_path,'node_scripts/get_target_repo_installed_version.js'), str(name)])
  return res.strip()


class GetLastPackageVersionCommand(sublime_plugin.TextCommand):

  def run( self, edit, name ):
    jsresult = popen.get_node_output(['node', os.path.join(pkg_path,'node_scripts/get_target_repo_installed_version.js'), str(name)])

    res = jsresult.strip()

    if res :
      for sel in self.view.sel() :
        self.view.replace(edit, sel, res)

class LastPackageVersionCommand(sublime_plugin.TextCommand):
  def run(self, edit):

    def on_done( name ):
      self.view.run_command('get_last_package_version', { 'name' : name })

    self.view.window().show_input_panel('Enter lib name', '', on_done, None, None)
