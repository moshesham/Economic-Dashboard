"""
CPI Basket of Goods Configuration

Defines the Consumer Price Index basket of goods as defined by the Bureau of Labor Statistics (BLS).
The weights are based on the relative importance of each category in consumer spending.

The CPI basket is divided into major groups and subgroups, each with their corresponding
FRED series IDs for tracking price changes.

Reference:
- BLS CPI Relative Importance: https://www.bls.gov/cpi/tables/relative-importance/home.htm
- FRED CPI Data: https://fred.stlouisfed.org/categories/9

Note: Weights are approximate and based on BLS relative importance data.
These weights are updated periodically by the BLS (typically every 2 years).
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class CPIItem:
    """Represents a single item in the CPI basket."""
    name: str
    fred_series_id: str
    weight: float  # Relative importance (percentage of total CPI)
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    update_frequency: str = "monthly"  # CPI data is released monthly


# =============================================================================
# CPI BASKET CONFIGURATION
# Based on BLS Relative Importance data (December 2023)
# Total weights should sum to approximately 100%
# =============================================================================

CPI_BASKET: Dict[str, List[CPIItem]] = {
    # ==========================================================================
    # FOOD AND BEVERAGES (~13.5% of CPI)
    # ==========================================================================
    "food_and_beverages": [
        CPIItem(
            name="Food at Home",
            fred_series_id="CUSR0000SAF11",
            weight=8.17,
            category="Food and Beverages",
            subcategory="Food at Home",
            description="Food purchased for off-premises consumption"
        ),
        CPIItem(
            name="Food Away from Home",
            fred_series_id="CUSR0000SEFV",
            weight=5.36,
            category="Food and Beverages",
            subcategory="Food Away from Home",
            description="Food purchased for immediate consumption at restaurants, etc."
        ),
        CPIItem(
            name="Alcoholic Beverages",
            fred_series_id="CUSR0000SAF116",
            weight=0.89,
            category="Food and Beverages",
            subcategory="Alcoholic Beverages",
            description="Beer, wine, and spirits"
        ),
        # Detailed food subcategories
        CPIItem(
            name="Cereals and Bakery Products",
            fred_series_id="CUSR0000SAF111",
            weight=1.05,
            category="Food and Beverages",
            subcategory="Food at Home - Cereals and Bakery",
            description="Bread, cereals, rice, pasta"
        ),
        CPIItem(
            name="Meats, Poultry, Fish, and Eggs",
            fred_series_id="CUSR0000SAF112",
            weight=1.86,
            category="Food and Beverages",
            subcategory="Food at Home - Meats",
            description="Beef, pork, chicken, fish, eggs"
        ),
        CPIItem(
            name="Dairy and Related Products",
            fred_series_id="CUSR0000SEFJ",
            weight=0.86,
            category="Food and Beverages",
            subcategory="Food at Home - Dairy",
            description="Milk, cheese, ice cream"
        ),
        CPIItem(
            name="Fruits and Vegetables",
            fred_series_id="CUSR0000SAF113",
            weight=1.26,
            category="Food and Beverages",
            subcategory="Food at Home - Fruits and Vegetables",
            description="Fresh fruits and vegetables"
        ),
    ],

    # ==========================================================================
    # HOUSING (~44.4% of CPI) - Largest category
    # ==========================================================================
    "housing": [
        CPIItem(
            name="Shelter",
            fred_series_id="CUSR0000SAH1",
            weight=36.17,
            category="Housing",
            subcategory="Shelter",
            description="Rent of primary residence and owners' equivalent rent"
        ),
        CPIItem(
            name="Rent of Primary Residence",
            fred_series_id="CUSR0000SEHA",
            weight=7.69,
            category="Housing",
            subcategory="Shelter - Rent",
            description="Rent paid by tenants"
        ),
        CPIItem(
            name="Owners' Equivalent Rent",
            fred_series_id="CUSR0000SEHC",
            weight=26.68,
            category="Housing",
            subcategory="Shelter - OER",
            description="Imputed rent for homeowners"
        ),
        CPIItem(
            name="Fuels and Utilities",
            fred_series_id="CUSR0000SAH2",
            weight=4.06,
            category="Housing",
            subcategory="Fuels and Utilities",
            description="Electricity, natural gas, fuel oil"
        ),
        CPIItem(
            name="Electricity",
            fred_series_id="CUSR0000SEHF01",
            weight=2.47,
            category="Housing",
            subcategory="Utilities - Electricity",
            description="Electric utility services"
        ),
        CPIItem(
            name="Utility (Piped) Gas Service",
            fred_series_id="CUSR0000SEHF02",
            weight=0.69,
            category="Housing",
            subcategory="Utilities - Natural Gas",
            description="Natural gas utility services"
        ),
        CPIItem(
            name="Household Furnishings and Operations",
            fred_series_id="CUSR0000SAH3",
            weight=4.18,
            category="Housing",
            subcategory="Furnishings and Operations",
            description="Furniture, appliances, and household operations"
        ),
    ],

    # ==========================================================================
    # APPAREL (~2.5% of CPI)
    # ==========================================================================
    "apparel": [
        CPIItem(
            name="Apparel",
            fred_series_id="CUSR0000SAA",
            weight=2.47,
            category="Apparel",
            subcategory="All Apparel",
            description="Men's, women's, children's clothing and footwear"
        ),
        CPIItem(
            name="Men's Apparel",
            fred_series_id="CUSR0000SAA1",
            weight=0.66,
            category="Apparel",
            subcategory="Men's Apparel",
            description="Men's and boys' apparel"
        ),
        CPIItem(
            name="Women's Apparel",
            fred_series_id="CUSR0000SAA2",
            weight=1.16,
            category="Apparel",
            subcategory="Women's Apparel",
            description="Women's and girls' apparel"
        ),
        CPIItem(
            name="Footwear",
            fred_series_id="CUSR0000SEAE",
            weight=0.62,
            category="Apparel",
            subcategory="Footwear",
            description="All footwear"
        ),
    ],

    # ==========================================================================
    # TRANSPORTATION (~15.2% of CPI)
    # ==========================================================================
    "transportation": [
        CPIItem(
            name="Private Transportation",
            fred_series_id="CUSR0000SAT1",
            weight=14.04,
            category="Transportation",
            subcategory="Private Transportation",
            description="New and used vehicles, motor fuel, maintenance"
        ),
        CPIItem(
            name="New Vehicles",
            fred_series_id="CUSR0000SETA01",
            weight=3.98,
            category="Transportation",
            subcategory="Private - New Vehicles",
            description="New cars and trucks"
        ),
        CPIItem(
            name="Used Cars and Trucks",
            fred_series_id="CUSR0000SETA02",
            weight=2.36,
            category="Transportation",
            subcategory="Private - Used Vehicles",
            description="Used cars and trucks"
        ),
        CPIItem(
            name="Motor Fuel (Gasoline)",
            fred_series_id="CUSR0000SETB01",
            weight=3.01,
            category="Transportation",
            subcategory="Private - Gasoline",
            description="Gasoline (all types)"
        ),
        CPIItem(
            name="Motor Vehicle Insurance",
            fred_series_id="CUSR0000SETE",
            weight=2.92,
            category="Transportation",
            subcategory="Private - Insurance",
            description="Motor vehicle insurance premiums"
        ),
        CPIItem(
            name="Motor Vehicle Maintenance and Repair",
            fred_series_id="CUSR0000SETD",
            weight=1.12,
            category="Transportation",
            subcategory="Private - Maintenance",
            description="Vehicle maintenance and repair services"
        ),
        CPIItem(
            name="Public Transportation",
            fred_series_id="CUSR0000SAT2",
            weight=1.15,
            category="Transportation",
            subcategory="Public Transportation",
            description="Airline fares, intercity transportation"
        ),
        CPIItem(
            name="Airline Fares",
            fred_series_id="CUSR0000SETG01",
            weight=0.59,
            category="Transportation",
            subcategory="Public - Airline",
            description="Commercial airline tickets"
        ),
    ],

    # ==========================================================================
    # MEDICAL CARE (~8.4% of CPI)
    # ==========================================================================
    "medical_care": [
        CPIItem(
            name="Medical Care",
            fred_series_id="CUSR0000SAM",
            weight=8.35,
            category="Medical Care",
            subcategory="All Medical Care",
            description="Medical care commodities and services"
        ),
        CPIItem(
            name="Medical Care Commodities",
            fred_series_id="CUSR0000SAM1",
            weight=1.53,
            category="Medical Care",
            subcategory="Commodities",
            description="Prescription drugs, medical equipment"
        ),
        CPIItem(
            name="Prescription Drugs",
            fred_series_id="CUSR0000SEMF01",
            weight=1.03,
            category="Medical Care",
            subcategory="Commodities - Prescription Drugs",
            description="Prescription medications"
        ),
        CPIItem(
            name="Medical Care Services",
            fred_series_id="CUSR0000SAM2",
            weight=6.82,
            category="Medical Care",
            subcategory="Services",
            description="Physician services, hospital services"
        ),
        CPIItem(
            name="Physicians' Services",
            fred_series_id="CUSR0000SEMC01",
            weight=1.53,
            category="Medical Care",
            subcategory="Services - Physicians",
            description="Physician services"
        ),
        CPIItem(
            name="Hospital Services",
            fred_series_id="CUSR0000SEMD01",
            weight=2.17,
            category="Medical Care",
            subcategory="Services - Hospital",
            description="Hospital room and services"
        ),
        CPIItem(
            name="Health Insurance",
            fred_series_id="CUSR0000SEME",
            weight=0.89,
            category="Medical Care",
            subcategory="Services - Insurance",
            description="Health insurance premiums"
        ),
    ],

    # ==========================================================================
    # RECREATION (~5.3% of CPI)
    # ==========================================================================
    "recreation": [
        CPIItem(
            name="Recreation",
            fred_series_id="CUSR0000SAR",
            weight=5.31,
            category="Recreation",
            subcategory="All Recreation",
            description="Video and audio, pets, sporting goods, admissions"
        ),
        CPIItem(
            name="Video and Audio",
            fred_series_id="CUSR0000SERA01",
            weight=1.12,
            category="Recreation",
            subcategory="Video and Audio",
            description="Television, audio equipment, streaming services"
        ),
        CPIItem(
            name="Pets, Pet Products and Services",
            fred_series_id="CUSR0000SERB",
            weight=1.22,
            category="Recreation",
            subcategory="Pets",
            description="Pets and pet-related products and services"
        ),
        CPIItem(
            name="Sporting Goods",
            fred_series_id="CUSR0000SERC01",
            weight=0.56,
            category="Recreation",
            subcategory="Sporting Goods",
            description="Sports equipment and supplies"
        ),
        CPIItem(
            name="Admissions",
            fred_series_id="CUSR0000SERF",
            weight=0.78,
            category="Recreation",
            subcategory="Admissions",
            description="Movies, concerts, sporting events"
        ),
    ],

    # ==========================================================================
    # EDUCATION AND COMMUNICATION (~6.2% of CPI)
    # ==========================================================================
    "education_and_communication": [
        CPIItem(
            name="Education and Communication",
            fred_series_id="CUSR0000SAE",
            weight=6.18,
            category="Education and Communication",
            subcategory="All Education and Communication",
            description="Tuition, telephone services, computer hardware"
        ),
        CPIItem(
            name="Education",
            fred_series_id="CUSR0000SAE1",
            weight=2.73,
            category="Education and Communication",
            subcategory="Education",
            description="Tuition, school fees, childcare"
        ),
        CPIItem(
            name="Tuition, Other School Fees, and Childcare",
            fred_series_id="CUSR0000SEEB",
            weight=2.73,
            category="Education and Communication",
            subcategory="Education - Tuition",
            description="College tuition, school fees, daycare"
        ),
        CPIItem(
            name="Communication",
            fred_series_id="CUSR0000SAE2",
            weight=3.45,
            category="Education and Communication",
            subcategory="Communication",
            description="Telephone services, internet, postal services"
        ),
        CPIItem(
            name="Telephone Services",
            fred_series_id="CUSR0000SEED",
            weight=1.89,
            category="Education and Communication",
            subcategory="Communication - Telephone",
            description="Wireless and landline telephone services"
        ),
        CPIItem(
            name="Information Technology, Hardware and Services",
            fred_series_id="CUSR0000SEEE",
            weight=0.87,
            category="Education and Communication",
            subcategory="Communication - IT",
            description="Computers, tablets, software, internet services"
        ),
    ],

    # ==========================================================================
    # OTHER GOODS AND SERVICES (~3.7% of CPI)
    # ==========================================================================
    "other_goods_and_services": [
        CPIItem(
            name="Other Goods and Services",
            fred_series_id="CUSR0000SAG",
            weight=3.67,
            category="Other Goods and Services",
            subcategory="All Other",
            description="Personal care, tobacco, financial services"
        ),
        CPIItem(
            name="Personal Care",
            fred_series_id="CUSR0000SAG1",
            weight=2.43,
            category="Other Goods and Services",
            subcategory="Personal Care",
            description="Personal care products and services"
        ),
        CPIItem(
            name="Tobacco and Smoking Products",
            fred_series_id="CUSR0000SEGA",
            weight=0.52,
            category="Other Goods and Services",
            subcategory="Tobacco",
            description="Cigarettes, tobacco products"
        ),
        CPIItem(
            name="Personal Care Services",
            fred_series_id="CUSR0000SEGB",
            weight=1.03,
            category="Other Goods and Services",
            subcategory="Personal Care Services",
            description="Haircuts, spa services"
        ),
    ],
}


# =============================================================================
# HEADLINE CPI INDICES
# =============================================================================
CPI_HEADLINE_INDICES: Dict[str, CPIItem] = {
    "all_items": CPIItem(
        name="CPI All Items",
        fred_series_id="CPIAUCSL",
        weight=100.0,
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: All Items"
    ),
    "core_cpi": CPIItem(
        name="Core CPI (Less Food and Energy)",
        fred_series_id="CPILFESL",
        weight=100.0,  # Core weight (excludes food and energy)
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: All Items Less Food and Energy"
    ),
    "food": CPIItem(
        name="CPI Food",
        fred_series_id="CPIUFDSL",
        weight=13.52,
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: Food"
    ),
    "energy": CPIItem(
        name="CPI Energy",
        fred_series_id="CPIENGSL",
        weight=6.87,
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: Energy"
    ),
    "services": CPIItem(
        name="CPI Services",
        fred_series_id="CUSR0000SAS",
        weight=62.78,
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: Services"
    ),
    "commodities": CPIItem(
        name="CPI Commodities",
        fred_series_id="CUSR0000SAC",
        weight=37.22,
        category="Headline",
        description="Consumer Price Index for All Urban Consumers: Commodities"
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_cpi_items() -> List[CPIItem]:
    """Get a flat list of all CPI basket items."""
    all_items = []
    for category_items in CPI_BASKET.values():
        all_items.extend(category_items)
    return all_items


def get_all_fred_series() -> Dict[str, str]:
    """Get all FRED series IDs as a dictionary {name: series_id}."""
    series = {}
    for item in get_all_cpi_items():
        series[item.name] = item.fred_series_id
    for key, item in CPI_HEADLINE_INDICES.items():
        series[item.name] = item.fred_series_id
    return series


def get_headline_series() -> Dict[str, str]:
    """Get headline CPI series as a dictionary {name: series_id}."""
    return {item.name: item.fred_series_id for item in CPI_HEADLINE_INDICES.values()}


def get_category_items(category: str) -> List[CPIItem]:
    """Get all CPI items for a specific category."""
    return CPI_BASKET.get(category, [])


def get_category_weights() -> Dict[str, float]:
    """Get the total weight for each category."""
    weights = {}
    for category, items in CPI_BASKET.items():
        # Use the first (main) item's weight as the category weight
        if items:
            weights[category] = items[0].weight
    return weights


def get_items_by_weight(min_weight: float = 1.0) -> List[CPIItem]:
    """Get all CPI items with weight >= min_weight."""
    return [item for item in get_all_cpi_items() if item.weight >= min_weight]


def get_primary_series() -> Dict[str, str]:
    """
    Get primary CPI series for efficient data loading.
    These are the main category indices that cover most of the CPI.
    """
    primary_items = [
        # Headline indices
        CPI_HEADLINE_INDICES["all_items"],
        CPI_HEADLINE_INDICES["core_cpi"],
        CPI_HEADLINE_INDICES["food"],
        CPI_HEADLINE_INDICES["energy"],
        # Major categories (first item from each category)
        CPI_BASKET["food_and_beverages"][0],  # Food at Home
        CPI_BASKET["housing"][0],  # Shelter
        CPI_BASKET["apparel"][0],  # Apparel
        CPI_BASKET["transportation"][0],  # Private Transportation
        CPI_BASKET["medical_care"][0],  # Medical Care
        CPI_BASKET["recreation"][0],  # Recreation
        CPI_BASKET["education_and_communication"][0],  # Education and Communication
        CPI_BASKET["other_goods_and_services"][0],  # Other
        # Key volatility drivers
        CPI_BASKET["transportation"][3],  # Motor Fuel (Gasoline)
        CPI_BASKET["housing"][3],  # Fuels and Utilities
    ]
    return {item.name: item.fred_series_id for item in primary_items}


# =============================================================================
# DATA FRESHNESS CONFIGURATION
# =============================================================================

CPI_UPDATE_SCHEDULE = {
    "frequency": "monthly",
    "typical_release_day": 10,  # Usually released around the 10th-15th of month
    "cache_ttl_hours": 24,  # Cache data for 24 hours before refresh
    "max_cache_age_days": 7,  # Force refresh if cache is older than 7 days
}


def get_cache_ttl() -> timedelta:
    """Get the cache time-to-live for CPI data."""
    return timedelta(hours=CPI_UPDATE_SCHEDULE["cache_ttl_hours"])


def get_max_cache_age() -> timedelta:
    """Get the maximum cache age before forced refresh."""
    return timedelta(days=CPI_UPDATE_SCHEDULE["max_cache_age_days"])
