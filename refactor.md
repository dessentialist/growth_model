# Growth Model UI Full Restructuring Implementation Plan

## Overview
This document outlines the **FRONT-END ONLY** restructuring of the Growth Model UI to implement the new table-based input system as specified in `migration.md`. 

**CRITICAL: This is a UI-layer change only. The backend remains completely unchanged:**
- **YAML scenario files**: Keep existing structure and format
- **BPTK_Py integration**: No modifications to model logic
- **Scenario validation**: Uses existing backend validation
- **Data persistence**: Existing YAML read/write mechanisms preserved
- **Model execution**: No changes to simulation engine

**LEVERAGING EXISTING ARCHITECTURE:**
The implementation will **modify and extend** the existing framework-agnostic UI components rather than rebuilding from scratch. The current `ui/state.py`, `ui/components/`, and `ui/services/` architecture provides an excellent foundation that we will enhance to meet the new requirements.

The implementation follows a phased approach where each phase delivers working functionality before proceeding to the next, ensuring no fallback mechanisms or hardcoded defaults are used. All changes are purely presentational and user experience improvements.

## Core Principles
- **FRONT-END ONLY**: All changes are UI-layer only; backend remains completely unchanged
- **LEVERAGE EXISTING**: Modify and extend current framework-agnostic UI components
- **No Fallback Mechanisms**: All parameters must come from user inputs; no hardcoded defaults in the model
- **Save Button Protection**: Tabs 1, 2, and 3 must have save buttons to prevent accidental parameter destruction
- **Framework Agnostic Business Logic**: Business logic modules must be completely independent of UI framework
- **Incremental Validation**: Each phase must be fully functional before proceeding to the next
- **Zero Backend Changes**: All modifications are UI-layer only; BPTK_Py integration remains untouched
- **Dynamic Table Generation**: Tables must update based on primary mapping changes without data loss
- **YAML Compatibility**: Must generate and consume existing YAML scenario format without modification

## Architecture Guidelines

### **FRONT-END ONLY IMPLEMENTATION**
**This restructuring is purely a UI-layer change. The following backend components remain completely unchanged:**

- **YAML Scenario Files**: Existing structure, format, and validation rules preserved
- **BPTK_Py Integration**: Model logic, simulation engine, and execution unchanged
- **Scenario Validation**: Backend validation rules and error handling unchanged
- **Data Persistence**: YAML read/write mechanisms and file handling unchanged
- **Model Execution**: Simulation parameters, agent behavior, and KPI calculation unchanged
- **Backend APIs**: All existing backend functions and interfaces unchanged

**What Changes:**
- UI presentation and user interaction patterns
- Data entry methods (from forms to tables)
- Tab structure and navigation (from 7 to 8 tabs)
- Front-end state management and validation
- User experience and workflow

**What Stays the Same:**
- All backend logic and model behavior
- YAML file structure and format
- Scenario validation rules
- Model execution and results
- File I/O and persistence

**New Tab Structure (8 tabs total):**
1. **Simulation Definitions**: Market/Sector/Product list management
2. **Simulation Specs**: Runtime controls and scenario management
3. **Primary Mapping**: Sector-product mapping with insights
4. **Client Revenue**: Comprehensive parameter tables (19 parameters)
5. **Direct Market Revenue**: Product-specific parameters (9 parameters)
6. **Lookup Points**: Time-series production capacity and pricing
7. **Runner**: Scenario execution and monitoring
8. **Logs**: Simulation logs and monitoring

### **LEVERAGING EXISTING COMPONENTS**
**Current Architecture to Preserve and Enhance:**

- **`ui/state.py`**: Extend existing state classes for new tab requirements
- **`ui/components/`**: Modify existing editors to use table-based input
- **`ui/services/`**: Enhance existing services for new functionality
- **Framework Agnostic Design**: Maintain existing separation of concerns
- **State Management**: Extend current state synchronization patterns

**Modification Strategy:**
- **Extend, Don't Replace**: Add new state fields and methods to existing classes
- **Enhance Components**: Convert existing form-based editors to table-based
- **Preserve APIs**: Maintain existing component interfaces where possible
- **Add New Components**: Create new components for new tab requirements
- **State Extensions**: Add new state classes for new data structures

### Business Logic Separation
- All business logic must be in `src/ui_logic/` modules (existing pattern)
- UI components only handle presentation and user interaction
- State management must be framework-agnostic (existing pattern)
- Validation and data transformation logic must be reusable

### Data Flow Patterns
- **Maintain existing YAML-based scenario management**: No changes to YAML structure or format
- **Use reactive state management patterns**: UI state management only, no backend changes
- **Implement proper error boundaries and validation**: UI validation only, backend validation unchanged
- **Ensure all user inputs are properly validated**: UI validation before sending to existing backend
- **Changes propagate only when save buttons are clicked**: UI state management, YAML generation unchanged
- **YAML compatibility**: Must generate exact same YAML format that existing backend expects

