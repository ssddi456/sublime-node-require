import sublime
import sublime_plugin
import os

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
          self.view.insert(edit, sel.a, '\'' + module_rel_path + '\'' )
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