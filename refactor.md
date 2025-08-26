# Growth Model UI Full Restructuring Implementation Plan

## Overview
This document outlines the **FRONT-END ONLY** restructuring of the Growth Model UI to implement the new table-based input system as specified in `migration.md`. 

**CRITICAL: This is a UI-layer change only. The backend remains completely unchanged:**
- **YAML scenario files**: Keep existing structure and format
- **BPTK_Py integration**: No modifications to model logic
- **Scenario validation**: Uses existing backend validation
- **Data persistence**: Existing YAML read/write mechanisms preserved
- **Model execution**: No changes to simulation engine

The implementation follows a phased approach where each phase delivers working functionality before proceeding to the next, ensuring no fallback mechanisms or hardcoded defaults are used. All changes are purely presentational and user experience improvements.

## Core Principles
- **FRONT-END ONLY**: All changes are UI-layer only; backend remains completely unchanged
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
- Tab structure and navigation
- Front-end state management and validation
- User experience and workflow

**What Stays the Same:**
- All backend logic and model behavior
- YAML file structure and format
- Scenario validation rules
- Model execution and results
- File I/O and persistence

### Business Logic Separation
- All business logic must be in `src/ui_logic/` modules
- UI components only handle presentation and user interaction
- State management must be framework-agnostic
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
- Shared components must be framework-agnostic
- State synchronization must work across all tabs
- Error handling must be consistent across all components
- Dynamic table generation must preserve unsaved changes

### Save Button Requirements
- **Tab 1 (Simulation Definitions)**: Save button for Market/Sector/Product lists
- **Tab 2 (Simulation Specs)**: Save button for Runtime and Scenario settings
- **Tab 3 (Primary Mapping)**: Save button for sector-product mappings
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
**Total Duration**: 8 weeks  
**Phases**: 8 phases with incremental delivery  
**Approach**: Phased implementation with each phase fully functional

---

### Phase 1: Core Infrastructure and New Tab Structure
**Duration**: 1 week  
**Objective**: Establish new tab structure and core state management system

#### Tasks
1. **Create New Tab Structure**
   - Replace current 7 tabs with new structure from migration.md
   - Implement tab navigation system with proper routing
   - Create base layouts for each new tab
   - Establish tab dependency relationships

2. **Core State Management System**
   - Design new state structure for dynamic tables
   - Implement save button state management
   - Create unsaved changes tracking system
   - Establish cross-tab state synchronization patterns

3. **Basic Tab Framework**
   - Create placeholder content for all 7 tabs
   - Implement basic tab switching and navigation
   - Establish consistent UI patterns across tabs
   - Add save button placeholders with basic functionality

#### Success Criteria
- [ ] All 7 new tabs render correctly with proper navigation
- [ ] Tab switching works without errors
- [ ] Save buttons exist on tabs 1, 2, and 3
- [ ] Basic state management system is functional
- [ ] No hardcoded values in any business logic
- [ ] All existing functionality preserved

#### Testing Strategy
- **Unit Tests**: Test tab navigation and state management
- **Integration Tests**: Verify tab switching and basic functionality
- **UI Tests**: Ensure all tabs render and navigate correctly
- **State Tests**: Verify save button state management

#### Debugging Approach
- **Tab Navigation Debugging**: Log all tab switching events
- **State Debugging**: Implement state inspection tools
- **Save Button Debugging**: Track save button state changes
- **Error Boundaries**: Add proper error handling for tab rendering

#### Deliverables
- New tab structure with navigation
- Core state management system
- Save button framework
- Basic tab layouts

---

### Phase 2: Simulation Definitions Tab (Tab 1)
**Duration**: 1 week  
**Objective**: Implement comprehensive market/sector/product management with save protection

#### Tasks
1. **Market/Sector/Product Lists**
   - Create editable tables for Market, Sector, and Product lists
   - Implement add/edit/delete functionality for each list
   - Add validation for list integrity and relationships
   - Implement save button with change protection

2. **Dynamic List Management**
   - Create list dependency validation (products must belong to sectors)
   - Implement list change tracking for unsaved changes
   - Add visual indicators for modified lists
   - Create list export/import functionality

