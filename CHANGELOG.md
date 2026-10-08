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

### Bicycle cost correction (2026-10-08)

- Replace the negative glider-cost intercept for the three BEV bicycle classes with a positive mass-proportional prior: EUR 500 for a reference 12 kg mechanical bicycle, divided by the existing 1.2 reference markup. The price proxy comes from ZIV's 2025 German bicycle market report; transfer to e-bike gliders remains an engineering assumption.
- Apply the coefficients across all native years, retain relative slope uncertainty and preserve other vehicle scopes. Keep motor/battery costs separate; no cost clipping is added.
- Correct the default 2025 `Bicycle <25` purchase cost from −EUR 188.98 to EUR 1,250.49 and total cost from −EUR 0.01499/km to EUR 0.09621/km. The original strict expected failure now passes as a normal regression, with additional uncertainty and discounted-cash-flow checks.
- Verify unchanged mass, energy and LCIA results in completed before/after runs. Record the remaining roughly 51% difference from the German average complete e-bike price; this is not a whole-vehicle market calibration.

### Small-vehicle cost correction (2026-10-08)

- Replace negative glider fits for BEV kick-scooters, petrol mopeds and both small-scooter powertrains with positive scoped priors. Use an Oxelo mechanical-scooter mass/price proxy and frozen reference residuals based on Mash, NIU and Piaggio prices; document source dates, excluded fees and unmatched vehicle specifications.
- Keep battery/motor costs separate, preserve relative slope uncertainty and carry the coefficients consistently across native years. These are provisional assumptions, not independent validation of ownership costs.
- Verify positive costs, discounted cash flows and component-price sensitivity. Complete 24 before/after inventory/LCIA cases and 104 annual cases; physical outputs, inventory matrices and LCIA remain unchanged.
- Keep the unexplained BEV heat-pump charge visible and exclude it from residual calibration pending a separate correction. See [small-vehicle costs](docs/small_vehicle_costs.rst).

### Heat-pump default correction (2026-10-08)

- Remove the inherited EUR 300 cabin heat-pump charge from every BEV two-wheeler default across all native years. Use deterministic zero, including stochastic input sampling; keep explicit user values in the existing purchase-cost calculation.
- Verify a EUR 300 purchase reduction without markup, correct annualization, and unchanged remaining model outputs, inventory matrices and LCIA in 54 completed before/after cases across all nine available BEV sizes and 2020/2025/2030.
- Preserve glider priors and charger assumptions. Default 2025 purchase costs now include EUR 374.26 for the kick-scooter, EUR 950.49 for Bicycle <25 and EUR 1,999.00 for Scooter <4kW. Earlier audit tables remain historical; see [heat-pump costs](docs/heat_pump_costs.rst).

### Kick-scooter charger cost correction (2026-10-08)

- Replace the shared BEV charger price only for the electric kick-scooter with a EUR 70 mode and EUR 40-100 triangular engineering range, informed by NIU replacement-retail listings. Document the undated/current-price proxy, unmatched equipment and distinction from OEM costs.
- Carry the same prior across native years, preserve explicit overrides and leave glider priors, other vehicle classes and physical charger/inventory assumptions unchanged.
- Reduce the 2025 kick-scooter purchase result from EUR 374.26 to EUR 279.91. Verify completed costs at uncertainty endpoints, cost annualization, 24 before/after inventory/LCIA cases with three control classes, and 26 annual runs. See [charger evidence and limitations](docs/kick_scooter_charger_costs.rst).

### BEV sizing correction (2026-10-08)

- Converge range-driven battery capacity, vehicle mass and energy demand together, with bounded per-cell checks. The 2025 small scooter now needs 5.594 kWh for a 200 km target, instead of the inconsistent 5.373 kWh result.
- Preserve range/capacity/mass precedence and scoped overrides. Apply consumption overrides after building the energy trace, propagate fixed curb mass through component sizing, and align labelled samples.
- Test four chemistries, 2020/2025/2030 and all available BEV sizes, including independent mass/energy balances, fresh capacity-constrained runs and completed battery/electricity inventory coefficients. Default outputs remain unchanged across all size/powertrain combinations in those three years. See [battery sizing](docs/bev_sizing.rst); this is a physical-consistency repair, not empirical recalibration.

### Battery replacement correction (2026-10-08)

- Remove the mandatory one-replacement minimum for two-wheelers. Allow zero when lifetime throughput fits within the first battery life; retain fractional allocation and the existing cap of three replacements.
- Preserve the initial battery, sizing, energy use and purchase costs. Propagate the corrected factor through replacement costs, battery supply, disposal and LCIA. All nine available BEV sizes have zero replacements with default 2020/2025/2030 inputs.
- Verify 27 paired before/after default cases and completed zero/fractional/multiple/capped replacement scenarios. The 2025 kick-scooter battery supply falls from 3.2 to 1.6 kg and total modelled cost from EUR 0.20450 to EUR 0.17331/vkm. Earlier audit tables retain their historical results. See [replacement accounting](docs/battery_replacements.rst).
- Keep the deliberate minimum-one-replacement bus assumption unchanged and documented in `carculator_bus`.

### Known limitations

- Negative glider costs in the repaired bicycle and small-vehicle scopes are resolved, but charger costs for other classes, human-only bicycle inputs, complete e-bike costs and currency-year consistency still require review. See [bicycle costs](docs/bicycle_costs.rst) and [small-vehicle costs](docs/small_vehicle_costs.rst).
- Manufacturer comparisons do not establish new empirical two-wheeler calibration.

See [validation](docs/validity.rst) and [release preparation](RELEASING.md) for scope and verification instructions.
