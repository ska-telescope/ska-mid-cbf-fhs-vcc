from ska_mid_cbf_fhs_common.base_classes.device.utils.admin_online import AdminOnline


class VccAdminOnline(AdminOnline):
    def check_controller_specific(self):
        return super().check_controller_specific()
