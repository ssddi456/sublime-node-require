import sublime
import sublime_plugin
import os
from subprocess import Popen, PIPE
from tempfile import SpooledTemporaryFile as tempfile
import json
import string
import re

pkg_path = os.path.abspath(os.path.dirname(__file__))
re_require = r'(var\s\w+\s*=\s*require\([^\(\)]*\))'
re_require_nw = r'(var\s\w+\s*=\s*global\.require\([^\(\)]*\))'
re_empty   = r'^\n?\s*\n?\s*\n?$'

class RequireNodeCommand(sublime_plugin.TextCommand):
    def is_inline_require_region( self ):
        def getlastline(line):
            prlin = view.line(line.a-1)
            prlin = view.substr(prlin)
            return prlin
          
        def getthisline(line):
            return view.substr(line)

        view   = self.view       
        region = view.sel()[0]
        line   = view.line(region)

        return re.search(self.re_require, getthisline(line)) != None or re.search(self.re_require, getlastline(line)) != None

    def write_require(self, resolvers, edit):
        view = self.view
        def getlastline(line):
          prlin = view.line(line.a-1)
          prlin = view.substr(prlin)
          return prlin
        
        def getthisline(line):
          return view.substr(line)

        # TODO : add module detect
        def write_node_require ( require_directive ) :
          lens = 0
          spos = 0
          region = view.sel()[0]
          line   = view.line(region)

          if re.search(self.re_require, getthisline(line)) != None :
            print('this line is require')
            spos = line.b
            lens = view.insert(edit, line.b, '\n'+require_directive)
          elif re.search(self.re_require, getlastline(line)) != None :
            print('last line is require')
            spos = line.a
            lens = view.insert(edit, line.a, require_directive)
          else :
            print('last line not require')
            spos = line.b
            if re.search(re_empty, getlastline(line)) :
              lens = view.insert(edit, line.b, require_directive )
            else :
              lens = view.insert(edit, line.b, '\n'+require_directive)

          pos = lens + spos
          view.sel().clear()
          view.sel().add(sublime.Region(pos))

          view.show(pos)

        def write_requirejs ( module_name, module_path ) :
          _edit = view.begin_edit('add package')
          path_point     = ( view.find(r'require\(\[\n', 0 ) or view.find(r'define\(\[\n', 0 ) ).b
          # check if has load a module
          path_block_end = view.find( r'\],function\(', path_point).a
          paths = view.substr( sublime.Region(path_point, path_block_end))
          has_module = False
          if re.search(re_empty, paths ) :
            view.insert(edit, path_point, '\t'+module_path +'\n');
          else:
            has_module = True
            view.insert(edit, path_point, '\t'+module_path +',\n');

          module_point = view.find(r'\],function\(\n', path_point).b
          
          if not has_module :
            view.insert(edit, module_point, '\t'+module_name +'\n');
          else:
            view.insert(edit, module_point, '\t'+module_name +',\n');

          view.end_edit(_edit)

        def write(index):
            if index == -1:
                return
            [module_candidate_name, module_rel_path] = resolvers[index]()

            if module_candidate_name.find("-") != -1:
                upperWords = [string.capitalize(word) for word in module_candidate_name.split("-")[1::]]
                module_candidate_name = string.join(module_candidate_name.split("-")[0:1] + upperWords, "")

            require_directive = self.node_tpl % (module_candidate_name, get_path(module_rel_path))

            if self.type == 'nodejs' or self.type == 'amdjs':
              write_node_require( require_directive )
            elif self.type == 'requirejs' :
              if self.is_node_webkit :
                if self.is_inline_require_region() :
                  write_node_require( require_directive )
                  return
              
              write_requirejs( module_candidate_name, get_path(module_rel_path) )


        def get_path(path):
            settings = sublime.load_settings(__name__ + '.sublime-settings')
            quotes_type = settings.get('quotes_type')
            quote = "'"
            if quotes_type == "double":
                quote = "\""
            return quote + path + quote

        return write
    def write_path ( self, resolvers, edit ):
      def write( index ) :
        [module_candidate_name, module_rel_path] = resolvers[index]()
        for sel in self.view.sel() :
          self.view.insert(edit, sel.a, module_rel_path)
      return write
    def resolve_from_file(self, full_path, with_ext):
        def resolve():
            file = self.view.file_name()
            file_wo_ext = os.path.splitext(full_path)[0]
            module_candidate_name = os.path.basename(file_wo_ext).replace(".", "")
            if with_ext : 
              module_rel_path = os.path.relpath(full_path, os.path.dirname(file))
            else :
              module_rel_path = os.path.relpath(file_wo_ext, os.path.dirname(file))

            if module_rel_path[:3] != ".." + os.path.sep:
                module_rel_path = "." + os.path.sep + module_rel_path

            return [module_candidate_name, module_rel_path.replace(os.path.sep, "/")]
        return resolve

    def get_suggestion_from_nodemodules(self):
        resolvers = []
        suggestions = []
        current_file_dirs = self.view.file_name().split(os.path.sep)
        current_dir = os.path.split(self.view.file_name())[0]
        if len(self.view.window().folders())!= 0 :
          for x in range(len(self.view.window().folders()[0].split(os.path.sep)), len(current_file_dirs))[::-1]:
              candidate = os.path.join(current_dir, "node_modules")
              if os.path.exists(candidate):
                  for dir in [name for name in os.listdir(candidate)
                                   if os.path.isdir(os.path.join(candidate, name)) and name != ".bin"]:
                      resolvers.append(lambda dir=dir: [dir, dir])
                      suggestions.append("module: " + dir)
                  break
              current_dir = os.path.split(current_dir)[0]
        return [resolvers, suggestions]

    def get_suggestion_from_nodemodules_g(self):
        resolvers = []
        suggestions =[]
        g_node_path = os.environ.get('NODE_PATH')
        if g_node_path != None :
          for dir in [ name for name in os.listdir(g_node_path)
                            if os.path.isdir(os.path.join(g_node_path, name)) and name != ".bin"]:
            resolvers.append( lambda dir= dir:[dir,dir])
            suggestions.append("globle module: "+ dir )
        return [resolvers, suggestions]
        
    def get_suggestion_native_modules(self):
        NODE_MODULES_LIST = os.path.join(pkg_path,'node_modules.list')
        try:
            if os.path.exists(NODE_MODULES_LIST) :
                source = open(NODE_MODULES_LIST)
                results= json.loads(source.read())
                source.close()
            else :
                # load native node modules from node
                f = tempfile()
                f.write('console.log(Object.keys(process.binding("natives")))')
                f.seek(0)
                jsresult = (Popen(['node'], stdout=PIPE, stdin=f)).stdout.read().replace("'", '"')
                f.close()
                # write list to list file
                results = json.loads(jsresult)
                source = open(NODE_MODULES_LIST,'w')
                source.write(jsresult)
                source.close()

            result = [[(lambda ni=ni: [ni, ni]) for ni in results],
                    ["native: " + ni for ni in results]]
            return result
        
        except Exception:
           return [[], []]

    def run(self, edit):
        view = self.view
        file_name, file_ext = os.path.splitext(view.file_name())
        
        if file_ext == '.js' :
          self.type = 'nodejs'
        else :
          self.type = 'other'
          
        self.node_tpl   = "var %s = require(%s);"
        self.re_require = re_require
        self.is_node_webkit = False

        if view.find(r'require\(\[', 0 ) or view.find(r'define\(\[\n', 0 ) :
          self.type = 'requirejs'

        elif view.find(re_require,0 ) :
          self.type = 'nodejs'
        elif view.find(r'define\s*\(\s*function\s*\(\s*require\s*,\s*exports\s*,\s*module\s*\)\s*\{',0) :
          # for fcking seajs
          self.type = 'amdjs' 
        if view.find_all(re_require_nw,0 ) :
          self.node_tpl = "var %s = global.require(%s);"
          self.re_require = re_require_nw
          self.is_node_webkit = True

        print 'is nw', self.is_node_webkit, 'type', self.type

        # read from project folders
        _folders = self.view.window().folders()

        suggestions = []
        resolvers   = []

        if len(_folders) != 0 :
          for folder in _folders:
            path_depth = len ( os.path.abspath(folder) ) + len(os.path.sep)
            #create suggestions for all files in the project
            for root, subFolders, files in os.walk(folder, topdown=True):
              #max 3 rescure
              
              if root[ path_depth:].count(os.path.sep) == 4:
                  subFolders[:] = []
                  continue
              if root.startswith(os.path.join(folder, "node_modules")) :
                  continue
              if root.startswith(os.path.join(folder, ".git")):
                  continue
              if root.startswith(os.path.join(folder, ".svn")):
                  continue
              for file in files:

                  # get ext
                  file_name, file_ext = os.path.splitext( file )
                  # js file only
                  if file_name == 'fileinput' :
                    print file
                  if self.type != 'other' and (file_ext != '.js' and file_ext != '.json' ):
                      continue
                  # module index specific 
                  if file == "index.js":
                      resolvers.append(self.resolve_from_file(root, self.type == 'other' ))
                      suggestions.append([os.path.split(root)[1], root])
                      continue
                  # add sug
                  
                  resolvers.append(self.resolve_from_file(os.path.join(root, file),  self.type == 'other' ))
                  suggestions.append([file, root.replace(folder, "", 1) or file])

        if self.type != 'other' and ((self.type == 'requirejs' and self.is_inline_require_region() ) or self.type != 'requirejs' ) :
            #create suggestions for modules in node_modules folder
            [resolvers_from_nm, suggestions_from_nm]     = self.get_suggestion_from_nodemodules()
            resolvers                                   += resolvers_from_nm
            suggestions                                 += suggestions_from_nm

            #create suggestions from buildin modules
            [resolvers_from_native, suggestions_from_nm] = self.get_suggestion_native_modules()
            resolvers                                   += resolvers_from_native
            suggestions                                 += suggestions_from_nm

            #create suggestions from global modules
            [resolvers_from_native, suggestions_from_nm] = self.get_suggestion_from_nodemodules_g()
            resolvers                                   += resolvers_from_native
            suggestions                                 += suggestions_from_nm
        if self.type == 'other' :
          self.view.window().show_quick_panel(suggestions, self.write_path(resolvers, edit))
        else :
          self.view.window().show_quick_panel(suggestions, self.write_require(resolvers, edit))