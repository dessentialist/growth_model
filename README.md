# Product Growth System

A hybrid System Dynamics + Agent-Based Modeling (SD+ABM) simulation system for analyzing growth patterns across any industry or sector. The system models anchor client behavior, direct client dynamics, and product supply-demand interactions with fully customizable sectors and products.

## 🚀 Features

- **Hybrid Modeling**: Combines System Dynamics (SD) for aggregate flows with Agent-Based Modeling (ABM) for individual client behavior
- **Industry Agnostic**: Models any sectors and products you define - Defense, Nuclear, Semiconductors, Aviation, or any custom industry
- **Multi-Product Support**: Handles any product types with configurable parameters and market dynamics
- **Flexible Scenarios**: YAML-based scenario configuration with runtime overrides
- **Interactive UI**: Streamlit-based scenario editor and runner
- **Comprehensive KPIs**: Revenue, capacity utilization, lead generation, and client metrics
- **Visualization**: Built-in plotting and analysis tools
- **Generalized Architecture**: No hard-coded industry assumptions - everything is configurable

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
python simulate_growth.py --preset price_shock

# Using a custom scenario file
python simulate_growth.py --scenario scenarios/my_scenario.yaml

# Generate plots
python simulate_growth.py --preset baseline --visualize
```

## 📁 Project Structure

```
Growth-Model/
├── src/                    # Core simulation engine
│   ├── growth_model.py        # SD model builder
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
├── simulate_growth.py      # Main simulation runner
└── Makefile                # Build automation
```

## 🔧 Configuration

### Model Parameters

The system uses `inputs.json` for default parameters. You can customize:

- **Sectors**: Define any industry sectors (e.g., Defense, Nuclear, Semiconductors, Aviation, or custom sectors)
- **Products**: Define any product types with their specific characteristics
- **Anchor Parameters**: Sector-specific client behavior (activation delays, lead generation, requirement phases)
- **Product Parameters**: Direct client behavior and market dynamics
- **Capacity & Pricing**: Time-series data for production capacity and product pricing
- **Primary Product Map**: Sector-to-product assignments with start years

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

### Scenario Overrides

Scenarios can override any parameter without modifying `inputs.json`:

```yaml
runspecs:
  starttime: 2025.0
  stoptime: 2030.0
  dt: 0.25

overrides:
  constants:
    anchor_lead_generation_rate_Your_Sector: 50.0
    requirement_to_order_lag_Your_Sector: 2.0
  
  points:
    price_Your_Product: [[2025, 100], [2030, 120]]
    max_capacity_Your_Product: [[2025, 1000], [2030, 1500]]

seeds:
  active_anchor_clients:
    Your_Sector: 5
  direct_clients:
    Your_Product: 10
```

## 📊 Understanding the Model

### System Dynamics Components

- **Client Flows**: Lead generation → conversion → activation → requirements
- **Product Flows**: Capacity constraints → fulfillment ratios → delivery delays
- **Revenue Calculation**: Per-product pricing × delivered quantities

### Agent-Based Components

- **Anchor Clients**: Multi-phase requirement patterns with project lifecycles
- **Direct Clients**: Continuous demand generation with growth patterns
- **Product Allocation**: Capacity-constrained fulfillment with delays

### Key Metrics

- **Revenue**: Total and by-sector breakdowns
- **Capacity Utilization**: Product production efficiency
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
docker build -f Dockerfile.ui -t product-growth-ui .

# Run with volume mounts
docker run --rm -p 8501:8501 \
  -v "$PWD/scenarios:/app/scenarios" \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/output:/app/output" \
  product-growth-ui
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

- [ ] Additional product types and market dynamics
- [ ] Enhanced visualization options
- [ ] Performance optimization
- [ ] Cloud deployment support
- [ ] API endpoints for external integration
- [ ] Multi-market support (EU, Asia, etc.)

---

**Note**: This is a research and analysis tool designed to be industry-agnostic. You can model any sector or product by configuring the inputs. Results should be validated against real-world data and used as part of a comprehensive analysis framework.
