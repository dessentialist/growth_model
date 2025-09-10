# Product Growth System UI - Complete Usage Guide

This document explains the comprehensive 10-tab UI system for the Product Growth System, a flexible, industry-agnostic simulation tool that can model any sectors and products you define.

## 🏗️ Current 10-Tab UI Structure

The UI provides a modern, intuitive interface with comprehensive scenario management capabilities:

### **Tab 1: Simulation Definitions**
**Purpose**: Manage the foundational market, sector, and product lists that define your simulation universe.

**Features**:
- **Market List Management**: Add, edit, and delete market definitions (e.g., "Global", "US", "EU")
- **Sector List Management**: Define industry sectors (e.g., "Manufacturing", "Healthcare", "Technology")
- **Product List Management**: Specify products and materials (e.g., "Software Licenses", "Medical Devices")
- **Table-Based Input**: Modern `st.data_editor()` interface for easy list management
- **Save Button Protection**: Changes must be explicitly saved to prevent accidental data loss
- **Dynamic Content**: Lists update in real-time across all other tabs

**When to Use**: Start here to define your industry structure before configuring scenarios.

### **Tab 2: Simulation Specs** (Phase 1)
**Purpose**: Configure runtime parameters and manage scenarios.

**Features**:
- **Runtime Controls**: Set start time, stop time, and time step (dt)
- **Anchor Mode**: Choose between "sector" or "sm"
- **Scenario Management UX (explicit)**:
  - **Current scenario** status displayed
  - **Load existing**: select from "Available scenarios (to load)" and click "Load Selected Scenario"
  - **Overwrite current**: button directly under Load; saves in-place to the currently loaded scenario
  - **Save as New**: enter "New scenario name" and click to create a new YAML (guarded against duplicates)

**Workflows**:
1. Load existing → pick from dropdown → Load Selected Scenario
2. Save changes back → Save (Overwrite current: <name>)
3. Create new → enter New scenario name → Save as New

### **Tab 3: Primary Mapping**
**Purpose**: Define which sectors use which products and when they start using them.

**Features**:
- **Sector-Product Mapping**: Visual interface for mapping sectors to products
- **Start Year Configuration**: Set when each sector-product combination begins
- **Mapping Insights**: Real-time analysis of proposed changes
- **Dynamic Table Generation**: Tables update automatically based on list changes
- **Save Button Protection**: All mapping changes must be explicitly saved
- **Change Tracking**: Visual indicators for unsaved changes

**When to Use**: After defining your sectors and products, map their relationships.

Note on save semantics: On save, the UI writes a complete snapshot of `overrides.primary_map` for all sectors that exactly matches the Primary Mapping tab. Sectors with no selected products are saved with empty lists, preventing fallback to the baseline mapping in `inputs.json`.

### **Tab 4: Seeds**
**Purpose**: Configure initial seeding for anchor clients and direct clients.

**Features**:
- **SM-Mode Support**: Configure active anchor clients and elapsed quarters per sector-product combination
- **Sector-Mode Support**: Configure sector-level seeding (legacy mode)
- **Primary Mapping Integration**: Only shows combinations defined in your Primary Mapping
- **Case-Insensitive Lookup**: Robust handling of capitalization differences
- **Active Anchor Clients**: Set number of active clients at simulation start (t0)
- **Elapsed Quarters**: Configure aging since client activation (quarters)
- **Completed Projects**: Set backlog of completed projects at t0
- **Direct Clients**: Configure direct client counts per product
- **Dynamic Content**: Interface adapts based on anchor mode and primary mapping

**When to Use**: Set up the initial state of your simulation with pre-existing clients and their history.

### **Tab 5: Client Revenue**
**Purpose**: Configure comprehensive client revenue parameters (20 total parameters).

**Features**:
- **Two Subtabs**: Market Activation and Orders for organized parameter management
- **Market Activation Parameters (9)**: 
  - anchor_start_year, anchor_client_activation_delay
  - anchor_lead_generation_rate, lead_to_pc_conversion_rate
  - project_generation_rate, max_projects_per_pc, project_duration
  - projects_to_client_conversion, ATAM
