import json

from app.adapters.base import RawMediaItem, SourceAdapter, map_record


class JSONAdapter(SourceAdapter):
    source_type = "json"

    def fetch(self, config: dict) -> list[RawMediaItem]:
        raw_bytes: bytes = config["file_bytes"]
        field_mapping = config.get("field_mapping")
        data = json.loads(raw_bytes.decode(config.get("encoding", "utf-8")))
        records_path = config.get("records_path")  # e.g. "items" if JSON is {"items": [...]}
        records = data.get(records_path, []) if records_path else data
        if not isinstance(records, list):
            raise ValueError("JSON payload must resolve to a list of records")
        return [map_record(r, field_mapping) for r in records]