### Component Design
- Each tab must be a self-contained module with save functionality
- Shared components must be framework-agnostic (existing pattern)
- State synchronization must work across all tabs (existing pattern)
- Error handling must be consistent across all components
- Dynamic table generation must preserve unsaved changes
- **Modify existing components** rather than rebuilding

### Save Button Requirements
- **Tab 1 (Simulation Definitions)**: Save button for Market/Sector/Product lists
- **Tab 2 (Simulation Specs)**: Save button for Runtime and Scenario settings
- **Tab 3 (Primary Mapping)**: Save button for sector-product mappings
- **Tab 4 (Client Revenue)**: Save button for comprehensive parameter changes
- **Tab 5 (Direct Market Revenue)**: Save button for product-specific parameters
- **Tab 6 (Lookup Points)**: Save button for time-series data changes
- **Tab 7 (Runner)**: Save button for execution settings
- **Tab 8 (Logs)**: Save button for log configuration
- **Save Behavior**: Changes only propagate when save is clicked
- **Unsaved Changes**: Visual indicators for unsaved changes
- **Data Protection**: No accidental parameter destruction

### YAML Compatibility Requirements
- **Existing YAML Structure**: Must generate YAML files identical to current format
- **Backend Validation**: Must pass all existing backend validation rules
- **Scenario Loading**: Must load existing YAML files without modification
- **Parameter Mapping**: UI parameters must map 1:1 to existing YAML structure
- **No Format Changes**: YAML output must be compatible with existing backend

## Implementation Phases

### Timeline Summary
**Total Duration**: 8 weeks (increased due to missing tabs)  
**Phases**: 8 phases with incremental delivery  
**Approach**: Modify existing components with phased implementation

---

### Phase 1: Extend State Management and Create New Tab Structure
**Duration**: 1 week  
**Objective**: Extend existing state classes and establish new tab structure

#### Tasks
1. **Extend Existing State Classes**
   - **Modify `ui/state.py`**: Add new state classes for Simulation Definitions, Client Revenue, Direct Market Revenue, Lookup Points
   - **Extend `UIState`**: Add new state objects for new tabs
   - **Preserve Existing**: Keep all current state classes and methods unchanged
   - **Add New Methods**: Add methods for new data structures while maintaining compatibility

2. **Create New Tab Structure**
   - **Modify `ui/app.py`**: Replace current 7 tabs with new structure from migration.md
   - **Preserve Existing Logic**: Keep existing tab logic for Runspecs, Constants, Points, Primary Map, Seeds
   - **Add New Tabs**: Add Simulation Definitions, Client Revenue, Direct Market Revenue, Lookup Points, Runner, Logs tabs
   - **Maintain Navigation**: Use existing tab navigation patterns

3. **Extend State Management System**
   - **Enhance Existing**: Extend current state synchronization patterns
   - **Add Save Button State**: Implement save button state management for new tabs
   - **Create Unsaved Changes Tracking**: Add tracking for new tab types
   - **Maintain Compatibility**: Ensure existing functionality works unchanged

#### Success Criteria
- [ ] All existing state classes and methods preserved and functional
- [ ] New state classes added for new tab requirements
- [ ] New tab structure renders correctly with proper navigation (7 tabs total)
- [ ] Existing tabs (Runspecs, Constants, Points, Primary Map, Seeds) work unchanged
- [ ] Save button framework established for new tabs
- [ ] No hardcoded values in any business logic
- [ ] All existing functionality preserved

#### Testing Strategy
- **State Compatibility Tests**: Verify existing state classes work unchanged
- **New State Tests**: Test new state classes and methods
- **Tab Navigation Tests**: Verify new tab structure works correctly
- **Existing Functionality Tests**: Ensure all existing tabs work unchanged
- **State Tests**: Verify save button state management

#### Debugging Approach
- **State Compatibility Debugging**: Monitor existing state class behavior
- **New State Debugging**: Track new state class operations
- **Tab Navigation Debugging**: Log all tab switching events
- **Save Button Debugging**: Track save button state changes
- **Error Boundaries**: Add proper error handling for new tabs

#### Deliverables
- Extended state management system
- New tab structure with navigation (7 tabs total)
- Save button framework for new tabs
- Preserved existing functionality

---

### Phase 2: Modify Simulation Definitions Tab (Tab 1)
**Duration**: 1 week  
**Objective**: Convert existing components to table-based input for market/sector/product management

#### Tasks
1. **Modify Existing Components**
   - **Enhance `constants_editor.py`**: Convert to table-based input for lists
   - **Preserve Functionality**: Keep all existing validation and business logic
   - **Add Table Interface**: Implement `st.data_editor()` for list management
   - **Maintain API**: Keep existing component interface unchanged