- **Orders Parameters (11)**:
  - Phase durations: initial_phase_duration, ramp_phase_duration
  - Requirement rates: initial_requirement_rate, ramp_requirement_rate, steady_requirement_rate
  - Growth rates: initial_req_growth, ramp_req_growth, steady_req_growth
  - Timing: requirement_to_order_lag
  - Overrides: ramp_requirement_rate_override, steady_requirement_rate_override
  - Limits: requirement_limit_multiplier
- **Dynamic Content**: Tables populate based on primary mapping selections
- **Reset Functionality**: Separate reset buttons for each subtab
- **Table-Based Input**: Modern data editor with Enter-to-commit behavior
- **Per-Sector-Product Organization**: Parameters organized by sector-product combinations

**When to Use**: Configure detailed client behavior and revenue generation parameters.

### **Tab 6: Direct Market Revenue**
**Purpose**: Set product-specific direct market revenue parameters (9 parameters).

**Features**:
- **Two Subtabs**: Market Activation and Orders for organized parameter management
- **Market Activation Parameters (5)**:
  - lead_start_year, inbound_lead_generation_rate, outbound_lead_generation_rate
  - lead_to_c_conversion_rate, TAM
- **Orders Parameters (4)**:
  - lead_to_requirement_delay, requirement_to_fulfilment_delay
  - avg_order_quantity_initial, client_requirement_growth
  - requirement_limit_multiplier
- **Dynamic Content**: Tables update with product list changes
- **Reset Functionality**: Separate reset buttons for each subtab
- **Table-Based Input**: Modern data editor with Enter-to-commit behavior
- **Product-Specific Organization**: Parameters organized by individual products


**When to Use**: Configure direct market revenue streams for each product.

### **Tab 7: Lookup Points**
**Purpose**: Configure time-series data for production capacity and pricing.

**Features**:
- **Production Capacity Tables**: Maximum capacity per product per year (max_capacity_<product>)
- **Pricing Tables**: Price per unit per product per year (price_<product>)
- **Year-Based Structure**: Years as rows, products as columns for easy editing
- **Dynamic Year Management**: Add new years with number input and "Add row" buttons
- **Reset Functionality**: Separate reset buttons for capacity and pricing tables
- **Hold-Last Policy**: Model automatically handles per-quarter scaling and hold-last-value policy
- **Table-Based Input**: Modern data editor with dynamic row management
- **Auto-Sorting**: Years automatically sorted when new rows are added

**When to Use**: Set capacity constraints and pricing strategies over time.

### **Tab 8: Runner**
**Purpose**: Execute scenarios and monitor simulation progress.

**Features**:
- **Output File Naming**: Custom output file name for results CSV (independent of scenario name)
- **Scenario Validation**: Validate current configuration before execution
- **Execution Options**: 
  - Debug logs (verbose runner logging)
- **Run Controls**: Start/Stop simulation execution
- **Status Monitoring**: Real-time execution status (PID, scenario, start time)
- **Stale Status Cleanup**: Clear stale execution status when needed
- **Auto-Refresh**: Automatic status updates during execution
- **Completion Alerts**: Success notifications when runs complete
- **Results Integration**: Directs users to Results tab for output viewing

**When to Use**: Execute your configured scenarios and monitor progress.

### **Tab 9: Logs**
**Purpose**: Monitor simulation logs and system activity.

**Features**:
- **Real Simulation Logs**: Live logs from the simulation engine
- **Log Filtering**: Filter by log level (DEBUG, INFO, WARNING, ERROR) and substring search
- **View Modes**: "From session start" or "Tail" (last 2000 lines)
- **Log Export**: Download visible log content as text files
- **Auto-Refresh**: Optional 2-second auto-refresh during monitoring
- **File Statistics**: Log path, size, and existence status
- **Manual Refresh**: Control when to update log display

**When to Use**: Monitor simulation execution and debug issues.

### **Tab 10: Results**
**Purpose**: Preview simulation results including CSV data and generated plots.

