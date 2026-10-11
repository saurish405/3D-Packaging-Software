#include <vector>
#include <cmath>
#include <algorithm>
#include "types.h"

// Filters products that fall within a target height range [target_height - tolerance, target_height + tolerance]
std::vector<Product> filter_products_by_height(const std::vector<Product>& products, float target_height, float tolerance) {
    std::vector<Product> filtered;
    for (const auto& p : products) {
        if (std::abs(p.height - target_height) <= tolerance) {
            filtered.push_back(p);
        }
    }
    return filtered;
}

// Determines the height of a layer based on the tallest item successfully packed within it
float get_max_placement_height(const std::vector<Placement>& placements) {
    float max_h = 0.0f;
    for (const auto& pl : placements) {
        if (pl.height > max_h) {
            max_h = pl.height;
        }
    }
    return max_h;
}