2. **Implement List Management Tables**
   - **Market List Table**: Editable table for market definitions (Market 1, Market 2, etc.)
   - **Sector List Table**: Editable table for sector definitions with market relationships (Sector 1, Sector 2, etc.)
   - **Product List Table**: Editable table for product definitions with sector relationships (Product 1, Product 2, etc.)
   - **Dependency Validation**: Implement existing validation rules in table format

3. **Add Save Button Functionality**
   - **Extend Existing Save Pattern**: Use existing save button patterns from other components
   - **Implement Change Tracking**: Track unsaved changes for lists
   - **Add Visual Indicators**: Show unsaved changes clearly
   - **Implement Rollback**: Allow rollback of unsaved changes

#### Success Criteria
- [ ] All three lists (Market, Sector, Product) are editable in table format
- [ ] Existing validation rules work correctly in table format
- [ ] Save button prevents accidental data loss
- [ ] Unsaved changes are clearly indicated
- [ ] List dependencies are properly validated
- [ ] No hardcoded defaults are used
- [ ] Existing functionality preserved

#### Testing Strategy
- **Component Modification Tests**: Test modified existing components
- **Table Functionality Tests**: Test table-based input operations
- **Validation Tests**: Verify existing validation rules work in tables
- **Save Button Tests**: Test save functionality and change protection
- **Compatibility Tests**: Ensure existing scenarios still work

#### Debugging Approach
- **Component Debugging**: Monitor modified component behavior
- **Table Debugging**: Track table operations and data updates
- **Validation Debugging**: Monitor validation in table format
- **Save Button Debugging**: Track save operations and state changes
- **Compatibility Debugging**: Monitor existing functionality

#### Deliverables
- Modified existing components with table-based input
- Market/Sector/Product list tables
- Save button with change protection
- Preserved existing validation and functionality

---

### Phase 3: Modify Simulation Specs Tab (Tab 2)
**Duration**: 1 week  
**Objective**: Enhance existing runspecs form with save protection and new scenario management

#### Tasks
1. **Enhance Existing Runspecs Form**
   - **Modify `runspecs_form.py`**: Add save button and change tracking
   - **Preserve Functionality**: Keep all existing validation and input logic
   - **Add Save Protection**: Implement save button to prevent accidental changes
   - **Maintain API**: Keep existing component interface unchanged

2. **Add New Scenario Management**
   - **Runtime Controls**: start time, stop time, dt (time steps)
   - **Anchor Mode Selection**: Sector-Product Mapping mode vs Sector mode
   - **Scenario Name Input**: Add scenario name input field
   - **Load Scenario Functionality**: Implement scenario loading from existing YAML files
   - **Reset to Baseline**: Add baseline reset functionality (baseline as 'special' scenario)
   - **Save Button Integration**: Integrate with existing save button framework

3. **Enhance Validation and State Management**
   - **Extend Existing Validation**: Add new validation rules for scenario management
   - **Implement Change Tracking**: Track unsaved changes for runspecs
   - **Add Visual Indicators**: Show unsaved changes clearly
   - **Implement Rollback**: Allow rollback of unsaved changes

#### Success Criteria
- [ ] Runtime controls (start/stop/dt) are editable and validated
- [ ] Anchor mode selection (sector vs sector+product) works correctly
- [ ] Scenario name and management functions work
- [ ] Load scenario functionality works correctly
- [ ] Reset to baseline functionality works correctly
- [ ] Save button prevents accidental changes
- [ ] All parameters are properly validated
- [ ] No hardcoded defaults are used
- [ ] Existing functionality preserved

#### Testing Strategy
- **Component Enhancement Tests**: Test enhanced existing components
- **New Functionality Tests**: Test new scenario management features
- **Validation Tests**: Verify enhanced validation rules
- **Save Button Tests**: Test save functionality and change protection
- **Compatibility Tests**: Ensure existing scenarios still work

#### Debugging Approach
- **Component Enhancement Debugging**: Monitor enhanced component behavior
- **New Functionality Debugging**: Track new feature operations
- **Validation Debugging**: Monitor enhanced validation
- **Save Button Debugging**: Track save operations and state changes
- **Compatibility Debugging**: Monitor existing functionality

#### Deliverables
- Enhanced runspecs form with save protection
- New scenario management functionality
- Save button with change protection
- Preserved existing validation and functionality

---

### Phase 4: Modify Primary Mapping Tab (Tab 3)
**Duration**: 1 week  
**Objective**: Enhance existing primary map editor with save protection and dynamic table generation

#### Tasks
1. **Enhance Existing Primary Map Editor**
   - **Modify `primary_map_editor.py`**: Add save button and change tracking
   - **Preserve Functionality**: Keep all existing mapping logic and validation
   - **Add Save Protection**: Implement save button to prevent accidental changes
   - **Maintain API**: Keep existing component interface unchanged

