from app.adapters.base import RawMediaItem, SourceAdapter, map_record
from app.seed.demo_data_generator import generate_demo_records


class DemoAdapter(SourceAdapter):
    """מספק נתוני הדגמה סינתטיים. אינו ספק חיצוני אמיתי — מסומן בבירור
    כ-demo ברמת SourceConnection.source_type, ולא מעורבב עם נתוני אמת
    (סעיף 18 במפרט)."""

    source_type = "demo"

    def fetch(self, config: dict) -> list[RawMediaItem]:
        count = config.get("item_count", 200)
        seed = config.get("seed", 42)
        records = generate_demo_records(count=count, seed=seed)
        return [map_record(r, None) for r in records]
