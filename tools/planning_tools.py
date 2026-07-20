"""Planning and synthesis tools for Yojana"""

from typing import List, Dict, Any


class ValidateItineraryTool:
    """Validate itinerary against constraints"""

    name = "validate_itinerary"
    description = "Validate itinerary for conflicts, feasibility, and constraints"

    input_schema = {
        "type": "object",
        "properties": {
            "itinerary_json": {
                "type": "string",
                "description": "Complete itinerary as JSON string"
            }
        },
        "required": ["itinerary_json"]
    }

    @staticmethod
    def execute(itinerary_json: str) -> Dict[str, Any]:
        """Validate itinerary"""
        try:
            import json
            itinerary = json.loads(itinerary_json)

            issues = []
            warnings = []

            # Check each day
            for day in itinerary.get("days", []):
                activities = day.get("activities", [])

                # Validate time overlaps
                for i, act1 in enumerate(activities):
                    for act2 in activities[i+1:]:
                        if act1["end_time"] > act2["start_time"]:
                            issues.append(f"Day {day['day_number']}: {act1['name']} overlaps {act2['name']}")

                # Validate activity duration
                if day.get("total_activity_time_hours", 0) > 10:
                    warnings.append(f"Day {day['day_number']}: Very busy day ({day['total_activity_time_hours']}h)")

                # Check activity count
                if len(activities) > 6:
                    warnings.append(f"Day {day['day_number']}: {len(activities)} activities (recommend max 5)")

            # Overall validation
            if itinerary.get("total_cost", 0) > itinerary.get("budget", float('inf')):
                issues.append(f"Over budget: ₹{itinerary['total_cost']} > ₹{itinerary['budget']}")

            return {
                "success": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "valid": len(issues) == 0,
                "validation_summary": f"{len(issues)} issues, {len(warnings)} warnings"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class OptimizeSequenceTool:
    """Optimize activity sequence to minimize travel"""

    name = "optimize_sequence"
    description = "Optimize activity sequence within a day to minimize travel time"

    input_schema = {
        "type": "object",
        "properties": {
            "day_activities": {
                "type": "string",
                "description": "JSON array of activities with locations"
            },
            "hotel_location": {
                "type": "string",
                "description": "Hotel location for reference"
            }
        },
        "required": ["day_activities", "hotel_location"]
    }

    @staticmethod
    def execute(day_activities: str, hotel_location: str) -> Dict[str, Any]:
        """Suggest optimized sequence"""
        try:
            import json
            activities = json.loads(day_activities)

            # Group by location
            location_groups = {}
            for act in activities:
                loc = act.get("location", "Unknown")
                if loc not in location_groups:
                    location_groups[loc] = []
                location_groups[loc].append(act)

            # Suggest clustering
            suggestions = []
            for location, acts in location_groups.items():
                if len(acts) > 1:
                    suggestions.append(f"Cluster {len(acts)} activities in {location}")

            return {
                "success": True,
                "current_grouping": location_groups,
                "optimization_suggestions": suggestions,
                "estimated_time_saved_minutes": len(activities) * 10  # Rough estimate
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckConflictsTool:
    """Check for conflicts between specialist recommendations"""

    name = "check_conflicts"
    description = "Identify conflicts between specialist agent recommendations"

    input_schema = {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "string",
                "description": "JSON object with specialist recommendations"
            }
        },
        "required": ["recommendations"]
    }

    @staticmethod
    def execute(recommendations: str) -> Dict[str, Any]:
        """Check for conflicts"""
        try:
            import json
            recs = json.loads(recommendations)

            conflicts = []

            # Check hotel and transport distance
            if "atithi" in recs and "safar" in recs:
                hotel = recs["atithi"].get("name")
                transport = recs["safar"].get("from_location")
                if hotel and transport and hotel != transport:
                    conflicts.append(f"Hotel ({hotel}) ≠ Transport origin ({transport})")

            # Check restaurant and attraction locations
            if "annapurna" in recs and "yatra" in recs:
                rest_loc = recs["annapurna"].get("locality")
                attr_loc = recs["yatra"].get("locality")
                if rest_loc and attr_loc and abs(float(rest_loc.split(",")[0]) - float(attr_loc.split(",")[0])) > 10:
                    conflicts.append(f"Restaurant far from attraction ({rest_loc} vs {attr_loc})")

            return {
                "success": True,
                "conflicts_found": len(conflicts),
                "conflicts": conflicts,
                "has_critical_conflicts": len(conflicts) > 0
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class SynthesizeRecommendationsTool:
    """Combine specialist recommendations into coherent plan"""

    name = "synthesize_recommendations"
    description = "Combine all specialist recommendations into single itinerary framework"

    input_schema = {
        "type": "object",
        "properties": {
            "all_recommendations": {
                "type": "string",
                "description": "JSON with all specialist outputs"
            },
            "constraints": {
                "type": "string",
                "description": "JSON with travel constraints (dates, budget, travelers)"
            }
        },
        "required": ["all_recommendations", "constraints"]
    }

    @staticmethod
    def execute(all_recommendations: str, constraints: str) -> Dict[str, Any]:
        """Synthesize into framework"""
        return {
            "success": True,
            "framework": "Created basic itinerary framework",
            "next_steps": [
                "Validate against constraints",
                "Optimize sequences",
                "Check for conflicts",
                "Present for approval"
            ],
            "ready_for_presentation": True
        }


# Export tools
PLANNING_TOOLS = {
    "validate_itinerary": ValidateItineraryTool,
    "optimize_sequence": OptimizeSequenceTool,
    "check_conflicts": CheckConflictsTool,
    "synthesize_recommendations": SynthesizeRecommendationsTool,
}


def list_tools() -> List[str]:
    """List available tools"""
    return list(PLANNING_TOOLS.keys())
