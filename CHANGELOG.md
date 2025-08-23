# Changelog

All notable changes to the FFF Growth System v2 project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-19

### Added
- **Hybrid SD+ABM Architecture**: Combined System Dynamics and Agent-Based Modeling
- **Multi-Sector Support**: Defense, Nuclear, Semiconductors, Aviation sectors
- **Multi-Material Support**: Silicon Carbide, Boron Fiber, UHT, and other materials
- **Interactive Streamlit UI**: Scenario editor and runner with real-time validation
- **YAML Scenario System**: Flexible configuration with runtime overrides
- **Comprehensive KPI Extraction**: Revenue, capacity utilization, lead metrics
- **Visualization Tools**: Built-in plotting and analysis capabilities
- **Docker Support**: Containerized UI deployment option
- **Extensive Test Suite**: Unit tests covering all major components
- **Documentation**: Comprehensive guides and technical architecture docs

### Features
- **Phase 1**: JSON-based input ingestion and validation
- **Phase 2**: Canonical naming system for SD/ABM elements
- **Phase 3**: Scenario loader with strict validation
- **Phase 4**: Core SD model for direct clients and material flows
- **Phase 5**: ABM anchor client agents with lifecycle management
- **Phase 6**: ABM→SD gateways and anchor deliveries
- **Phase 7**: Stepwise runner with scheduler integration
- **Phase 8**: KPI extraction and CSV output generation
- **Phase 9**: Validation, logging, and error handling
- **Phase 10**: Regression testing and baseline validation
- **Phase 11**: Preset scenario management and validation
- **Phase 12**: Visualization and plotting capabilities
- **Phase 13**: Multi-material anchor support
- **Phase 14**: Scenario-based seeding system
- **Phase 15**: Variable horizon simulation support
- **Phase 16**: Per-(sector, material) parameter targeting
- **Phase 17**: SM-mode for strict per-(s,m) modeling

### Technical Improvements
- **Modular Architecture**: Clean separation of concerns
- **Type Safety**: Comprehensive type hints throughout
- **Error Handling**: Robust validation and error reporting
- **Performance**: Optimized simulation loops and data structures
- **Cross-Platform**: Support for macOS, Linux, and Windows

## [1.0.0] - Legacy Version

- Initial prototype implementation
- Basic System Dynamics model
- Limited sector and material support

---

## Version History Notes

- **Major versions** (X.0.0): Significant architectural changes
- **Minor versions** (X.Y.0): New features and capabilities
- **Patch versions** (X.Y.Z): Bug fixes and improvements

## Future Roadmap

### Planned for v2.1.0
- [ ] Additional material types
- [ ] Enhanced visualization options
- [ ] Performance optimization
- [ ] Cloud deployment support

### Planned for v2.2.0
- [ ] API endpoints for external integration
- [ ] Advanced scenario analysis tools
- [ ] Machine learning integration
- [ ] Real-time data feeds

### Long-term Goals
- [ ] Multi-market support (EU, Asia)
- [ ] Advanced agent behaviors
- [ ] Monte Carlo simulation
- [ ] Sensitivity analysis tools