3. **Save Button Implementation**
   - Implement save button that commits changes to state
   - Add unsaved changes indicators
   - Implement change rollback functionality
   - Add confirmation dialogs for destructive operations

#### Success Criteria
- [ ] All three lists (Market, Sector, Product) are editable in table format
- [ ] Add/edit/delete operations work correctly
- [ ] Save button prevents accidental data loss
- [ ] Unsaved changes are clearly indicated
- [ ] List dependencies are properly validated
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **List Management Tests**: Test all CRUD operations
- **Dependency Tests**: Verify list relationship validation
- **Save Button Tests**: Test save functionality and change protection
- **Validation Tests**: Ensure all list operations are properly validated

#### Debugging Approach
- **List Operation Debugging**: Log all list CRUD operations
- **Dependency Debugging**: Track list relationship changes
- **Save Button Debugging**: Monitor save button state and operations
- **Validation Debugging**: Log all validation failures with context

#### Deliverables
- Editable Market/Sector/Product tables
- Save button with change protection
- List dependency validation system
- Change tracking and rollback functionality

---

### Phase 3: Simulation Specs Tab (Tab 2)
**Duration**: 1 week  
**Objective**: Implement runtime controls and scenario management with save protection

#### Tasks
1. **Runtime Controls**
   - Create editable fields for start time, stop time, dt
   - Implement anchor mode selection (sector vs sector+product)
   - Add validation for time parameters and mode selection
   - Implement save button for runtime settings

2. **Scenario Management**
   - Create scenario name input and management
   - Implement load scenario functionality
   - Add scenario reset to baseline functionality
   - Implement save button for scenario settings

3. **Save Button Integration**
   - Implement save button that commits runtime and scenario changes
   - Add unsaved changes tracking for both sections
   - Implement change rollback functionality
   - Add validation before save operations

#### Success Criteria
- [ ] Runtime controls (start/stop/dt) are editable and validated
- [ ] Anchor mode selection works correctly
- [ ] Scenario name and management functions work
- [ ] Save button prevents accidental changes
- [ ] All parameters are properly validated
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Runtime Tests**: Test all time parameter inputs and validation
- **Mode Tests**: Verify anchor mode selection and validation
- **Scenario Tests**: Test scenario management functionality
- **Save Button Tests**: Verify save functionality and change protection

#### Debugging Approach
- **Runtime Debugging**: Log all time parameter changes
- **Mode Debugging**: Track anchor mode selection changes
- **Scenario Debugging**: Monitor scenario management operations
- **Save Button Debugging**: Track save operations and validation

#### Deliverables
- Editable runtime controls
- Scenario management functionality
- Save button with change protection
- Comprehensive validation system

---

### Phase 4: Primary Mapping Tab (Tab 3)
**Duration**: 1 week  
**Objective**: Implement sector-product mapping with save protection and dynamic table generation

#### Tasks
1. **Sector-Product Mapping Interface**
   - Create dynamic table for sector-product combinations
   - Implement product selection per sector with start years
   - Add mapping insights and summary display
   - Implement save button for mapping changes

2. **Dynamic Table Generation**
   - Create tables that update based on sector/product list changes
   - Implement mapping validation and integrity checks
   - Add visual feedback for mapping relationships
   - Implement mapping export/import functionality

3. **Save Button and Change Protection**
   - Implement save button that commits mapping changes
   - Add unsaved changes tracking for mappings
   - Implement change rollback functionality
   - Add confirmation for mapping modifications

#### Success Criteria
- [ ] Sector-product mapping table is fully functional
- [ ] Dynamic table generation works correctly
- [ ] Mapping insights and summary are displayed
- [ ] Save button prevents accidental mapping changes
- [ ] All mappings are properly validated
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Mapping Tests**: Test all mapping operations
- **Dynamic Table Tests**: Verify table generation and updates
- **Validation Tests**: Ensure mapping integrity
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **Mapping Debugging**: Log all mapping operations
- **Table Generation Debugging**: Track dynamic table updates
- **Validation Debugging**: Monitor mapping validation
- **Save Button Debugging**: Track save operations

#### Deliverables
- Dynamic sector-product mapping table
- Save button with change protection
- Mapping insights and summary
- Change tracking and rollback functionality

---