2. **Implement Dynamic Table Generation**
   - **Enhance Existing Tables**: Modify existing table generation for dynamic updates
   - **Sector-Product Mapping Interface**: Enhance existing mapping interface
   - **Mapping Insights and Summary**: Add enhanced display of mapping relationships
   - **Dynamic Updates**: Implement tables that update based on list changes

3. **Add Save Button and Change Protection**
   - **Extend Existing Save Pattern**: Use existing save button patterns
   - **Implement Change Tracking**: Track unsaved changes for mappings
   - **Add Visual Indicators**: Show unsaved changes clearly
   - **Implement Rollback**: Allow rollback of unsaved changes

#### Success Criteria
- [ ] Sector-product mapping table is fully functional
- [ ] Dynamic table generation works correctly
- [ ] Mapping insights and summary are displayed
- [ ] Save button prevents accidental mapping changes
- [ ] All mappings are properly validated
- [ ] No hardcoded defaults are used
- [ ] Existing functionality preserved

#### Testing Strategy
- **Component Enhancement Tests**: Test enhanced existing components
- **Dynamic Table Tests**: Test dynamic table generation and updates
- **Validation Tests**: Verify mapping validation in enhanced format
- **Save Button Tests**: Test save functionality and change protection
- **Compatibility Tests**: Ensure existing mappings still work

#### Debugging Approach
- **Component Enhancement Debugging**: Monitor enhanced component behavior
- **Dynamic Table Debugging**: Track dynamic table updates
- **Validation Debugging**: Monitor mapping validation
- **Save Button Debugging**: Track save operations and state changes
- **Compatibility Debugging**: Monitor existing functionality

#### Deliverables
- Enhanced primary map editor with save protection
- Dynamic table generation system
- Save button with change protection
- Preserved existing mapping functionality

---

### Phase 5: Create Client Revenue Tab (Tab 4)
**Duration**: 1.5 weeks  
**Objective**: Create new component for comprehensive client revenue parameter tables with exact parameter coverage

#### Tasks
1. **Create New Client Revenue Component**
   - **New Component**: Create `client_revenue_editor.py` following existing patterns
   - **Follow Existing Architecture**: Use same patterns as existing components
   - **Framework Agnostic**: Ensure component is framework-agnostic like existing ones
   - **State Integration**: Integrate with existing state management system

2. **Implement Dynamic Parameter Tables with Exact Parameter Coverage**
   - **Market Activation Parameters**: 
     - ATAM (total anchor clients for sector-material combination)
     - anchor_start_year (market activation year)
     - anchor_lead_generation_rate (leads per quarter)
     - lead_to_pc_conversion_rate (lead to potential client conversion)
     - project_generation_rate (projects per quarter from potential client)
     - project_duration (average project duration in quarters)
     - projects_to_client_conversion (projects needed to become client)
     - max_projects_per_pc (maximum projects per potential client)
     - anchor_client_activation_delay (delay before commercial orders)
   - **Orders Parameters**:
     - initial_phase_duration (initial testing phase quarters)
     - initial_requirement_rate (starting kg/quarter/client)
     - initial_req_growth (percentage growth in initial phase)
     - ramp_phase_duration (ramp-up phase quarters)
     - ramp_requirement_rate (starting kg/quarter in ramp phase)
     - ramp_req_growth (percentage growth in ramp phase)
     - steady_requirement_rate (starting kg/quarter in steady state)
     - steady_req_growth (percentage growth in steady state)
     - requirement_to_order_lag (requirement to delivery delay)
   - **Seeds Parameters**:
     - completed_projects_sm (completed projects backlog)
     - active_anchor_clients_sm (active clients at T0)
     - elapsed_quarters (aging since client activation)

3. **Implement Dynamic Content Management**
   - **Y-axis as sector_product values**: Tables dynamically populate based on primary mapping selections
   - **Dynamic Content**: Tables that update when primary mapping changes
   - **Parameter Validation**: Implement validation rules for all parameter types
   - **Save Button**: Implement save button following existing patterns

#### Success Criteria
- [ ] Dynamic parameter tables generate correctly based on mappings
- [ ] All 19 specific parameters are properly implemented (9 Market Activation + 9 Orders + 3 Seeds)
- [ ] Y-axis shows sector_product combinations from primary mapping
- [ ] Parameter validation works correctly
- [ ] Save button prevents accidental parameter changes
- [ ] Tables update dynamically with mapping changes
- [ ] No hardcoded defaults are used
- [ ] Integrates seamlessly with existing system

#### Testing Strategy
- **New Component Tests**: Test new client revenue component
- **Table Generation Tests**: Test dynamic table creation and updates
- **Parameter Tests**: Verify all 19 parameter categories and validation
- **Dynamic Update Tests**: Test table updates with mapping changes
- **Integration Tests**: Test integration with existing system
- **Save Button Tests**: Verify save functionality and change protection

