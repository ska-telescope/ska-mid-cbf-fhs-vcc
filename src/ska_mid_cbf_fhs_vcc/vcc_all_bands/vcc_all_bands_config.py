
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
		"frequency_band": {
			"type": "string",
			"enum": ["1", "2", "3", "4", "5a", "5b"]
		},
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
		"vcc_gain": {
			"type": "array", 
			"items": {"type": "number"}
		},
		"noise_diode_transition_holdoff_seconds": {
			"type": "integer",
			"minimum": 0,
			"maximum": 65535
		},
		"band_5_tuning": {"type": "number"},
	},
    "required": [
        "config_id",
        "dish_sample_rate",
        "samples_per_frame",
        "frequency_band",
        "frequency_band_offset_stream_1",
        "frequency_band_offset_stream_2",
        "vcc_gain",
        "noise_diode_transition_holdoff_seconds"
    ]
}