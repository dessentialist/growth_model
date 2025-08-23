# Product Growth System UI - Usage Explanations

This document explains how the different UI controls work in the Product Growth System, a flexible, industry-agnostic simulation tool that can model any sectors and products you define.

## Run Preset (sidebar)
**What it runs**: A scenario file already on disk: `scenarios/<preset>.yaml` or `.json`.
**How it's invoked**: We pass `--preset <name>` to the runner.
**What it ignores**: Anything you've edited in the UI state that you haven't saved into a scenario file.
**When to use**: Fast smoke/regression runs of a known preset without touching the editor.
**Extras**: Honors Debug, Generate plots, and KPI row checkboxes.

## Validate, Save, and Run (sidebar)
**What it runs**: The scenario you're currently editing in the UI.
**How it's invoked**: We first validate the in-memory state, write it to `scenarios/<name>.yaml` (auto-suffix if needed), then run with `--scenario <that path>`.
**What it includes**: Every change you've made in Runspecs, Constants, Points, Primary Map, Seeds.
**When to use**: Iterative editing-and-run workflow.

## Validate & Save (main navigation tab)
**What it does**: Validates your current UI state and lets you save to YAML. It does not run anything.
**Preset loader here**: Lets you load or duplicate existing scenario files into the editor. Loading a preset here still does not run; it just populates the UI state.

## Key UI Features for Industry Flexibility

The UI is designed to work with any sectors and products you configure:

- **Runspecs**: Set time horizons and anchor modes for your specific industry needs
- **Constants**: Override parameters for any sectors or products defined in your inputs
- **Points**: Configure time-varying price and capacity data for your products
- **Primary Map**: Define which sectors use which products and when they start
- **Seeds**: Set initial conditions for existing clients in your market

## In other words:
- **Sidebar "Run Preset"** runs an existing file by name and ignores unsaved UI edits.
- **Sidebar "Validate, Save, and Run"** runs exactly what you've built in the editor (after validation and saving).
- **The "Validate & Save" tab** is for preparing/inspecting files; running is done via the sidebar.

## Industry Customization
The system automatically adapts to your configuration:
- Define any sectors (e.g., "Manufacturing", "Healthcare", "Technology")
- Define any products (e.g., "Software Licenses", "Medical Devices", "Cloud Services")
- Set industry-specific parameters and market dynamics
- No hard-coded assumptions about specific industries or product types