import sublime
import sublime_plugin
import os
from subprocess import Popen, PIPE

import json
import string
import re
import sys

from subprocess import Popen, PIPE

pkg_path = os.path.abspath(os.path.dirname(__file__))

python_version = sys.version_info[0]

if python_version == 3 :
  from . import last_package_version
  from . import suggestion_from_folder
  from . import popen
else:
  import popen
  import last_package_version
  import suggestion_from_folder

re_require = r'(^.*var\s\w+\s*=\s*require\(([^\(\)]+)\).*$)'
re_require_nw = r'(^.*var\s\w+\s*=\s*global\.require\([^\(\)]+\)$)'
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

    def write_require(self, resolvers):
      def write(index):
        if index == -1:
            return

        self.view.run_command('write_require', { 'resolvers' : resolvers, 'index' : index })

      return write

    def write_path ( self, resolvers ):
      def write( index ) :
        if index == -1 :
          return
        self.view.run_command('write_path', { 'resolvers' : resolvers, 'index' : index })
      return write

    def find_package_json(self):
        resolvers = []
        suggestions = []
        current_file_dirs = self.full_name.split(os.path.sep)
        current_dir = os.path.split(self.full_name)[0]
        if len(self.window.folders())!= 0 :
            for x in range(len(self.window.folders()[0].split(os.path.sep)), len(current_file_dirs)):
                candidate = os.path.join(current_dir, "package.json")
                
                if os.path.isfile(candidate) : 
                    return candidate

                current_dir = os.path.split(current_dir)[0]
        return False

    def update_package_json(self, package_json_file_path, module_name):

      package_file = open(package_json_file_path, 'r')
      package_info = json.loads(package_file.read())
      package_file.close()

      if "dependencies" in package_info :
        dependencies = package_info["dependencies"]
      else :
        dependencies = {}

      if module_name in dependencies : 
        return
      else : 
        dependencies[module_name] = last_package_version.get_module_last_version(module_name)

      package_info["dependencies"] = dependencies

      package_file = open(package_json_file_path, 'w')
      package_file.write(json.dumps(package_info, indent=2, sort_keys=False))
      package_file.close()


    def get_suggestion_from_nodemodules(self):
        resolvers = []
        suggestions = []
        current_file_dirs = self.full_name.split(os.path.sep)
        current_dir = os.path.split(self.full_name)[0]
        if len(self.window.folders())!= 0 :
          for x in range(len(self.window.folders()[0].split(os.path.sep)), len(current_file_dirs)):
              candidate = os.path.join(current_dir, "node_modules")
              if os.path.exists(candidate):
                  for dir in [name for name in os.listdir(candidate)
                                   if os.path.isdir(os.path.join(candidate, name)) and name != ".bin"]:
                      resolvers.append([dir, dir, 'is_installed'])
                      suggestions.append("module: " + dir)
                  break
              current_dir = os.path.split(current_dir)[0]
        return [resolvers, suggestions]

    def get_suggestion_from_nodemodules_g(self):
        resolvers = []
        suggestions =[]
        pathes = [os.environ.get('NODE_PATH')]
        for _path in pathes :
          if _path != None :
            for dir in [ name for name in os.listdir(_path)
                              if os.path.isdir(os.path.join(_path, name)) and name != ".bin"]:
              resolvers.append([dir, dir, 'is_global' ])
              suggestions.append("global module: "+ dir )
        return [resolvers, suggestions]
        
    def get_suggestion_native_modules(self):
        path = os.path
        NODE_MODULES_LIST = path.join(pkg_path,'node_modules.list')
        try:
            if os.path.exists(NODE_MODULES_LIST) :
                print('cache file exists')
                source = open(NODE_MODULES_LIST)
                results= json.loads(source.read())
                source.close()
            else :
                # load native node modules from node
                jsresult = popen.get_node_output(['node',
                  path.join(pkg_path, 'node_scripts/get_native_bindings.js')]);

                jsresult = jsresult.strip().replace("'", '"')

                # write list to cache file
                results = json.loads(jsresult)
                source = open(NODE_MODULES_LIST,'w')
                source.write(jsresult)
                source.close()
                print('write cache file success')

            result = [
                        [[ni, ni, 'is_native'] for ni in results],
                        ["native: " + ni for ni in results]
                      ]
            return result
        
        except Exception:
          print('load native bindings fail')
          return [[], []]

    def type_check( self ):
      view = self.view

      self.full_name = view.file_name()
      self.window = view.window()

      file_name, file_ext = os.path.splitext( self.full_name )


      if file_ext in ['.js', '.ts'] :
        self.type = 'nodejs'
      elif file_ext in ['.es6', '.jsx'] :
        self.type = 'es6'
      else :
        self.type = 'other'
        
      self.node_tpl   = "var %s = require(%s);"
      self.re_require = re_require
      self.is_node_webkit = False

      if view.find(r'require\(\[', 0 ) or view.find(r'define\(\[', 0 ) :
        self.type = 'requirejs'

      elif view.find(re_require,0 ) :
        self.type = 'nodejs'
      elif view.find(r'define\s*\(\s*function\s*\(\s*require\s*,\s*exports\s*,\s*module\s*\)\s*\{',0) :
        # for fcking seajs
        self.type = 'commonjs' 
      elif self.type == 'nodejs' and view.find(r'^\s*(export|import) ', 0):
        self.type = 'es6'

      if self.type == 'es6' : 
        self.node_tpl   = "import * from %s = require(%s);"
        self.re_require = r'import .+ from ([^;]+);|import ([^;]+);'

      if view.find(re_require_nw,0 ) :
        self.node_tpl = "var %s = global.require(%s);"
        self.re_require = re_require_nw
        self.is_node_webkit = True

      print( 'is nw', self.is_node_webkit, 'type', self.type)

    def get_current_require( self ):
      view = self.view
      if self.type == 'nodejs' or self.type == 'commonjs' :
        '''
        [[val : 'pos', pos: range (whole line)]]
        '''
        ret = []
        require_rangs = self.view.find_all( self.re_require )
        for r_range in require_rangs :
          module_declare = view.substr(r_range)
          module_declare = re.search(re_require, module_declare)

          if module_declare.group(2):
            ret.append([ module_declare.group(2)[1:-1],r_range])
          elif module_declare.group(1):
            ret.append([ module_declare.group(1)[1:-1],r_range])

        return ret
      elif self.type == 'requirejs' : 
        '''
        [[val : 'pos', pos: range (with quote and comma and crlf), declare_pos:range]]
        '''
        ret = []

        path_point   = ( view.find(r'require\s*\(\[', 0 ) or view.find(r'define\s*\(\[', 0 ) ).b
        delimiter    = view.find( r'\]\s*,\s*function\s*\(', path_point)
        module_point = delimiter.b
        module_end   = view.find(r'\)\s*\{', module_point).a

        paths_region = sublime.Region(path_point,delimiter.a)
        modules_region = sublime.Region(module_point,module_end)
        r_paths = view.substr( paths_region )
        r_declares=view.substr( modules_region )

        if r_paths.strip() == '' :
          return ret

        print(  r_paths.split(r','))
        r_paths = r_paths.split(r',')
        r_declares = r_declares.split(r',')

        last_path_point = paths_region.a
        last_module_point = modules_region.a
        idx = 0
        for r_path in r_paths :
          r_declare = r_declares[idx]
          _last_path_point   = last_path_point + len(r_path) + 1
          _last_module_point = last_module_point + len(r_declare) + 1
          
          print( r_path, r_declare)
          ret.append([r_path.strip(), 
                      sublime.Region( last_path_point,   _last_path_point),
                      sublime.Region( last_module_point, _last_module_point)
                    ])

          last_path_point   = _last_path_point
          last_module_point = _last_module_point
          idx+=1
        return ret
      else:
        return []
    def run(self, edit):
      view = self.view
      self.full_name = view.file_name()

      if not self.full_name :
        return

      self.window = view.window()

      self.type_check()        

      # read from project folders
      _folders = self.window.folders()

      suggestions, resolvers = suggestion_from_folder.require_from_folder( _folders, self.full_name, self.type )

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
      
      if self.type == 'requirejs' :
        # hard code amd module-id
        hard_code_module_ids = {
          'jquery' : '$',
          'ko': 'ko',
          'underscore' : '__'
        }
        for module_id, module_name in hard_code_module_ids.items() :
          resolvers.append([hard_code_module_ids[module_id],module_id, 'is_hard_code'])
          suggestions.append('solid :: ' + module_id )

      if self.type == 'other' :
        self.window.show_quick_panel(suggestions, self.write_path(resolvers))
      else :
        self.window.show_quick_panel(suggestions, self.write_require(resolvers))