### Phase 5: Client Revenue Tab (Tab 4)
**Duration**: 1.5 weeks  
**Objective**: Implement comprehensive client revenue parameter tables with dynamic content

#### Tasks
1. **Dynamic Parameter Table Generation**
   - Create tables that populate based on primary mapping selections
   - Implement parameter grouping (Market Activation, Orders, Seeds)
   - Add comprehensive parameter coverage for all sector-product combinations
   - Implement save button for parameter changes

2. **Parameter Categories and Validation**
   - Implement Market Activation parameters (ATAM, anchor_start_year, etc.)
   - Implement Orders parameters (phase durations, rates, growth)
   - Implement Seeds parameters (completed projects, active clients, elapsed quarters)
   - Add parameter validation and dependency checking

3. **Dynamic Content Management**
   - Implement tables that update when primary mapping changes
   - Add parameter import/export functionality
   - Implement bulk parameter editing capabilities
   - Add parameter search and filtering

#### Success Criteria
- [ ] Dynamic parameter tables generate correctly based on mappings
- [ ] All parameter categories are properly implemented
- [ ] Parameter validation works correctly
- [ ] Save button prevents accidental parameter changes
- [ ] Tables update dynamically with mapping changes
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Table Generation Tests**: Test dynamic table creation and updates
- **Parameter Tests**: Verify all parameter categories and validation
- **Dynamic Update Tests**: Test table updates with mapping changes
- **Save Button Tests**: Verify save functionality and change protection

#### Debugging Approach
- **Table Generation Debugging**: Log all table generation events
- **Parameter Debugging**: Track parameter changes and validation
- **Dynamic Update Debugging**: Monitor table update operations
- **Save Button Debugging**: Track save operations

#### Deliverables
- Dynamic client revenue parameter tables
- Comprehensive parameter coverage
- Save button with change protection
- Dynamic content management system

---

### Phase 6: Direct Market Revenue Tab (Tab 5)
**Duration**: 1 week  
**Objective**: Implement product-specific direct market revenue parameters

#### Tasks
1. **Product-Specific Parameter Tables**
   - Create tables for direct market revenue parameters per product
   - Implement parameters (lead generation, conversion rates, delays, quantities)
   - Add parameter validation and dependency checking
   - Implement save button for parameter changes

2. **Parameter Management**
   - Implement lead generation parameters (inbound/outbound rates)
   - Implement conversion and delay parameters
   - Implement order quantity and growth parameters
   - Add parameter import/export functionality

3. **Dynamic Content and Validation**
   - Implement tables that update with product list changes
   - Add parameter validation rules
   - Implement bulk parameter editing
   - Add parameter search and filtering

#### Success Criteria
- [ ] Direct market revenue tables are fully functional
- [ ] All parameters are properly implemented and validated
- [ ] Tables update dynamically with product changes
- [ ] Save button prevents accidental parameter changes
- [ ] Parameter validation works correctly
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Parameter Tests**: Test all direct market revenue parameters
- **Validation Tests**: Verify parameter validation rules
- **Dynamic Update Tests**: Test table updates with product changes
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **Parameter Debugging**: Log all parameter changes
- **Validation Debugging**: Monitor parameter validation
- **Dynamic Update Debugging**: Track table update operations
- **Save Button Debugging**: Track save operations

#### Deliverables
- Direct market revenue parameter tables
- Comprehensive parameter coverage
- Save button with change protection
- Dynamic content management system

---

### Phase 7: Lookup Points Tab (Tab 6)
**Duration**: 1 week  
**Objective**: Implement time-series lookup points for production capacity and pricing

#### Tasks
1. **Time-Series Parameter Tables**
   - Create tables for production capacity and pricing per product
   - Implement year-based parameter input
   - Add parameter validation and interpolation
   - Implement save button for parameter changes

2. **Parameter Management**
   - Implement production capacity parameters per product per year
   - Implement pricing parameters per product per year
   - Add parameter validation and consistency checking
   - Implement parameter import/export functionality

3. **Time-Series Validation**
   - Implement year range validation
   - Add parameter interpolation validation
   - Implement bulk parameter editing
   - Add parameter search and filtering

