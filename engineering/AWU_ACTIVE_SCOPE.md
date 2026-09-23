# Active AWU Scope Enforcement

ENG-02.7 makes the **active Agent Work Unit** the executable Git boundary.

Resolution is fail-closed:

1. read permanent `project_state.json`;
2. scan `engineering/work_units/*.json`;
3. require exactly one `IN_PROGRESS` AWU;
4. require its parent lot/task/manifest to match permanent state;
5. require the AWU allowlist to stay inside the parent work-item allowlist;
6. validate AWU contract, complexity, split, risk and context;
7. diff `scope_base_sha...HEAD`;
8. require every changed path inside AWU allowlist and outside AWU forbidden paths.

The parent ENG manifest remains an upper bound. It can never widen an active AWU.

Task transitions must atomically close the old active AWU and activate the next task's AWU
before AWU-aware CI can pass.
