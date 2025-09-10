# Product Growth System – Business User Tutorial

**Audience**: Business stakeholders who want to install the tool, use the UI to build scenarios, run the model, and read outputs/plots. No coding required.

## 🎯 What You'll Get

- **10-Tab Browser UI** to edit scenarios, manage parameters, and run simulations
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

**By default, your browser opens at http://localhost:8501**

## 🎯 Common Business Questions This System Answers

Before diving into the technical details, let's understand what business value this system provides:

### **Strategic Planning Questions**
- **"What if we double our production capacity?"** → Test capacity expansion scenarios
- **"How will price changes affect our revenue?"** → Model price sensitivity across products
- **"What's the impact of entering new markets?"** → Add new sectors and analyze growth potential
- **"How long does it take for new clients to become profitable?"** → Track client lifecycle and conversion rates

### **Operational Questions**
- **"Are we capacity-constrained or demand-constrained?"** → Analyze fulfillment ratios and capacity utilization
- **"Which products should we prioritize for investment?"** → Compare revenue potential across product lines
- **"What's our optimal pricing strategy over time?"** → Test different pricing scenarios and their impact
- **"How many sales resources do we need?"** → Model lead generation and conversion requirements

### **Financial Questions**
- **"What's our revenue forecast for the next 5 years?"** → Generate detailed quarterly projections
- **"How sensitive is our business to key parameters?"** → Run sensitivity analysis on critical factors
- **"What's the ROI of different growth strategies?"** → Compare scenarios with different investment levels

## 🏗️ Understanding the 10-Tab UI Structure

The UI is organized into 10 logical tabs that guide you through the complete simulation setup process:

### **Tab 1: Simulation Definitions**
**Purpose**: Define your simulation universe
- **Markets**: Set global or regional market scope (e.g., "US", "EU", "Global")
- **Sectors**: Define business sectors (e.g., "Defense", "Healthcare", "Automotive")
- **Products**: Define products and materials (e.g., "Software Licenses", "Medical Devices")

**When to Use**: Start here to establish the foundation. Add or remove items as needed. Changes here automatically update related components in other tabs.

### **Tab 2: Simulation Specs**
**Purpose**: Configure runtime parameters and manage scenarios
- **Timeline**: Set start year, stop year, and time step (quarterly recommended)
- **Anchor Mode**: Choose between "sector" or "sm" (sector-material mode)
- **Scenario Management**: Load existing scenarios, save changes, or create new ones

**When to Use**: Set your simulation timeframe and choose which scenario to work with.

### **Tab 3: Primary Mapping**
**Purpose**: Map sectors to products
- **Sector-Product Relationships**: Define which combinations are valid
- **Start Year Configuration**: Set when each sector-product combination begins
- **Mapping Insights**: See parameter coverage for each combination

**When to Use**: After defining your sectors and products, map their relationships. This determines which combinations appear in the revenue tabs.

### **Tab 4: Seeds**
**Purpose**: Configure initial seeding for your simulation
- **Active Anchor Clients**: Set number of pre-existing clients at simulation start
- **Elapsed Quarters**: Configure how long clients have been active
- **Completed Projects**: Set backlog of completed projects
- **Direct Clients**: Configure direct client counts per product

**When to Use**: Set up the initial state of your simulation with pre-existing clients and their history.

### **Tab 5: Client Revenue**
**Purpose**: Configure client revenue parameters (20 total parameters)
- **Market Activation (9 params)**: Lead generation, conversion rates, client activation
- **Orders (11 params)**: Order behavior, project duration, fulfillment, requirement limits

**When to Use**: Configure detailed client behavior and revenue generation parameters.

### **Tab 6: Direct Market Revenue**
**Purpose**: Configure product-specific parameters (9 parameters)
- **Market Activation (5 params)**: Lead generation, conversion rates, market size
- **Orders (4 params)**: Order timing, quantities, growth rates

**When to Use**: Set parameters for each product. These control pricing, capacity, and market dynamics during simulation.

### **Tab 7: Lookup Points**
**Purpose**: Define time-series data
- **Production Capacity**: Year-by-year capacity constraints per product
- **Pricing**: Year-by-year pricing per product
- **Timeline Management**: Extend or modify the simulation timeline

**When to Use**: Set capacity constraints and pricing strategies over time.

### **Tab 8: Runner**
**Purpose**: Execute scenarios and monitor progress
- **Scenario Selection**: Choose from saved scenarios or run current configuration
- **Execution Settings**: Debug mode, plot generation, KPI options
- **Real-time Monitoring**: Watch simulation progress live
- **Results Display**: View CSV data and generated plots

**When to Use**: Execute your configured scenarios and monitor progress.

### **Tab 9: Logs**
**Purpose**: Monitor simulation logs and system activity
- **Real-time Logs**: Live simulation engine output
- **Filtering**: Search by log level, source, or content
- **Export**: Download logs for external analysis

**When to Use**: Monitor simulation execution and debug issues.

