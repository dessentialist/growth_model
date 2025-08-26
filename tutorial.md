# Product Growth System – Business User Tutorial

**Audience**: Business stakeholders who want to install the tool, use the UI to build scenarios, run the model, and read outputs/plots. No coding required.

## 🎯 What You'll Get

- **8-Tab Browser UI** to edit scenarios, manage parameters, and run simulations
- **Live logs and real-time monitoring** during simulation execution
- **KPI CSV exports** with comprehensive business metrics
- **Downloadable static plots** for presentations and reports
- **Preset scenarios** you can run as-is or load into the editor to customize
- **Flexible, industry-agnostic system** that can model any sectors and products you define

## 🚀 Quick Installation Guide

### Prerequisites
- **macOS** (recommended), **Windows**, or **Linux**
- **Python 3.12+** and **Git**
- **4GB+ RAM** for smooth operation

### Method 1: Single Command Setup (Recommended)

**For All Platforms (Windows, macOS, Linux):**
```bash
# Clone the repository
git clone https://github.com/dessentialist/Growth_Model.git
cd Growth_Model

# Single command to setup everything and launch UI
python setup_cross_platform.py
```

This single command will:
- ✅ Create virtual environment
- ✅ Install all dependencies  
- ✅ Run test suite (107 tests)
- ✅ Launch the Streamlit UI automatically

### Method 2: Using Make Commands (macOS/Linux Users)

```bash
# Clone the repository
git clone https://github.com/dessentialist/Growth_Model.git
cd Growth_Model

# Install dependencies and setup environment
make install

# Launch the UI
make run_ui
```

### Method 3: Manual Setup (Advanced Users)

```bash
# Clone and set up virtual environment
git clone https://github.com/dessentialist/Growth_Model.git
cd Growth_Model

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Launch the UI
streamlit run ui/app.py
```



**By default, your browser opens at http://localhost:8501**

## 🏗️ Understanding the 8-Tab UI Structure

The UI is organized into 8 logical tabs that guide you through the complete simulation setup process:

### Tab 1: Simulation Definitions
**Purpose**: Define your simulation universe
- **Markets**: Set global or regional market scope
- **Sectors**: Define business sectors (e.g., Defense, Aerospace, Automotive)
- **Products**: Define products (e.g., UHT, Silicon Carbide Fiber)

**How to Use**: Start here to establish the foundation. Add or remove items as needed. Changes here automatically update related components in other tabs.

### Tab 2: Simulation Specs
**Purpose**: Configure runtime parameters
- **Start Year**: When your simulation begins
- **Stop Year**: When your simulation ends
- **Time Step (dt)**: How frequently the model updates (e.g., quarterly, annually)
- **Scenario Settings**: Save and manage different configurations

**How to Use**: Set your timeline and save configurations. The form validates inputs and shows errors if values are invalid.

### Tab 3: Primary Mapping
**Purpose**: Map sectors to products
- **Sector-Product Relationships**: Define which combinations are valid
- **Mapping Insights**: See parameter coverage for each combination
- **Dynamic Table Generation**: Automatically creates parameter tables

**How to Use**: Use "Add Mapping" to create new sector-product relationships. This determines which combinations appear in the revenue tabs.

### Tab 4: Client Revenue
**Purpose**: Configure 19 client revenue parameters across three categories
- **Market Activation (9 params)**: Lead generation, conversion rates, client activation
- **Orders (9 params)**: Order behavior, project duration, fulfillment
- **Seeds (3 params)**: Initial client base and project backlog

**How to Use**: Configure parameters by sector-product combinations. Use the tabs to switch between parameter groups. Click "Save" after making changes.

### Tab 5: Direct Market Revenue
**Purpose**: Configure 9 product-specific parameters
- **Pricing**: Product pricing strategies
- **Capacity**: Production capacity constraints
- **Market Dynamics**: Growth patterns and market behavior

**How to Use**: Set parameters for each product. These control pricing, capacity, and market dynamics during simulation.

### Tab 6: Lookup Points
**Purpose**: Define time-series data
- **Production Capacity**: Year-by-year capacity constraints per product
- **Pricing**: Year-by-year pricing per product
- **Timeline Management**: Extend or modify the simulation timeline

**How to Use**: Set values for each product and year combination. Use "Add Year" to extend the timeline or "Add Product" for new products.

### Tab 7: Runner
**Purpose**: Execute scenarios and monitor progress
- **Scenario Selection**: Choose from saved scenarios or run current configuration
- **Execution Settings**: Debug mode, plot generation, KPI options
- **Real-time Monitoring**: Watch simulation progress live
- **Results Display**: View CSV data and generated plots
- **Execution History**: Track previous runs and access outputs

**How to Use**: Select a scenario, configure settings, then click "Run Simulation". Monitor progress and view results.

### Tab 8: Logs
**Purpose**: Analyze simulation execution
- **Real-time Logs**: Live simulation engine output
- **Filtering**: Search by log level, source, or content
- **Export**: Download logs for external analysis
- **Debugging**: Identify and troubleshoot issues

**How to Use**: View execution logs, use filters to find specific information, and export for analysis.

## 📋 Step-by-Step Workflow Examples

### Workflow A: Quick Baseline Verification
1. **Open UI** → Navigate to **Runner** tab
2. **Select Scenario**: Choose "baseline" from the dropdown
3. **Configure Settings**: Enable "Generate Plots" and "Debug Mode"
4. **Run Simulation**: Click "Run Simulation"
5. **Review Results**: Check logs, CSV preview, and plots