class WriteRequireCommand(RequireNodeCommand):

  def run( self, edit, resolvers, index):

    self.type_check()

    view = self.view

    def lodash(name):
      if name.find("-") != -1:
        name = "_".join(name.split("-"))
      return name

    def camelcase(name):
      name = string.capwords(name, '-').replace('-', '')
      name = name[0].lower() + name[1::]
      return name

    def get_path(path):
        settings = sublime.load_settings(__name__ + '.sublime-settings')
        quotes_type = settings.get('quotes_type')
        quote = "'"
        if quotes_type == "double":
            quote = "\""

        path, ext_name = os.path.splitext(path)
        return quote + path + quote

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

      path_point     = ( view.find(r'require\s*\(\[', 0 ) or view.find(r'define\s*\(\[', 0 ) ).b
      # check if has load a module
      delimiter = view.find( r'\]\s*,\s*function\s*\(', path_point)
      path_block_end = delimiter.a
      paths_region = sublime.Region(path_point, path_block_end)
      paths = view.substr( paths_region )
      has_module = False
      if paths.strip() == '' :
        view.replace(edit, paths_region, '')
        view.insert(edit, path_point, '\n\t'+module_path +'\n')
      else:
        has_module = True
        view.insert(edit, path_point, '\n\t'+module_path +',')

      delimiter = view.find( r'\]\s*,\s*function\s*\(', path_point)
      module_point = delimiter.b
      module_end   = view.find(r'\)\s*\{', module_point).a
      if not has_module :
        view.replace(edit, sublime.Region(module_point,module_end),'')
        view.insert(edit, module_point, '\n\t'+module_name +'\n')
      else:
        view.insert(edit, module_point, '\n\t'+module_name +',')

    def write_es6_import( module_candidate_name, module_rel_path, module_flag ):
      lens = 0
      spos = 0
      region = view.sel()[0]
      line   = view.line(region)

      if module_flag == 'is_relative_file' :
        # parse file exports

        path = os.path


        module_export_names = popen.get_node_output(['node', 
            path.normpath(path.join(pkg_path,'node_scripts/get_exports_names.js')),
            path.normpath(path.join(path.dirname(self.full_name), module_rel_path))
          ])

        if len(module_export_names) == 0 :
          module_export_names = module_candidate_name
        else:
          module_export_names = module_export_names.strip()

        print('module_export_names', module_export_names)

        require_directive = 'import {0} from {1};'.format(module_export_names, get_path(module_rel_path))
      else :
        require_directive = 'import {0} from {1};'.format(module_candidate_name, get_path(module_rel_path))

      print(require_directive)


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


    [module_candidate_name, module_rel_path, module_flag] = resolvers[index]

    module_candidate_name = camelcase(module_candidate_name)

    module_info = (module_candidate_name, get_path(module_rel_path))

    if self.type == 'nodejs' or self.type == 'commonjs':
      require_directive = self.node_tpl % module_info

      write_node_require( require_directive )

      package_json = self.find_package_json()

      is_global_module =  module_flag == 'is_global'

      if package_json and is_global_module:

        self.update_package_json(package_json, module_rel_path)

    elif self.type == 'requirejs' :
      if self.is_node_webkit :
        if self.is_inline_require_region() :
          write_node_require( require_directive )
          return
      
      require_directive = self.node_tpl % module_info

      write_requirejs( module_candidate_name, module_rel_path )

    elif self.type == 'es6':

      write_es6_import( module_candidate_name, module_rel_path, module_flag )

    package_json = self.find_package_json()

    is_global_module =  module_flag == 'is_global'

    if package_json and is_global_module:

      self.update_package_json(package_json, module_rel_path)


