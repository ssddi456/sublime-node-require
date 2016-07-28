import sublime
import sublime_plugin
import os
import json
import sys

python_version = sys.version_info[0]

if python_version == 3 :
  import urllib.request
  urlopen = urllib.request.urlopen
else :
  import urllib2
  urlopen = urllib2.urlopen

class InsertPathCommand(sublime_plugin.TextCommand):
  """
    docstring for InsertPathCommand
  """
  def resolve_from_file ( self, full_path ):
    def resolver () :
      file = self.view.file_name()

      module_rel_path = os.path.relpath(full_path, os.path.dirname(file))

      if module_rel_path[:3] != ".." + os.path.sep:
        module_rel_path = "." + os.path.sep + module_rel_path

      return module_rel_path.replace(os.path.sep, "/")
    return resolver

  def write_path(self, resolvers, edit):
    def write( index ) :
        if index == -1:
          return
        module_rel_path = resolvers[index]()
        self.view.run_command("sublime_node_require_replace", {"chrs": module_rel_path})

    return write
  
  def run(self, edit):
    
    # project folder list
    
    folders = self.view.window().folders()

    suggestions = []
    resolvers   = [] 

    if len( folders ) != 0 :
      for folder in folders :
        for root, subFolders, files in os.walk(folder, topdown=True):

          if root.startswith(os.path.join(folder, ".")):
            continue
          if folder.startswith("."):
            continue

          for file in files :
            print(file)
            resolvers.append(self.resolve_from_file(os.path.join(root, file) ))
            suggestions.append([file, root.replace(folder, "", 1) or file])

    self.view.window().show_quick_panel(suggestions, self.write_path(resolvers, edit))

class InsertStaticfilePathCommand(sublime_plugin.TextCommand):
  """docstring for InsertStaticfilePathCommand"""
  def run(self, edit):
    def on_done( name):
      url = "http://api.staticfile.org/v1/search?q=%s" % name
      request = urlopen(url)
      res = request.read()
      print(res)

      packages = json.loads( res.decode('utf8') )

      suggestions = []
      resolvers   = []

      for lib in packages['libs'] :
        for asset in lib['assets'] :
          for asset_file in asset['files'] :
            suggestions.append( asset['version'] + ' :: ' + asset_file )
            resolvers.append( 'http://cdn.staticfile.org/%s/%s/%s' % (lib["name"], asset["version"], asset_file) )

      def write ( index ):
        if index == -1 :
          return
        resolved = resolvers[index]
        self.view.run_command("sublime_node_require_replace", {"chrs": resolved})

      self.view.window().show_quick_panel( suggestions, write )

    self.view.window().show_input_panel('Enter lib name', '', on_done, None, None)


