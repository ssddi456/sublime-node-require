var fs = require('fs');
var path = require('path');
var module_name = process.argv[2];


var module_main_path = require.resolve(module_name);
module_main_path = module_main_path.split(path.sep);
var node_module_index = module_main_path.lastIndexOf('node_modules');

module_main_path = module_main_path.slice(0, node_module_index + 2).join(path.sep);
var package_info = path.join(module_main_path,'package.json');

package_info = JSON.parse(fs.readFileSync(package_info));
var version = package_info.version;
console.log( '~' + version );