class WritePathCommand(RequireNodeCommand):
  def run( self, edit, resolvers, index):
    [module_candidate_name, module_rel_path, module_flag] = resolvers[index]
    for sel in self.view.sel() :
      self.view.insert(edit, sel.a, module_rel_path)


class DeRequireNodeExecCommand(RequireNodeCommand):
  def run(self, edit, index):
    self.type_check()
    requires = self.get_current_require()

    # todos make

    if self.type == 'requirejs':
      req = requires[index]

      # last item should remove leading comma, but not what is follow
      if req == requires[-1] :
        req_1_a = req[1].a
        req_2_a = req[2].a
        if index != 0 :
          req_1_a -= 1
          req_2_a -= 1

        req_1_b = req[1].b - 2
        req_2_b = req[2].b - 2

        req[1] = sublime.Region( req_1_a, req_1_b)
        req[2] = sublime.Region( req_2_a, req_2_b)

      self.view.replace(edit, req[2], '')
      self.view.replace(edit, req[1], '')

class DeRequireNodeCommand(RequireNodeCommand):
  def run(self, edit):
    view = self.view
    self.type_check()
    requires = self.get_current_require()
    
    def delete_req ( index ):
      if index == -1:
        return
      self.view.run_command('de_require_node_exec', { 'index' : index})

    self.window.show_quick_panel([r_path[0].strip('"\'') for r_path in requires], delete_req)

class GoToRequireCommand(RequireNodeCommand):
  def run(self, edit):
    view = self.view
    self.full_name = view.file_name();
    self.window = view.window()

    self.type_check()
    requires = self.get_current_require()

    def goto_require(index):
      if index == -1:
        return

      r_path = requires[index][0].strip("'")
      target_file = os.path.join( os.path.split( self.full_name)[0], r_path + '.js' )
      print( 'target file:' +  target_file)

      if os.path.isfile( target_file ) :
        self.window.open_file( target_file )

    self.window.show_quick_panel([r_path[0].strip('"\'') for r_path in requires], goto_require)