**Features**:
- **Latest CSV Preview**: Automatically displays the most recent results CSV
- **Full Data Table**: Complete KPI table with all simulation metrics
- **Plot Gallery**: Displays generated plots from simulation runs (up to 8 plots in 2-column layout)
- **Auto-Discovery**: Automatically finds latest results in output directory
- **Empty State Guidance**: Clear instructions when no results are available

**When to Use**: View and analyze simulation results after execution.

## 🔒 Save Button Protection System

### **Why Save Buttons Are Important**
- **Prevents Data Loss**: No accidental parameter destruction
- **Clear User Intent**: Users must explicitly commit changes
- **Data Integrity**: Ensures all changes are intentional and validated
- **Consistent UX**: Same pattern across all tabs

### **How Save Button Protection Works**
1. **Change Detection**: UI tracks all user modifications
2. **Visual Indicators**: Clear warnings for unsaved changes
3. **Button States**: Save buttons only enabled when changes exist
4. **Explicit Action**: Changes only propagate when save is clicked
5. **State Persistence**: Saved changes persist across UI interactions

## 🔄 Reset Functionality

### **Reset to Default Buttons**
Many tabs now include "Reset to default" buttons that restore parameters to their last-saved values:

- **Client Revenue Tab**: Separate reset buttons for Market Activation and Orders subtabs
- **Direct Market Revenue Tab**: Separate reset buttons for Market Activation and Orders subtabs  
- **Lookup Points Tab**: Separate reset buttons for Production Capacity and Pricing
- **Seeds Tab**: Single reset button for all seeding parameters

### **How Reset Works**
1. **Last-Saved Snapshot**: UI maintains snapshots of last-saved parameter values
2. **Widget Key Rotation**: Reset buttons rotate widget keys to force clean redraws
3. **Selective Restoration**: Only restores parameters that were previously saved
4. **Visual Feedback**: Shows count of restored cells and new widget key
5. **State Consistency**: Ensures UI state matches restored values

### **Reset Benefits**
- **Quick Recovery**: Easily undo accidental changes
- **Clean Slate**: Start fresh from known good state
- **Testing**: Quickly test different parameter sets
- **Comparison**: Compare current vs. last-saved values

## 🎯 Enhanced Scenario Management

### **Creating New Scenarios**
1. **Navigate to Tab 2 (Simulation Specs)**
2. **Type custom scenario name** in "Scenario Name" field
3. **Press Enter** to commit the name change
4. **Click "Save New Scenario"** button that appears
5. **New YAML file created** with current configuration
6. **Scenario becomes active** and appears in dropdown

### **Loading Existing Scenarios**
1. **Navigate to Tab 2 (Simulation Specs)**
2. **Select scenario** from "Load Existing Scenario" dropdown
3. **Click "Load [scenario]"** button
4. **Parameters load immediately** from selected scenario
5. **Status updates** to show loaded scenario
6. **All tabs reflect** the loaded scenario configuration

### **Scenario Status Display**
- **📝 Current Scenario**: Shows active scenario name with clear visual indicators
- **📁 Loaded Scenario**: [scenario_name] (when scenario is loaded)
- **Real-time updates** when scenarios are loaded or created
- **Clear visual feedback** on current scenario state
- **Bootstrap Persistence**: Last selected scenario automatically restored on UI reload

### **Enhanced Scenario Management Features**
- **Permissible Override Keys Reference**: Expandable section showing available constants and points counts
- **Lenient SM Validation**: Special validation mode for SM-mode scenarios with orphan constant handling
- **Scenario Validation**: Comprehensive validation against backend rules before execution
- **Last Selection Persistence**: UI remembers last selected scenario and anchor mode across sessions
- **Error Handling**: Detailed error messages for validation failures and loading issues

## 🚀 Key Workflows

### **Complete Scenario Creation Workflow**
1. **Tab 1**: Define your markets, sectors, and products
2. **Tab 2**: Set runtime parameters and create new scenario
3. **Tab 3**: Map sector-product relationships
4. **Tab 4**: Configure initial seeding (active clients, elapsed quarters, etc.)
5. **Tab 5**: Configure client revenue parameters
6. **Tab 6**: Set direct market revenue parameters
7. **Tab 7**: Configure capacity and pricing over time
8. **Tab 8**: Execute the scenario
9. **Tab 9**: Monitor execution logs
10. **Tab 10**: View and analyze results

