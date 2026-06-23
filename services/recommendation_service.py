from models.train import Train
from datetime import datetime, timedelta


# Classes where RAC is structurally impossible
NO_RAC_CLASSES = {"CC", "EC", "2S"}

# Simulated availability — in production, query live train inventory
MOCK_AVAILABILITY = {
    "SF": "AVAILABLE",
    "EXP": "AVAILABLE",
    "RAJ": "LIMITED",
    "SHT": "AVAILABLE",
}


def get_recommendations(data: dict, prob_cnf: float) -> list:
    if prob_cnf >= 50.0:
        return []

    src = data["source_station"]
    dest = data["destination_station"]
    req_class = data["class_type"]
    journey_date = datetime.strptime(data["journey_date"], "%Y-%m-%d")

    recommendations = []

    # 1. Alternative trains on same route
    alt_trains = Train.query.filter(
        Train.source_station == src,
        Train.destination_station == dest,
        Train.train_number != str(data["train_number"]),
    ).limit(3).all()

    for t in alt_trains:
        entry = {
            "type": "ALTERNATIVE_TRAIN",
            "train_number": t.train_number,
            "train_name": t.train_name,
            "train_type": t.train_type,
            "class": req_class if req_class not in _restricted_classes(t.train_type) else _best_class(t.train_type),
            "availability": MOCK_AVAILABILITY.get(t.train_type, "CHECK"),
            "journey_date": data["journey_date"],
        }
        recommendations.append(entry)

    # 2. Alternative date (next day)
    alt_date = (journey_date + timedelta(days=1)).strftime("%Y-%m-%d")
    recommendations.append({
        "type": "ALTERNATIVE_DATE",
        "train_number": str(data["train_number"]),
        "class": req_class,
        "journey_date": alt_date,
        "availability": "LIKELY_AVAILABLE",
        "note": "Next day availability typically 20-35% higher",
    })

    # 3. Alternative class (upgrade/downgrade)
    alt_class = _suggest_alt_class(req_class)
    if alt_class:
        recommendations.append({
            "type": "ALTERNATIVE_CLASS",
            "train_number": str(data["train_number"]),
            "class": alt_class,
            "journey_date": data["journey_date"],
            "availability": "AVAILABLE",
            "note": f"Switch from {req_class} to {alt_class} for higher confirmation chance",
        })

    return recommendations


def _restricted_classes(train_type: str) -> set:
    if train_type == "RAJ":
        return {"SL", "2S"}
    if train_type == "SHT":
        return {"SL", "2S", "1A", "2A", "3A"}
    return set()


def _best_class(train_type: str) -> str:
    if train_type == "SHT":
        return "CC"
    return "3A"


def _suggest_alt_class(cls: str) -> str:
    downgrade_map = {"1A": "2A", "2A": "3A", "3A": "SL"}
    upgrade_map = {"SL": "3A"}
    return downgrade_map.get(cls) or upgrade_map.get(cls, "")
