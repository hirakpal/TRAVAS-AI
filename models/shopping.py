"""Shopping domain models for Bazaar Shopping Agent"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ShopType(Enum):
    """Types of shops"""
    MARKET = "Market/Bazaar"
    SOUVENIR_SHOP = "Souvenir Shop"
    MALL = "Shopping Mall"
    BOUTIQUE = "Boutique"
    HANDICRAFT = "Handicraft Store"
    SPICE_MARKET = "Spice Market"
    ANTIQUE = "Antique Store"
    ELECTRONICS = "Electronics"
    JEWELRY = "Jewelry Shop"
    CLOTHING = "Clothing Store"
    BOOKSTORE = "Bookstore"
    ART_GALLERY = "Art Gallery"


class ItemCategory(Enum):
    """Product categories"""
    SPICES = "Spices"
    HANDICRAFTS = "Handicrafts"
    TEXTILES = "Textiles/Fabrics"
    JEWELRY = "Jewelry"
    CERAMICS = "Ceramics/Pottery"
    SOUVENIRS = "Souvenirs"
    ELECTRONICS = "Electronics"
    BOOKS = "Books"
    CLOTHING = "Clothing"
    ARTWORK = "Artwork"
    AYURVEDA = "Ayurvedic Products"
    COCONUT_PRODUCTS = "Coconut Products"


class CrowdLevel(Enum):
    """Shop crowd levels"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class Review:
    """Shop review"""
    reviewer_name: str
    rating: float  # 1-5
    comment: str
    date: str  # ISO format
    helpful_count: int = 0


@dataclass
class Item:
    """Product item for sale"""
    name: str
    category: ItemCategory
    price: float  # In INR
    description: str
    quality: str  # Budget/Mid-range/Premium/Luxury
    is_authentic: bool = True  # Real vs fake/imitation
    bargainable: bool = False  # Can negotiate price


@dataclass
class Shop:
    """Shopping location model"""
    id: str
    name: str
    shop_type: ShopType
    address: str
    city: str
    locality: str

    # Contact
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None

    # Ratings & Reviews
    rating: float = 4.0  # 1-5
    num_reviews: int = 0
    reviews: List[Review] = field(default_factory=list)

    # Hours
    opening_time: str = "10:00"
    closing_time: str = "20:00"
    closed_on: List[str] = field(default_factory=list)  # Days closed

    # Location Info
    distance_from_city_center: float = 0
    distance_from_hotel: Optional[float] = None
    google_maps_link: Optional[str] = None

    # Shopping Experience
    typical_crowd_level: CrowdLevel = CrowdLevel.MODERATE
    crowd_by_time: dict = field(default_factory=dict)  # {"morning": "Low", "evening": "High"}
    best_time_to_visit: str = "Morning"
    bargaining_possible: bool = False

    # Features
    items_available: List[Item] = field(default_factory=list)
    product_categories: List[ItemCategory] = field(default_factory=list)
    authenticity_guaranteed: bool = True
    warranty_available: bool = False

    # Facilities
    payment_methods: List[str] = field(default_factory=list)  # Cash, Card, UPI
    has_wifi: bool = False
    has_parking: bool = False
    wheelchair_accessible: bool = False
    refund_policy: str = "No refund"

    # Price Range
    min_price: float = 0
    max_price: float = 10000
    price_range: str = "Budget-Mid-range"

    # Special
    tourist_friendly: bool = True
    negotiable_prices: bool = False
    accepts_international_cards: bool = False
    delivery_available: bool = False

    # Description
    description: str = ""
    special_offers: List[str] = field(default_factory=list)
    popular_items: List[str] = field(default_factory=list)

    def get_average_rating(self) -> float:
        """Calculate average rating"""
        if not self.reviews:
            return self.rating
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def is_accessible(self) -> bool:
        """Check if wheelchair accessible"""
        return self.wheelchair_accessible

    def get_crowd_at_time(self, time_period: str) -> str:
        """Get crowd level at time"""
        return self.crowd_by_time.get(time_period, "Unknown")

    def __repr__(self) -> str:
        return f"<Shop name='{self.name}' type={self.shop_type.value} rating={self.rating}>"


@dataclass
class ShoppingPreferences:
    """User's shopping preferences"""
    interested_categories: List[str] = field(default_factory=list)
    budget: Optional[float] = None
    quality_preference: str = "Mid-range"  # Budget/Mid-range/Premium/Luxury
    prefer_authentic: bool = True
    prefer_bargaining: bool = False
    wheelchair_accessible: bool = False

    # Gift preferences
    for_gifts: bool = False
    num_people: int = 0
    gift_type: Optional[str] = None

    # Shopping style
    prefer_local_markets: bool = True  # vs malls
    prefer_haggling: bool = False
    time_available_hours: Optional[float] = None

    preferred_payment: str = "Cash"  # Cash/Card/UPI


@dataclass
class ShoppingItinerary:
    """Shopping plan for a day"""
    day: int
    date: str
    shops: List[dict] = field(default_factory=list)  # [{shop_id, time, duration, items}]
    estimated_budget: float = 0
    estimated_travel_time: float = 0
    description: str = ""
