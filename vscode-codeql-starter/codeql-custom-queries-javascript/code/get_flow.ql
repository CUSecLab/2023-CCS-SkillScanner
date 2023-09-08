/**
 * @name Empty block
 * @kind path-problem
 * @problem.severity warning
 * @id javascript/example/empty-block
 */



import javascript
import DataFlow
import DataFlow::PathGraph


class MyConfig extends TaintTracking::Configuration {
  MyConfig() { this = "MyConfig" }
  override predicate isSource(Node node) { 
    node.getFile().getFileType() = "javascript"
  }

  override predicate isSink(Node node) { 
    node.getFile().getFileType() = "javascript"
  }

  predicate hasAttriFlowPath(SourcePathNode source, SinkPathNode sink){
    source.getNode().getFile() = sink.getNode().getFile()
    and
    source.getNode().getStartLine() = sink.getNode().getStartLine()
    and
    source.getNode().getEndLine() = sink.getNode().getEndLine()
  //  and
  //  source.getNode().getStartColumn() = sink.getNode().getStartColumn()
    and
    source.getNode().getEndColumn() = sink.getNode().getEndColumn() - 2
    and 
    sink.toString().indexOf(" " + source.toString().substring(0,1)) > -1
    and
    sink.toString().indexOf("()") > -1
  }

  predicate hasFuncFlowPath(SourcePathNode source, SinkPathNode sink){
    exists(
    Token token
    |
    token.toString() != ")"
    and
    token.getNextToken().toString() = "."
    and
    token.getNextToken().getNextToken().getNextToken().toString() = "("
    and
    token.getNextToken().getNextToken().getNextToken().getNextToken().toString() != ")"
    and
    source.getNode().getAstNode().getLastToken() = token
    and
    sink.getNode().getAstNode().getLastToken() = token.getNextToken().getNextToken().getNextToken().getNextToken()
    |
    source = source
    and
    sink = sink
    )
  }

  predicate hasDictFlowPath(SourcePathNode source, SinkPathNode sink){
    exists(
    ObjectExpr obj
    |
    obj.getFile().toString().indexOf("/home/song/rsc") > -1  
    and
    obj.getAChild().getParent() = sink.getNode().getAstNode()
    and
    obj.getAChild().getAChild() = source.getNode().getAstNode()
    |
    source = source
    and
    sink = sink
    )
  }

  predicate allFlowPath(SourcePathNode source, SinkPathNode sink){
    hasAttriFlowPath(source, sink)
    or
    hasFuncFlowPath(source, sink)
    or
    hasDictFlowPath(source, sink)
    or
    hasFlowPath(source, sink)
  }
}

from MyConfig cfg, SourcePathNode source, SinkPathNode sink
where 
cfg.hasFlowPath(source, sink)
and
cfg.isSource(source.getNode())
and
cfg.isSink(sink.getNode())
select source.getNode(), source, sink, "source: $@ \t sink: $@", source.getNode(), source.getNode().toString(), sink.getNode(), sink.getNode().toString()
//select source, sink
