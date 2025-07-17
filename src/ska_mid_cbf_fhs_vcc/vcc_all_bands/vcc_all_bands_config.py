schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "VCC All Bands Controller Configuration",
    "description": "Configuration object for the VCC All Bands Controller",
    "type": "object",
    "properties": {
        "config_id": {"type": "string"},
        "expected_dish_id": {"type": "string"},
        "dish_sample_rate": {
            "type": "integer",
            "minimum": 3960000000,
            "maximum": 11891998800,
        },
        "samples_per_frame": {"type": "integer"},
        "frequency_band": {"type": "string", "enum": ["1", "2", "3", "4", "5a", "5b"]},
        "frequency_band_offset_stream_1": {
            "type": "integer",
            "min": -100000000,
            "max": 100000000,
        },
        "frequency_band_offset_stream_2": {
            "type": "integer",
            "min": -100000000,
            "max": 100000000,
        },
        "vcc_gain": {"type": "array", "items": {"type": "number"}},
        "noise_diode_transition_holdoff_seconds": {"type": "integer", "minimum": 0, "maximum": 65535},
        "band_5_tuning": {"type": "number"},
        "b123_pwrm": {"type": "object", "properties": {"averaging_time": {"type": "integer"}, "flagging": {"type": "integer"}}},
        "b45a_pwrm": {"type": "object", "properties": {"averaging_time": {"type": "integer"}, "flagging": {"type": "integer"}}},
        "b5b_pwrm": {"type": "object", "properties": {"averaging_time": {"type": "integer"}, "flagging": {"type": "integer"}}},
        "fs_lanes": {
            "type": "array",
            "items": {"type": "object", "properties": {"averaging_time": {"type": "integer"}, "flagging": {"type": "integer"}}},
        },
    },
    "required": [
        "config_id",
        "expected_dish_id",
        "dish_sample_rate",
        "samples_per_frame",
        "frequency_band",
        "frequency_band_offset_stream_1",
        "vcc_gain",
        "noise_diode_transition_holdoff_seconds",
        "b123_pwrm",
        "b45a_pwrm",
        "b5b_pwrm",
    ],
}

# fmt: off
example_config = {
    "config_id": "1",
    "expected_dish_id": "MKT001",
    "dish_sample_rate": 3960000000,
    "samples_per_frame": 18,
    "vcc_gain": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "frequency_band": "2",
    "noise_diode_transition_holdoff_seconds": 0,
    "frequency_band_offset_stream_1": 110,
    "frequency_band_offset_stream_2": 56,
    "b123_pwrm": {"averaging_time": 1, "flagging": 0},
    "b45a_pwrm": {"averaging_time": 1, "flagging": 0},
    "b5b_pwrm": {"averaging_time": 1, "flagging": 0},
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