### **Iterative Scenario Development**
1. **Load existing scenario** from Tab 2
2. **Make modifications** across any tabs
3. **Save changes** using tab-specific save buttons
4. **Validate configuration** before execution
5. **Run simulation** and analyze results
6. **Iterate and refine** based on outcomes

## 🔧 Technical Features

### **Dynamic Content Management**
- **Cross-tab dependencies**: Changes in one tab affect others
- **Real-time updates**: Tables and displays update automatically
- **Data consistency**: All tabs show synchronized information
- **Performance optimization**: Efficient rendering of large datasets
- **Widget Key Rotation**: Reset functionality uses key rotation for clean redraws

### **State Management**
- **Persistent state**: UI state survives across interactions
- **Session state**: Scenario tracking persists across reruns
- **Clean separation**: UI state separate from business logic
- **Error handling**: Comprehensive validation and error recovery
- **Last-Saved Snapshots**: Maintains snapshots for reset functionality
- **Bootstrap Persistence**: Automatic restoration of last selected scenario

### **Backend Integration**
- **YAML compatibility**: Generates existing backend format
- **Validation**: Uses existing backend validation rules
- **Execution**: Full integration with simulation engine
- **Results**: Real-time access to simulation outputs
- **Service Layer**: Clean separation between UI and backend logic
- **Path Management**: Centralized path handling for scenarios, logs, and output

### **UI Architecture**
- **Component-Based Design**: Modular tab components with shared base class
- **Service Layer**: Dedicated services for scenarios, validation, and execution
- **State Classes**: Typed dataclasses for different UI state aspects
- **Helper Utilities**: Shared utilities for common UI operations

## 💡 Best Practices

### **Getting Started**
1. **Start with Tab 1**: Define your industry structure first
2. **Use Tab 2**: Create your first scenario with basic parameters
3. **Build incrementally**: Add complexity one tab at a time
4. **Save frequently**: Use save buttons to preserve your work
5. **Validate before running**: Ensure configuration is correct

### **Scenario Management**
1. **Use descriptive names**: Clear scenario names help organization
2. **Create baseline scenarios**: Establish reference configurations
3. **Version your scenarios**: Use naming conventions for iterations
4. **Document changes**: Keep track of what each scenario represents
5. **Backup important scenarios**: Export and save critical configurations

### **Parameter Configuration**
1. **Start with defaults**: Use baseline values as starting points
2. **Validate ranges**: Ensure parameters are within reasonable bounds
3. **Test incrementally**: Make small changes and test effects
4. **Document assumptions**: Note the reasoning behind parameter choices
5. **Iterate systematically**: Methodically refine your configuration

## 🎉 Benefits of the New System

### **User Experience**
- **Intuitive workflow**: Logical progression from setup to execution
- **Visual feedback**: Clear indicators for all system states
- **Error prevention**: Save buttons prevent accidental data loss
- **Consistent interface**: Same patterns across all tabs

### **Functionality**
- **Complete coverage**: All 107+ parameters accessible through UI
- **Real-time updates**: Dynamic content that responds to changes
- **Scenario management**: Full lifecycle from creation to execution
- **Integration**: Seamless connection with backend systems
- **Results visualization**: Built-in CSV preview and plot gallery
- **Advanced execution**: Multiple execution options and monitoring

### **Maintainability**
- **Clean architecture**: Separation of UI and business logic
- **Modular design**: Each tab handles specific functionality
- **Extensible framework**: Easy to add new features
- **Testing coverage**: Comprehensive testing of all components

This comprehensive 10-tab UI system provides a professional, enterprise-grade interface for managing complex simulation scenarios while maintaining the flexibility and power of the underlying Growth Model system. The interface is designed to be intuitive for new users while providing advanced features for power users, with robust error handling, state management, and seamless integration with the simulation backend.