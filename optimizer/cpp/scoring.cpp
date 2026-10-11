#include <vector>
#include <cmath>
#include "types.h"

// Evaluates a layer layout's optimization score.
// A higher score indicates a better arrangement.
float score_layer_layout(
    const std::vector<Placement>& placements, 
    int grid_width, int grid_height,
    float cell_size_mm
) {
    if (placements.empty()) return 0.0f;

    float total_area_occupied = 0.0f;
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    float total_weight = 0.0f;

    for (const auto& pl : placements) {
        float area = pl.length * pl.width;
        total_area_occupied += area;

        float cx = pl.x + pl.length / 2.0f;
        float cy = pl.y + pl.width / 2.0f;

        sum_x += pl.weight * cx;
        sum_y += pl.weight * cy;
        total_weight += pl.weight;
    }

    float grid_physical_w = grid_width * cell_size_mm;
    float grid_physical_l = grid_height * cell_size_mm;
    float total_grid_area = grid_physical_w * grid_physical_l;

    // Space utilization ratio (0.0 to 1.0)
    float area_utilization = total_area_occupied / total_grid_area;

    // Center of gravity horizontal alignment score (0.0 to 1.0)
    float cog_alignment = 1.0f;
    if (total_weight > 0.0f) {
        float cog_x = sum_x / total_weight;
        float cog_y = sum_y / total_weight;

        float center_x = grid_physical_w / 2.0f;
        float center_y = grid_physical_l / 2.0f;

        float dist = std::sqrt(std::pow(cog_x - center_x, 2) + std::pow(cog_y - center_y, 2));
        float max_dist = std::sqrt(std::pow(center_x, 2) + std::pow(center_y, 2));

        if (max_dist > 0.0f) {
            cog_alignment = 1.0f - (dist / max_dist);
        }
    }

    // Combined score: heavily prioritize volume utilization, with a secondary CoG balance bonus
    // Score range: 0.0 to ~1.1
    float score = area_utilization + 0.1f * cog_alignment;
    return score;
}
