######
#
# Borrowed from the MDA FW teams Bitstream package for use with testing in the pipeline
# https://gitlab.com/ska-telescope/ska-mid-cbf/infra/ska-mid-cbf-bitstreams/-/blob/main/raw/ska-mid-cbf-agilex-vcc/drivers/fpga_driver_common/driver/py_driver_wrap.py?ref_type=heads
#
#######

import ctypes
import fcntl
import logging
import pathlib
import sys
import os
import importlib
from contextlib import contextmanager

sys.path.append(os.path.join(os.path.dirname(__file__)))


def _get_vfio_group_id(device_name):
    link_path = pathlib.Path("/sys/bus/pci/devices/") / device_name / "iommu_group"
    group_path = link_path.readlink()
    group_number = int(group_path.parts[-1])
    return group_number

VFIO_TYPE1_IOMMU = 1
VFIO_BASE = 0x3B00 + 100
VFIO_SET_IOMMU = VFIO_BASE + 2
VFIO_GROUP_SET_CONTAINER = VFIO_BASE + 4
VFIO_GROUP_GET_DEVICE_FD = VFIO_BASE + 6
VFIO_DEVICE_GET_REGION_INFO = VFIO_BASE + 8

VFIO_REGION_INFO_FLAG_READ  = 1 << 0 # Region supports read
VFIO_REGION_INFO_FLAG_WRITE = 1 << 1 # Region supports write
VFIO_REGION_INFO_FLAG_MMAP  = 1 << 2 # Region supports mmap

class vfio_region_info(ctypes.Structure):
    _fields_ = [
        ("argsz", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),  
        ("index", ctypes.c_uint32),  # Region index */
        ("resv",  ctypes.c_uint32),  # Reserved for alignment */
        ("size",   ctypes.c_uint64), # Region size (bytes) */
        ("offset", ctypes.c_uint64), # Region offset from start of device fd */
    ]

def _vfio_open_device_fd(device_name : str, region_num : int = 2):
    # Do vfio stuff to get a file handle.
    with open("/dev/vfio/vfio", 'rb') as container_fd:
        group_id = _get_vfio_group_id(device_name)
        group_path = "/dev/vfio/" + str(group_id)
        with open(group_path, 'wb') as group_fd:
            # set_group_container
            ctnr = ctypes.c_int(container_fd.fileno())
            fcntl.ioctl(group_fd, VFIO_GROUP_SET_CONTAINER, ctnr)
            # Set IOMMU model we want
            fcntl.ioctl(container_fd, VFIO_SET_IOMMU, VFIO_TYPE1_IOMMU)
            # Get a file descripter to memmap.
            dev = bytearray(device_name, 'ascii')
            device_fd = fcntl.ioctl(group_fd, VFIO_GROUP_GET_DEVICE_FD, dev)

    # Get information about the region.
    region_info_bytes = bytearray(vfio_region_info(argsz=32, index=region_num))
    fcntl.ioctl(device_fd, VFIO_DEVICE_GET_REGION_INFO, region_info_bytes)
    region_info = vfio_region_info.from_buffer(region_info_bytes)

    logging.info(f"Region {region_info.index}: size={region_info.size/1024/1024} MiB, offset=0x{region_info.offset:08X}, flags = {region_info.flags}, file={device_fd}")
    if region_info.size <= 0:
        raise ValueError(f"Region {region_num} has zeros size, so can't be mapped.")
    return device_fd, int(region_info.offset)

def _open_device_fd_inner(memory_location : str, region_num = 2):
    # Open the device file that accesses the registers.
    if pathlib.Path(memory_location).exists():
        memfile = open(memory_location, 'r+b')
        file_handle = memfile.fileno()
        bridge_addr = -1  # uses bridge offset from the DeTrI json file.
    elif len(memory_location) > 0 and ":" in memory_location:
        # PCIe bus address.
        # Setup VFIO
        file_handle, bridge_addr = _vfio_open_device_fd(memory_location, region_num)
    else:
        raise Exception(f"Unknown memory location: {memory_location}. Expecting a file like /dev/mem or a PCIe bus address like 0000:81:00.0")

    return file_handle, bridge_addr

@contextmanager
def open_device_fd(memory_location : str, region_num = 2):
    file_handle = None
    try:
        file_handle, bridge_addr = _open_device_fd_inner(memory_location, region_num)
        yield file_handle, bridge_addr
    finally:
        if file_handle is not None:
            os.close(file_handle)

def _struct_to_dict(obj):
    if hasattr(obj, "name") and hasattr(obj, "value"):  # Enum case
        return obj.name
    elif isinstance(obj, (int, float, str, bool, type(None))):  # Base cases
        return obj
    elif isinstance(obj, (list, tuple)):  # Handle sequences
        return [_struct_to_dict(item) for item in obj]
    elif hasattr(obj, "__dict__"):  # Python objects with __dict__
        return {key: _struct_to_dict(value) for key, value in vars(obj).items()}
    else:  # Fallback to dir-based inspection for pybind structs
        return {
            attr: _struct_to_dict(getattr(obj, attr))
            for attr in dir(obj)
            if not attr.startswith("_")
        }

