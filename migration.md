# Product Growth System – Migration Plan

## Overview
This document outlines the migration strategy for converting the Growth System UI from form-based input to table-based input format, improving user experience while maintaining all existing functionality.

## Current State
The system currently uses a hybrid approach:
- **Constants Editor**: Individual input boxes with summary table view
- **Points Editor**: Already uses `st.data_editor()` for time-series data (excellent!)
- **Primary Map Editor**: Form-based with individual inputs per product
- **Seeds Editor**: Form-based inputs

## Migration Phase 18: Table Input Conversion

### Objective
Convert all model input editors from form-based to table-based input format using Streamlit's `st.data_editor()` component, excluding scenario control parameters (runspecs).

### Scope
**In Scope:**
- Constants Editor (per-sector, per-product, per-(sector,product) parameters)
- Primary Map Editor (sector→product mappings with start years)
- Seeds Editor (anchor clients, direct clients, completed projects)

**Out of Scope:**
- Runspecs (starttime, stoptime, dt, anchor_mode) - keep as form inputs
- Points Editor - already converted, maintain current implementation

### Implementation Plan

#### Phase 18.1: Constants Editor Conversion
**Tasks:**
1. **Data Structure Transformation**
   - Convert `ScenarioOverridesState.constants` from `Dict[str, float]` to DataFrame format
   - Create DataFrame with columns: `Parameter | Value | Category | Description`
   - Group parameters by category (Anchor, Other Clients, SM-specific)

2. **UI Component Refactor**
   - Replace individual `st.number_input()` components with `st.data_editor()`
   - Add inline editing capabilities for parameter values
   - Maintain filtering and search functionality
   - Add bulk import/export (CSV) capabilities

3. **State Management Updates**
   - Update `render_constants_editor()` to handle DataFrame input/output
   - Ensure real-time validation works with table edits
   - Maintain callback pattern for state updates

**Success Criteria:**
- Constants editor displays as editable table
- All existing validation logic preserved
- CSV import/export functionality working
- Performance comparable to current implementation

#### Phase 18.2: Primary Map Editor Conversion
**Tasks:**
1. **Data Structure Transformation**
   - Convert `PrimaryMapState.by_sector` to DataFrame format
   - Create DataFrame with columns: `Sector | Product | StartYear | Current_StartYear`
   - Show current vs. proposed mapping side-by-side

2. **UI Component Refactor**
   - Replace form-based inputs with `st.data_editor()`
   - Enable inline editing of start years
   - Add row-level add/remove functionality
   - Maintain sector-based grouping

3. **Validation Integration**
   - Ensure start year validation works with table edits
   - Maintain product existence validation
   - Add visual indicators for invalid entries

**Success Criteria:**
- Primary map editor displays as editable table
- Current vs. proposed mapping clearly visible
- All validation rules enforced
- Row-level operations working

#### Phase 18.3: Seeds Editor Conversion
**Tasks:**
1. **Data Structure Transformation**
   - Convert `SeedsState` to DataFrame format
   - Create separate tables for different seed types:
     - Anchor seeds: `Sector | Product | Active_Clients | Elapsed_Quarters | Completed_Projects`
     - Direct client seeds: `Product | Initial_Clients`
   - Handle both sector-mode and SM-mode structures

2. **UI Component Refactor**
   - Replace form inputs with `st.data_editor()`
   - Enable inline editing of seed values
   - Add conditional columns based on anchor_mode
   - Maintain validation for non-negative integers

3. **Mode-Specific Handling**
   - Ensure SM-mode seeds require valid (sector, product) pairs
   - Maintain sector-mode vs. SM-mode exclusivity
   - Add visual indicators for mode-specific requirements

**Success Criteria:**
- Seeds editor displays as editable table(s)
- Mode-specific validation enforced
- All seed types properly handled
- Integer validation working

### Technical Implementation Details

