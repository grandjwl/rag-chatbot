# llmServer/tests/fakes/fake_metadata_bundle.py

from app.core.metadata_bundle import MetadataBundle

def build_fake_metadata():

    return MetadataBundle(
        refine_cache={},
        column_map={},
        data_stats={
            "min_date": "2020-01-01",
            "max_date": "2024-12-31",
        },
        schema_context="Table sales(product_id, amount, date)",
        valid_joins={}
    )