#### Debugging Approach
- **New Component Debugging**: Monitor new component behavior
- **Table Generation Debugging**: Log all table generation events
- **Parameter Debugging**: Track parameter changes and validation
- **Dynamic Update Debugging**: Monitor table update operations
- **Integration Debugging**: Monitor integration with existing system
- **Save Button Debugging**: Track save operations

#### Deliverables
- New client revenue component
- Dynamic parameter tables with exact parameter coverage (19 parameters)
- Save button with change protection
- Seamless integration with existing system

---

### Phase 6: Create Direct Market Revenue Tab (Tab 5)
**Duration**: 1 week  
**Objective**: Create new component for product-specific direct market revenue parameters

#### Tasks
1. **Create Direct Market Revenue Component**
   - **New Component**: Create `direct_market_revenue_editor.py` following existing patterns
   - **Product-Specific Parameters**: Implement all 9 required parameters per product
   - **Dynamic Content**: Tables that update with product list changes
   - **Save Button**: Implement save button following existing patterns

2. **Implement Exact Parameter Coverage**
   - **lead_start_year**: Year material begins receiving other-client leads
   - **inbound_lead_generation_rate**: Per quarter inbound leads for material
   - **outbound_lead_generation_rate**: Per quarter outbound leads for material
   - **lead_to_c_conversion_rate**: Lead to client conversion (fraction)
   - **lead_to_requirement_delay**: Lead-to-requirement delay for first order (quarters)
   - **requirement_to_fulfilment_delay**: Requirement-to-delivery delay for running requirements (quarters)
   - **avg_order_quantity_initial**: Starting order quantity (units per client)
   - **client_requirement_growth**: Percentage growth of order quantity per quarter
   - **TAM**: Total addressable market for other clients (clients)

3. **Implement Dynamic Content Management**
   - **Y-axis as sector_product values**: Tables dynamically populate based on primary mapping selections
   - **Dynamic Content**: Tables that update with product list changes
   - **Parameter Validation**: Implement validation rules for all parameter types
   - **Save Button**: Implement save button following existing patterns

#### Success Criteria
- [ ] Direct market revenue tables are fully functional
- [ ] All 9 specific parameters are properly implemented and validated
- [ ] Y-axis shows sector_product combinations from primary mapping
- [ ] Tables update dynamically with product changes
- [ ] Save button prevents accidental parameter changes
- [ ] Parameter validation works correctly
- [ ] No hardcoded defaults are used
- [ ] Integrate seamlessly with existing system

#### Testing Strategy
- **New Component Tests**: Test new direct market revenue component
- **Parameter Tests**: Test all 9 parameters and validation
- **Dynamic Update Tests**: Test table updates with product changes
- **Integration Tests**: Test integration with existing system
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **New Component Debugging**: Monitor new component behavior
- **Parameter Debugging**: Track parameter changes and validation
- **Dynamic Update Debugging**: Track table update operations
- **Integration Debugging**: Monitor integration with existing system
- **Save Button Debugging**: Track save operations

#### Deliverables
- Direct market revenue component
- Dynamic parameter tables with exact parameter coverage (9 parameters)
- Save button with change protection
- Seamless integration with existing system

---

### Phase 7: Create Lookup Points Tab (Tab 6)
**Duration**: 1 week  
**Objective**: Create new component for time-series lookup points for production capacity and pricing

#### Tasks
1. **Create Lookup Points Component**
   - **New Component**: Create `lookup_points_editor.py` following existing patterns
   - **Time-Series Parameters**: Implement production capacity and pricing per product per year
   - **Year-Based Input**: Tables with years as columns and products as rows
   - **Save Button**: Implement save button following existing patterns

2. **Implement Exact Parameter Coverage**
   - **Production Capacity in Units**: max_capacity_<product> lookup tables
   - **Price Per Unit**: price_<product> lookup tables
   - **Year-Based Structure**: Years as columns, products as rows
   - **Dynamic Content**: Tables that update with product list changes

3. **Implement Dynamic Content Management**
   - **Y-axis as years**: Tables with years as columns
   - **Product Rows**: Each product gets a row in the table
   - **Parameter Validation**: Implement validation rules for time-series data
   - **Save Button**: Implement save button following existing patterns

#### Success Criteria
- [ ] Lookup points tables are fully functional
- [ ] Production capacity tables (max_capacity_<product>) work correctly
- [ ] Price tables (price_<product>) work correctly
- [ ] Year-based structure is properly implemented
- [ ] Parameter validation works correctly
- [ ] Save button prevents accidental parameter changes
- [ ] Time-series consistency is maintained
- [ ] No hardcoded defaults are used
- [ ] Integrate seamlessly with existing system

