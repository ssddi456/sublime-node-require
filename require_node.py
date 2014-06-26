import sublime
import sublime_plugin
import os
from subprocess import Popen, PIPE
from tempfile import SpooledTemporaryFile as tempfile
import json
import string
import re
import suggestion_from_folder

pkg_path = os.path.abspath(os.path.dirname(__file__))
re_require = r'(^.*var\s\w+\s*=\s*require\([^\(\)]*\).*$)'
re_require_nw = r'(^.*var\s\w+\s*=\s*global\.require\([^\(\)]*\)$)'
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

          view.end_edit(_edit)

        def write(index):
            if index == -1:
                return
            [module_candidate_name, module_rel_path] = resolvers[index]()

            if module_candidate_name.find("-") != -1:
                upperWords = [string.capitalize(word) for word in module_candidate_name.split("-")[1::]]
                module_candidate_name = string.join(module_candidate_name.split("-")[0:1] + upperWords, "")

            require_directive = self.node_tpl % (module_candidate_name, get_path(module_rel_path))

            if self.type == 'nodejs' or self.type == 'commonjs':
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
        if index == -1 :
          return

        [module_candidate_name, module_rel_path] = resolvers[index]()
        for sel in self.view.sel() :
          self.view.insert(edit, sel.a, module_rel_path)
      return write

    def get_suggestion_from_nodemodules(self):
        resolvers = []
        suggestions = []
        current_file_dirs = self.full_name.split(os.path.sep)
        current_dir = os.path.split(self.full_name)[0]
        if len(self.window.folders())!= 0 :
          for x in range(len(self.window.folders()[0].split(os.path.sep)), len(current_file_dirs))[::-1]:
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

    def type_check( self ):
      file_name, file_ext = os.path.splitext( self.full_name )
      view = self.view

      if file_ext == '.js' :
        self.type = 'nodejs'
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
      if view.find(re_require_nw,0 ) :
        self.node_tpl = "var %s = global.require(%s);"
        self.re_require = re_require_nw
        self.is_node_webkit = True

      print 'is nw', self.is_node_webkit, 'type', self.type

    def get_current_require( self ):
      view = self.view
      if self.type == 'nodejs' or self.type == 'commonjs' :
        '''
        [[val : 'pos', pos: range (whole line)]]
        '''
        ret = []
        require_rangs = self.view.find_all( self.re_require )
        for r_range in require_rangs :
          ret.append([ view.substr(r_range),r_range])
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

        print  r_paths.split(r',')
        r_paths = r_paths.split(r',')
        r_declares = r_declares.split(r',')

        last_path_point = paths_region.a
        last_module_point = modules_region.a
        idx = 0
        for r_path in r_paths :
          r_declare = r_declares[idx]
          _last_path_point   = last_path_point + len(r_path) + 1
          _last_module_point = last_module_point + len(r_declare) + 1
          
          print r_path, r_declare
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
          'knockout': 'ko',
          'underscore' : '__'
        }
        for module_id, module_name in hard_code_module_ids.items() :
          resolvers.append(lambda dir=module_id: [hard_code_module_ids[dir],dir])
          suggestions.append('solid :: ' + module_id )

      if self.type == 'other' :
        self.window.show_quick_panel(suggestions, self.write_path(resolvers, edit))
      else :
        print suggestions
        self.window.show_quick_panel(suggestions, self.write_require(resolvers, edit))

class DeRequireNodeCommand(RequireNodeCommand):
  def run(self, edit):
    view = self.view
    self.full_name = view.file_name()
    self.window = view.window()

    self.type_check()
    requires = self.get_current_require()
    
    def delete_req ( index ):
      if index == -1:
        return
      _edit = view.begin_edit()

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

        view.replace(_edit, req[2],'')
        view.replace(_edit, req[1],'')

      view.end_edit(_edit)

    self.window.show_quick_panel([r_path[0] for r_path in requires], delete_req)

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
      print 'target file:' +  target_file

      if os.path.isfile( target_file ) :
        self.window.open_file( target_file )

    self.window.show_quick_panel([r_path[0] for r_path in requires], goto_require)