### Workflow B: Create Custom Scenario
1. **Simulation Definitions**: Set up your markets, sectors, and products
2. **Simulation Specs**: Configure start/stop years and time step
3. **Primary Mapping**: Map sectors to products
4. **Client Revenue**: Configure client behavior parameters
5. **Direct Market Revenue**: Set product-specific parameters
6. **Lookup Points**: Define capacity and pricing over time
7. **Validate & Save**: Save your scenario with a descriptive name
8. **Run**: Execute your custom scenario

### Workflow C: Modify Existing Scenario
1. **Load Scenario**: Use "Load Scenario" in the Runner tab
2. **Make Changes**: Navigate to relevant tabs and modify parameters
3. **Save As**: Save with a new name to preserve the original
4. **Run**: Execute the modified scenario
5. **Compare**: Use the execution history to compare results

## 🔧 Advanced Features

### Scenario Management
- **Save Multiple Versions**: Create variations of scenarios
- **Version Control**: Track changes and iterations
- **Export/Import**: Share scenarios with team members

### Parameter Validation
- **Real-time Validation**: UI prevents invalid configurations
- **Error Messages**: Clear explanations of validation issues
- **Auto-completion**: Smart suggestions for parameter names

### Results Analysis
- **KPI Extraction**: Comprehensive business metrics
- **Visualization**: Multiple chart types and formats
- **Data Export**: CSV, PNG, and other formats

## 📊 Understanding Outputs

### Where to Find Results
- **Logs**: `logs/run.log` (also streamed in UI)
- **KPI CSV**: `output/Growth_System_Complete_Results.csv`
- **Scenario-specific CSV**: `output/Growth_System_Complete_Results_<scenario>.csv`
- **Plots**: `output/plots/*.png` (rendered inline and downloadable)

### Key Business Metrics
- **Revenue**: Total and by-sector breakdowns
- **Capacity Utilization**: Product production efficiency
- **Lead Generation**: Client acquisition metrics
- **Client Evolution**: Potential → Pending → Active transitions

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### "I can't see my parameters after adding a new mapping"
- **Solution**: In Primary Mapping, click "Apply Mapping for Sector" first
- **Why**: The UI needs to refresh the parameter tables

#### "Validation errors about missing parameters"
- **Solution**: Ensure all required parameters are set for your sector-product combinations
- **Why**: The system validates completeness before running

#### "No plots showing in the UI"
- **Solution**: Check "Generate Plots" is enabled in the Runner tab before running
- **Why**: Plot generation is optional and must be explicitly enabled

#### "Simulation runs but produces no results"
- **Solution**: Check the Logs tab for error messages
- **Why**: The system logs all execution details for debugging

#### "Can't save my scenario"
- **Solution**: Ensure all required fields are filled and validation passes
- **Why**: The system prevents saving invalid configurations

### Performance Tips
- **Close other applications** when running large simulations
- **Use appropriate time steps** (quarterly for detailed analysis, annual for long-term planning)
- **Limit the number of sectors/products** for faster execution
- **Enable debug mode only when needed** (slows execution)

## 🔄 Command-Line Alternatives (Advanced Users)

If you prefer command-line operation:

```bash
# Run a preset scenario
python simulate_growth.py --preset baseline --debug --visualize

# Run a specific scenario file
python simulate_growth.py --scenario scenarios/your_case.yaml --visualize

# Available flags
--kpi-sm-revenue-rows    # Include per-sector-product revenue details
--kpi-sm-client-rows     # Include per-sector-product client details
--debug                  # Enable detailed logging
--visualize              # Generate plots
```

## 📚 Reference Materials

- **`inputs.md`**: Detailed input parameter documentation
- **`technical_architecture.md`**: System design and data flow
- **`index.md`**: Comprehensive codebase overview
- **Example scenarios**: `scenarios/` folder with working examples

## 🎯 Best Practices for Business Users

### Planning Your Simulation
1. **Start Simple**: Begin with a few sectors and products
2. **Define Clear Objectives**: What questions are you trying to answer?
3. **Set Realistic Timeframes**: Consider data availability and business cycles
4. **Document Assumptions**: Keep track of parameter choices and rationale

### Managing Scenarios
1. **Use Descriptive Names**: Include date and purpose in scenario names
2. **Version Control**: Save iterations to track changes
3. **Document Changes**: Note what was modified and why
4. **Share Results**: Export and share findings with stakeholders

### Interpreting Results
1. **Check Logs First**: Ensure simulation completed successfully
2. **Validate Assumptions**: Do results align with expectations?
3. **Sensitivity Analysis**: Test key parameters to understand impact
4. **Document Insights**: Record findings and recommendations

## 🆘 Getting Help

### Self-Service Resources
1. **Check this tutorial** for step-by-step guidance
2. **Review example scenarios** in the `scenarios/` folder
3. **Use the UI help text** (info boxes in each tab)
4. **Check the logs** for detailed error information

### When to Ask for Help
- **System errors** that prevent operation
- **Unexpected results** that can't be explained
- **Performance issues** that significantly slow operation
- **Feature requests** for new capabilities

## 🚀 Ready to Start?

You now have everything you need to:
1. **Install and launch** the Growth Model UI
2. **Navigate the 8-tab interface** confidently
3. **Create and run scenarios** for your business needs
4. **Analyze results** and generate insights
5. **Troubleshoot common issues** independently

**Start with Workflow A (Quick Baseline Verification) to get familiar with the system, then explore creating custom scenarios using the step-by-step workflow.**

---

**Note**: This is a research and analysis tool designed to be industry-agnostic. You can model any sector or product by configuring the inputs. Results should be validated against real-world data and used as part of a comprehensive analysis framework.