#### Testing Strategy
- **New Component Tests**: Test new lookup points component
- **Parameter Tests**: Test all lookup point parameters
- **Time-Series Tests**: Verify time-series validation
- **Dynamic Update Tests**: Test table updates with product changes
- **Validation Tests**: Test parameter validation rules
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **New Component Debugging**: Monitor new component behavior
- **Parameter Debugging**: Track parameter changes and validation
- **Time-Series Debugging**: Monitor time-series validation
- **Dynamic Update Debugging**: Track table update operations
- **Validation Debugging**: Track parameter validation
- **Save Button Debugging**: Track save operations

#### Deliverables
- Lookup points component
- Time-series parameter management (production capacity and pricing)
- Save button with change protection
- Comprehensive validation system

---

### Phase 8: Create Runner and Logs Tabs (Tabs 7-8)
**Duration**: 0.5 weeks  
**Objective**: Create new components for scenario execution and monitoring functionality

#### Tasks
1. **Create Runner Tab Component (Tab 7)**
   - **New Component**: Create `runner_tab.py` following existing patterns
   - **Scenario Controls**: Save, validate, and run controls
   - **Execution Monitoring**: Scenario execution monitoring and progress tracking
   - **Status Display**: Real-time status display and error handling
   - **Save Button**: Implement save button following existing patterns

2. **Create Logs Tab Component (Tab 8)**
   - **New Component**: Create `logs_tab.py` following existing patterns
   - **Simulation Logs**: Display simulation logs with real-time streaming
   - **Log Filtering**: Log filtering and search capabilities
   - **Log Export**: Log export functionality
   - **Save Button**: Implement save button following existing patterns

3. **Integrate with Existing System**
   - **State Management**: Integrate with existing state management patterns
   - **Validation**: Use existing validation client and patterns
   - **YAML Generation**: Ensure compatibility with existing YAML format
   - **Consistent Patterns**: Follow same patterns as existing components

#### Success Criteria
- [ ] Runner tab provides complete scenario execution control
- [ ] Logs tab displays simulation logs correctly
- [ ] All parameter tabs integrate with runner functionality
- [ ] Scenario validation works comprehensively
- [ ] Error handling provides clear user feedback
- [ ] Save buttons prevent accidental changes
- [ ] No hardcoded defaults are used
- [ ] Integrate seamlessly with existing system

#### Testing Strategy
- **New Component Tests**: Test new runner and logs components
- **Execution Tests**: Test all execution controls
- **Log Tests**: Verify log display and streaming
- **Integration Tests**: Test parameter tab integration
- **Validation Tests**: Test comprehensive scenario validation
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **New Component Debugging**: Monitor new component behavior
- **Execution Debugging**: Log all execution operations
- **Log Debugging**: Monitor log display and streaming
- **Integration Debugging**: Track parameter tab integration
- **Validation Debugging**: Monitor scenario validation
- **Save Button Debugging**: Track save operations

#### Deliverables
- Runner tab component
- Logs tab component
- Save buttons with change protection
- Seamless integration with existing system

## Testing Strategy

### **Backend Compatibility Testing**
**Since this is front-end only, we must ensure complete compatibility with existing backend:**

- **YAML Generation Tests**: Verify generated YAML matches existing format exactly
- **Backend Validation Tests**: Ensure all UI inputs pass existing backend validation
- **Scenario Loading Tests**: Verify existing YAML files load correctly in new UI
- **Parameter Mapping Tests**: Confirm UI parameters map correctly to YAML structure
- **Integration Tests**: Test complete workflow from UI input to backend execution

### Unit Testing
- **Existing Component Tests**: Test modified existing components
- **New Component Tests**: Test new components following existing patterns
- **State Management Tests**: Test extended state management system
- **Validation Logic Tests**: Test all validation rules and error handling
- **Utility Functions Tests**: Test all helper and utility functions

### Integration Testing
- **Tab Integration**: Test interaction between different tabs
- **State Synchronization**: Verify state consistency across components
- **Data Flow**: Test complete data flow from input to output
- **Error Handling**: Test error propagation and recovery
- **Backend Compatibility**: Test complete workflow with existing backend

### UI Testing
- **Component Rendering**: Test all UI components render correctly
- **User Interaction**: Test all user interactions and responses
- **Responsive Design**: Test UI behavior across different screen sizes
- **Accessibility**: Test accessibility features and compliance
- **Table Functionality**: Test all table-based input operations

### End-to-End Testing
- **Complete Workflows**: Test complete user workflows
- **Scenario Management**: Test full scenario lifecycle
- **Data Persistence**: Test data saving and loading
- **Performance**: Test performance under realistic conditions
- **Backend Integration**: Test complete workflow with existing backend

## Debugging and Monitoring