### **Tab 10: Results**
**Purpose**: Preview simulation results including CSV data and generated plots
- **Latest CSV Preview**: Automatically displays the most recent results CSV
- **Full Data Table**: Complete KPI table with all simulation metrics
- **Plot Gallery**: Displays generated plots from simulation runs

**When to Use**: View and analyze simulation results after execution.

## 📋 Step-by-Step Business Scenarios

### **Scenario 1: Quick Baseline Verification**
*"I want to see how the system works with default settings"*

1. **Open UI** → Navigate to **Runner** tab
2. **Select Scenario**: Choose "baseline" from the dropdown
3. **Configure Settings**: Enable "Generate Plots" and "Debug Mode"
4. **Run Simulation**: Click "Run Simulation"
5. **Review Results**: Check logs, CSV preview, and plots

**What You'll Learn**: How the system works, what outputs look like, and basic navigation.

### **Scenario 2: Capacity Expansion Analysis**
*"What if we double our production capacity starting in 2026?"*

1. **Load Baseline**: Go to Tab 2, load "baseline" scenario
2. **Modify Capacity**: Go to Tab 7 (Lookup Points)
   - Find "Production Capacity" section
   - Double all capacity values from 2026 onwards
   - Click "Save" to commit changes
3. **Create New Scenario**: Go to Tab 2, enter "double_capacity_2026" as new scenario name
4. **Save Scenario**: Click "Save as New"
5. **Run Simulation**: Go to Tab 8, run the new scenario
6. **Compare Results**: Go to Tab 10, compare with baseline results

**Business Insight**: You'll see how capacity constraints affect revenue and identify optimal investment timing.

### **Scenario 3: Price Sensitivity Analysis**
*"How will a 20% price increase affect our revenue?"*

1. **Load Baseline**: Go to Tab 2, load "baseline" scenario
2. **Modify Pricing**: Go to Tab 7 (Lookup Points)
   - Find "Pricing" section
   - Increase all prices by 20% from 2026 onwards
   - Click "Save" to commit changes
3. **Create New Scenario**: Go to Tab 2, enter "price_increase_20pct" as new scenario name
4. **Save Scenario**: Click "Save as New"
5. **Run Simulation**: Go to Tab 8, run the new scenario
6. **Analyze Results**: Go to Tab 10, compare revenue and client acquisition

**Business Insight**: You'll understand price elasticity and optimal pricing strategies.

### **Scenario 4: New Market Entry**
*"What if we enter the Healthcare sector with our existing products?"*

1. **Add New Sector**: Go to Tab 1 (Simulation Definitions)
   - Add "Healthcare" to the sectors list
   - Click "Save" to commit changes
2. **Map Products**: Go to Tab 3 (Primary Mapping)
   - Add mapping for Healthcare → Silicon_Carbide_Fiber
   - Set start year to 2027
   - Click "Save" to commit changes
3. **Configure Parameters**: Go to Tab 5 (Client Revenue)
   - Set parameters for Healthcare + Silicon_Carbide_Fiber combination
   - Use similar values to Defense sector as starting point
   - Click "Save" to commit changes
4. **Create New Scenario**: Go to Tab 2, enter "healthcare_entry" as new scenario name
5. **Save Scenario**: Click "Save as New"
6. **Run Simulation**: Go to Tab 8, run the new scenario
7. **Analyze Results**: Go to Tab 10, see new revenue stream

**Business Insight**: You'll understand market entry timing, resource requirements, and revenue potential.

### **Scenario 5: Lead Generation Optimization**
*"What if we increase our lead generation by 50%?"*

1. **Load Baseline**: Go to Tab 2, load "baseline" scenario
2. **Modify Lead Generation**: Go to Tab 5 (Client Revenue)
   - Find "Market Activation" subtab
   - Increase "anchor_lead_generation_rate" by 50% for key sectors
   - Click "Save" to commit changes
3. **Create New Scenario**: Go to Tab 2, enter "higher_leads" as new scenario name
4. **Save Scenario**: Click "Save as New"
5. **Run Simulation**: Go to Tab 8, run the new scenario
6. **Analyze Results**: Go to Tab 10, compare client acquisition and revenue

**Business Insight**: You'll understand the ROI of marketing investments and optimal lead generation levels.

## 🔧 Advanced Business Scenarios

### **Scenario 6: Competitive Analysis**
*"What if a competitor enters our market and reduces our lead generation by 30%?"*

1. **Load Baseline**: Go to Tab 2, load "baseline" scenario
2. **Modify Lead Generation**: Go to Tab 5 (Client Revenue)
   - Reduce "anchor_lead_generation_rate" by 30% for all sectors
   - Click "Save" to commit changes
3. **Create New Scenario**: Go to Tab 2, enter "competitive_threat" as new scenario name
4. **Save Scenario**: Click "Save as New"
5. **Run Simulation**: Go to Tab 8, run the new scenario
6. **Analyze Results**: Go to Tab 10, see impact on revenue and market share

**Business Insight**: You'll understand competitive vulnerability and defensive strategies.

