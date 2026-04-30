"""
Constants, mappings, and configuration for textile design assistant.

Contains size mappings, color families, occasion filters, and design system
configuration used throughout the application.
"""

# ============================================================================
# STRIPE SIZE MAPPING
# ============================================================================
STRIPE_SIZE_MAP = {
    "Micro":  {"min": 0.2, "max": 1.0},
    "Small":  {"min": 0.2, "max": 2.0},
    "Medium": {"min": 0.2, "max": 4.0},
    "Large":  {"min": 0.5, "max": 10.0},
}
"""Stripe size ranges in millimeters. Maps size names to min/max values."""


# ============================================================================
# DESIGN SIZE MAPPING
# ============================================================================
DESIGN_SIZE_MAP = {
    "Micro":     {"min": 0.1,  "max": 1.0},
    "Small":     {"min": 0.5,  "max": 2.0},
    "Medium":    {"min": 2.0,  "max": 5.0},
    "Large":     {"min": 5.0,  "max": 25.0},
    "Full Size": {"min": 25.0, "max": 100.0},
}
"""Design repeat size ranges in centimeters. Maps size names to min/max values."""


# ============================================================================
# OCCASION-BASED SIZE FILTERING
# ============================================================================
OCCASION_SIZE_MAP = {
    "Formal":     ["Micro", "Small", "Medium"],
    "Casual":     ["Medium", "Large"],
    "Party Wear": ["Micro", "Small", "Medium", "Large", "Full Size"],
}
"""Allowed design sizes by market occasion. Filters available sizes in UI."""


# ============================================================================
# COLOR FAMILY PALETTE DEFINITIONS
# ============================================================================
COLOR_FAMILIES = {
    "Navy Blue":    {"family": ["Royal Blue", "Steel Blue"],      "harmony": ["Cobalt Blue", "Indigo"],    "contrast": ["Gold", "White"]},
    "Sky Blue":     {"family": ["Baby Blue", "Powder Blue"],      "harmony": ["Cerulean", "Teal"],         "contrast": ["White", "Coral"]},
    "White":        {"family": ["Ivory", "Cream"],                "harmony": ["Light Grey", "Silver"],     "contrast": ["Navy Blue", "Black"]},
    "Black":        {"family": ["Charcoal", "Dark Grey"],         "harmony": ["Slate", "Graphite"],        "contrast": ["White", "Gold"]},
    "Grey":         {"family": ["Light Grey", "Slate"],           "harmony": ["Silver", "Charcoal"],       "contrast": ["White", "Red"]},
    "Beige":        {"family": ["Cream", "Sand"],                 "harmony": ["Tan", "Khaki"],             "contrast": ["Brown", "Burgundy"]},
    "Forest Green": {"family": ["Light Green", "Dark Green"],     "harmony": ["Olive", "Moss"],            "contrast": ["Gold", "Red"]},
    "Burgundy":     {"family": ["Wine", "Maroon"],                "harmony": ["Rose", "Mauve"],            "contrast": ["Gold", "Cream"]},
    "Red":          {"family": ["Crimson", "Scarlet"],            "harmony": ["Orange Red", "Rose"],       "contrast": ["White", "Navy Blue"]},
    "Yellow":       {"family": ["Lemon", "Mustard"],              "harmony": ["Gold", "Amber"],            "contrast": ["Black", "Navy Blue"]},
}
"""
Color family definitions. Each base color has family, harmony, and contrast
colors used for palette generation. Used by build_color_palette().
"""