class Py_Driver_Wrap:
    def __init__(self, name: str, driver_info : dict, pybind_module_name: str, register_file_handle: int, bridge_address_offset : int, logger: logging.Logger):
        """
        Initialize a driver for the given instance name, based on the configuration contained in the DeTrI JSON

        Args: 
            name (str): The name of the driver instance, as defined in the DeTrI JSON.
            driver_info (dict): The configuration dict for the driver instance, as defined in the DeTrI JSON.
            pybind_module_name (str): The name of the (compiled) pybind module, which contains all driver submodules.
            register_file_handle (int): The file number of the open file that represents the memory mapped register bus.
            bridge_address_offset (int): The address in the file where the register bus begins.
            logger (logging.Logger): A Python logger instance for logging messages redirected from the drivers' C++.

        Raises:
            KeyError: If the provided driver instance name is not found in the py_drivers file.
        """

        self.name = name
        self.pybind_module_name = pybind_module_name
        self.driver_info = driver_info

        # Get the driver name for this driver instance:
        self.driver_name = self.driver_info["driver"]

        # Get the driver submodule name for this driver instance:
        self.driver_submodule_name = self.driver_info["driver"].replace("_driver", "")

        logger.info(f"Instantiating instance '{self.name}' of driver '{self.driver_submodule_name}'.")

        # Import the base submodule, and the driver submodule, from the master pybind module:
        base_submodule = importlib.import_module(f"{self.pybind_module_name}.fpga_driver_base")
        self.driver_submodule = importlib.import_module(f"{self.pybind_module_name}.{self.driver_submodule_name}")

        # Setup CLogger to redirect log messages from C++ to python
        class CLogger(base_submodule.Logger):
            severity_to_level = {
                base_submodule.LogLevel.Failure: logging.CRITICAL,
                base_submodule.LogLevel.Error: logging.ERROR,
                base_submodule.LogLevel.Warning: logging.WARNING,
                base_submodule.LogLevel.Info: logging.INFO,
                base_submodule.LogLevel.Pass: logging.INFO,
                base_submodule.LogLevel.Debug: logging.DEBUG,
                base_submodule.LogLevel.Trace: logging.DEBUG,
            }
            level_to_severity = {v: k for k, v in reversed(severity_to_level.items())}

            def __init__(self, logger: logging.Logger):
                """Init the C logger with the provided python log level"""
                self.logger = logger
                base_submodule.Logger.__init__(self, self.level_to_severity[logger.getEffectiveLevel()])
                self._monkey_patch_set_level()

            def log_message(self, severity, msg):
                """Override the C log_message and forward logs to the python logger"""
                self.logger.log(self.severity_to_level[severity], msg)

            def _monkey_patch_set_level(self):
                """Hook the python setLevel function and forward the new level to C"""
                original_setLevel = self.logger.setLevel

                def patched_setLevel(level):
                    original_setLevel(level)
                    severity = self.level_to_severity[level]
                    self.logger.info(f"Setting C logger to level {severity}")
                    self.set_logging_level(severity)

                self.logger.setLevel = patched_setLevel

        self.c_logger = CLogger(logger)

        # Loop through the register sets of this driver instance, and populate the regsetinfos dict:
        self.regsetinfos = {}
        self.meta={}
        for regset_id, regset_info in self.driver_info.get("register_sets", {}).items():
            # Get the unique pybind class for this regset's param type (i.e. csr_param_t, phy_param_t, etc, as named in driver's pybind wrapper)
            # If no param struct is defined in header, and has no pybind class in wrapper, fall back on (empty) BaseParams type in base module
            param_class_name = f"{regset_id}_param_t"
            param_class = getattr(self.driver_submodule, param_class_name, base_submodule.base_param_t)
            parameters = regset_info.get("parameters", {})
            param_t = param_class()
            for k, v in parameters.items():
                setattr(param_t, k, v)

            bridge_address = regset_info["bridge_address"] if bridge_address_offset < 0 else bridge_address_offset

            self.regsetinfos[regset_id] = base_submodule.RegisterSetInfo(
                file_handle=register_file_handle,
                address=bridge_address + regset_info['firmware_offset'],
                depth=regset_info["firmware_depth"],
                version=regset_info["regdef"]["version"],
                parameters=param_t,
            )
            self.meta[regset_id]=dict(
                address=hex(regset_info['firmware_offset']),
                depth=regset_info["firmware_depth"],
                version=regset_info["regdef"]["version"],
            )

        self.driver = self.driver_submodule.driver(self.regsetinfos, self.c_logger)

    def configure(self, config=None):
        cfg = self.driver_submodule.config_t()
        if config is not None:
            for k, v in config.items():
                setattr(cfg, k, v)
        self.driver.configure(cfg)
            
    def status(self, clear: bool = False):
        status = self.driver_submodule.status_t()
        self.driver.status(status, clear)
        return _struct_to_dict(status)

    def start(self):
        self.driver.start()

    def stop(self, force: bool = False):
        self.driver.stop(force)

    def recover(self):
        self.driver.recover()


def main():
    import math
    import mmap
    # Example usage:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    memory_location="0000:01:00.0"
    region_num = 2

    reg_addr = 0x500
    size = 128*4 #bytes.

    def ceil_pow2(num) -> int:
        return int(2 ** math.ceil(math.log2(num)))

    with open_device_fd(memory_location, region_num) as (file_handle, bridge_addr):
        base_address = bridge_addr + reg_addr
        page_offset = base_address % mmap.PAGESIZE
        page_address = base_address - page_offset
        length = ceil_pow2(size) + page_offset
        memmap = mmap.mmap(
            fileno = file_handle,
            length=length,
            offset=page_address,
            flags=mmap.MAP_SHARED,
        )
        reg_file = memoryview(memmap).cast("I")
        

        print(hex(page_address), hex(page_offset), hex(base_address))
        print(len(reg_file))

        for addr in range(page_offset//4, (page_offset+size)//4):
            print(f"0x{addr*4:04X}: 0x{reg_file[addr]:08x}, {reg_file[addr]}")

if __name__ == "__main__":
    exit(main())