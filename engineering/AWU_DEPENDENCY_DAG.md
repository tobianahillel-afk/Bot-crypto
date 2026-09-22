# Agent Work Unit Dependency DAG

ENG-02.2 adds set-level semantics above the individual AWU contract.

A complete AWU graph must satisfy:

- unique AWU IDs;
- every declared dependency is present in the validated graph;
- no dependency cycles;
- a dependency within the same parent work-item may not come from a later parent task;
- `READY`, `IN_PROGRESS` and `DONE` nodes require every direct predecessor to be `DONE`;
- at most one AWU is `IN_PROGRESS` for a given parent task.

The validator returns a deterministic topological order when the graph is valid.

This does not yet score complexity or split oversized units; those are ENG-02.3 and
ENG-02.4.