#### Success Criteria
- [ ] Lookup points tables are fully functional
- [ ] All time-series parameters are properly implemented
- [ ] Parameter validation works correctly
- [ ] Save button prevents accidental parameter changes
- [ ] Time-series consistency is maintained
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Parameter Tests**: Test all lookup point parameters
- **Time-Series Tests**: Verify time-series validation
- **Validation Tests**: Test parameter validation rules
- **Save Button Tests**: Test save functionality and change protection

#### Debugging Approach
- **Parameter Debugging**: Log all parameter changes
- **Time-Series Debugging**: Monitor time-series validation
- **Validation Debugging**: Track parameter validation
- **Save Button Debugging**: Track save operations

#### Deliverables
- Lookup points parameter tables
- Time-series parameter management
- Save button with change protection
- Comprehensive validation system

---

### Phase 8: Runner and Logs Tabs (Tab 7)
**Duration**: 0.5 weeks  
**Objective**: Implement scenario execution and monitoring functionality

#### Tasks
1. **Runner Tab Implementation**
   - Create scenario save, validate, and run controls
   - Implement scenario execution monitoring
   - Add progress tracking and status display
   - Implement error handling and user feedback

2. **Logs Tab Implementation**
   - Create simulation logs display
   - Implement real-time log streaming
   - Add log filtering and search capabilities
   - Implement log export functionality

3. **Integration and Validation**
   - Integrate with all parameter tabs
   - Implement comprehensive scenario validation
   - Add execution result display
   - Implement error recovery mechanisms

#### Success Criteria
- [ ] Runner tab provides complete scenario execution control
- [ ] Logs tab displays simulation logs correctly
- [ ] All parameter tabs integrate with runner functionality
- [ ] Scenario validation works comprehensively
- [ ] Error handling provides clear user feedback
- [ ] No hardcoded defaults are used

#### Testing Strategy
- **Runner Tests**: Test all execution controls
- **Logs Tests**: Verify log display and streaming
- **Integration Tests**: Test parameter tab integration
- **Validation Tests**: Test comprehensive scenario validation

#### Debugging Approach
- **Runner Debugging**: Log all execution operations
- **Logs Debugging**: Monitor log display and streaming
- **Integration Debugging**: Track parameter tab integration
- **Validation Debugging**: Monitor scenario validation

#### Deliverables
- Complete runner functionality
- Logs display and management
- Parameter tab integration
- Comprehensive validation system

---

## Testing Strategy

### **Backend Compatibility Testing**
**Since this is front-end only, we must ensure complete compatibility with existing backend:**

- **YAML Generation Tests**: Verify generated YAML matches existing format exactly
- **Backend Validation Tests**: Ensure all UI inputs pass existing backend validation
- **Scenario Loading Tests**: Verify existing YAML files load correctly in new UI
- **Parameter Mapping Tests**: Confirm UI parameters map correctly to YAML structure
- **Integration Tests**: Test complete workflow from UI input to backend execution

### Unit Testing
- **Business Logic**: Test all business logic modules independently
- **Component Logic**: Test component behavior and state management
- **Validation Logic**: Test all validation rules and error handling
- **Utility Functions**: Test all helper and utility functions

### Integration Testing
- **Tab Integration**: Test interaction between different tabs
- **State Synchronization**: Verify state consistency across components
- **Data Flow**: Test complete data flow from input to output
- **Error Handling**: Test error propagation and recovery

### UI Testing
- **Component Rendering**: Test all UI components render correctly
- **User Interaction**: Test all user interactions and responses
- **Responsive Design**: Test UI behavior across different screen sizes
- **Accessibility**: Test accessibility features and compliance

### End-to-End Testing
- **Complete Workflows**: Test complete user workflows
- **Scenario Management**: Test full scenario lifecycle
- **Data Persistence**: Test data saving and loading
- **Performance**: Test performance under realistic conditions

## Debugging and Monitoring

### Logging Strategy
- **Business Logic Logging**: Log all business operations with context
- **UI Interaction Logging**: Log user interactions and component state
- **Error Logging**: Log all errors with stack traces and context
- **Performance Logging**: Log performance metrics and bottlenecks

### Error Handling
- **Error Boundaries**: Implement proper error boundaries at component level
- **User Feedback**: Provide clear error messages and recovery options
- **Error Recovery**: Implement automatic error recovery where possible
- **Error Reporting**: Collect and report errors for analysis

