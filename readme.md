This repos now is very different with origin one.

It will check if the  file is a js file, then check if a requirejs module or node module or a node-webkit module, and inert with different require parttern.

Helper to add node.js "require" clause to modules. 

Just press *ctrl+shift+m*, select the file and boom! 

* Windows: ctrl+shift+m
* Linux: ctrl+shift+m
* OSx: ctrl+shift+m

![screencast](http://i.imgur.com/wlOrt.gif)

## load modules

Besides any javascript file you have in your directory, use:

* native: [name] for things like "fs", "net", etc.
* module: [name] for modules inside your node_modules folder
* globle module: [name] for modules inside your $NODE_PATH / %node_path% folder

## other files 

If not in a .js file, this plugin will scane all file in your project folder, create relative path to load.

## Installation

### With [Package Decontrol](https://github.com/jfromaniello/Sublime-Package-Decontrol)

~~~
ssddi456/sublime-node-require
~~~

### With Git

~~~
git clone https://github.com/ssddi456/sublime-node-require.git ./sublime-node-require
~~~

In your sublime text package folder.
