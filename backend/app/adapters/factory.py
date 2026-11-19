from app.adapters.base import SourceAdapter
from app.adapters.csv_adapter import CSVAdapter
from app.adapters.demo_adapter import DemoAdapter
from app.adapters.generic_api_adapter import GenericAPIAdapter
from app.adapters.json_adapter import JSONAdapter

_ADAPTERS: dict[str, type[SourceAdapter]] = {
    "csv": CSVAdapter,
    "json": JSONAdapter,
    "api_generic": GenericAPIAdapter,
    "demo": DemoAdapter,
}


def get_adapter(source_type: str) -> SourceAdapter:
    adapter_cls = _ADAPTERS.get(source_type)
    if not adapter_cls:
        raise ValueError(f"Unknown source_type: {source_type}")
    return adapter_cls()
