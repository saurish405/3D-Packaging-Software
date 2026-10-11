#include <vector>
#include <string>
#include <algorithm>
#include <set>
#include <cmath>
#include <iostream>
#include "types.h"

extern std::vector<OrientedSize> generate_rotations(const Product& p);

struct ExtremePoint {
    float x, y, z;

    bool operator==(const ExtremePoint& other) const {
        return std::abs(x - other.x) < 0.1f &&
               std::abs(y - other.y) < 0.1f &&
               std::abs(z - other.z) < 0.1f;
    }
};

// Check 3D AABB non-overlapping collision
static bool check_3d_overlap(
    float x1, float y1, float z1, float l1, float w1, float h1,
    float x2, float y2, float z2, float l2, float w2, float h2
) {
    if (x1 + l1 <= x2 + 0.01f || x2 + l2 <= x1 + 0.01f) return false;
    if (y1 + w1 <= y2 + 0.01f || y2 + w2 <= y1 + 0.01f) return false;
    if (z1 + h1 <= z2 + 0.01f || z2 + h2 <= z1 + 0.01f) return false;
    return true;
}

// Calculate fraction of item bottom area supported by underlying items or floor
static float calculate_ep_support_ratio(
    float x, float y, float z, float length, float width,
    const std::vector<Placement>& placed_items
) {
    if (z <= 0.05f) return 1.0f; // Container floor support

    float total_area = length * width;
    if (total_area <= 0.0f) return 0.0f;

    float supported_area = 0.0f;

    for (const auto& pl : placed_items) {
        // Check if top face of pl matches z (within tolerance)
        if (std::abs((pl.z + pl.height) - z) < 0.5f) {
            float ix1 = std::max(x, pl.x);
            float ix2 = std::min(x + length, pl.x + pl.length);
            float iy1 = std::max(y, pl.y);
            float iy2 = std::min(y + width, pl.y + pl.width);

            if (ix2 > ix1 && iy2 > iy1) {
                supported_area += (ix2 - ix1) * (iy2 - iy1);
            }
        }
    }
    return supported_area / total_area;
}

// Project a point (px, py, pz) downwards to the highest top face underneath it
static float project_z_downward(
    float px, float py, float pz,
    const std::vector<Placement>& placed_items
) {
    float max_support_z = 0.0f;
    for (const auto& pl : placed_items) {
        if (px >= pl.x - 0.01f && px <= pl.x + pl.length + 0.01f &&
            py >= pl.y - 0.01f && py <= pl.y + pl.width + 0.01f) {
            float top = pl.z + pl.height;
            if (top <= pz + 0.01f && top > max_support_z) {
                max_support_z = top;
            }
        }
    }
    return max_support_z;
}

