import sublime
import sublime_plugin
import os
import urllib2
import json

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
        module_rel_path = resolvers[index]()
        for sel in self.view.sel() :
          self.view.insert(edit, sel.a, module_rel_path )
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
            print file
            resolvers.append(self.resolve_from_file(os.path.join(root, file) ))
            suggestions.append([file, root.replace(folder, "", 1) or file])

    self.view.window().show_quick_panel(suggestions, self.write_path(resolvers, edit))

class InsertStaticfilePathCommand(sublime_plugin.TextCommand):
  """docstring for InsertStaticfilePathCommand"""
  def run(self, edit):
    def on_done( name):
      url = "http://api.staticfile.org/v1/search?q=%s" % name
      request = urllib2.urlopen(url)
      res = request.read()
      print( res )

      packages = json.loads( res )

      suggestions = []
      resolvers   = []

      for lib in packages['libs'] :
        for asset in lib['assets'] :
          for asset_file in asset['files'] :
            suggestions.append( asset['version'] + ' :: ' + asset_file )
            resolvers.append( 'http://cdn.staticfile.org/%s/%s/%s' % (lib["name"], asset["version"], asset_file) )

      def write ( index ):
        resolved = resolvers[index]
        for sel in self.view.sel() :
          self.view.replace(edit, sel, resolved )

      self.view.window().show_quick_panel( suggestions, write )

    self.view.window().show_input_panel('Enter {username}/{repository name}', '', on_done, self.on_change, self.on_cancel)

  def on_cancel(self, name):
    pass

  def on_change(self, name):
    pass

