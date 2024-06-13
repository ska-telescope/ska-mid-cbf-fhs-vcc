#include <pybind11/pybind11.h>
#include "vcc.h"

namespace py = pybind11;

PYBIND11_MODULE(very_course_channelizer_20, m) {
    py::class_<VCC_20>(m, "VCC_20")
        .def(py::init<uintptr_t>())
        .def("registerRead", &VCC_20::registerRead)
        .def("registerWrite", &VCC_20::registerWrite)
        .def("recover", &VCC_20::recover)
        .def("configure", &VCC_20::configure)
        .def("start", &VCC_20::start)
        .def("stop", &VCC_20::stop)
        .def("deconfigure", &VCC_20::deconfigure);
        .def("status", &VCC_20::status);
}