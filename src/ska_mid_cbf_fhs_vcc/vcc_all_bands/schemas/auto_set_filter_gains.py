vcc_all_bands_auto_set_filter_gains_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "VCC All Bands Auto Set Filter Gains Command Schema",
    "description": "Schema object for the AutoSetFilterGains command describing what properties the Scan command can have and which ones are required",
    "type": "object",
    "properties": {
        "headrooms": {"type": "list[float]"},
        "transaction_id": {"type": "string"},
    },
    "required": [],
}
