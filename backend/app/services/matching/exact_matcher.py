"""Deterministic exact matching engine for medicine equivalence."""
from typing import Optional
from app.core.normalization import (
    normalize_salt_name,
    normalize_dosage_form,
    extract_strength,
    extract_release_type,
    parse_composition,
)


def ingredients_match(
    branded_ingredients: list[dict],
    generic_ingredients: list[dict],
) -> tuple[bool, list[str]]:
    """
    Check if two sets of ingredients match exactly.
    Returns (is_match, list_of_reasons).
    """
    reasons = []

    if len(branded_ingredients) != len(generic_ingredients):
        reasons.append(
            f"Different number of ingredients: {len(branded_ingredients)} vs {len(generic_ingredients)}"
        )
        return False, reasons

    # Create normalized sets for comparison
    branded_set = set()
    for ing in branded_ingredients:
        norm_name = normalize_salt_name(ing.get("name", ""))
        strength = ing.get("strength")
        unit = ing.get("unit", "mg")
        branded_set.add((norm_name, strength, unit))

    generic_set = set()
    for ing in generic_ingredients:
        norm_name = normalize_salt_name(ing.get("name", ""))
        strength = ing.get("strength")
        unit = ing.get("unit", "mg")
        generic_set.add((norm_name, strength, unit))

    if branded_set == generic_set:
        reasons.append("Same active ingredients with same strengths")
        return True, reasons
    else:
        # Find differences
        only_in_branded = branded_set - generic_set
        only_in_generic = generic_set - branded_set
        if only_in_branded:
            reasons.append(f"Ingredients only in branded: {only_in_branded}")
        if only_in_generic:
            reasons.append(f"Ingredients only in generic: {only_in_generic}")
        return False, reasons


def exact_match(
    branded: dict,
    generic: dict,
) -> tuple[bool, list[str], float]:
    """
    Perform deterministic exact match between a branded medicine and a generic.
    
    Args:
        branded: dict with keys: name, ingredients (list of dicts with name, strength, unit), 
                 dosage_form, release_type
        generic: dict with same structure
    
    Returns:
        (is_exact_match, list_of_reasons, confidence_score)
    """
    reasons = []
    confidence = 1.0

    # 1. Check ingredients
    ingredients_ok, ingredient_reasons = ingredients_match(
        branded.get("ingredients", []),
        generic.get("ingredients", []),
    )
    reasons.extend(ingredient_reasons)

    if not ingredients_ok:
        return False, reasons, 0.0

    # 2. Check dosage form
    branded_form = normalize_dosage_form(branded.get("dosage_form", ""))
    generic_form = normalize_dosage_form(generic.get("dosage_form", ""))

    if branded_form and generic_form:
        if branded_form != generic_form:
            reasons.append(f"Different dosage form: {branded_form} vs {generic_form}")
            return False, reasons, 0.0
        else:
            reasons.append(f"Same dosage form: {branded_form}")
    elif branded_form or generic_form:
        # One has form, other doesn't — reduce confidence but don't fail
        confidence *= 0.8
        reasons.append("Dosage form partially verified")

    # 3. Check release type
    branded_release = branded.get("release_type")
    generic_release = generic.get("release_type")

    if branded_release and generic_release:
        if branded_release != generic_release:
            reasons.append(f"Different release type: {branded_release} vs {generic_release}")
            return False, reasons, 0.0
        else:
            reasons.append(f"Same release type: {branded_release}")
    elif branded_release or generic_release:
        confidence *= 0.9
        reasons.append("Release type partially verified")

    # 4. Check strength for each ingredient
    for b_ing in branded.get("ingredients", []):
        b_strength = b_ing.get("strength")
        b_unit = b_ing.get("unit", "mg")
        b_name = normalize_salt_name(b_ing.get("name", ""))

        for g_ing in generic.get("ingredients", []):
            g_name = normalize_salt_name(g_ing.get("name", ""))
            if b_name == g_name:
                g_strength = g_ing.get("strength")
                g_unit = g_ing.get("unit", "mg")
                if b_strength and g_strength:
                    if b_strength != g_strength or b_unit != g_unit:
                        reasons.append(
                            f"Different strength for {b_name}: {b_strength}{b_unit} vs {g_strength}{g_unit}"
                        )
                        return False, reasons, 0.0
                    else:
                        reasons.append(f"Same strength for {b_name}: {b_strength}{b_unit}")

    return True, reasons, confidence


def find_exact_matches(
    branded: dict,
    generic_medicines: list[dict],
) -> list[dict]:
    """
    Find all exact matches for a branded medicine in a list of generic medicines.
    
    Returns list of matches with confidence scores, sorted by confidence.
    """
    matches = []
    for generic in generic_medicines:
        is_match, reasons, confidence = exact_match(branded, generic)
        if is_match:
            matches.append({
                "generic": generic,
                "reasons": reasons,
                "confidence": confidence,
            })
    # Sort by confidence descending
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches
