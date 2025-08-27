# Product Growth System UI - Complete Usage Guide

This document explains the comprehensive 8-tab UI system for the Product Growth System, a flexible, industry-agnostic simulation tool that can model any sectors and products you define.

## 🏗️ New 8-Tab UI Structure

The UI has been completely restructured to provide a modern, intuitive interface with comprehensive scenario management capabilities:

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

### **Tab 2: Simulation Specs**
**Purpose**: Configure runtime parameters and manage scenario creation/loading.

**Features**:
- **Runtime Controls**: Set start time, stop time, and time step (dt) for your simulation
- **Anchor Mode Selection**: Choose between "sector" mode (legacy) or "sm" mode (per-sector-product)
- **Enhanced Scenario Management**:
  - **Scenario Name Input**: Type custom names for new scenarios
  - **Save New Scenario Button**: Appears when typing custom names (requires Enter to activate)
  - **Load Existing Scenarios**: Dropdown to select and load saved scenarios
  - **Reset to Baseline**: Return to default configuration
- **Real-Time Status Display**: Shows which scenario is currently loaded
- **Save Button Protection**: Runtime parameter changes must be explicitly saved

**Key Workflow**:
1. **Type custom scenario name** → "Save New Scenario" button appears
2. **Press Enter** → Button becomes fully functional
3. **Click button** → Creates new YAML file with current configuration
4. **Load scenarios** → Status updates immediately to show loaded scenario

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

### **Tab 4: Client Revenue**
**Purpose**: Configure comprehensive client revenue parameters (19 total parameters).

**Features**:
- **Market Activation Parameters (9)**: ATAM, anchor_start_year, lead generation rates, project parameters
- **Orders Parameters (9)**: Phase durations, requirement rates, growth percentages, delivery lags
- **Seeds Parameters (3)**: Completed projects, active clients, elapsed time
- **Dynamic Content**: Tables populate based on primary mapping selections
- **Organized Groups**: Logical grouping with clear descriptions
- **Save Button Protection**: All parameter changes must be explicitly saved

**When to Use**: Configure detailed client behavior and revenue generation parameters.

### **Tab 5: Direct Market Revenue**
**Purpose**: Set product-specific direct market revenue parameters (9 parameters).

**Features**:
- **Lead Generation**: Inbound/outbound lead rates and conversion parameters
- **Order Management**: Initial quantities, growth rates, and delivery delays
- **Market Size**: Total addressable market (TAM) configuration
- **Dynamic Content**: Tables update with product list changes
- **Save Button Protection**: All parameter changes must be explicitly saved

**When to Use**: Configure direct market revenue streams for each product.

### **Tab 6: Lookup Points**
**Purpose**: Configure time-series data for production capacity and pricing.

**Features**:
- **Production Capacity Tables**: Maximum capacity per product per year
- **Pricing Tables**: Price per unit per product per year
- **Year-Based Structure**: Years as columns, products as rows
- **Dynamic Content**: Tables update with product list changes
- **Save Button Protection**: All time-series data changes must be explicitly saved

**When to Use**: Set capacity constraints and pricing strategies over time.

### **Tab 7: Runner**
**Purpose**: Execute scenarios and monitor simulation progress.

**Features**:
- **Scenario Execution**: Save, validate, and run current configuration
- **Real-Time Monitoring**: Live progress tracking and status updates
- **Results Display**: CSV data and generated plots from simulation
- **Execution History**: Track previous runs and file management
- **Backend Integration**: Full integration with simulation engine
- **Save Button Protection**: Execution settings must be explicitly saved

**When to Use**: Execute your configured scenarios and view results.

### **Tab 8: Logs**
**Purpose**: Monitor simulation logs and system activity.

**Features**:
- **Real Simulation Logs**: Live logs from the simulation engine
- **Log Filtering**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
- **Log Export**: Download and analyze log data
- **Real-Time Statistics**: Live log counts and file information
- **Save Button Protection**: Log configuration settings must be explicitly saved

**When to Use**: Monitor simulation execution and debug issues.

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
- **📝 Default Scenario**: working_scenario (when using default)
- **📁 Loaded Scenario**: [scenario_name] (when scenario is loaded)
- **Real-time updates** when scenarios are loaded or created
- **Clear visual feedback** on current scenario state

## 🚀 Key Workflows

### **Complete Scenario Creation Workflow**
1. **Tab 1**: Define your markets, sectors, and products
2. **Tab 2**: Set runtime parameters and create new scenario
3. **Tab 3**: Map sector-product relationships
4. **Tab 4**: Configure client revenue parameters
5. **Tab 5**: Set direct market revenue parameters
6. **Tab 6**: Configure capacity and pricing over time
7. **Tab 7**: Execute the scenario
8. **Tab 8**: Monitor execution logs

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

### **State Management**
- **Persistent state**: UI state survives across interactions
- **Session state**: Scenario tracking persists across reruns
- **Clean separation**: UI state separate from business logic
- **Error handling**: Comprehensive validation and error recovery

### **Backend Integration**
- **YAML compatibility**: Generates existing backend format
- **Validation**: Uses existing backend validation rules
- **Execution**: Full integration with simulation engine
- **Results**: Real-time access to simulation outputs

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
- **Complete coverage**: All 107 parameters accessible through UI
- **Real-time updates**: Dynamic content that responds to changes
- **Scenario management**: Full lifecycle from creation to execution
- **Integration**: Seamless connection with backend systems

### **Maintainability**
- **Clean architecture**: Separation of UI and business logic
- **Modular design**: Each tab handles specific functionality
- **Extensible framework**: Easy to add new features
- **Testing coverage**: Comprehensive testing of all components

This new UI system provides a professional, enterprise-grade interface for managing complex simulation scenarios while maintaining the flexibility and power of the underlying Growth Model system.