/**
 * @name Empty block
 * @kind problem
 * @problem.severity warning
 * @id javascript/example/empty-block
 */

import javascript
import DataFlow
import DataFlow::PathGraph

/*
class MyConfig extends TaintTracking::Configuration {
  MyConfig() { this = "MyConfig" }  
  override predicate isSource(Node node) { node.getFile().toString().indexOf("/home/song/rsc/codeql/skill_for_dataset/src/ddbController.js") > -1 }
  override predicate isSink(Node node) { 
    node.getFile().toString().indexOf("/home/song/rsc/codeql/skill_for_dataset") > -1  
  }}

from MyConfig cfg, PathNode source, PathNode sink
where cfg.hasFlowPath(source, sink)
select source, sink
*/

from ControlFlowNode cfg
where
cfg.getFile().toString().indexOf("/home/song/rsc/codeql/skill_for_dataset") > -1
select cfg




/*
// for ask_value: this.emit(":ask", 'Welcome!')
from ControlFlowNode cfg
where
cfg.getFile().toString().indexOf("/home/song/rsc/codeql/skill_for_dataset") > -1
and
cfg.getAPredecessor().toString() = "this.emit"
and
(
cfg.toString() = "':ask'"
or
cfg.toString() = "':tell'"
)
select cfg
//, cfg.getAPredecessor(), cfg.getASuccessor()




from Token token
where
token.getFile().toString().indexOf("/home/song/rsc/codeql/skill_for_dataset") > -1
and
token.toString() = "this"
and
token.getNextToken().toString() = "."
and
token.getNextToken().getNextToken().toString() = "emit"
and
token.getNextToken().getNextToken().getNextToken().toString() = "("
and
//(
token.getNextToken().getNextToken().getNextToken().getNextToken().toString() = "':ask'"
//or
//token.getNextToken().getNextToken().getNextToken().getNextToken().toString() = "':tell'"
//)

select token,
//token.getNextToken().getNextToken().getNextToken().getNextToken().toString()

token.getNextToken().getNextToken().getNextToken().getNextToken().getNextToken().getNextToken().toString()
*/