### Logging Strategy
- **Existing Component Logging**: Preserve existing logging patterns
- **New Component Logging**: Add logging for new components
- **State Management Logging**: Log all state management operations
- **Error Logging**: Log all errors with stack traces and context
- **Performance Logging**: Log performance metrics and bottlenecks

### Error Handling
- **Error Boundaries**: Implement proper error boundaries at component level
- **User Feedback**: Provide clear error messages and recovery options
- **Error Recovery**: Implement automatic error recovery where possible
- **Error Reporting**: Collect and report errors for analysis
- **Preserve Existing**: Maintain existing error handling patterns

### Monitoring Tools
- **State Inspection**: Tools for inspecting component and application state
- **Performance Monitoring**: Real-time performance metrics
- **Error Tracking**: Comprehensive error tracking and reporting
- **User Analytics**: Track user behavior and workflow patterns
- **Backend Compatibility**: Monitor backend integration and validation

## Quality Assurance

### Code Quality
- **Linting**: Enforce consistent code style and quality
- **Type Checking**: Use type hints and validation
- **Documentation**: Comprehensive code documentation
- **Code Review**: Peer review process for all changes
- **Preserve Patterns**: Maintain existing code quality patterns

### Performance Requirements
- **Response Time**: UI interactions must respond within 100ms
- **Rendering Performance**: Complex tables must render within 2 seconds
- **Memory Usage**: Memory usage must remain stable during extended use
- **Scalability**: UI must handle large datasets without performance degradation
- **Existing Performance**: Maintain or improve existing performance

### Security Requirements
- **Input Validation**: All user inputs must be properly validated
- **Data Sanitization**: All data must be sanitized before processing
- **Access Control**: Implement proper access control for sensitive operations
- **Audit Logging**: Log all sensitive operations for audit purposes
- **Preserve Security**: Maintain existing security patterns

## Risk Mitigation

### Technical Risks
- **Component Modification**: Risk of breaking existing functionality during modification
- **State Management Complexity**: Risk of state synchronization issues
- **Dynamic Table Generation**: Risk of performance issues with large tables
- **Cross-Tab Dependencies**: Risk of circular dependencies and infinite loops
- **Data Integrity**: Risk of data corruption during complex operations

### Mitigation Strategies
- **Incremental Implementation**: Each phase must be fully functional before proceeding
- **Comprehensive Testing**: Extensive testing at each phase
- **Rollback Plan**: Ability to rollback to previous working version
- **Performance Monitoring**: Continuous performance monitoring throughout development
- **Preserve Existing**: Maintain existing functionality while adding new features

### Contingency Plans
- **Phase Rollback**: If any phase fails, rollback to previous working state
- **Alternative Approaches**: Have alternative implementation approaches ready
- **Extended Timeline**: Buffer time for unexpected issues
- **Expert Consultation**: Access to framework experts if needed
- **Component Isolation**: Isolate changes to prevent cascading failures

## Success Metrics

### Functional Metrics
- [ ] All requested features implemented and working
- [ ] No regression in existing functionality
- [ ] All validations and error handling working correctly
- [ ] Performance meets or exceeds requirements
- [ ] Save buttons prevent accidental data loss
- [ ] Backend compatibility maintained

### Quality Metrics
- [ ] All tests passing
- [ ] Code coverage above 90%
- [ ] No critical bugs or security vulnerabilities
- [ ] Documentation complete and accurate
- [ ] Existing patterns preserved

### User Experience Metrics
- [ ] UI is intuitive and user-friendly
- [ ] All workflows are efficient and logical
- [ ] Error messages are clear and actionable
- [ ] Performance meets user expectations
- [ ] Save buttons provide clear data protection
- [ ] Table-based input improves usability

## Conclusion

This implementation plan provides a comprehensive roadmap for **FRONT-END ONLY** restructuring of the Growth Model UI to implement the new table-based input system as specified in `migration.md`. 

**CRITICAL SUCCESS FACTOR: Backend Compatibility**
The phased approach ensures each step delivers working functionality while maintaining **complete compatibility with existing backend systems**. This is not a rewrite or backend modification - it's purely a UI enhancement that leverages your existing excellent framework-agnostic architecture.

**LEVERAGING EXISTING EXCELLENCE:**
The plan emphasizes **modifying and extending** your existing components rather than rebuilding:
- **Extend, Don't Replace**: Add new functionality to existing components
- **Preserve Patterns**: Maintain your excellent framework-agnostic design
- **Enhance Architecture**: Build upon your solid foundation
- **Maintain Compatibility**: Keep all existing functionality working

The plan emphasizes:
- **FRONT-END ONLY** - all backend logic, YAML structure, and validation remain unchanged
- **LEVERAGE EXISTING** - modify and extend current excellent components
- **No fallback mechanisms** - all parameters must come from user inputs
- **Save button protection** - preventing accidental parameter destruction
- **YAML compatibility** - must generate identical format to existing backend
- **Comprehensive testing** at each phase with backend compatibility validation
- **Incremental validation** to catch issues early
- **Risk mitigation** through proper planning and contingencies
- **Quality assurance** through proper processes and metrics

