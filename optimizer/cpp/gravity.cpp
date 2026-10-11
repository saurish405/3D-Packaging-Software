#include <vector>
#include <cmath>
#include <map>
#include "types.h"

// Calculates the 3D Center of Gravity coordinates of the packed items
bool calculate_cog(const std::vector<Placement>& placements, float& cog_x, float& cog_y, float& cog_z, float& total_weight) {
    total_weight = 0.0f;
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    float sum_z = 0.0f;

    for (const auto& pl : placements) {
        float cx = pl.x + pl.length / 2.0f;
        float cy = pl.y + pl.width / 2.0f;
        float cz = pl.z + pl.height / 2.0f;

        sum_x += pl.weight * cx;
        sum_y += pl.weight * cy;
        sum_z += pl.weight * cz;
        total_weight += pl.weight;
    }

    if (total_weight > 0.0f) {
        cog_x = sum_x / total_weight;
        cog_y = sum_y / total_weight;
        cog_z = sum_z / total_weight;
        return true;
    } else {
        cog_x = 0.0f;
        cog_y = 0.0f;
        cog_z = 0.0f;
        return false;
    }
}

// Normalized center of gravity score: 100 is dead center, 0 is far corners
float get_cog_score(float cog_x, float cog_y, float carton_w, float carton_l) {
    float center_x = carton_w / 2.0f;
    float center_y = carton_l / 2.0f;

    float dist = std::sqrt(std::pow(cog_x - center_x, 2) + std::pow(cog_y - center_y, 2));
    float max_dist = std::sqrt(std::pow(center_x, 2) + std::pow(center_y, 2));

    if (max_dist > 0.0f) {
        return 100.0f * (1.0f - (dist / max_dist));
    }
    return 100.0f;
}

// Physical downward pressure calculation
// Calculates the accumulated weight stacked on top of each placed item
std::map<int, float> calculate_stack_weights(
    const std::vector<Layer>& layers,
    int grid_width, int grid_height
) {
    std::map<int, float> item_stack_weights;
    int num_layers = layers.size();
    if (num_layers == 0) return item_stack_weights;

    // Grid of pressure accumulating weight for the layer above
    // pressure_grids[layer_idx][row][col]
    std::vector<std::vector<std::vector<float>>> pressure_grids(
        num_layers,
        std::vector<std::vector<float>>(grid_height, std::vector<float>(grid_width, 0.0f))
    );

    // Propagate forces downwards from top layer to bottom
    for (int k = num_layers - 1; k >= 0; --k) {
        const auto& layer = layers[k];
        
        // Map placement IDs to placements for lookup
        std::map<int, Placement> pl_map;
        for (const auto& pl : layer.placements) {
            pl_map[pl.id] = pl;
            // Initialize this placement's stack weight
            item_stack_weights[pl.id] = 0.0f;
        }

        // Sum up the pressures resting on each item in layer k
        for (const auto& pl : layer.placements) {
            float item_pressure = 0.0f;
            for (int r = pl.gy; r < pl.gy + pl.gl; ++r) {
                for (int c = pl.gx; c < pl.gx + pl.gw; ++c) {
                    item_pressure += pressure_grids[k][r][c];
                }
            }
            item_stack_weights[pl.id] = item_pressure;

            // Total weight of this item to be supported by the layer below
            float total_item_weight = pl.weight + item_pressure;

            if (k > 0) {
                // Find supporting cells in layer k-1
                const auto& lower_layer = layers[k-1];
                int support_cells = 0;
                for (int r = pl.gy; r < pl.gy + pl.gl; ++r) {
                    for (int c = pl.gx; c < pl.gx + pl.gw; ++c) {
                        if (r >= 0 && r < grid_height && c >= 0 && c < grid_width) {
                            if (lower_layer.grid[r][c] != 0) {
                                support_cells++;
                            }
                        }
                    }
                }

                // Distribute weight onto supporting cells in layer k-1
                if (support_cells > 0) {
                    float force_per_cell = total_item_weight / support_cells;
                    for (int r = pl.gy; r < pl.gy + pl.gl; ++r) {
                        for (int c = pl.gx; c < pl.gx + pl.gw; ++c) {
                            if (r >= 0 && r < grid_height && c >= 0 && c < grid_width) {
                                if (lower_layer.grid[r][c] != 0) {
                                    pressure_grids[k-1][r][c] += force_per_cell;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return item_stack_weights;
}
