vcc_all_bands_update_ip_block_logging_levels_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "VCC All Bands UpdateIPBlockLoggingLevels Command Input",
    "description": "Input JSON for the UpdateIPBlockLoggingLevels command of the VCC All Bands controller",
    "type": "object",
    "properties": {
        "ip_blocks": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "level": {
            "type": "string",
            "enum": [
                "OFF",
                "FATAL",
                "CRITICAL",
                "ERROR",
                "WARNING",
                "WARN",
                "INFO",
                "DEBUG",
            ],
        },
    },
    "required": [
        "ip_blocks",
        "level",
    ],
}
