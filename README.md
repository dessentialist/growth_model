
# Product Growth System

A sophisticated hybrid System Dynamics + Agent-Based Modeling (SD+ABM) simulation system designed for strategic business planning and growth forecasting across any industry or sector. The system combines the power of continuous system dynamics for market flows with discrete agent-based modeling for individual client behavior, providing comprehensive scenario analysis capabilities.

## 🚀 Key Features & Benefits

### **Strategic Planning Capabilities**
- **Multi-Scenario Analysis**: Test capacity expansion, price changes, market entry, and competitive threats
- **Industry Agnostic**: Model any sectors and products by simply configuring inputs - no hard-coded assumptions
- **Revenue Forecasting**: Generate detailed quarterly projections with 20+ KPI metrics
- **Capacity Planning**: Optimize production capacity and pricing strategies over time
- **Market Entry Analysis**: Evaluate new market opportunities and resource requirements

### **Advanced Modeling Architecture**
- **Hybrid SD+ABM**: Combines System Dynamics for aggregate market flows with Agent-Based Modeling for individual client behavior
- **Dual Client Types**: Models both anchor clients (long-term strategic relationships) and direct clients (market-driven demand)
- **Flexible Modes**: Support for both sector-level and sector-material (SM) level modeling granularity
- **Real-time Validation**: Comprehensive parameter validation and scenario integrity checks

### **Modern User Interface**
- **10-Tab Streamlit UI**: Complete scenario editor and runner with intuitive parameter management
- **Save Button Protection**: Prevents accidental data loss with change tracking across all tabs
- **Dynamic Content**: Tables and interfaces that adapt based on your sector-product selections
- **Real-time Monitoring**: Live execution logs and progress tracking
- **Results Visualization**: Built-in CSV preview and plot generation

## 🏗️ Understanding the Growth Model

### **Core Architecture**

The Product Growth System uses a hybrid modeling approach that combines two powerful simulation paradigms:

#### **System Dynamics (SD) Component**
- **Purpose**: Models aggregate market flows, capacity constraints, and revenue generation
- **Implementation**: Built using BPTK_Py framework with stocks, flows, converters, and lookup tables
- **Key Flows**: Lead generation → client conversion → requirement generation → capacity fulfillment → revenue calculation
- **Time Resolution**: Quarterly time steps (dt=0.25) for detailed business planning

#### **Agent-Based Modeling (ABM) Component**
- **Purpose**: Models individual client behavior and decision-making processes
- **Implementation**: Custom Python agents with deterministic lifecycles and decision rules
- **Key Agents**: Anchor clients with multi-phase requirement patterns and project lifecycles
- **Integration**: Agents feed aggregated demand into SD model via gateway converters

### **Key Business Concepts**

#### **Anchor Clients**
- **Definition**: Long-term strategic clients with established relationships and predictable demand patterns
- **Behavior**: Multi-phase requirement evolution (initial → ramp → steady state)
- **Lifecycle**: Potential → Pending Activation → Active → Project Completion → Product Supply
- **Parameters**: Lead generation rates, conversion rates, project duration, activation delays
- **Revenue Impact**: High-value, predictable revenue streams with project-based delivery

#### **Direct Clients**
- **Definition**: Market-driven clients acquired through standard sales channels
- **Behavior**: Continuous demand generation with growth patterns over time
- **Lifecycle**: Lead generation → conversion → continuous ordering
- **Parameters**: Lead generation rates, conversion rates, order quantities, growth rates
- **Revenue Impact**: Scalable revenue streams with market-driven demand

#### **Direct Market Revenue**
- **Definition**: Revenue generated from direct client sales outside of anchor relationships
- **Components**: Lead generation, conversion rates, order quantities, pricing
- **Market Dynamics**: TAM (Total Addressable Market) constraints and competitive factors
- **Growth Patterns**: Client cohort aging with per-client order limits

### **Modeling Modes for Anchor Clients**

#### **Sector Mode (Default)**
- **Granularity**: Sector-level parameter management
- **Use Case**: High-level strategic planning and market analysis
- **Parameters**: Single set of parameters per sector across all products
- **Complexity**: Lower complexity, easier to configure and understand

