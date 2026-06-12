import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

LocationInput = Union[str, Tuple[float, float], Sequence[float], Dict[str, float]]


class CrimeRiskAgent:
    """A lightweight location-based crime risk analysis agent."""

    def __init__(self) -> None:
        self._now = datetime.now()
        self.area_profiles: List[Dict[str, Any]] = [
            {
                "name": "Downtown",
                "lat": -26.2041,
                "lon": 28.0473,
                "population": 45000,
                "population_density": 6200,
                "vulnerability": 0.9,
                "description": "Busy commercial center with mixed retail, transport and nightlife."
            },
            {
                "name": "Suburban East",
                "lat": -26.1500,
                "lon": 28.1000,
                "population": 22000,
                "population_density": 2100,
                "vulnerability": 0.4,
                "description": "Residential suburb with lower incident frequency."
            },
            {
                "name": "Industrial District",
                "lat": -26.1800,
                "lon": 28.0200,
                "population": 12000,
                "population_density": 3500,
                "vulnerability": 0.8,
                "description": "Warehouse zone with theft risk around infrastructure and loading areas."
            },
            {
                "name": "University Precinct",
                "lat": -26.1880,
                "lon": 28.0570,
                "population": 18000,
                "population_density": 4100,
                "vulnerability": 0.7,
                "description": "Student and staff area with variable risk over the academic year."
            }
        ]

        now = self._now
        self.crime_records: List[Dict[str, Any]] = [
            {
                "area": "Downtown",
                "lat": -26.2048,
                "lon": 28.0470,
                "type": "Robbery",
                "severity": "High",
                "reported_at": now - timedelta(hours=1, minutes=20),
            },
            {
                "area": "Downtown",
                "lat": -26.2035,
                "lon": 28.0458,
                "type": "Burglary",
                "severity": "Medium",
                "reported_at": now - timedelta(hours=5),
            },
            {
                "area": "Downtown",
                "lat": -26.2052,
                "lon": 28.0485,
                "type": "Vehicle Theft",
                "severity": "High",
                "reported_at": now - timedelta(days=1, hours=2),
            },
            {
                "area": "Suburban East",
                "lat": -26.1514,
                "lon": 28.0992,
                "type": "Burglary",
                "severity": "Medium",
                "reported_at": now - timedelta(days=2, hours=3),
            },
            {
                "area": "Suburban East",
                "lat": -26.1490,
                "lon": 28.1017,
                "type": "Petty Theft",
                "severity": "Low",
                "reported_at": now - timedelta(days=3),
            },
            {
                "area": "Industrial District",
                "lat": -26.1788,
                "lon": 28.0195,
                "type": "Equipment Theft",
                "severity": "High",
                "reported_at": now - timedelta(hours=8),
            },
            {
                "area": "Industrial District",
                "lat": -26.1795,
                "lon": 28.0210,
                "type": "Vandalism",
                "severity": "Medium",
                "reported_at": now - timedelta(days=1, hours=12),
            },
            {
                "area": "University Precinct",
                "lat": -26.1885,
                "lon": 28.0562,
                "type": "Pickpocketing",
                "severity": "Low",
                "reported_at": now - timedelta(hours=2, minutes=40),
            },
            {
                "area": "University Precinct",
                "lat": -26.1870,
                "lon": 28.0580,
                "type": "Assault",
                "severity": "High",
                "reported_at": now - timedelta(days=1, hours=6),
            },
            {
                "area": "University Precinct",
                "lat": -26.1890,
                "lon": 28.0550,
                "type": "Burglary",
                "severity": "Medium",
                "reported_at": now - timedelta(days=4),
            }
        ]

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c

    def _normalize_location(self, location: LocationInput) -> Dict[str, Any]:
        if isinstance(location, str):
            return {"descriptor": location.strip(), "lat": None, "lon": None}

        if isinstance(location, dict):
            return {"descriptor": "Coordinates", "lat": float(location["lat"]), "lon": float(location["lon"])}

        if isinstance(location, (list, tuple)) and len(location) == 2:
            return {"descriptor": "Coordinates", "lat": float(location[0]), "lon": float(location[1])}

        raise ValueError("Location must be a neighborhood string, a coord tuple, or a dict with lat/lon.")

    def _match_area_by_name(self, descriptor: str) -> Optional[Dict[str, Any]]:
        normalized = descriptor.lower().strip()
        for profile in self.area_profiles:
            if normalized == profile["name"].lower() or profile["name"].lower() in normalized:
                return profile
        return None

    def _find_nearest_area(self, lat: float, lon: float) -> Dict[str, Any]:
        nearest = min(self.area_profiles, key=lambda profile: self._haversine(lat, lon, profile["lat"], profile["lon"]))
        return nearest

    def count_crimes_near_location(self, location: LocationInput, radius_km: float = 2.0) -> Dict[str, Any]:
        normalized = self._normalize_location(location)
        if normalized["lat"] is None or normalized["lon"] is None:
            profile = self._match_area_by_name(normalized["descriptor"]) or self.area_profiles[0]
            lat, lon = profile["lat"], profile["lon"]
        else:
            lat, lon = normalized["lat"], normalized["lon"]
            profile = self._find_nearest_area(lat, lon)

        nearby_records = [
            record for record in self.crime_records
            if self._haversine(lat, lon, record["lat"], record["lon"]) <= radius_km
        ]

        counts_by_type: Dict[str, int] = {}
        for record in nearby_records:
            counts_by_type[record["type"]] = counts_by_type.get(record["type"], 0) + 1

        return {
            "query": normalized["descriptor"],
            "matched_area": profile["name"],
            "center_lat": lat,
            "center_lon": lon,
            "search_radius_km": radius_km,
            "nearby_crime_count": len(nearby_records),
            "counts_by_type": counts_by_type,
            "nearby_records": nearby_records,
            "profile": profile,
        }

    def _time_risk_weight(self, timestamp: datetime) -> float:
        hour = timestamp.hour
        if 0 <= hour < 6:
            return 1.0
        if 6 <= hour < 12:
            return 0.6
        if 12 <= hour < 18:
            return 0.7
        return 0.85

    @staticmethod
    def _severity_multiplier(severity: str) -> float:
        return {
            "Low": 0.8,
            "Medium": 1.0,
            "High": 1.2,
            "Critical": 1.4,
        }.get(severity, 1.0)

    def calculate_risk_score(self, location: LocationInput, timestamp: Optional[datetime] = None, radius_km: float = 2.0) -> Dict[str, Any]:
        if timestamp is None:
            timestamp = self._now

        counts = self.count_crimes_near_location(location, radius_km)
        base_count = counts["nearby_crime_count"]
        severity_weights = [self._severity_multiplier(record["severity"]) for record in counts["nearby_records"]]
        avg_severity = sum(severity_weights) / len(severity_weights) if severity_weights else 1.0

        profile = counts["profile"]
        population = max(profile.get("population", 1), 1)
        density_score = min(profile.get("population_density", 0) / 7000.0, 1.0)
        trend_score = self._recent_trend_score(counts["matched_area"])
        time_weight = self._time_risk_weight(timestamp)

        count_score = min(base_count / 8.0, 1.0)
        severity_score = min((avg_severity - 0.8) / 0.6, 1.0)
        vulnerability_score = profile.get("vulnerability", 0.5)

        raw_score = (
            count_score * 0.35
            + severity_score * 0.2
            + density_score * 0.15
            + trend_score * 0.15
            + vulnerability_score * 0.1
            + time_weight * 0.05
        )
        score = round(min(max(raw_score, 0.0), 1.0) * 100)

        if score < 30:
            risk_level = "LOW"
        elif score < 55:
            risk_level = "MODERATE"
        elif score < 75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        if population > 0:
            crimes_per_1000 = round(base_count / (population / 1000), 2)
        else:
            crimes_per_1000 = 0.0

        return {
            "location_query": counts["query"],
            "matched_area": counts["matched_area"],
            "timestamp": timestamp.isoformat(),
            "search_radius_km": counts["search_radius_km"],
            "nearby_crime_count": base_count,
            "crimes_per_1000": crimes_per_1000,
            "risk_score": score,
            "risk_level": risk_level,
            "crime_density": round(density_score * 100, 1),
            "trend_score": round(trend_score * 100, 1),
            "time_score": round(time_weight * 100, 1),
            "top_crime_types": sorted(counts["counts_by_type"].items(), key=lambda x: x[1], reverse=True),
            "details": counts,
        }

    def _recent_trend_score(self, area_name: str) -> float:
        recent = [
            record for record in self.crime_records
            if record["area"] == area_name and (self._now - record["reported_at"]).days < 7
        ]
        if not recent:
            return 0.2
        return min(len(recent) / 5.0, 1.0)

    def analyze_location(self, location: LocationInput, timestamp: Optional[datetime] = None, radius_km: float = 2.0) -> Dict[str, Any]:
        risk = self.calculate_risk_score(location, timestamp, radius_km)
        if risk["risk_level"] in {"HIGH", "CRITICAL"}:
            advice = [
                "Avoid walking alone after dark.",
                "Stay in well-lit areas.",
                "Keep valuables stored securely.",
                "Notify local authorities of suspicious behavior."
            ]
        elif risk["risk_level"] == "MODERATE":
            advice = [
                "Remain aware of your surroundings.",
                "Travel in groups when possible.",
                "Lock doors and secure personal items." ]
        else:
            advice = ["Maintain normal safety practices.", "Report unusual incidents to local security."]

        return {
            "summary": {
                "location_query": risk["location_query"],
                "matched_area": risk["matched_area"],
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
                "top_crime_types": risk["top_crime_types"],
            },
            "analysis": risk,
            "recommendations": advice,
        }


if __name__ == "__main__":
    agent = CrimeRiskAgent()
    sample_query = "Downtown"
    report = agent.analyze_location(sample_query)
    import json

    print(json.dumps(report, indent=2))