### **Scenario 7: Economic Downturn**
*"What if there's a recession and our conversion rates drop by 25%?"*

1. **Load Baseline**: Go to Tab 2, load "baseline" scenario
2. **Modify Conversion Rates**: Go to Tab 5 (Client Revenue)
   - Reduce "lead_to_pc_conversion_rate" by 25% for all sectors
   - Click "Save" to commit changes
3. **Create New Scenario**: Go to Tab 2, enter "recession_scenario" as new scenario name
4. **Save Scenario**: Click "Save as New"
5. **Run Simulation**: Go to Tab 8, run the new scenario
6. **Analyze Results**: Go to Tab 10, see impact on revenue and recovery time

**Business Insight**: You'll understand business resilience and recovery strategies.

## 📊 Understanding Your Results

### **Key Business Metrics to Watch**

#### **Revenue Metrics**
- **Total Revenue**: Overall business performance
- **Revenue by Sector**: Which markets are most profitable
- **Revenue by Product**: Which products drive growth
- **Revenue Growth Rate**: How fast the business is growing

#### **Client Metrics**
- **Active Clients**: Current client base size
- **Client Acquisition Rate**: How fast you're gaining new clients
- **Client Conversion Rate**: How well leads convert to clients
- **Client Lifetime Value**: Long-term client profitability

#### **Operational Metrics**
- **Capacity Utilization**: How efficiently you're using production capacity
- **Fulfillment Ratio**: Demand vs. supply balance
- **Lead Generation**: Marketing effectiveness
- **Project Completion**: Delivery performance

#### **Financial Metrics**
- **Revenue per Client**: Average client value
- **Revenue per Product**: Product profitability
- **Revenue per Sector**: Market profitability
- **Growth Rate**: Business expansion rate

### **How to Read the Plots**

#### **Revenue Plots**
- **Total Revenue**: Shows overall business growth trajectory
- **Revenue by Sector**: Identifies which markets are growing fastest
- **Revenue by Product**: Shows which products are most profitable

#### **Client Plots**
- **Leads and Clients**: Shows lead generation and conversion effectiveness
- **Capacity Utilization**: Identifies production bottlenecks
- **Order Basket vs. Delivery**: Shows demand vs. supply balance

## 🚨 Troubleshooting Guide

### **Common Issues and Solutions**

#### **"I can't see my parameters after adding a new mapping"**
- **Solution**: In Primary Mapping, click "Apply Mapping for Sector" first
- **Why**: The UI needs to refresh the parameter tables

#### **"Validation errors about missing parameters"**
- **Solution**: Ensure all required parameters are set for your sector-product combinations
- **Why**: The system validates completeness before running

#### **"No plots showing in the UI"**
- **Solution**: Check "Generate Plots" is enabled in the Runner tab before running
- **Why**: Plot generation is optional and must be explicitly enabled

#### **"Simulation runs but produces no results"**
- **Solution**: Check the Logs tab for error messages
- **Why**: The system logs all execution details for debugging

#### **"Can't save my scenario"**
- **Solution**: Ensure all required fields are filled and validation passes
- **Why**: The system prevents saving invalid configurations

### **Performance Tips**
- **Close other applications** when running large simulations
- **Use appropriate time steps** (quarterly for detailed analysis, annual for long-term planning)
- **Limit the number of sectors/products** for faster execution
- **Enable debug mode only when needed** (slows execution)

## 🎯 Best Practices for Business Users

### **Planning Your Simulation**
1. **Start Simple**: Begin with a few sectors and products
2. **Define Clear Objectives**: What questions are you trying to answer?
3. **Set Realistic Timeframes**: Consider data availability and business cycles
4. **Document Assumptions**: Keep track of parameter choices and rationale

### **Managing Scenarios**
1. **Use Descriptive Names**: Include date and purpose in scenario names
2. **Version Control**: Save iterations to track changes
3. **Document Changes**: Note what was modified and why
4. **Share Results**: Export and share findings with stakeholders

### **Interpreting Results**
1. **Check Logs First**: Ensure simulation completed successfully
2. **Validate Assumptions**: Do results align with expectations?
3. **Sensitivity Analysis**: Test key parameters to understand impact
4. **Document Insights**: Record findings and recommendations

## 🆘 Getting Help

### **Self-Service Resources**
1. **Check this tutorial** for step-by-step guidance
2. **Review example scenarios** in the `scenarios/` folder
3. **Use the UI help text** (info boxes in each tab)
4. **Check the logs** for detailed error information


## 🚀 Ready to Start?

You now have everything you need to:
1. **Install and launch** the Growth Model UI
2. **Navigate the 10-tab interface** confidently
3. **Create and run scenarios** for your business needs
4. **Analyze results** and generate insights
5. **Troubleshoot common issues** independently

**Start with Scenario 1 (Quick Baseline Verification) to get familiar with the system, then explore the business scenarios that match your needs.**

---

**Note**: This is a research and analysis tool designed to be industry-agnostic. You can model any sector or product by configuring the inputs. Results should be validated against real-world data and used as part of a comprehensive analysis framework.