#### **Sector-Material (SM) Mode**
- **Granularity**: Per-sector-product combination parameter management
- **Use Case**: Detailed product-specific analysis and optimization
- **Parameters**: Individual parameter sets for each sector-product combination
- **Complexity**: Higher complexity, more detailed control and analysis

### **Configuration System**

#### **inputs.json - The Baseline Configuration**
- **Purpose**: Defines the default model parameters and structure
- **Components**:
  - **Lists**: Markets, sectors, and products that define your simulation universe
  - **Anchor Parameters**: 20+ parameters controlling anchor client behavior
  - **Direct Client Parameters**: 9 parameters controlling direct market dynamics
  - **Production Data**: Time-series capacity constraints per product
  - **Pricing Data**: Time-series pricing per product
  - **Primary Mapping**: Which sectors use which products and when

#### **Scenario Overrides - Customizing the Baseline**
- **Purpose**: Modify any parameter without changing the baseline configuration
- **Format**: YAML files with structured overrides
- **Types**:
  - **Constants**: Override any parameter value
  - **Points**: Override time-series data (capacity, pricing)
  - **Seeds**: Set initial conditions (active clients, completed projects)
  - **Primary Map**: Override sector-product relationships

### **Key Libraries & Dependencies**

#### **Core Simulation Engine**
- **BPTK_Py (v2.1.1)**: System Dynamics framework providing stocks, flows, converters, and lookup tables
- **Pandas (v2.3.0+)**: Data manipulation and analysis for parameter tables and results
- **NumPy (v2.3.1+)**: Numerical computing for mathematical operations and data processing

#### **User Interface**
- **Streamlit (v1.48.1+)**: Modern web-based UI framework for scenario editing and monitoring
- **Pillow (v11.3.0+)**: Image processing for plot generation and display

#### **Data Processing & Visualization**
- **Matplotlib (v3.10.3+)**: Plotting and visualization for results analysis
- **SciPy (v1.15.3+)**: Scientific computing for advanced mathematical operations
- **PyYAML (v6.0.2+)**: YAML file parsing for scenario configuration

#### **Development & Testing**
- **Pytest (v8.4.1+)**: Testing framework ensuring code reliability and stability

## 📋 Prerequisites

- Python 3.12+ or 3.13+
- macOS, Linux, or Windows (tested on macOS)
- Git

## 🛠️ Installation

### Single Command Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd growth_model_2

# Single command to setup everything and launch UI
python setup_cross_platform.py
```

This single command will:
- ✅ Create virtual environment
- ✅ Install all dependencies  
- ✅ Run test suite (107 tests)
- ✅ Launch the Streamlit UI automatically

**No additional tools required** - just Python 3.12+ and Git!

### Alternative: Using Make (Unix/Linux/macOS)

```bash
# Clone the repository
git clone <your-repo-url>
cd growth_model_2

# Install dependencies and create virtual environment
make install

# Verify installation
make test

# Launch UI
make run_ui
```

### Manual Setup (Advanced Users)

```bash
# Clone the repository
git clone <your-repo-url>
cd growth_model_2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Launch UI
streamlit run ui/app.py
```

## 🎯 Quick Start

### Run the Interactive UI

**Option 1: Single Command (Recommended)**
```bash
python setup_cross_platform.py
```

**Option 2: Using Make (Unix/Linux/macOS)**
```bash
make run_ui
```

Both options open a clean, modern 10-tab Streamlit interface at `http://localhost:8501` where you can:

**Tab 1: Simulation Definitions**
- Manage market, sector, and product lists
- Add/edit/delete sectors and products with table-based input
- Save button protection prevents data loss
- Dynamic content updates across all tabs

**Tab 2: Simulation Specs**
- Runtime controls (start time, stop time, dt)
- Anchor mode selection (Sector vs Sector-Material mode)
- Enhanced scenario management (load, save, create new)
- Save button protection for all settings

**Tab 3: Primary Mapping**
- Sector-wise product selection with start year configuration
- Mapping insights and parameter coverage analysis
- Dynamic table generation based on your selections

