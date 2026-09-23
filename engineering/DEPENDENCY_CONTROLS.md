# Dependency Controls — ENG-04.2

ENG-04.2 deliberately reuses the repository's existing Python dependency model instead of
introducing another package manager.

## Current-lock vulnerability control

The dedicated workflow installs the exact `requirements-dev.lock` and executes the already
declared `pip-audit==2.9.0` with:

```text
-r requirements-dev.lock --disable-pip --strict --progress-spinner off
```

`--disable-pip` prevents dependency re-resolution during the audit. The workflow runs only
when dependency/control files change, on manual dispatch, and once per week so newly published
advisories are still detected even when the lock has not changed.

## Introduced-dependency control

Pull requests additionally run GitHub's public-repository Dependency Review Action:

- version: `v5.0.0`
- exact commit: `a1d282b36b6f3519aa1f3fc636f609c47dddb294`
- fail threshold: `low`
- scopes: runtime + development + unknown
- vulnerability check: enabled
- license check: intentionally deferred to supply-chain governance
- comments: disabled
- warn-only: disabled
- OpenSSF display: disabled here to keep this gate focused

## Manifest integrity

The local zero-network validator requires:

- exact parity between `pyproject.toml [project.optional-dependencies].dev` and
  `requirements-dev.in`;
- `requirements-dev.txt` to contain only `-r requirements-dev.lock`;
- every lock entry to be an exact `name==version` pin;
- each direct dev dependency to exist at the exact same version in the lock;
- no new runtime dependency while this AWU explicitly forbids project dependency changes.

No project dependency version is changed by ENG-04.2.
