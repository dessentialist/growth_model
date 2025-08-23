# FFF Growth System v2

A hybrid System Dynamics + Agent-Based Modeling (SD+ABM) simulation system for analyzing growth patterns in the FFF (Fiber, Fabric, and Film) industry. The system models anchor client behavior, direct client dynamics, and material supply-demand interactions across multiple sectors.

## 🚀 Features

- **Hybrid Modeling**: Combines System Dynamics (SD) for aggregate flows with Agent-Based Modeling (ABM) for individual client behavior
- **Multi-Sector Support**: Models Defense, Nuclear, Semiconductors, Aviation, and other sectors
- **Multi-Material Support**: Handles Silicon Carbide, Boron Fiber, UHT, and other advanced materials
- **Flexible Scenarios**: YAML-based scenario configuration with runtime overrides
- **Interactive UI**: Streamlit-based scenario editor and runner
- **Comprehensive KPIs**: Revenue, capacity utilization, lead generation, and client metrics
- **Visualization**: Built-in plotting and analysis tools

## 📋 Prerequisites

- Python 3.12+ or 3.13+
- macOS, Linux, or Windows (tested on macOS)
- Git

## 🛠️ Installation

### Option 1: Using Make (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd Growth-Model

# Install dependencies and create virtual environment
make install

# Verify installation
make test
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Growth-Model

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## 🎯 Quick Start

### Run the Interactive UI

```bash
make run_ui
```

This opens a Streamlit interface at `http://localhost:8501` where you can:
- Edit scenario parameters
- Run simulations
- View results and plots
- Save custom scenarios

### Run a Baseline Simulation

```bash
make run_baseline
```

This runs the default baseline scenario and generates output files.

### Run with Custom Scenario

```bash
# Using a preset scenario
python simulate_fff_growth.py --preset price_shock

# Using a custom scenario file
python simulate_fff_growth.py --scenario scenarios/my_scenario.yaml

# Generate plots
python simulate_fff_growth.py --preset baseline --visualize
```

## 📁 Project Structure

```
Growth-Model/
├── src/                    # Core simulation engine
│   ├── fff_growth_model.py    # SD model builder
│   ├── abm_anchor.py          # Anchor client agents
│   ├── scenario_loader.py     # Scenario validation
│   └── kpi_extractor.py       # Results processing
├── ui/                     # Streamlit interface
│   ├── app.py                 # Main UI application
│   └── components/            # UI widgets
├── scenarios/              # Scenario configurations
│   ├── baseline.yaml          # Default scenario
│   ├── price_shock.yaml       # Price sensitivity example
│   └── high_capacity.yaml     # Capacity expansion example
├── tests/                   # Test suite
├── viz/                     # Visualization utilities
├── inputs.json             # Default model parameters
├── simulate_fff_growth.py  # Main simulation runner
└── Makefile                # Build automation
```

## 🔧 Configuration

### Model Parameters

The system uses `inputs.json` for default parameters:

- **Anchor Parameters**: Sector-specific client behavior (activation delays, lead generation, requirement phases)
- **Material Parameters**: Direct client behavior and market dynamics
- **Capacity & Pricing**: Time-series data for production capacity and material pricing
- **Primary Material Map**: Sector-to-material assignments with start years

### Scenario Overrides

Scenarios can override any parameter without modifying `inputs.json`:

```yaml
runspecs:
  starttime: 2025.0
  stoptime: 2030.0
  dt: 0.25

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

## 📊 Understanding the Model

### System Dynamics Components

- **Client Flows**: Lead generation → conversion → activation → requirements
- **Material Flows**: Capacity constraints → fulfillment ratios → delivery delays
- **Revenue Calculation**: Per-material pricing × delivered quantities

### Agent-Based Components

- **Anchor Clients**: Multi-phase requirement patterns with project lifecycles
- **Direct Clients**: Continuous demand generation with growth patterns
- **Material Allocation**: Capacity-constrained fulfillment with delays

### Key Metrics

- **Revenue**: Total and by-sector breakdowns
- **Capacity Utilization**: Material production efficiency
- **Lead Generation**: Anchor and direct client acquisition
- **Client Evolution**: Potential → Pending → Active transitions

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

## 🐳 Docker (Optional)

```bash
# Build UI container
docker build -f Dockerfile.ui -t fff-ui .

# Run with volume mounts
docker run --rm -p 8501:8501 \
  -v "$PWD/scenarios:/app/scenarios" \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/output:/app/output" \
  fff-ui
```

## 📚 Documentation

- **`index.md`**: Comprehensive codebase overview
- **`inputs.md`**: Detailed input parameter documentation
- **`technical_architecture.md`**: System design and equations
- **`implementation_plan.md`**: Development roadmap and phases
- **`tutorial.md`**: Step-by-step usage guide

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

[Add your license information here]

## 🆘 Support

For questions or issues:
1. Check the documentation in the `docs/` folder
2. Review existing issues
3. Create a new issue with detailed information

## 🎯 Roadmap

- [ ] Additional material types
- [ ] Enhanced visualization options
- [ ] Performance optimization
- [ ] Cloud deployment support
- [ ] API endpoints for external integration

---

**Note**: This is a research and analysis tool. Results should be validated against real-world data and used as part of a comprehensive analysis framework.