**Tab 4: Seeds**
- Configure initial seeding for anchor and direct clients
- Support for both sector and SM modes
- Active clients, elapsed quarters, and completed projects
- Primary mapping integration

**Tab 5: Client Revenue**
- 20 comprehensive parameters organized in 2 groups:
  - Market Activation (9 parameters): ATAM, lead generation, conversion rates
  - Orders (11 parameters): Phase durations, rates, growth, and limits

**Tab 6: Direct Market Revenue**
- 9 product-specific parameters in 2 groups:
  - Market Activation (5 parameters): Lead generation, conversion rates, TAM
  - Orders (4 parameters): Timing, quantities, growth rates

**Tab 7: Lookup Points**
- Time-series production capacity and pricing
- Year-based structure with dynamic row management
- Hold-last-value policy for extended timelines

**Tab 8: Runner**
- Scenario execution controls and monitoring
- Real-time progress tracking and status display
- Output file naming and execution options

**Tab 9: Logs**
- Live simulation logs with filtering capabilities
- Export functionality for analysis
- Auto-refresh and manual refresh options

**Tab 10: Results**
- Latest CSV preview with complete KPI data
- Plot gallery displaying generated visualizations
- Auto-discovery of latest results

All tabs feature save button protection, change tracking, and dynamic content management. The interface is clean and focused, with comprehensive parameter coverage and real-time validation.

### Run a Baseline Simulation

```bash
make run_baseline
```

This runs the default baseline scenario and generates output files.

### Run with Custom Scenario

```bash
# Using a preset scenario
python simulate_growth.py --preset price_shock

# Using a custom scenario file
python simulate_growth.py --scenario scenarios/my_scenario.yaml

# Generate plots
python simulate_growth.py --preset baseline --visualize
```

## 📁 Project Structure

```
FFF_Growth_System_v2/
├── src/                    # Core simulation engine
│   ├── growth_model.py        # SD model builder with BPTK_Py integration
│   ├── abm_anchor.py          # Anchor client agents (sector & SM modes)
│   ├── scenario_loader.py     # Scenario validation and YAML processing
│   ├── kpi_extractor.py       # Results processing and CSV generation
│   ├── phase1_data.py         # Input data loading and validation
│   ├── naming.py              # Canonical naming utilities
│   ├── validation.py          # Model validation and echo utilities
│   └── utils_logging.py       # Logging configuration
├── ui/                     # 10-Tab Streamlit interface
│   ├── app.py                 # Main 10-tab UI application
│   ├── components/            # Tab components and widgets
│   ├── services/              # UI services (scenario, validation, execution)
│   ├── state.py               # UI state management
│   └── utils/                 # UI helper utilities
├── scenarios/              # Scenario configurations
│   ├── baseline.yaml          # Default baseline scenario
├── Inputs/                 # Legacy CSV data (for reference)
├── tests/                   # Comprehensive test suite (107 tests)
├── viz/                     # Visualization utilities
├── logs/                    # Simulation logs and echo files
├── output/                  # Generated CSV results and plots
├── development_documentation/ # Technical documentation
├── user_documentation/      # User guides and tutorials
├── inputs.json             # Baseline model parameters
├── simulate_growth.py      # Main simulation runner
├── setup_cross_platform.py # Cross-platform setup script
└── Makefile                # Build automation
```

## 🔧 How the Model Works

### **Simulation Execution Flow**

1. **Initialization Phase**
   - Load baseline parameters from `inputs.json`
   - Apply scenario overrides from YAML files
   - Validate all parameters and constraints
   - Initialize System Dynamics model with BPTK_Py

2. **Agent Creation Phase**
   - Create anchor client agents based on sector configuration
   - Initialize direct client cohorts for each product
   - Set initial conditions (seeds) for active clients and completed projects

3. **Stepwise Simulation Loop** (Quarterly)
   - **Agent Action**: Each anchor client generates requirements based on lifecycle phase
   - **Demand Aggregation**: Collect all agent requirements and direct client demand
   - **Capacity Check**: Calculate fulfillment ratios based on production capacity
   - **Revenue Calculation**: Compute revenue from fulfilled orders and pricing
   - **State Update**: Advance all stocks, flows, and agent states
   - **KPI Capture**: Record metrics for the current time step