By following this plan, we can successfully deliver a modern, feature-rich UI that provides the enhanced user experience requested while maintaining **100% backend compatibility** and ensuring data integrity through save button protection.

**The backend will continue to work exactly as it does today - only the user interface will be improved by enhancing your existing excellent components.**

---

## Implementation Notes

### **Complete Parameter Coverage by Tab**
**This implementation plan ensures complete coverage of all parameters specified in `migration.md`:**

**Tab 1: Simulation Definitions**
- Market list management (Market 1, Market 2, etc.)
- Sector list management (Sector 1, Sector 2, etc.)
- Product list management (Product 1, Product 2, etc.)

**Tab 2: Simulation Specs**
- Runtime controls (start time, stop time, dt)
- Anchor mode selection (Sector vs Sector+Product mode)
- Scenario name and management
- Load scenario functionality
- Reset to baseline functionality

**Tab 3: Primary Mapping**
- Sector-wise product selection
- Mapping insights and summary
- Dynamic table generation based on list changes

**Tab 4: Client Revenue (19 Parameters)**
- **Market Activation (9 parameters)**: ATAM, anchor_start_year, anchor_lead_generation_rate, lead_to_pc_conversion_rate, project_generation_rate, project_duration, projects_to_client_conversion, max_projects_per_pc, anchor_client_activation_delay
- **Orders (9 parameters)**: initial_phase_duration, initial_requirement_rate, initial_req_growth, ramp_phase_duration, ramp_requirement_rate, ramp_req_growth, steady_requirement_rate, steady_req_growth, requirement_to_order_lag
- **Seeds (3 parameters)**: completed_projects_sm, active_anchor_clients_sm, elapsed_quarters

**Tab 5: Direct Market Revenue (9 Parameters)**
- lead_start_year, inbound_lead_generation_rate, outbound_lead_generation_rate, lead_to_c_conversion_rate, lead_to_requirement_delay, requirement_to_fulfilment_delay, avg_order_quantity_initial, client_requirement_growth, TAM

**Tab 6: Lookup Points**
- Production Capacity in Units (max_capacity_<product>)
- Price Per Unit (price_<product>)
- Year-based structure with years as columns

**Tab 7: Runner**
- Scenario save, validate, and run controls
- Execution monitoring and progress tracking

**Tab 8: Logs**
- Simulation logs display and monitoring
- Log filtering and export functionality

### **Component Modification Strategy**
**Instead of rebuilding, we will modify existing components:**

1. **Extend Existing State Classes**: Add new fields and methods to existing classes
2. **Enhance Existing Components**: Convert form-based input to table-based input
3. **Preserve Existing APIs**: Keep all existing interfaces and methods unchanged
4. **Add New Components**: Create new components only for completely new functionality
5. **Maintain Patterns**: Follow existing patterns for consistency

### Save Button Implementation Pattern
All save buttons must follow this consistent pattern (extending existing patterns):
1. **Change Tracking**: Track all unsaved changes in component state
2. **Visual Indicators**: Show clear indicators for unsaved changes
3. **Save Validation**: Validate all changes before saving
4. **State Commit**: Only commit changes when save is clicked
5. **Rollback Support**: Provide ability to rollback unsaved changes

### Dynamic Table Generation Pattern
All dynamic tables must follow this pattern (extending existing patterns):
1. **Data Source**: Tables populate from current state, not hardcoded values
2. **Change Propagation**: Changes only propagate when explicitly saved
3. **Dependency Management**: Handle cross-tab dependencies correctly
4. **Performance Optimization**: Ensure tables render efficiently
5. **Error Handling**: Gracefully handle table generation errors

### No Fallback Mechanisms
The system must never use fallback mechanisms:
1. **No Hardcoded Defaults**: All values must come from user input or existing data
2. **No Automatic Fallbacks**: System must fail gracefully if required data is missing
3. **User-Driven Values**: All parameters must be explicitly set by users
4. **Validation Required**: All inputs must pass validation before use
5. **Clear Error Messages**: Users must understand what data is required

### **Preserving Existing Excellence**
**Key principles for maintaining your excellent architecture:**

1. **Framework Agnostic**: Keep all business logic framework-agnostic
2. **State Management**: Extend existing state management patterns
3. **Component Design**: Follow existing component design patterns
4. **Validation**: Use existing validation patterns and clients
5. **Testing**: Maintain existing testing patterns and coverage
6. **Documentation**: Update documentation to reflect changes
7. **Performance**: Maintain or improve existing performance
8. **Security**: Preserve existing security patterns
