var argv = process.argv;

var fs = require('fs');
var path    = require('path');
var estraverse = require('estraverse');
var esprima = require('esprima');

var target_file= argv[2];
try{
  var ast = esprima.parse(fs.readFileSync(target_file,'utf8'), { sourceType: 'module' });
} catch(e){
  console.log('');
  console.error(e);
  process.exit(0);
}

console.error(target_file);

var export_node_types = [

                    // static analise will not go that far
                    'ExportAllDeclaration',
                    // for defaults
                    'ExportDefaultDeclaration',
                    'ExportNamedDeclaration',
                    'ExportSpecifier'
                  ];

var has_default = false;
var names = [];


function look_for_short_declare(root, count) {
  count = count || 0;
  if( count > 100 ){
    console.error('wtf?');
    return;
  }

  root.properties.forEach(( node ) => {
    if(　node.shorthand ){
      names.push(node.key.name); 
    } else {
      look_for_short_declare(node.value, count + 1);
    }
  });
}

estraverse.traverse(ast,{
  enter : (node, parent) => {
    if( node.type == 'ExportDefaultDeclaration' ){
      has_default = true;
    } else if( node.type == 'ExportNamedDeclaration' ){
      if( node.declaration  ){
        if( node.declaration.declarations ){
          node.declaration.declarations.forEach(( node )=>{
            var id = node.id;
            if( id.type == 'Identifier' ){
              names.push(node.id.name)
            } else if( id.properties && id.properties.length ){

              //
              // object patterns
              // 递归查找shorthand的property
              //
              look_for_short_declare(id);
             }
          })
        } else {
          names.push(node.declaration.id.name);
        }
      } 
      if( node.specifiers && node.specifiers.length ){
        console.error(JSON.stringify(node.declaration))
        node.specifiers.forEach(( node )=>{
          names.push(node.exported.name)
        });
      }
    }
  }
});

console.error('has_default', has_default);
var res = ( has_default ? 'default' : '' ) 
        + ( has_default && names.length ? ', ' : '' )
        + ( names.length ? '{ ' + names.join(', ' ) + ' }': '');

console.log(res + '');
process.exit(0);
