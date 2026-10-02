vcc_all_bands_configure_scan_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "VCC All Bands Controller Configuration",
    "description": "Configuration object for the VCC All Bands Controller",
    "type": "object",
    "properties": {
        "config_id": {"type": "string"},
        "transaction_id": {"type": "string"},
        "expected_dish_id": {"type": "string"},
        "dish_sample_rate": {
            "type": "integer",
            "minimum": 3960000000,
            "maximum": 11891998800,
        },
        "frequency_band": {"type": "string", "enum": ["1", "2", "3", "4", "5a", "5b"]},
        "frequency_band_offset_stream1": {
            "type": "integer",
            "min": -100000000,
            "max": 100000000,
        },
        "frequency_band_offset_stream2": {
            "type": "integer",
            "min": -100000000,
            "max": 100000000,
        },
        "vcc_gains_stream_1": {"type": "array", "items": {"type": "number"}},
        "noise_diode_transition_holdoff_count": {"type": "integer", "minimum": 0, "maximum": 65535},
        "band_5_tuning": {"type": "number"},
        "b123_power_meter": {
            "type": "object", 
            "properties": {
                "averaging_time": {"type": "integer"}, 
                "flagging": {"type": "integer"},
            }, 
            "required": [
                "averaging_time",
                "flagging",
            ],
        },
        "b45_1_power_meter": {
            "type": "object", 
            "properties": {
                "averaging_time": {"type": "integer"}, 
                "flagging": {"type": "integer"},
            }, 
            "required": [
                "averaging_time",
                "flagging",
            ],
        },
        "b45_2_power_meter": {
            "type": "object", 
            "properties": {
                "averaging_time": {"type": "integer"}, 
                "flagging": {"type": "integer"},
            }, 
            "required": [
                "averaging_time",
                "flagging",
            ],
        },
        "fs_lanes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "vlan_id": {"type": "integer"},
                    "fs_id": {"type": "integer"},
                    "power_meter": {
                        "type": "object", 
                        "properties": {
                            "averaging_time": {"type": "integer"}, 
                            "flagging": {"type": "integer"},
                        }, 
                        "required": [
                            "averaging_time",
                            "flagging",
                        ],
                    },  
                },
                "required": [
                    "vlan_id",
                    "fs_id",
                    "power_meter",
                ],
            },
        },
    },
    "required": [
        "config_id",
        "expected_dish_id",
        "dish_sample_rate",
        "frequency_band",
        "frequency_band_offset_stream1",
        "vcc_gains_stream_1",
        "noise_diode_transition_holdoff_count",
        "b123_power_meter",
        "b45_1_power_meter",
        "b45_2_power_meter",
        "fs_lanes",
    ],
    #    "additionalProperties": False,  # TODO uncomment once schema and test data are correct and match
}

# fmt: off
example_config = {
    "config_id": "1",
    "expected_dish_id": "MKT001",
    "dish_sample_rate": 3960000000,
    "vcc_gains_stream_1": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "frequency_band": "2",
    "noise_diode_transition_holdoff_count": 0,
    "frequency_band_offset_stream1": 110,
    "frequency_band_offset_stream2": 56,
    "b123_power_meter": {"averaging_time": 1, "flagging": 0},
    "b45_1_power_meter": {"averaging_time": 1, "flagging": 0},
    "b45_2_power_meter": {"averaging_time": 1, "flagging": 0},
    "fs_lanes": [
        {"vlan_id": 2, "fs_id": 1, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 2, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 3, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 4, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 5, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 6, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 7, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 8, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 9, "averaging_time": 1, "flagging": 0},
        {"vlan_id": 2, "fs_id": 10, "averaging_time": 1, "flagging": 0}
    ]
}