### Monitoring Tools
- **State Inspection**: Tools for inspecting component and application state
- **Performance Monitoring**: Real-time performance metrics
- **Error Tracking**: Comprehensive error tracking and reporting
- **User Analytics**: Track user behavior and workflow patterns

## Quality Assurance

### Code Quality
- **Linting**: Enforce consistent code style and quality
- **Type Checking**: Use type hints and validation
- **Documentation**: Comprehensive code documentation
- **Code Review**: Peer review process for all changes

### Performance Requirements
- **Response Time**: UI interactions must respond within 100ms
- **Rendering Performance**: Complex tables must render within 2 seconds
- **Memory Usage**: Memory usage must remain stable during extended use
- **Scalability**: UI must handle large datasets without performance degradation

### Security Requirements
- **Input Validation**: All user inputs must be properly validated
- **Data Sanitization**: All data must be sanitized before processing
- **Access Control**: Implement proper access control for sensitive operations
- **Audit Logging**: Log all sensitive operations for audit purposes

## Risk Mitigation

### Technical Risks
- **Complex State Management**: Risk of state synchronization issues
- **Dynamic Table Generation**: Risk of performance issues with large tables
- **Cross-Tab Dependencies**: Risk of circular dependencies and infinite loops
- **Data Integrity**: Risk of data corruption during complex operations

### Mitigation Strategies
- **Incremental Implementation**: Each phase must be fully functional before proceeding
- **Comprehensive Testing**: Extensive testing at each phase
- **Rollback Plan**: Ability to rollback to previous working version
- **Performance Monitoring**: Continuous performance monitoring throughout development

### Contingency Plans
- **Phase Rollback**: If any phase fails, rollback to previous working state
- **Alternative Approaches**: Have alternative implementation approaches ready
- **Extended Timeline**: Buffer time for unexpected issues
- **Expert Consultation**: Access to framework experts if needed

## Success Metrics

### Functional Metrics
- [ ] All requested features implemented and working
- [ ] No regression in existing functionality
- [ ] All validations and error handling working correctly
- [ ] Performance meets or exceeds requirements
- [ ] Save buttons prevent accidental data loss

### Quality Metrics
- [ ] All tests passing
- [ ] Code coverage above 90%
- [ ] No critical bugs or security vulnerabilities
- [ ] Documentation complete and accurate

### User Experience Metrics
- [ ] UI is intuitive and user-friendly
- [ ] All workflows are efficient and logical
- [ ] Error messages are clear and actionable
- [ ] Performance meets user expectations
- [ ] Save buttons provide clear data protection

## Conclusion

This implementation plan provides a comprehensive roadmap for **FRONT-END ONLY** restructuring of the Growth Model UI to implement the new table-based input system as specified in `migration.md`. 

**CRITICAL SUCCESS FACTOR: Backend Compatibility**
The phased approach ensures each step delivers working functionality while maintaining **complete compatibility with existing backend systems**. This is not a rewrite or backend modification - it's purely a UI enhancement.

The plan emphasizes:
- **FRONT-END ONLY** - all backend logic, YAML structure, and validation remain unchanged
- **No fallback mechanisms** - all parameters must come from user inputs
- **Save button protection** - preventing accidental parameter destruction
- **YAML compatibility** - must generate identical format to existing backend
- **Comprehensive testing** at each phase with backend compatibility validation
- **Incremental validation** to catch issues early
- **Risk mitigation** through proper planning and contingencies
- **Quality assurance** through proper processes and metrics

By following this plan, we can successfully deliver a modern, feature-rich UI that provides the enhanced user experience requested while maintaining **100% backend compatibility** and ensuring data integrity through save button protection.

**The backend will continue to work exactly as it does today - only the user interface will be improved.**

---

## Implementation Notes

### Save Button Implementation Pattern
All save buttons must follow this consistent pattern:
1. **Change Tracking**: Track all unsaved changes in component state
2. **Visual Indicators**: Show clear indicators for unsaved changes
3. **Save Validation**: Validate all changes before saving
4. **State Commit**: Only commit changes when save is clicked
5. **Rollback Support**: Provide ability to rollback unsaved changes

### Dynamic Table Generation Pattern
All dynamic tables must follow this pattern:
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
