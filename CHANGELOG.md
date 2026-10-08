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

### Petrol efficiency correction (2026-10-08)

- Restore the historical efficiency trajectory for five petrol moped/scooter/motorcycle classes, replacing the defective 0.5–2% inputs. Use 18% in 2020, the linear midpoint 18.3665% in 2025, and 18.7331% in 2030; retain triangular ±25% relative uncertainty. Other inputs are unchanged.
- Record all original affected records and the historical Git source. The numerical assumption in the originally cited Cox–Mutel paper remains unverified; this is a provisional engineering prior, not a new empirical calibration.
- Reduce the default 2025 11–35 kW motorcycle result from 103.69 to 5.646 L/100 km. Add six manufacturer screening observations, completed inventory/fuel/CO2 checks and annual checks. Substantial unmatched residuals remain; see [evidence and limitations](docs/petrol_efficiency.rst).

### Known limitations

- Electric-bicycle glider-cost inputs can still produce a negative total cost; the strict expected-failure test remains in place.
- Manufacturer comparisons do not establish new empirical two-wheeler calibration.
- Custom string sample labels can fail alignment in the shared energy calculation; normal numeric sample labels are covered by the petrol regressions.
- The coupled target-range repair was validated for passenger cars; two-wheeler target-range overrides have not received equivalent qualification.

See [validation](docs/validity.rst) and [release preparation](RELEASING.md) for scope and verification instructions.
