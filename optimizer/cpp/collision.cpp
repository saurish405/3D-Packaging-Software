#include <vector>
#include "types.h"

// Check if a rectangle of size (gw, gl) can be placed at (gx, gy) on the occupancy grid
bool can_place_on_grid(const std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl) {
    int grid_height = grid.size();
    if (grid_height == 0) return false;
    int grid_width = grid[0].size();

    // Check boundary constraints
    // Note: gx corresponds to columns (width), gy corresponds to rows (length)
    if (gx < 0 || gx + gw > grid_width || gy < 0 || gy + gl > grid_height) {
        return false;
    }

    // Check overlap with other items
    for (int r = gy; r < gy + gl; ++r) {
        for (int c = gx; c < gx + gw; ++c) {
            if (grid[r][c] != 0) {
                return false;
            }
        }
    }
    return true;
}

// Calculate what fraction of the bottom of a box is supported by the layer below
float calculate_support_ratio(const std::vector<std::vector<int>>& lower_grid, int gx, int gy, int gw, int gl) {
    int lower_height = lower_grid.size();
    if (lower_height == 0) return 0.0f;
    int lower_width = lower_grid[0].size();

    int supported_cells = 0;
    int total_cells = gw * gl;

    for (int r = gy; r < gy + gl; ++r) {
        for (int c = gx; c < gx + gw; ++c) {
            // Out of bounds in lower grid means no support
            if (r >= 0 && r < lower_height && c >= 0 && c < lower_width) {
                if (lower_grid[r][c] != 0) {
                    supported_cells++;
                }
            }
        }
    }

    return (float)supported_cells / total_cells;
}
