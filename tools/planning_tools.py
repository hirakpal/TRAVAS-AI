"""Planning and synthesis tools for Yojana"""

from typing import List, Dict, Any, Optional, Tuple


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


class SubmitItineraryTool:
    """Tool for Yojana to submit the final itinerary as a structured,
    schema-typed object rather than free-form prose.

    This is the actual contract-validation fix: previously Yojana's
    create_itinerary() returned whatever markdown text Claude produced, and
    nothing downstream (Parikshak, the UI, storage) enforced any structure
    on it - no guarantee of valid day numbers, no guarantee two activities
    don't overlap, no guarantee costs were even numeric. models/itinerary.py
    already defines a proper TravelItinerary/DayPlan/ScheduledActivity
    schema for exactly this purpose, but nothing ever populated it. This
    tool is called with tool_choice forced (not left to the model's
    discretion), so a structured submission is mandatory, not optional.
    """

    name = "submit_itinerary"
    description = (
        "Submit the complete finalized itinerary in structured form, covering every "
        "day and every scheduled activity with times, locations, and costs. Call this "
        "once you have a finished plan - it is what gets validated and shown to the user."
    )

    input_schema = {
        "type": "object",
        "properties": {
            "destination": {"type": "string"},
            "start_date": {"type": "string", "description": "e.g. '26 Jan'"},
            "end_date": {"type": "string", "description": "e.g. '30 Jan'"},
            "num_travelers": {"type": "integer"},
            "total_cost": {"type": "number", "description": "Total estimated cost across the whole trip, in INR"},
            "budget": {"type": "number", "description": "The traveler's stated total budget, in INR, if known"},
            "days": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "day_number": {"type": "integer"},
                        "date": {"type": "string"},
                        "theme": {"type": "string"},
                        "activities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "activity_type": {
                                        "type": "string",
                                        "enum": ["Hotel", "Breakfast", "Lunch", "Dinner", "Snack",
                                                 "Attraction", "Shopping", "Transport", "Rest", "Adventure"],
                                    },
                                    "start_time": {"type": "string", "description": "24-hour HH:MM"},
                                    "end_time": {"type": "string", "description": "24-hour HH:MM"},
                                    "location": {"type": "string"},
                                    "cost": {"type": "number", "description": "Cost in INR, 0 if free"},
                                    "source_agent": {
                                        "type": "string",
                                        "description": "Which specialist recommended this: atithi, annapurna, yatra, safar, or bazaar",
                                    },
                                },
                                "required": ["name", "activity_type", "start_time", "end_time", "location"],
                            },
                        },
                    },
                    "required": ["day_number", "date", "activities"],
                },
            },
        },
        "required": ["destination", "start_date", "end_date", "num_travelers", "days"],
    }

    @staticmethod
    def execute(**kwargs) -> Dict[str, Any]:
        # Not invoked through the normal tool_result round-trip - Yojana
        # reads block.input directly off the forced tool_use response and
        # hands it to parse_and_validate_itinerary(). Implemented for
        # interface consistency with the other tools only.
        return {"success": True}


def parse_and_validate_itinerary(data: Dict[str, Any]) -> Tuple[Optional[Any], List[str], List[str]]:
    """Parse a submit_itinerary tool call's input into the TravelItinerary
    schema and run deterministic (non-LLM-judgment) validation on it.

    Returns (itinerary_or_None, issues, warnings). itinerary is None only if
    parsing itself failed (e.g. required fields missing/malformed) - that
    failure is itself a contract violation and is included in `issues`.
    """
    from models.itinerary import TravelItinerary, DayPlan, ScheduledActivity, ActivityType

    issues: List[str] = []
    warnings: List[str] = []

    try:
        days = []
        for day_data in data.get("days", []):
            day_number = day_data.get("day_number", 0)
            activities = []
            for i, act_data in enumerate(day_data.get("activities", [])):
                raw_type = act_data.get("activity_type", "Attraction")
                try:
                    activity_type = ActivityType(raw_type)
                except ValueError:
                    issues.append(
                        f"Day {day_number}: unknown activity_type '{raw_type}' for "
                        f"'{act_data.get('name', 'unnamed activity')}' - not one of the allowed types"
                    )
                    activity_type = ActivityType.ATTRACTION

                cost = act_data.get("cost", 0) or 0
                try:
                    cost = float(cost)
                except (TypeError, ValueError):
                    issues.append(f"Day {day_number}: non-numeric cost for '{act_data.get('name', '?')}': {cost!r}")
                    cost = 0.0

                activities.append(ScheduledActivity(
                    id=f"d{day_number}_a{i}",
                    name=act_data.get("name", "Unnamed activity"),
                    activity_type=activity_type,
                    start_time=act_data.get("start_time", ""),
                    end_time=act_data.get("end_time", ""),
                    duration_minutes=act_data.get("duration_minutes", 0),
                    location=act_data.get("location", ""),
                    cost=cost,
                    source_agent=act_data.get("source_agent", ""),
                ))

            # Deterministic overlap check - not an LLM judgment call, a real
            # comparison of HH:MM strings (consistent zero-padded 24h format
            # sorts correctly as strings).
            timed = sorted(
                [a for a in activities if a.start_time and a.end_time],
                key=lambda a: a.start_time,
            )
            for a1, a2 in zip(timed, timed[1:]):
                if a1.end_time > a2.start_time:
                    issues.append(
                        f"Day {day_number}: '{a1.name}' ({a1.start_time}-{a1.end_time}) overlaps "
                        f"'{a2.name}' ({a2.start_time}-{a2.end_time})"
                    )

            if len(activities) > 6:
                warnings.append(f"Day {day_number}: {len(activities)} activities scheduled (recommend max 5-6)")

            daily_cost = sum(a.cost for a in activities)
            days.append(DayPlan(
                day_number=day_number,
                date=day_data.get("date", ""),
                theme=day_data.get("theme", ""),
                activities=activities,
                activity_count=len(activities),
                daily_cost=daily_cost,
            ))

        # Day-number sanity: sequential and unique, not just "however the
        # model happened to number them."
        day_numbers = [d.day_number for d in days]
        if day_numbers and (sorted(day_numbers) != day_numbers or len(set(day_numbers)) != len(day_numbers)):
            issues.append(f"Day numbers are not sequential/unique: {day_numbers}")

        total_cost = data.get("total_cost")
        computed_cost = sum(d.daily_cost for d in days)
        if total_cost is None:
            total_cost = computed_cost
        else:
            try:
                total_cost = float(total_cost)
            except (TypeError, ValueError):
                issues.append(f"Non-numeric total_cost: {total_cost!r}")
                total_cost = computed_cost

        budget = data.get("budget")
        if budget:
            try:
                budget = float(budget)
                if total_cost > budget:
                    issues.append(f"Total cost ₹{total_cost:,.0f} exceeds budget ₹{budget:,.0f}")
            except (TypeError, ValueError):
                pass

        itinerary = TravelItinerary(
            id=f"itin_{str(data.get('destination', 'trip')).lower().replace(' ', '_')}",
            destination=data.get("destination", "Unknown"),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            num_travelers=data.get("num_travelers", 0),
            days=days,
            total_duration_days=len(days),
            total_cost=total_cost,
            total_activities=sum(len(d.activities) for d in days),
            is_validated=True,
            validation_issues=issues,
        )
        return itinerary, issues, warnings

    except Exception as e:
        return None, [f"Structured itinerary failed to parse: {str(e)}"], []


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
