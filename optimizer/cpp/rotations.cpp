#include <vector>
#include <string>
#include <set>
#include <algorithm>
#include "types.h"

std::vector<OrientedSize> generate_rotations(const Product& p) {
    std::set<OrientedSize> unique_rots;
    
    // We analyze allowed vertical axes
    // Convert allowed_rotations to uppercase for case-insensitive matching
    std::string rot = p.allowed_rotations;
    std::transform(rot.begin(), rot.end(), rot.begin(), ::toupper);

    // Z-vertical (flat placement) is always allowed for all products.
    // X-vertical and Y-vertical (tipping) are only allowed if XYZ is specified.
    bool allow_z = true;
    bool allow_x = (rot.find("XYZ") != std::string::npos);
    bool allow_y = (rot.find("XYZ") != std::string::npos);

    // 1. Z-axis is vertical (original height remains height)
    if (allow_z) {
        unique_rots.insert({p.length, p.width, p.height});
        unique_rots.insert({p.width, p.length, p.height});
    }

    // 2. X-axis is vertical (original length becomes height)
    if (allow_x) {
        unique_rots.insert({p.width, p.height, p.length});
        unique_rots.insert({p.height, p.width, p.length});
    }

    // 3. Y-axis is vertical (original width becomes height)
    if (allow_y) {
        unique_rots.insert({p.length, p.height, p.width});
        unique_rots.insert({p.height, p.length, p.width});
    }

    std::vector<OrientedSize> result(unique_rots.begin(), unique_rots.end());
    return result;
}
