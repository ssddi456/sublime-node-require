import os

def require_from_folder( _folders, cur, rtype="" ):
  resolvers   = []
  suggestions = []

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
        if root.startswith(os.path.join(folder, ".")):
            continue
        for file in files:

          # get ext
          file_name, file_ext = os.path.splitext( file )
          # js file only
          if file_name == 'fileinput' :
            print file
          if rtype != 'other' and (file_ext != '.js' and file_ext != '.json' ):
              continue
          # module index specific 
          if file == "index.js":
              resolvers.append  ( resolve_from_file (cur, root, rtype == 'other' ))
              suggestions.append( [os.path.split(root)[1], root])
              continue
          # add sug
          
          resolvers.append(resolve_from_file(cur, os.path.join(root, file),  rtype == 'other' ))
          suggestions.append([ file, root.replace(folder, "", 1) or file ])
  return suggestions, resolvers

def resolve_from_file( cur, full_path, with_ext):
  def resolve():
    file_wo_ext = os.path.splitext(full_path)[0]
    module_candidate_name = os.path.basename(file_wo_ext).replace(".", "")
    dir_name =  os.path.dirname(cur)

    if with_ext : 
      module_rel_path = os.path.relpath(full_path, dir_name)
    else :
      module_rel_path = os.path.relpath(file_wo_ext, dir_name)

    if module_rel_path[:3] != ".." + os.path.sep:
        module_rel_path = "." + os.path.sep + module_rel_path

    return [module_candidate_name, module_rel_path.replace(os.path.sep, "/"), 'is_relative_file']
  return resolve