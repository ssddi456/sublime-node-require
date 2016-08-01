This repos now is very different with origin one.

It will check if the  file is a js file, then check if a requirejs module or node module or a node-webkit module, and inert with different require parttern.

Helper to add node.js "require" clause to modules. 

Just press *ctrl+shift+m*, select the file and boom! 

* Windows: ctrl+shift+m
* Linux: ctrl+shift+m
* OSx: ctrl+shift+m

![screencast](http://i.imgur.com/wlOrt.gif)


## requirements

nodejs > 4.x 

estraverse

esprima


## install

### With Git

the sublime text custom plugins folder is ```Data/Packages```

```cd %sublime_root%/Data/Packages/```

```git clone https://github.com/ssddi456/sublime-node-require.git```

```cd sublime-node-require```

```npm install``` ( for nodejs 6.x  modules should install locally)


### With [Package Decontrol](https://github.com/jfromaniello/Sublime-Package-Decontrol)

sublimetext2 only

~~~
ssddi456/sublime-node-require
~~~

then enjoy.


## load modules

Besides any javascript file you have in your directory :

* native: [name] for things like "fs", "net", etc.
* module: [name] for modules inside your node_modules folder
* globle module: [name] for modules inside your $NODE_PATH / %node_path% folder
* [name] for local files in your project

for es6 files (.es6|.jsx by default and other with ```import```|```export``` statments), will check imported file's exports, and list all exported names.

## other files 

If not in a .js file, this plugin will scane all file in your project folder, create relative path to load.

## goto file 

```[add require]go to require module``` will bring you to the required module

## remove require

```[add require]remove require``` will remove the select required module

## Trouble shooting

If node native module can not be found in suggestions, try specific your node with ```node_path``` in ```require_node.sublime-settings```