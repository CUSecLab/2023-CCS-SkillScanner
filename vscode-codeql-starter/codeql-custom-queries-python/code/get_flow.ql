/**
 * @name Empty scope
 * @kind problem
 * @problem.severity warning
 * @id python/example/empty-scope
 */

import python
import semmle.python.dataflow.new.TaintTracking
import semmle.python.ApiGraphs


class MyAnalysisConfiguration extends TaintTracking::Configuration {
  MyAnalysisConfiguration() { this = "MyAnalysisConfiguration" }
  override predicate isSource(DataFlow::Node source){
    source.getLocation().toString().indexOf("/zfs/socbd/liao5/real-time-tweet/tweepy/codeql/skills") > -1
    and
    source.getLocation().toString().indexOf(".py") > -1
  }

  override predicate isSink(DataFlow::Node sink){
    sink.getLocation().toString().indexOf("/zfs/socbd/liao5/real-time-tweet/tweepy/codeql/skills") > -1
    and
    sink.getLocation().toString().indexOf(".py") > -1
  }
}

from MyAnalysisConfiguration dataflow
, DataFlow::Node source
, DataFlow::Node sink
where
dataflow.hasFlow(source, sink)
and
dataflow.isSource(source)
and
dataflow.isSink(sink)
select source, "source: $@ \t sink: $@", source, source.toString(), sink, sink.toString()
