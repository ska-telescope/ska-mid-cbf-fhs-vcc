vcc_all_bands_configure_vcc_bite_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "VCC All Bands Configure VCC Bite Command Schema",
    "description": "Schema object for the ConfigureVCCBite command describing what properties the ConfigureVCCBite command can have and which ones are required",
    "type": "object",
    "properties": {
        "receiver": {
            "type": "object",
            "properties": {
                "dish_id": {"type": "string"},
                "dish_sample_rate_MHz": {"type": "integer"},
                "noise_diode": {
                    "type": "object",
                    "properties": {
                        "dwell_time_us": {"type": "integer"},
                        "random_pattern_seed": {"type": "integer"},
                        "on_state_scaling_factor": {"type": "number"},
                    },
                    "required": ["dwell_time_us", "random_pattern_seed", "on_state_scaling_factor"],
                },
                "noise_info": {
                    "type": "object",
                    "properties": {
                        "pol_x": {
                            "type": "object",
                            "properties": {
                                "seed": {"type": "integer"},
                                "noise_std": {"type": "integer"},
                                "noise_mean": {"type": "integer"},
                            },
                            "required": ["seed", "noise_std", "noise_mean"],
                        },
                        "pol_y": {
                            "type": "object",
                            "properties": {
                                "seed": {"type": "integer"},
                                "noise_std": {"type": "integer"},
                                "noise_mean": {"type": "integer"},
                            },
                            "required": ["seed", "noise_std", "noise_mean"],
                        },
                    },
                },
            },
            "required": ["dish_id", "dish_sample_rate_MHz", "noise_diode"],
        },
        "source": {
            "type": "object",
            "properties": {
                "noise_info": {
                    "type": "object",
                    "properties": {
                        "pol_x": {
                            "type": "object",
                            "properties": {
                                "seed": {"type": "integer"},
                                "noise_std": {"type": "integer"},
                                "noise_mean": {"type": "integer"},
                            },
                            "required": ["seed", "noise_std", "noise_mean"],
                        },
                        "pol_y": {
                            "type": "object",
                            "properties": {
                                "seed": {"type": "integer"},
                                "noise_std": {"type": "integer"},
                                "noise_mean": {"type": "integer"},
                            },
                            "required": ["seed", "noise_std", "noise_mean"],
                        },
                    },
                    "required": ["pol_x", "pol_y"],
                },
                "pol_coupling_rho": {"type": "number"},
                "pol_Y_1_sample_delay": {"type": "boolean"},
            },
            "required": ["noise_info", "pol_coupling_rho", "pol_Y_1_sample_delay"],
        },
        "rfi": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pol_x": {
                        "type": "object",
                        "properties": {"frequency": {"type": "integer"}, "scale": {"type": "number"}},
                        "required": ["frequency", "scale"],
                    },
                    "pol_y": {
                        "type": "object",
                        "properties": {"frequency": {"type": "integer"}, "scale": {"type": "number"}},
                        "required": ["frequency", "scale"],
                    },
                },
                "required": ["pol_x"],
            },
        },
        "utc_start_time": {"type": "integer"},
        "band": {"type": "integer"},
        "transaction_id": {"type": "string"},
    },
    "required": ["receiver", "source", "rfi", "utc_start_time"],
}
