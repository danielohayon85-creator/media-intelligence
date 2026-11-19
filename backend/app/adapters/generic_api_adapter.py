"""Adapter גנרי ל-API של ספק ניטור חיצוני (סעיף 3 במפרט). עדיין לא מחובר
לספק אמיתי — ה-config מגדיר endpoint, שיטת הזדהות, מיפוי שדות וסינון ראשוני,
כך שחיבור ספק עתידי ידרוש הגדרה בלבד, לא שינוי קוד."""

import httpx

from app.adapters.base import RawMediaItem, SourceAdapter, map_record


class GenericAPIAdapter(SourceAdapter):
    source_type = "api_generic"

    def _build_auth_headers(self, config: dict) -> dict:
        auth_type = config.get("auth_type", "none")
        auth_value = config.get("auth_value")
        if auth_type == "bearer" and auth_value:
            return {"Authorization": f"Bearer {auth_value}"}
        if auth_type == "api_key" and auth_value:
            header_name = config.get("auth_header_name", "X-API-Key")
            return {header_name: auth_value}
        return {}

    def fetch(self, config: dict) -> list[RawMediaItem]:
        endpoint = config.get("endpoint")
        if not endpoint:
            raise ValueError("source config is missing 'endpoint'")

        headers = self._build_auth_headers(config)
        params = config.get("filters", {})
        timeout = config.get("timeout_seconds", 20)

        with httpx.Client(timeout=timeout) as client:
            response = client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        records_path = config.get("records_path")
        records = data.get(records_path, []) if records_path else data
        if not isinstance(records, list):
            raise ValueError("API response did not resolve to a list of records")

        field_mapping = config.get("field_mapping")
        return [map_record(r, field_mapping) for r in records]
