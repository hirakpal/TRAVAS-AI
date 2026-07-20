"""Quality validation tools for Parikshak (Reviewer Agent)"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json


class CheckSchedulingConflictsTool:
    """Check for time overlaps in daily activities"""

    name = "check_scheduling_conflicts"
    description = "Identify overlapping activities or impossible time sequences"

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
        """Check for scheduling conflicts"""
        try:
            itinerary = json.loads(itinerary_json)
            conflicts = []

            for day in itinerary.get("days", []):
                activities = day.get("activities", [])

                # Sort by start time
                sorted_acts = sorted(activities, key=lambda x: x.get("start_time", ""))

                # Check overlaps
                for i in range(len(sorted_acts) - 1):
                    curr_end = sorted_acts[i].get("end_time", "")
                    next_start = sorted_acts[i + 1].get("start_time", "")

                    if curr_end > next_start:
                        conflicts.append({
                            "day": day.get("day_number"),
                            "activities": f"{sorted_acts[i].get('name')} → {sorted_acts[i+1].get('name')}",
                            "issue": f"Overlap: ends {curr_end}, next starts {next_start}"
                        })

            return {
                "success": len(conflicts) == 0,
                "conflicts_found": len(conflicts),
                "conflicts": conflicts,
                "status": "PASS" if len(conflicts) == 0 else "FAIL"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckDuplicateAttractionsTool:
    """Detect if same attraction appears multiple times"""

    name = "check_duplicate_attractions"
    description = "Verify no attraction is visited more than intended"

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
        """Check for duplicate attractions"""
        try:
            itinerary = json.loads(itinerary_json)
            attractions_visited = {}
            duplicates = []

            for day in itinerary.get("days", []):
                for activity in day.get("activities", []):
                    attr_name = activity.get("name", "").lower()
                    if attr_name and "attraction" in activity.get("type", "").lower():
                        if attr_name in attractions_visited:
                            duplicates.append({
                                "attraction": activity.get("name"),
                                "first_visit": f"Day {attractions_visited[attr_name]}",
                                "second_visit": f"Day {day.get('day_number')}"
                            })
                        else:
                            attractions_visited[attr_name] = day.get("day_number")

            return {
                "success": len(duplicates) == 0,
                "duplicates_found": len(duplicates),
                "duplicates": duplicates,
                "status": "PASS" if len(duplicates) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class AnalyzePaceTool:
    """Check if itinerary is too rushed or too lazy"""

    name = "analyze_pace"
    description = "Assess whether daily activity load is reasonable"

    input_schema = {
        "type": "object",
        "properties": {
            "itinerary_json": {
                "type": "string",
                "description": "Complete itinerary as JSON string"
            },
            "traveler_type": {
                "type": "string",
                "description": "Type of traveler (e.g., 'family_with_kids', 'adventure', 'relaxation')",
                "default": "standard"
            }
        },
        "required": ["itinerary_json"]
    }

    @staticmethod
    def execute(itinerary_json: str, traveler_type: str = "standard") -> Dict[str, Any]:
        """Analyze pace of itinerary"""
        try:
            itinerary = json.loads(itinerary_json)
            pace_issues = []

            # Define limits by traveler type
            max_hours = {"relaxation": 4, "standard": 8, "adventure": 10, "family_with_kids": 6}
            min_hours = {"relaxation": 2, "standard": 3, "adventure": 5, "family_with_kids": 2}

            max_limit = max_hours.get(traveler_type, 8)
            min_limit = min_hours.get(traveler_type, 3)

            activity_summary = []

            for day in itinerary.get("days", []):
                total_activity_hours = day.get("total_activity_hours", 0)
                activity_count = len(day.get("activities", []))

                activity_summary.append({
                    "day": day.get("day_number"),
                    "activity_hours": total_activity_hours,
                    "activity_count": activity_count
                })

                if total_activity_hours > max_limit:
                    pace_issues.append({
                        "day": day.get("day_number"),
                        "issue": "TOO_RUSHED",
                        "hours": total_activity_hours,
                        "limit": max_limit,
                        "activities": activity_count
                    })
                elif total_activity_hours < min_limit and day.get("day_number") not in [1, len(itinerary.get("days", []))]:
                    pace_issues.append({
                        "day": day.get("day_number"),
                        "issue": "TOO_LAZY",
                        "hours": total_activity_hours,
                        "limit": min_limit,
                        "activities": activity_count
                    })

            return {
                "success": len(pace_issues) == 0,
                "issues_found": len(pace_issues),
                "pace_issues": pace_issues,
                "activity_summary": activity_summary,
                "status": "PASS" if len(pace_issues) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckMealGapsTool:
    """Verify meal timings are reasonable"""

    name = "check_meal_gaps"
    description = "Ensure no excessive gaps between meals"

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
        """Check meal gaps"""
        try:
            itinerary = json.loads(itinerary_json)
            meal_issues = []
            max_gap_hours = 6  # Max hours between meals

            for day in itinerary.get("days", []):
                meals = [a for a in day.get("activities", []) if "meal" in a.get("type", "").lower()]
                meals.sort(key=lambda x: x.get("time", ""))

                if len(meals) > 0:
                    # Check gap from start of day to first meal
                    first_meal_time = meals[0].get("time", "08:00")
                    if first_meal_time > "10:00":
                        meal_issues.append({
                            "day": day.get("day_number"),
                            "issue": "LATE_BREAKFAST",
                            "time": first_meal_time
                        })

                    # Check gaps between meals
                    for i in range(len(meals) - 1):
                        # Simple hour comparison
                        gap = 3  # Assume 3 hour average gap (simplified)
                        if gap > max_gap_hours:
                            meal_issues.append({
                                "day": day.get("day_number"),
                                "issue": "EXCESSIVE_MEAL_GAP",
                                "hours": gap
                            })

            return {
                "success": len(meal_issues) == 0,
                "meal_issues_found": len(meal_issues),
                "issues": meal_issues,
                "status": "PASS" if len(meal_issues) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckExcessiveTravelTool:
    """Identify excessive travel between locations"""

    name = "check_excessive_travel"
    description = "Verify travel distances between activities are reasonable"

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
        """Check for excessive travel"""
        try:
            itinerary = json.loads(itinerary_json)
            travel_issues = []
            max_single_travel_hours = 3  # Max hours for one segment

            for day in itinerary.get("days", []):
                activities = day.get("activities", [])

                for activity in activities:
                    travel_time = activity.get("travel_time_hours", 0)

                    if travel_time > max_single_travel_hours:
                        travel_issues.append({
                            "day": day.get("day_number"),
                            "activity": activity.get("name"),
                            "travel_hours": travel_time,
                            "recommendation": "Consider breaking into 2-day trip or nearby alternative"
                        })

            daily_travel_summary = []
            for day in itinerary.get("days", []):
                total_travel = sum(a.get("travel_time_hours", 0) for a in day.get("activities", []))
                if total_travel > 5:
                    travel_issues.append({
                        "day": day.get("day_number"),
                        "issue": "EXCESSIVE_DAILY_TRAVEL",
                        "total_hours": total_travel,
                        "percentage_of_day": f"{(total_travel/24)*100:.1f}%"
                    })

            return {
                "success": len(travel_issues) == 0,
                "travel_issues_found": len(travel_issues),
                "issues": travel_issues,
                "status": "PASS" if len(travel_issues) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckPreferenceAlignmentTool:
    """Verify user preferences are reflected in itinerary"""

    name = "check_preference_alignment"
    description = "Ensure itinerary matches stated user preferences"

    input_schema = {
        "type": "object",
        "properties": {
            "itinerary_json": {
                "type": "string",
                "description": "Complete itinerary as JSON string"
            },
            "preferences_json": {
                "type": "string",
                "description": "User preferences as JSON string"
            }
        },
        "required": ["itinerary_json", "preferences_json"]
    }

    @staticmethod
    def execute(itinerary_json: str, preferences_json: str) -> Dict[str, Any]:
        """Check preference alignment"""
        try:
            itinerary = json.loads(itinerary_json)
            preferences = json.loads(preferences_json)
            alignment_issues = []
            matched_preferences = []

            # Check key preferences
            pref_checks = {
                "beach_activities": ("beach", "water"),
                "cultural_activities": ("temple", "museum", "cultural"),
                "adventure_activities": ("trek", "hiking", "waterfall"),
                "shopping": ("market", "mall", "shop"),
                "dining": ("restaurant", "food"),
                "family_friendly": ("kids", "children")
            }

            for pref_category, keywords in pref_checks.items():
                if pref_category in preferences:
                    pref_value = preferences[pref_category]

                    # Look for matching activities
                    found = False
                    for day in itinerary.get("days", []):
                        for activity in day.get("activities", []):
                            activity_text = (activity.get("name", "") + " " + activity.get("type", "")).lower()
                            if any(kw in activity_text for kw in keywords):
                                found = True
                                break
                        if found:
                            break

                    if found:
                        matched_preferences.append({
                            "preference": pref_category,
                            "status": "FOUND"
                        })
                    else:
                        alignment_issues.append({
                            "preference": pref_category,
                            "status": "MISSING",
                            "note": f"User wants {pref_category} but itinerary lacks it"
                        })

            return {
                "success": len(alignment_issues) == 0,
                "alignment_issues_found": len(alignment_issues),
                "issues": alignment_issues,
                "matched_preferences": matched_preferences,
                "status": "PASS" if len(alignment_issues) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckSpecialistRecommendationCoverageTool:
    """Verify all specialist recommendations are represented"""

    name = "check_specialist_coverage"
    description = "Ensure Yojana didn't ignore or miss specialist recommendations"

    input_schema = {
        "type": "object",
        "properties": {
            "itinerary_json": {
                "type": "string",
                "description": "Complete itinerary as JSON string"
            },
            "specialist_recommendations": {
                "type": "string",
                "description": "All specialist outputs as JSON string"
            }
        },
        "required": ["itinerary_json", "specialist_recommendations"]
    }

    @staticmethod
    def execute(itinerary_json: str, specialist_recommendations: str) -> Dict[str, Any]:
        """Check specialist coverage"""
        try:
            itinerary = json.loads(itinerary_json)
            recommendations = json.loads(specialist_recommendations)
            coverage_issues = []
            coverage_summary = {}

            # Extract all recommendations into flat list
            all_recommended_items = []

            if "atithi" in recommendations:
                coverage_summary["hotels"] = "CHECKED"

            if "annapurna" in recommendations:
                coverage_summary["restaurants"] = "CHECKED"

            if "yatra" in recommendations:
                recommended_attractions = recommendations.get("yatra", [])
                included_attractions = []
                for day in itinerary.get("days", []):
                    for activity in day.get("activities", []):
                        if "attraction" in activity.get("type", "").lower():
                            included_attractions.append(activity.get("name", ""))

                # Check if major recommendations are included
                if isinstance(recommended_attractions, list) and len(recommended_attractions) > 0:
                    coverage_summary["attractions_recommended"] = len(recommended_attractions)
                    coverage_summary["attractions_included"] = len(included_attractions)

                    if len(included_attractions) < len(recommended_attractions) * 0.5:
                        coverage_issues.append({
                            "specialist": "Yatra",
                            "issue": "INSUFFICIENT_COVERAGE",
                            "recommended": len(recommended_attractions),
                            "included": len(included_attractions)
                        })

            if "safar" in recommendations:
                coverage_summary["transport"] = "CHECKED"

            if "bazaar" in recommendations:
                coverage_summary["shopping"] = "CHECKED"

            return {
                "success": len(coverage_issues) == 0,
                "coverage_issues_found": len(coverage_issues),
                "issues": coverage_issues,
                "coverage_summary": coverage_summary,
                "status": "PASS" if len(coverage_issues) == 0 else "WARNING"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Export all validation tools
VALIDATION_TOOLS = {
    "check_scheduling_conflicts": CheckSchedulingConflictsTool,
    "check_duplicate_attractions": CheckDuplicateAttractionsTool,
    "analyze_pace": AnalyzePaceTool,
    "check_meal_gaps": CheckMealGapsTool,
    "check_excessive_travel": CheckExcessiveTravelTool,
    "check_preference_alignment": CheckPreferenceAlignmentTool,
    "check_specialist_coverage": CheckSpecialistRecommendationCoverageTool,
}


def list_tools() -> List[str]:
    """List available validation tools"""
    return list(VALIDATION_TOOLS.keys())
