import csv
import io

from app.adapters.base import RawMediaItem, SourceAdapter, map_record


class CSVAdapter(SourceAdapter):
    source_type = "csv"

    def fetch(self, config: dict) -> list[RawMediaItem]:
        raw_bytes: bytes = config["file_bytes"]
        field_mapping = config.get("field_mapping")
        text = raw_bytes.decode(config.get("encoding", "utf-8"))
        reader = csv.DictReader(io.StringIO(text))
        return [map_record(row, field_mapping) for row in reader]
