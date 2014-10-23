import sublime
import sublime_plugin
import os
import json
from subprocess import Popen, PIPE, STDOUT

CREATE_NO_WINDOW = 0x08000000

class LastPackageVersionCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    def on_done( name ):
      jsresult = (Popen(['npm.cmd','info', str(name), 'versions', '--json'], stdout=PIPE,stderr=STDOUT, creationflags=CREATE_NO_WINDOW)).stdout.read()
      jsresult = jsresult.split('\n\n')
      try:
        jsresult = json.loads(jsresult[1])
        for sel in self.view.sel() :
          self.view.insert(edit, sel.a, jsresult[-1] )
      except Exception, e:
        pass

    def idol(name):
      pass

    self.view.window().show_input_panel('Enter lib name', '', on_done, idol, idol)