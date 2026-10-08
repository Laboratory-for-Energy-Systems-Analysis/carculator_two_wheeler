# Changelog

Notable user-facing changes to `carculator_two_wheeler`. The entry below is prepared for release;
it has not yet been published. Older entries, where present, retain their original record.

## [0.1.1] - Unreleased

### Compatibility and installation

- Require Python 3.12 (`>=3.12,<3.13`); older Python environments must be recreated.
- Use NumPy `>=1.26.4,<2` through the shared runtime.
- Require the stable `carculator_utils>=1.3.6` release, including its export extras.
- Build wheels and source distributions from centralized `pyproject.toml` metadata.
- Keep core model/LCIA use independent of Brightway; install `excel` or `brightway` extras for export. The Brightway extra targets the legacy stack (`bw2io<0.9`, `bw2data<4`, `bw2calc<2`).
- Align documentation versions with the package version and provide complete documentation-build dependencies.

### Model and inventory changes

- Add native 2025 inputs and explicit component-efficiency priors with consistent temporal extensions.
- Apply corrected shared stored-energy, terminal DC and charging boundaries, and mask unavailable configurations consistently.
- Honor custom parameter dictionaries and files, preserve caller-owned arrays, and bound per-cell sizing iterations.
- Correct year-based cost annualization, zero-rate handling and discounted component replacement.
- Add input, mass-balance, labelled-sample, financial and completed model/LCIA regressions.
- Inherit scoped battery overrides, fuel blend accounting, pollutant translation and non-mutating multi-year exports from the shared release.

### Documentation and verification

- Add current installation and executable 2025 quick-start examples, migration notes and a release checklist.
- Record calibration scope, measurement boundaries and numerical consistency separately from empirical validation.
- Verify built wheels and sdist-built wheels, packaged resource hashes, installed tests with export extras and offline core-only model/LCIA smoke runs.

### Release blocker

- The default 2025 `Motorcycle 11-35kW` / `ICEV-p` run uses 1% engine efficiency and returns about 33 MJ/km (104 L/100 km). This physically implausible default was exposed by the release README check; publication is pending a review of the input and its provenance. Passing execution tests do not resolve it.

### Known limitations

- Electric-bicycle glider-cost inputs can still produce a negative total cost; the strict expected-failure test remains in place.
- The recent measurement review does not establish new empirical two-wheeler calibration.
- The coupled target-range repair was validated for passenger cars; two-wheeler target-range overrides have not received equivalent qualification.

See [validation](docs/validity.rst) and [release preparation](RELEASING.md) for scope and verification instructions.
