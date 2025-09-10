"""
Framework-agnostic data management for the Growth Model UI.

This module handles all data-related operations including:
- Loading and validating input data
- Managing permissible keys and parameters
- Data transformation and processing
- Caching and optimization
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import logging
import json

from .state_manager import StateManager

logger = logging.getLogger(__name__)


class DataBundle:
    """Represents a bundle of data loaded from inputs.json."""
    
    def __init__(self, lists: Dict, anchor_params: Dict, other_params: Dict, 
                 production: Dict, pricing: Dict, primary_map: Dict):
        """Initialize a data bundle.
        
        Args:
            lists: Lists of markets, sectors, and products
            anchor_params: Anchor client parameters
            other_params: Other client parameters
            production: Production capacity data
            pricing: Pricing data
            primary_map: Primary mapping data
        """
        self.lists = lists
        self.anchor_params = anchor_params
        self.other_params = other_params
        self.production = production
        self.pricing = pricing
        self.primary_map = primary_map
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'lists': self.lists,
            'anchor_params': self.anchor_params,
            'other_params': self.other_params,
            'production': self.production,
            'pricing': self.pricing,
            'primary_map': self.primary_map
        }


class PermissibleKeys:
    """Represents permissible keys for different sections."""
    
    def __init__(self, constants: Set[str], points: Set[str], 
                 sectors: Set[str], products: Set[str]):
        """Initialize permissible keys.
        
        Args:
            constants: Set of permissible constant keys
            points: Set of permissible point keys
            sectors: Set of available sectors
            products: Set of available products
        """
        self.constants = constants
        self.points = points
        self.sectors = sectors
        self.products = products
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'constants': list(self.constants),
            'points': list(self.points),
            'sectors': list(self.sectors),
            'products': list(self.products)
        }


class DataManager:
    """
    Framework-agnostic data management.
    
    This class handles all data-related operations including:
    - Loading and validating input data
    - Managing permissible keys and parameters
    - Data transformation and processing
    - Caching and optimization
    """
    
    def __init__(self, state_manager: StateManager, project_root: Path):
        """Initialize the data manager.
        
        Args:
            state_manager: State manager instance
            project_root: Project root directory
        """
        self.state_manager = state_manager
        self.project_root = Path(project_root)
        self._data_bundle: Optional[DataBundle] = None
        self._permissible_keys_cache: Dict[str, PermissibleKeys] = {}
        self._last_anchor_mode: Optional[str] = None
        self._last_extra_pairs: Optional[List[Tuple[str, str]]] = None
        
    def load_data_bundle(self) -> Tuple[bool, Optional[str], Optional[DataBundle]]:
        """Load the data bundle from inputs.json.
        
        Returns:
            Tuple of (success, error_message, data_bundle)
        """
        try:
            inputs_file = self.project_root / "inputs.json"
            if not inputs_file.exists():
                return False, "inputs.json not found", None
            
            with open(inputs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required sections
            required_sections = ['lists', 'anchor_params', 'other_params', 'production', 'pricing', 'primary_map']
            for section in required_sections:
                if section not in data:
                    return False, f"Missing required section '{section}' in inputs.json", None
            
            # Create data bundle
            bundle = DataBundle(
                lists=data['lists'],
                anchor_params=data['anchor_params'],
                other_params=data['other_params'],
                production=data['production'],
                pricing=data['pricing'],
                primary_map=data['primary_map']
            )
            
            # Validate the bundle
            success, error = self._validate_data_bundle(bundle)
            if not success:
                return False, error, None
            
            self._data_bundle = bundle
            logger.info("Data bundle loaded successfully")
            return True, None, bundle
            
        except json.JSONDecodeError as e:
            error_msg = f"Error parsing inputs.json: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Error loading data bundle: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def get_data_bundle(self) -> Optional[DataBundle]:
        """Get the current data bundle.
        
        Returns:
            Current data bundle or None if not loaded
        """
        if self._data_bundle is None:
            success, error, bundle = self.load_data_bundle()
            if not success:
                logger.error(f"Failed to load data bundle: {error}")
                return None
        return self._data_bundle
    
    def get_permissible_keys(self, anchor_mode: str = "sector", 
                           extra_sm_pairs: Optional[List[Tuple[str, str]]] = None) -> PermissibleKeys:
        """Get permissible keys for the current configuration.
        
        Args:
            anchor_mode: Anchor mode ("sector" or "sm")
            extra_sm_pairs: Extra (sector, product) pairs for SM mode
            
        Returns:
            PermissibleKeys object
        """
        # Check cache
        cache_key = f"{anchor_mode}_{hash(str(extra_sm_pairs))}"
        if (cache_key in self._permissible_keys_cache and 
            self._last_anchor_mode == anchor_mode and 
            self._last_extra_pairs == extra_sm_pairs):
            return self._permissible_keys_cache[cache_key]
        
        # Get data bundle
        bundle = self.get_data_bundle()
        if bundle is None:
            # Return empty keys if bundle not available
            return PermissibleKeys(set(), set(), set(), set())
        
        # Generate permissible keys
        constants = self._generate_constant_keys(bundle, anchor_mode, extra_sm_pairs)
        points = self._generate_point_keys(bundle)
        sectors = set(bundle.lists.get('lists', {}).get('sectors', []))
        products = set(bundle.lists.get('lists', {}).get('products', []))
        
        # Create permissible keys object
        permissible_keys = PermissibleKeys(constants, points, sectors, products)
        
        # Cache the result
        self._permissible_keys_cache[cache_key] = permissible_keys
        self._last_anchor_mode = anchor_mode
        self._last_extra_pairs = extra_sm_pairs
        
        return permissible_keys
    
    def _generate_constant_keys(self, bundle: DataBundle, anchor_mode: str, 
                              extra_sm_pairs: Optional[List[Tuple[str, str]]]) -> Set[str]:
        """Generate permissible constant keys.
        
        Args:
            bundle: Data bundle
            anchor_mode: Anchor mode
            extra_sm_pairs: Extra (sector, product) pairs
            
        Returns:
            Set of permissible constant keys
        """
        constants = set()
        
        # Get sectors and products from the lists structure
        sectors = bundle.lists.get('lists', {}).get('sectors', [])
        products = bundle.lists.get('lists', {}).get('products', [])
        
        # Add anchor client parameters
        if anchor_mode == "sector":
            # Sector-level parameters
            for sector in sectors:
                constants.update([
                    f"anchor_start_year_{sector}",
                    f"anchor_client_activation_delay_{sector}",
                    f"anchor_lead_generation_rate_{sector}",
                    f"lead_to_pc_conversion_rate_{sector}",
                    f"project_generation_rate_{sector}",
                    f"max_projects_per_pc_{sector}",
                    f"project_duration_{sector}",
                    f"projects_to_client_conversion_{sector}",
                    f"initial_phase_duration_{sector}",
                    f"ramp_phase_duration_{sector}",
                    f"initial_requirement_rate_{sector}",
                    f"initial_req_growth_{sector}",
                    f"ramp_requirement_rate_{sector}",
                    f"ramp_req_growth_{sector}",
                    f"steady_requirement_rate_{sector}",
                    f"steady_req_growth_{sector}",
                    f"requirement_to_order_lag_{sector}",
                    f"ATAM_{sector}"
                ])
                
                # Per-(sector, product) requirement parameters
                for product in products:
                    constants.update([
                        f"initial_requirement_rate_{sector}_{product}",
                        f"initial_req_growth_{sector}_{product}",
                        f"ramp_requirement_rate_{sector}_{product}",
                        f"ramp_req_growth_{sector}_{product}",
                        f"steady_requirement_rate_{sector}_{product}",
                        f"steady_req_growth_{sector}_{product}",
                        f"requirement_to_order_lag_{sector}_{product}"
                    ])
        
        elif anchor_mode == "sm":
            # SM-mode: full per-(sector, product) parameters
            # Add extra pairs if provided
            if extra_sm_pairs:
                for sector, product in extra_sm_pairs:
                    if sector not in sectors:
                        sectors.append(sector)
                    if product not in products:
                        products.append(product)
            
            for sector in sectors:
                for product in products:
                    constants.update([
                        f"anchor_start_year_{sector}_{product}",
                        f"anchor_client_activation_delay_{sector}_{product}",
                        f"anchor_lead_generation_rate_{sector}_{product}",
                        f"lead_to_pc_conversion_rate_{sector}_{product}",
                        f"project_generation_rate_{sector}_{product}",
                        f"max_projects_per_pc_{sector}_{product}",
                        f"project_duration_{sector}_{product}",
                        f"projects_to_client_conversion_{sector}_{product}",
                        f"initial_phase_duration_{sector}_{product}",
                        f"ramp_phase_duration_{sector}_{product}",
                        f"initial_requirement_rate_{sector}_{product}",
                        f"initial_req_growth_{sector}_{product}",
                        f"ramp_requirement_rate_{sector}_{product}",
                        f"ramp_req_growth_{sector}_{product}",
                        f"steady_requirement_rate_{sector}_{product}",
                        f"steady_req_growth_{sector}_{product}",
                        f"requirement_to_order_lag_{sector}_{product}",
                        f"ATAM_{sector}_{product}"
                    ])
        
        # Add other client parameters
        for product in products:
            constants.update([
                f"lead_start_year_{product}",
                f"inbound_lead_generation_rate_{product}",
                f"outbound_lead_generation_rate_{product}",
                f"lead_to_c_conversion_rate_{product}",
                f"lead_to_requirement_delay_{product}",
                f"requirement_to_fulfilment_delay_{product}",
                f"avg_order_quantity_initial_{product}",
                f"client_requirement_growth_{product}",
                f"TAM_{product}"
            ])
        
        return constants
    
    def _generate_point_keys(self, bundle: DataBundle) -> Set[str]:
        """Generate permissible point keys.
        
        Args:
            bundle: Data bundle
            
        Returns:
            Set of permissible point keys
        """
        points = set()
        
        # Add price and capacity keys for each product
        for product in bundle.lists.get('lists', {}).get('products', []):
            points.update([
                f"price_{product}",
                f"max_capacity_{product}"
            ])
        
        return points
    
    def _validate_data_bundle(self, bundle: DataBundle) -> Tuple[bool, Optional[str]]:
        """Validate a data bundle.
        
        Args:
            bundle: Data bundle to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate lists
            if 'lists' not in bundle.lists:
                return False, "Missing 'lists' key in lists section"
            
            lists_data = bundle.lists['lists']
            if not isinstance(lists_data, dict):
                return False, "Lists section must be a dictionary"
            
            # Check for required lists
            required_lists = ['markets', 'sectors', 'products']
            for required_list in required_lists:
                if required_list not in lists_data:
                    return False, f"Missing required list '{required_list}'"
                
                if not isinstance(lists_data[required_list], list):
                    return False, f"List '{required_list}' must be an array"
            
            # Check for US market
            markets = lists_data.get('markets', [])
            if 'US' not in markets:
                return False, "Market 'US' must be present in markets list"
            
            # Validate anchor_params
            if not isinstance(bundle.anchor_params, dict):
                return False, "anchor_params must be a dictionary"
            
            # Validate other_params
            if not isinstance(bundle.other_params, dict):
                return False, "other_params must be a dictionary"
            
            # Validate production
            if not isinstance(bundle.production, dict):
                return False, "production must be a dictionary"
            
            # Validate pricing
            if not isinstance(bundle.pricing, dict):
                return False, "pricing must be a dictionary"
            
            # Validate primary_map
            if not isinstance(bundle.primary_map, dict):
                return False, "primary_map must be a dictionary"
            
            # Validate data consistency
            sectors = lists_data.get('sectors', [])
            products = lists_data.get('products', [])
            
            # Check that all sectors in anchor_params exist in lists
            for sector in bundle.anchor_params.keys():
                if sector not in sectors:
                    return False, f"Sector '{sector}' in anchor_params not found in sectors list"
            
            # Check that all products in other_params exist in lists
            for product in bundle.other_params.keys():
                if product not in products:
                    return False, f"Product '{product}' in other_params not found in products list"
            
            # Check that all products in production exist in lists
            for product in bundle.production.keys():
                if product not in products:
                    return False, f"Product '{product}' in production not found in products list"
            
            # Check that all products in pricing exist in lists
            for product in bundle.pricing.keys():
                if product not in products:
                    return False, f"Product '{product}' in pricing not found in products list"
            
            # Validate primary_map entries
            for sector, entries in bundle.primary_map.items():
                if sector not in sectors:
                    return False, f"Sector '{sector}' in primary_map not found in sectors list"
                
                if not isinstance(entries, list):
                    return False, f"Primary map entries for sector '{sector}' must be a list"
                
                for entry in entries:
                    if not isinstance(entry, dict):
                        return False, f"Primary map entry for sector '{sector}' must be a dictionary"
                    
                    if 'product' not in entry:
                        return False, f"Primary map entry for sector '{sector}' missing 'product' field"
                    
                    if 'start_year' not in entry:
                        return False, f"Primary map entry for sector '{sector}' missing 'start_year' field"
                    
                    product = entry['product']
                    if product not in products:
                        return False, f"Product '{product}' in primary map for sector '{sector}' not found in products list"
                    
                    try:
                        start_year = float(entry['start_year'])
                        if start_year < 0:
                            return False, (f"Start year in primary map for sector '{sector}' "
                                         f"product '{product}' cannot be negative")
                    except (ValueError, TypeError):
                        return False, (f"Start year in primary map for sector '{sector}' "
                                     f"product '{product}' must be a valid number")
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating data bundle: {e}"
    
    def get_sector_product_mapping(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the current sector to product mapping.
        
        Returns:
            Dictionary mapping sectors to their product configurations
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        return bundle.primary_map
    
    def get_available_sectors(self) -> List[str]:
        """Get list of available sectors.
        
        Returns:
            List of available sectors
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return []
        
        return bundle.lists.get('lists', {}).get('sectors', [])
    
    def get_available_products(self) -> List[str]:
        """Get list of available products.
        
        Returns:
            List of available products
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return []
        
        return bundle.lists.get('lists', {}).get('products', [])
    
    def get_anchor_params_for_sector(self, sector: str) -> Dict[str, Any]:
        """Get anchor parameters for a specific sector.
        
        Args:
            sector: Sector name
            
        Returns:
            Dictionary of anchor parameters for the sector
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        return bundle.anchor_params.get(sector, {})
    
    def get_anchor_params(self) -> Dict[str, Dict[str, Any]]:
        """Get all anchor parameters organized by parameter name.
        
        Returns:
            Dictionary mapping parameter names to sector values
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        # Reorganize data from sector-based to parameter-based
        result = {}
        for sector, params in bundle.anchor_params.items():
            for param_name, value in params.items():
                if param_name not in result:
                    result[param_name] = {}
                result[param_name][sector] = value
        
        return result
    
    def get_other_params(self) -> Dict[str, Dict[str, Any]]:
        """Get all other parameters organized by parameter name.
        
        Returns:
            Dictionary mapping parameter names to product values
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        # Reorganize data from product-based to parameter-based
        result = {}
        for product, params in bundle.other_params.items():
            for param_name, value in params.items():
                if param_name not in result:
                    result[param_name] = {}
                result[param_name][product] = value
        
        return result
    
    def get_sm_params(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all SM mode parameters organized by parameter name.
        
        Returns:
            Dictionary mapping parameter names to sector-product values
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        # Check if SM parameters exist
        if not hasattr(bundle, 'anchor_params_sm') or not bundle.anchor_params_sm:
            return {}
        
        # Reorganize data from sector-product-based to parameter-based
        result = {}
        for param_name, sector_data in bundle.anchor_params_sm.items():
            if param_name not in result:
                result[param_name] = {}
            
            for sector, product_data in sector_data.items():
                if sector not in result[param_name]:
                    result[param_name][sector] = {}
                
                for product, value in product_data.items():
                    result[param_name][sector][product] = value
        
        return result
    
    def get_other_params_for_product(self, product: str) -> Dict[str, Any]:
        """Get other parameters for a specific product.
        
        Args:
            product: Product name
            
        Returns:
            Dictionary of other parameters for the product
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return {}
        
        return bundle.other_params.get(product, {})
    
    def get_production_data_for_product(self, product: str) -> List[Tuple[float, float]]:
        """Get production data for a specific product.
        
        Args:
            product: Product name
            
        Returns:
            List of (year, capacity) tuples
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return []
        
        production_data = bundle.production.get(product, {})
        if not isinstance(production_data, dict):
            return []
        
        # Convert to list of tuples and sort by year
        data_points = []
        for year_str, capacity in production_data.items():
            try:
                year = float(year_str)
                capacity_val = float(capacity)
                data_points.append((year, capacity_val))
            except (ValueError, TypeError):
                continue
        
        return sorted(data_points, key=lambda x: x[0])
    
    def get_pricing_data_for_product(self, product: str) -> List[Tuple[float, float]]:
        """Get pricing data for a specific product.
        
        Args:
            product: Product name
            
        Returns:
            List of (year, price) tuples
        """
        bundle = self.get_data_bundle()
        if bundle is None:
            return []
        
        pricing_data = bundle.pricing.get(product, {})
        if not isinstance(pricing_data, dict):
            return []
        
        # Convert to list of tuples and sort by year
        data_points = []
        for year_str, price in pricing_data.items():
            try:
                year = float(year_str)
                price_val = float(price)
                data_points.append((year, price_val))
            except (ValueError, TypeError):
                continue
        
        return sorted(data_points, key=lambda x: x[0])
    
    def clear_cache(self) -> None:
        """Clear the permissible keys cache."""
        self._permissible_keys_cache.clear()
        self._last_anchor_mode = None
        self._last_extra_pairs = None
        logger.info("Data manager cache cleared")
    
    def reload_data(self) -> Tuple[bool, Optional[str]]:
        """Reload the data bundle and clear cache.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.clear_cache()
            success, error, bundle = self.load_data_bundle()
            if success:
                logger.info("Data reloaded successfully")
            return success, error
        except Exception as e:
            error_msg = f"Error reloading data: {e}"
            logger.error(error_msg)
            return False, error_msg
