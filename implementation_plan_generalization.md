### Migration Plan: Generalize System Dynamics Model

*Current status: Phase 5 completed; migration plan fully implemented.*

---

#### Phase 0 – Baseline Validation
1. **Run full test suite** to capture the current state and produce regression baselines.  
   - Test: `pytest`
2. **Create baseline output CSV** via runner to establish expected KPI behavior.  
   - Test: `python simulate_growth.py --scenario baseline`

---

#### Phase 1 – Introduce “product” terminology alongside “material”
1. **Add new data structures and naming helpers** for `product(s)` while keeping existing `material` references as deprecated aliases.  
2. **Update Phase‑1 data loader and naming utilities** to populate both `lists.products` and `lists.materials`, emitting warnings when legacy keys are used.  
3. **Incremental tests**  
   - `pytest tests/test_phase1_data.py tests/test_naming.py`  
   - `pytest tests/test_phase13_multimaterial.py` – ensures multimaterial scenarios still load.

---

#### Phase 2 – Rename domain references to “product”
1. **Migrate model logic and utilities**:  
   - Replace function/variable names (`material` → `product`) and adjust comments.  
   - Maintain backward‑compatibility stubs that warn on legacy API usage.  
2. **Refactor scenario YAMLs, inputs.json, and any hard‑coded lists** to use `product` keys. Provide a migration script for existing scenario files.  
3. **Update tests & fixtures**: rename references and ensure parameter coverage.  
4. **Incremental tests**  
   - `pytest tests/test_scenario_loader.py tests/test_phase4_model.py tests/test_phase6_gateways.py`  
   - `pytest tests/test_phase13_primary_map_override.py`  
   - Re‑run baseline scenario to confirm KPI CSV is identical aside from renamed columns.

---

#### Phase 3 – Remove Growth‑specific branding
1. **Rename entry points and modules** (`simulate_growth.py` → `simulate_growth.py`; package docstrings, logging, constants).  
2. **Scrub documentation, comments, and installation scripts** for “Growth” branding.  
3. **Incremental tests**  
   - `pytest tests/test_runner_smoke_e2e.py`  
   - `pytest tests/test_phase12_visualization.py tests/test_ui_services.py`  
   - Manually invoke CLI: `python simulate_growth.py --scenario baseline`  

---

#### Phase 4 – Verify user‑customizable sectors and products
1. **Audit UI and scenario loader** to ensure sector/product names are read purely from user inputs with no hard‑coded defaults.  
2. **Add validation and error messages** for missing or duplicate names.  
3. **Add/extend tests** that supply arbitrary sector/product names and confirm they propagate through the SD model, ABM layer, and output CSV.  
   - New test example: `test_custom_product_and_sector_names` verifying dynamic naming.  
4. **Incremental tests**  
   - `pytest tests/test_phase7_runner.py tests/test_phase8_kpis.py`  
   - `pytest tests/test_ui_builder.py tests/test_ui_state_roundtrip.py`

---

#### Phase 5 – Documentation & cleanup
1. **Update README, tutorials, architecture docs** to reflect generalized “Product Growth System” terminology.  
2. **Remove deprecated aliases** once external consumers have migrated; document removal in `CHANGELOG.md`.  
3. **Final regression tests**  
   - `pytest`  
   - Run baseline scenario and compare KPI CSVs to Phase‑0 baseline.

---

### Notes
- Each phase is independently mergeable, enabling incremental releases.  
- Tests listed for a phase are the minimum recommended set; running the full suite after major refactors is advised.  
- Maintain backward compatibility during earlier phases to avoid blocking existing users; only remove deprecated names in Phase 5 after clear notice.
