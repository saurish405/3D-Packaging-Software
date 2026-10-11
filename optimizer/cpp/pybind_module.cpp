#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "types.h"

namespace py = pybind11;

// Forward declarations of functions to bind
extern std::vector<Layer> run_optimization(
    float carton_w, float carton_l, float carton_h,
    const std::vector<Product>& products,
    const std::vector<int>& quantities,
    float top_clearance,
    float cell_size,
    float height_tolerance,
    float required_support_ratio,
    int max_steps
);

extern std::map<int, float> calculate_stack_weights(
    const std::vector<Layer>& layers,
    int grid_width, int grid_height
);

extern bool calculate_cog(
    const std::vector<Placement>& placements, 
    float& cog_x, float& cog_y, float& cog_z, 
    float& total_weight
);

extern float get_cog_score(
    float cog_x, float cog_y, 
    float carton_w, float carton_l
);

extern float calculate_support_ratio(
    const std::vector<std::vector<int>>& lower_grid,
    int gx, int gy, int gw, int gl
);

PYBIND11_MODULE(optimizer_cpp, m) {
    m.doc() = "C++ Core Tiling and 3D Layer Packing Optimization Engine";

    // Bind Product struct
    py::class_<Product>(m, "Product")
        .def(py::init<>())
        .def_readwrite("id", &Product::id)
        .def_readwrite("sku", &Product::sku)
        .def_readwrite("name", &Product::name)
        .def_readwrite("length", &Product::length)
        .def_readwrite("width", &Product::width)
        .def_readwrite("height", &Product::height)
        .def_readwrite("weight", &Product::weight)
        .def_readwrite("fragile", &Product::fragile)
        .def_readwrite("stackable", &Product::stackable)
        .def_readwrite("max_stack_weight", &Product::max_stack_weight)
        .def_readwrite("allowed_rotations", &Product::allowed_rotations);

    // Bind Placement struct
    py::class_<Placement>(m, "Placement")
        .def(py::init<>())
        .def_readwrite("id", &Placement::id)
        .def_readwrite("sku", &Placement::sku)
        .def_readwrite("name", &Placement::name)
        .def_readwrite("gx", &Placement::gx)
        .def_readwrite("gy", &Placement::gy)
        .def_readwrite("gw", &Placement::gw)
        .def_readwrite("gl", &Placement::gl)
        .def_readwrite("x", &Placement::x)
        .def_readwrite("y", &Placement::y)
        .def_readwrite("z", &Placement::z)
        .def_readwrite("length", &Placement::length)
        .def_readwrite("width", &Placement::width)
        .def_readwrite("height", &Placement::height)
        .def_readwrite("weight", &Placement::weight);

    // Bind Layer struct
    py::class_<Layer>(m, "Layer")
        .def(py::init<>())
        .def_readwrite("z_start", &Layer::z_start)
        .def_readwrite("height", &Layer::height)
        .def_readwrite("placements", &Layer::placements)
        .def_readwrite("grid", &Layer::grid);

    // Bind Functions
    m.def("run_optimization", &run_optimization, 
          "Run layer-by-layer carton packing backtracking search",
          py::arg("carton_w"), py::arg("carton_l"), py::arg("carton_h"),
          py::arg("products"), py::arg("quantities"),
          py::arg("top_clearance") = 20.0f, py::arg("cell_size") = 10.0f,
          py::arg("height_tolerance") = 5.0f, py::arg("required_support_ratio") = 0.70f,
          py::arg("max_steps") = 10000);

    m.def("calculate_stack_weights", &calculate_stack_weights,
          "Calculate weight resting on top of each placed item",
          py::arg("layers"), py::arg("grid_width"), py::arg("grid_height"));

    m.def("get_cog_score", &get_cog_score,
          "Calculate CoG scoring ratio",
          py::arg("cog_x"), py::arg("cog_y"), py::arg("carton_w"), py::arg("carton_l"));

    // Lambda wrapper to map reference parameters to Python tuple returns
    m.def("calculate_cog", [](const std::vector<Placement>& placements) {
        float cx = 0.0f, cy = 0.0f, cz = 0.0f, tot = 0.0f;
        bool ok = calculate_cog(placements, cx, cy, cz, tot);
        return py::make_tuple(ok, cx, cy, cz, tot);
    }, "Calculates Center of Gravity and returns tuple (success, x, y, z, total_weight)");

    m.def("calculate_support_ratio", &calculate_support_ratio,
          "Calculate physical surface support ratio from the layer underneath",
          py::arg("lower_grid"), py::arg("gx"), py::arg("gy"), py::arg("gw"), py::arg("gl"));
}