4. **Results Generation**
   - Extract comprehensive KPI data across all time steps
   - Generate CSV output with 20+ business metrics
   - Create visualization plots for key performance indicators

### **Key Model Equations**

#### **Anchor Client Lifecycle**
```
Potential Clients → Pending Activation → Active Clients
     ↓                    ↓                    ↓
Lead Generation → Conversion Rate → Project Generation → Project Completions → Product Supply
```

#### **Direct Client Cohorts**
```
New Leads → Client Conversion → Cohort Creation → Order Generation
     ↓              ↓                ↓              ↓
Lead Rate → Conversion Rate → Aging Process → Order Growth
```

#### **Capacity & Fulfillment**
```
Total Demand = Anchor Demand + Direct Client Demand
Fulfillment Ratio = min(1.0, Production Capacity / Total Demand)
Revenue = Fulfillment Ratio × Demand × Price
```

### **Parameter Categories**

The system manages 107+ parameters across several categories:

#### **Anchor Client Parameters (20 parameters)**
- **Market Activation**: Lead generation rates, conversion rates, activation delays
- **Project Lifecycle**: Project generation, duration, completion rates
- **Requirement Phases**: Initial, ramp, and steady-state parameters
- **Growth Dynamics**: Requirement growth rates and limits

#### **Direct Client Parameters (9 parameters)**
- **Lead Generation**: Inbound and outbound lead rates
- **Conversion**: Lead-to-client conversion rates
- **Order Behavior**: Order quantities, growth rates, timing delays
- **Market Constraints**: Total Addressable Market (TAM) limits

#### **Production & Pricing (Time-series)**
- **Capacity Constraints**: Maximum production per product per year
- **Pricing Strategy**: Price per unit per product per year
- **Timeline Management**: Hold-last-value policy for extended projections

## 🔧 Configuration

### **Baseline Configuration (inputs.json)**

The system uses `inputs.json` as the foundation for all simulations. This file contains:

- **Lists**: Markets, sectors, and products that define your simulation universe
- **Anchor Parameters**: 20+ parameters controlling anchor client behavior per sector
- **Direct Client Parameters**: 9 parameters controlling direct market dynamics per product
- **Production Data**: Time-series capacity constraints per product (2025-2031)
- **Pricing Data**: Time-series pricing per product (2025-2031)
- **Primary Mapping**: Which sectors use which products and when they start

### Customizing Sectors and Products

Edit `inputs.json` to define your own sectors and products:

```json
{
  "lists": [
    {
      "Sector": [
        "Your_Sector_1",
        "Your_Sector_2",
        "Custom_Industry"
      ]
    },
    {
      "Product": [
        "Your_Product_1",
        "Your_Product_2",
        "Custom_Product"
      ]
    }
  ]
}
```

The system will automatically adapt to use your custom sectors and products throughout the simulation.

### **Scenario Overrides System**

Scenarios allow you to modify any parameter without changing the baseline configuration:

```yaml
runspecs:
  starttime: 2025.0
  stoptime: 2030.0
  dt: 0.25
  anchor_mode: "sector"  # or "sm" for sector-material mode

overrides:
  constants:
    anchor_lead_generation_rate_Defense: 50.0
    requirement_to_order_lag_Defense: 2.0
  
  points:
    price_Silicon_Carbide_Fiber: [[2025, 100], [2030, 120]]
    max_capacity_Silicon_Carbide_Fiber: [[2025, 1000], [2030, 1500]]

seeds:
  active_anchor_clients:
    Defense: 5
  direct_clients:
    Silicon_Carbide_Fiber: 10
```

### **Business Value & Use Cases**

#### **Strategic Planning Scenarios**
- **Capacity Expansion**: "What if we double production capacity starting in 2026?"
- **Price Sensitivity**: "How will a 20% price increase affect revenue and market share?"
- **Market Entry**: "What's the impact of entering the Healthcare sector with existing products?"
- **Competitive Analysis**: "How will a 30% reduction in lead generation affect our business?"