// Main Extreme Point 3D optimization runner
std::vector<Layer> run_optimization(
    float carton_w, float carton_l, float carton_h,
    const std::vector<Product>& products,
    const std::vector<int>& quantities,
    float top_clearance,
    float cell_size,
    float height_tolerance,
    float required_support_ratio,
    int max_steps
) {
    int grid_width = static_cast<int>(std::floor(carton_w / cell_size));
    int grid_height = static_cast<int>(std::floor(carton_l / cell_size));

    if (grid_width <= 0 || grid_height <= 0) {
        return {};
    }

    std::vector<int> current_inventory = quantities;
    std::vector<Placement> all_placements;
    int unique_id_counter = 1;

    // Extreme points set initialized with container origin (0, 0, 0)
    std::vector<ExtremePoint> extreme_points = { {0.0f, 0.0f, 0.0f} };

    float max_allowed_h = carton_h - top_clearance;

    bool progress = true;
    int iterations = 0;

    while (progress && iterations < max_steps) {
        iterations++;
        progress = false;

        // Sort Extreme Points: lowest Z first (gravity), then lowest Y, then lowest X
        std::sort(extreme_points.begin(), extreme_points.end(), [](const ExtremePoint& a, const ExtremePoint& b) {
            if (std::abs(a.z - b.z) > 0.01f) return a.z < b.z;
            if (std::abs(a.y - b.y) > 0.01f) return a.y < b.y;
            return a.x < b.x;
        });

        int best_prod_idx = -1;
        OrientedSize best_rot = {0, 0, 0};
        ExtremePoint best_ep = {0, 0, 0};
        float best_score = -1e9f;

        // Search across inventory and extreme points
        for (size_t i = 0; i < products.size(); ++i) {
            if (current_inventory[i] <= 0) continue;

            const auto& p = products[i];
            std::vector<OrientedSize> rotations = generate_rotations(p);

            for (const auto& rot : rotations) {
                for (const auto& ep : extreme_points) {
                    // Bounds check
                    if (ep.x + rot.length > carton_w + 0.01f ||
                        ep.y + rot.width > carton_l + 0.01f ||
                        ep.z + rot.height > max_allowed_h + 0.01f) {
                        continue;
                    }

                    // Collision check
                    bool collides = false;
                    for (const auto& pl : all_placements) {
                        if (check_3d_overlap(ep.x, ep.y, ep.z, rot.length, rot.width, rot.height,
                                             pl.x, pl.y, pl.z, pl.length, pl.width, pl.height)) {
                            collides = true;
                            break;
                        }
                    }
                    if (collides) continue;

                    // Support ratio check
                    float support = calculate_ep_support_ratio(ep.x, ep.y, ep.z, rot.length, rot.width, all_placements);
                    if (support < required_support_ratio) continue;

                    // Score placement: prefer lower Z, lower Y, lower X, heavier items first
                    float score = - (ep.z * 10000.0f + ep.y * 100.0f + ep.x * 10.0f) + p.weight * 5.0f + (rot.length * rot.width * rot.height) / 10000.0f;

                    if (score > best_score) {
                        best_score = score;
                        best_prod_idx = static_cast<int>(i);
                        best_rot = rot;
                        best_ep = ep;
                    }
                }
            }
        }

        if (best_prod_idx != -1) {
            // Place the selected item
            const auto& p = products[best_prod_idx];
            Placement pl;
            pl.id = unique_id_counter++;
            pl.sku = p.sku;
            pl.name = p.name;
            pl.x = best_ep.x;
            pl.y = best_ep.y;
            pl.z = best_ep.z;
            pl.length = best_rot.length;
            pl.width = best_rot.width;
            pl.height = best_rot.height;
            pl.weight = p.weight;

            // Grid coordinates calculation
            pl.gx = static_cast<int>(std::floor(pl.x / cell_size));
            pl.gy = static_cast<int>(std::floor(pl.y / cell_size));
            pl.gw = static_cast<int>(std::ceil(pl.length / cell_size));
            pl.gl = static_cast<int>(std::ceil(pl.width / cell_size));

            all_placements.push_back(pl);
            current_inventory[best_prod_idx]--;
            progress = true;

            // Generate new Extreme Points from the placed box corners
            std::vector<ExtremePoint> new_points = {
                {best_ep.x + best_rot.length, best_ep.y, best_ep.z},
                {best_ep.x, best_ep.y + best_rot.width, best_ep.z},
                {best_ep.x, best_ep.y, best_ep.z + best_rot.height}
            };

            // Project new points downward if unsupported
            for (auto& np : new_points) {
                if (np.z > 0.0f && np.x < carton_w && np.y < carton_l) {
                    np.z = project_z_downward(np.x, np.y, np.z, all_placements);
                }
            }

            // Merge into extreme_points list (avoiding duplicates and out-of-bounds)
            for (const auto& np : new_points) {
                if (np.x < carton_w && np.y < carton_l && np.z < max_allowed_h) {
                    bool exists = false;
                    for (const auto& existing : extreme_points) {
                        if (existing == np) {
                            exists = true;
                            break;
                        }
                    }
                    if (!exists) {
                        extreme_points.push_back(np);
                    }
                }
            }
        }
    }

    // Now group 3D placements into visual layers for UI & 2D rendering
    if (all_placements.empty()) {
        return {};
    }

    // Sort placements by Z ascending
    std::sort(all_placements.begin(), all_placements.end(), [](const Placement& a, const Placement& b) {
        return a.z < b.z;
    });

    std::vector<Layer> result_layers;

    // Group placements into layers based on Z boundaries
    std::vector<float> z_boundaries;
    for (const auto& pl : all_placements) {
        bool assigned = false;
        for (float zb : z_boundaries) {
            if (std::abs(pl.z - zb) < height_tolerance || (pl.z >= zb && pl.z < zb + height_tolerance)) {
                assigned = true;
                break;
            }
        }
        if (!assigned) {
            z_boundaries.push_back(pl.z);
        }
    }

    std::sort(z_boundaries.begin(), z_boundaries.end());

    for (size_t k = 0; k < z_boundaries.size(); ++k) {
        float zb = z_boundaries[k];
        float next_zb = (k + 1 < z_boundaries.size()) ? z_boundaries[k + 1] : carton_h;

        Layer layer;
        layer.z_start = zb;
        float layer_max_h = 0.0f;

        // Initialize 2D grid matrix
        layer.grid = std::vector<std::vector<int>>(grid_height, std::vector<int>(grid_width, 0));

        for (const auto& pl : all_placements) {
            if (pl.z >= zb - 0.1f && pl.z < next_zb - 0.1f) {
                layer.placements.push_back(pl);
                if (pl.height > layer_max_h) {
                    layer_max_h = pl.height;
                }

                // Stamp onto 2D occupancy grid
                for (int r = pl.gy; r < pl.gy + pl.gl && r < grid_height; ++r) {
                    for (int c = pl.gx; c < pl.gx + pl.gw && c < grid_width; ++c) {
                        if (r >= 0 && c >= 0) {
                            layer.grid[r][c] = pl.id;
                        }
                    }
                }
            }
        }

        if (!layer.placements.empty()) {
            layer.height = layer_max_h;
            result_layers.push_back(layer);
        }
    }

    return result_layers;
}
