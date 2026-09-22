# Agent Work Unit Complexity Scoring V1

ENG-02.3 makes cognitive/technical complexity explicit and reproducible.

The score is the weighted sum of 12 closed factors:

- production module +1 each;
- contract/schema family +1 each;
- policy/config family +1 each;
- persistence/checksum boundary +1;
- mathematical/numeric semantics +2;
- temporal/lineage semantics +2;
- cross-domain interface +2 each;
- state-machine/concurrency +2;
- security/trust boundary +2;
- risk/execution permission +3;
- dependency change +1;
- CI/evidence topology change +1.

CI recalculates the score and checks basic under-declaration. ENG-02.3 intentionally
defines no mandatory split threshold; that belongs to ENG-02.4.