#### **Operational Optimization**
- **Resource Planning**: "How many sales resources do we need to meet growth targets?"
- **Production Planning**: "What's our optimal capacity utilization strategy?"
- **Pricing Strategy**: "What pricing approach maximizes revenue over 5 years?"
- **Lead Generation**: "What's the ROI of increasing marketing spend by 50%?"

#### **Risk Assessment**
- **Economic Downturn**: "How resilient is our business to a 25% conversion rate drop?"
- **Supply Chain Disruption**: "What happens if capacity is reduced by 30%?"
- **Market Saturation**: "When will we hit TAM limits and need new markets?"

## 📊 Key Performance Indicators (KPIs)

The system generates 20+ comprehensive business metrics:

### **Revenue Metrics**
- **Total Revenue**: Overall business performance and growth trajectory
- **Revenue by Sector**: Which markets are most profitable and growing fastest
- **Revenue by Product**: Product line performance and profitability analysis
- **Revenue Growth Rate**: Business expansion rate and acceleration

### **Client Metrics**
- **Active Anchor Clients**: Current strategic client base size and growth
- **Client Acquisition Rate**: How fast you're gaining new strategic clients
- **Client Conversion Rate**: Lead-to-client conversion effectiveness
- **Client Lifetime Value**: Long-term client profitability and retention

### **Operational Metrics**
- **Capacity Utilization**: Production efficiency and bottleneck identification
- **Fulfillment Ratio**: Demand vs. supply balance and delivery performance
- **Lead Generation**: Marketing effectiveness and lead quality
- **Project Completion**: Delivery performance and client satisfaction

### **Financial Metrics**
- **Revenue per Client**: Average client value and growth potential
- **Revenue per Product**: Product profitability and investment priorities
- **Revenue per Sector**: Market profitability and resource allocation
- **Growth Rate**: Business expansion rate and market penetration

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
python -m pytest tests/test_phase*.py
python -m pytest tests/test_ui*.py

# Run with coverage
python -m pytest --cov=src tests/
```



## 📚 Documentation

### **User Documentation**
- **`user_documentation/tutorial.md`**: Complete step-by-step business user guide with scenarios
- **`user_documentation/systems_elements.md`**: Business logic and system elements explanation
- **`user_documentation/ui_explanations.md`**: Comprehensive 10-tab UI usage guide

### **Technical Documentation**
- **`index.md`**: Comprehensive codebase overview and implementation status
- **`development_documentation/technical_architecture.md`**: System design, equations, and UI architecture


### **Quick Reference**
- **`inputs.md`**: Detailed input parameter documentation
- **`CHANGELOG.md`**: Version history and feature updates
- **`CONTRIBUTING.md`**: Development guidelines and contribution process

## 🔄 Development Workflow

1. **Setup**: `make install` creates virtual environment
2. **Develop**: Edit source files in `src/`
3. **Test**: `make test` runs test suite
4. **Run**: `make run_ui` for interactive development
5. **Lint**: `make lint` for code quality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Product Growth System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


### **CSV Data Extraction**
The system can extract data from CSV files and integrate them into the `inputs.json` structure:

```bash
# Extract CSV data and create inputs.json
python make_lint.py --extract-csv

# Or run directly
python extract_csv_to_inputs.py
```

## 🎯 Roadmap

- [ ] Enhanced visualization options with interactive plots
- [ ] Performance optimization for large-scale simulations
- [ ] Multi-market support with regional dynamics
- [ ] Advanced sensitivity analysis tools
- [ ] Monte Carlo simulation capabilities

## 🚀 Getting Started

1. **Install**: Run `python setup_cross_platform.py` for one-command setup
2. **Learn**: Read `user_documentation/tutorial.md` for step-by-step guidance
3. **Explore**: Try the baseline scenario to understand the system
4. **Customize**: Create your own sectors and products in the UI
5. **Analyze**: Run scenarios and analyze results in the Results tab

---

**Note**: This is a production-ready research and analysis tool designed to be industry-agnostic. You can model any sector or product by configuring the inputs. The system includes real-world data from the advanced materials industry but can be adapted to any business domain. Results should be validated against real-world data and used as part of a comprehensive strategic analysis framework.
