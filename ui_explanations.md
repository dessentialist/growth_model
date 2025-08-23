Run Preset (sidebar)
What it runs: A scenario file already on disk: scenarios/<preset>.yaml or .json.
How it’s invoked: We pass --preset <name> to the runner.
What it ignores: Anything you’ve edited in the UI state that you haven’t saved into a scenario file.
When to use: Fast smoke/regression runs of a known preset without touching the editor.
Extras: Honors Debug, Generate plots, and KPI row checkboxes.
Validate, Save, and Run (sidebar)
What it runs: The scenario you’re currently editing in the UI.
How it’s invoked: We first validate the in-memory state, write it to scenarios/<name>.yaml (auto-suffix if needed), then run with --scenario <that path>.
What it includes: Every change you’ve made in Runspecs, Constants, Points, Primary Map, Seeds.
When to use: Iterative editing-and-run workflow.
Validate & Save (main navigation tab)
What it does: Validates your current UI state and lets you save to YAML. It does not run anything.
Preset loader here: Lets you load or duplicate existing scenario files into the editor. Loading a preset here still does not run; it just populates the UI state.
In other words:
Sidebar “Run Preset” runs an existing file by name and ignores unsaved UI edits.
Sidebar “Validate, Save, and Run” runs exactly what you’ve built in the editor (after validation and saving).
The “Validate & Save” tab is for preparing/inspecting files; running is done via the sidebar.