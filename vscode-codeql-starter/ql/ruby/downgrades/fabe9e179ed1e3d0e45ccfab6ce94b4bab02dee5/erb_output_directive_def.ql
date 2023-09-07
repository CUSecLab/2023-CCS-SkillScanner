class AstNode extends @erb_ast_node {
  string toString() { none() }
}

class Location extends @location {
  string toString() { none() }
}

from AstNode id, AstNode child, Location loc
where erb_output_directive_def(id, child) and erb_ast_node_info(id, _, _, loc)
select id, child, loc