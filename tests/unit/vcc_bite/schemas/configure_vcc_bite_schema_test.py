import json

import jsonschema

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsConfigureVCCBiteSchema
from ska_mid_cbf_fhs_vcc.vcc_all_bands.schemas.configure_vcc_byte import vcc_all_bands_configure_vcc_bite_schema

class TestVCCAllBandsConfigureVCCBiteSchema:
    def test_vcc_all_bands_configure_vcc_bite_schema_valid_input_success(self):
        with open("tests/test_data/device_config/vcc_bite.json") as event_json_file:
            event_json = json.loads(event_json_file.read())

        jsonschema.validate(event_json, vcc_all_bands_configure_vcc_bite_schema)

    def test_vcc_all_bands_config_dataclass_matches_schema(self):
        with open("tests/test_data/device_config/vcc_bite.json") as event_json_file:
            event_json_str = event_json_file.read()
        # Assert implicitly that the following does not error (i.e. from type mismatch, missing value, etc)
        _ = VCCAllBandsConfigureVCCBiteSchema.from_json(event_json_str)