#### Data Transformation Functions
```python
def constants_dict_to_dataframe(constants: Dict[str, float], permissible_keys: List[str]) -> pd.DataFrame:
    """Convert constants dictionary to DataFrame for table editing."""
    # Implementation details...

def constants_dataframe_to_dict(df: pd.DataFrame) -> Dict[str, float]:
    """Convert edited DataFrame back to constants dictionary."""
    # Implementation details...

def primary_map_state_to_dataframe(state: PrimaryMapState, bundle: Phase1Bundle) -> pd.DataFrame:
    """Convert primary map state to DataFrame for table editing."""
    # Implementation details...

def seeds_state_to_dataframes(state: SeedsState, anchor_mode: str) -> Dict[str, pd.DataFrame]:
    """Convert seeds state to DataFrames for table editing."""
    # Implementation details...
```

#### Validation Integration
- Maintain all existing validation logic
- Add real-time validation feedback in table cells
- Ensure validation errors are clearly visible
- Maintain callback pattern for state updates

#### Performance Considerations
- Use `st.cache_data` for expensive transformations
- Minimize DataFrame recreations
- Optimize for typical scenario sizes (10-50 parameters)

### Testing Strategy

#### Unit Tests
- **Data Transformation Tests**: Verify dict↔DataFrame conversions
- **Validation Tests**: Ensure all validation rules work with table input
- **State Management Tests**: Verify state updates work correctly

#### Integration Tests
- **End-to-End Editor Tests**: Verify complete edit→validate→save flow
- **Performance Tests**: Ensure acceptable performance with large datasets
- **Cross-Editor Tests**: Verify interactions between different editors

#### User Acceptance Tests
- **Usability Tests**: Verify table editing is intuitive
- **Validation Tests**: Ensure error messages are clear
- **Workflow Tests**: Verify complete scenario creation process

### Migration Timeline

**Week 1-2: Phase 18.1 (Constants Editor)**
- Implement data transformation functions
- Refactor UI component
- Add tests and validation

**Week 3-4: Phase 18.2 (Primary Map Editor)**
- Implement data transformation functions
- Refactor UI component
- Add tests and validation

**Week 5-6: Phase 18.3 (Seeds Editor)**
- Implement data transformation functions
- Refactor UI component
- Add tests and validation

**Week 7: Integration and Testing**
- End-to-end testing
- Performance optimization
- User acceptance testing

### Risk Mitigation

#### Technical Risks
- **Data Loss**: Implement robust validation and backup mechanisms
- **Performance**: Monitor and optimize DataFrame operations
- **State Synchronization**: Ensure consistent state management

#### User Experience Risks
- **Learning Curve**: Provide clear documentation and help text
- **Data Entry Errors**: Implement comprehensive validation and error messages
- **Workflow Disruption**: Maintain all existing functionality during transition

### Success Metrics

#### Technical Metrics
- All editors successfully converted to table format
- Performance within 10% of current implementation
- Zero data loss during conversion
- All validation rules preserved

#### User Experience Metrics
- Reduced time to create scenarios (target: 30% improvement)
- Reduced user errors in parameter entry (target: 50% reduction)
- Positive user feedback on new interface
- Successful completion of user acceptance tests

### Future Enhancements

#### Phase 18.4: Advanced Table Features
- **Bulk Operations**: Copy/paste from Excel, bulk value updates
- **Templates**: Save/load parameter sets as templates
- **Versioning**: Track changes to parameter values
- **Collaboration**: Multi-user editing capabilities

#### Phase 18.5: Integration Improvements
- **Real-time Validation**: Immediate feedback on parameter changes
- **Auto-save**: Automatic saving of work-in-progress
- **Undo/Redo**: Parameter change history and rollback
- **Export Formats**: Additional export options (Excel, JSON)

## Conclusion

The migration to table-based input format represents a significant improvement in user experience while maintaining all existing functionality. The phased approach minimizes risk and allows for iterative improvement based on user feedback.

The use of Streamlit's `st.data_editor()` component provides a robust foundation for the new interface, with built-in support for inline editing, validation, and data manipulation. The existing points editor implementation serves as a proven pattern for the conversion.

By excluding scenario control parameters from this conversion, we maintain the simplicity of the runspecs interface while focusing on the more complex parameter editing tasks that will benefit most from table-based input.
