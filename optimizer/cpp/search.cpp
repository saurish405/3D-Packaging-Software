#include <vector>
#include <string>
#include <algorithm>
#include <cmath>
#include "types.h"

// External helper functions
extern std::vector<OrientedSize> generate_rotations(const Product& p);
extern bool can_place_on_grid(const std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl);
extern float calculate_support_ratio(const std::vector<std::vector<int>>& lower_grid, int gx, int gy, int gw, int gl);
extern void stamp_on_grid(std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl, int val);
extern void unstamp_on_grid(std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl);
extern float score_layer_layout(const std::vector<Placement>& placements, int grid_width, int grid_height, float cell_size_mm);

struct SearchState {
    std::vector<std::vector<int>> best_grid;
    std::vector<Placement> best_placements;
    float best_score = -1.0f;
    int steps_count = 0;
    int max_steps = 10000;
};

// Internal recursive backtracking solver
void backtrack_2d(
    std::vector<std::vector<int>>& current_grid,
    std::vector<Placement>& current_placements,
    std::vector<Product>& products,
    std::vector<int>& inventory,
    const std::vector<std::vector<int>>& lower_grid,
    float required_support_ratio,
    float cell_size,
    float current_z,
    float layer_base_height,
    float height_tolerance,
    int& unique_id_counter,
    SearchState& state
) {
    state.steps_count++;
    if (state.steps_count > state.max_steps) {
        return; // Search cutoff
    }

    // 1. Evaluate current packing layout and track the best
    float current_score = score_layer_layout(current_placements, current_grid[0].size(), current_grid.size(), cell_size);
    if (current_score > state.best_score) {
        state.best_score = current_score;
        state.best_grid = current_grid;
        state.best_placements = current_placements;
    }

    // 2. Find first empty cell (r, c) on the grid
    int r = -1, c = -1;
    int grid_height = current_grid.size();
    int grid_width = current_grid[0].size();
    for (int i = 0; i < grid_height && r == -1; i++) {
        for (int j = 0; j < grid_width && r == -1; j++) {
            if (current_grid[i][j] == 0) {
                r = i;
                c = j;
            }
        }
    }

    // Base case: grid is completely full
    if (r == -1) {
        return;
    }

    // 3. Try placing each available product from inventory
    bool placed_any = false;
    for (size_t i = 0; i < products.size(); i++) {
        if (inventory[i] <= 0) continue;

        // Generate allowed orientations
        std::vector<OrientedSize> rots = generate_rotations(products[i]);

        for (const auto& rot : rots) {
            // Filter orientations that violate the layer height tolerance
            if (std::abs(rot.height - layer_base_height) > height_tolerance) {
                continue;
            }

            // Convert physical dimensions to grid cells
            int gw = static_cast<int>(std::ceil(rot.length / cell_size));
            int gl = static_cast<int>(std::ceil(rot.width / cell_size));

            // Check grid collision
            if (!can_place_on_grid(current_grid, c, r, gw, gl)) {
                continue;
            }

            // Check support ratio from the layer below (if any)
            if (!lower_grid.empty()) {
                float support = calculate_support_ratio(lower_grid, c, r, gw, gl);
                if (support < required_support_ratio) {
                    continue;
                }
            }

            // Placement is valid! Stamp it and recurse
            placed_any = true;
            int unique_val = unique_id_counter++;
            stamp_on_grid(current_grid, c, r, gw, gl, unique_val);
            inventory[i]--;

            Placement pl;
            pl.id = unique_val;
            pl.sku = products[i].sku;
            pl.name = products[i].name;
            pl.gx = c;
            pl.gy = r;
            pl.gw = gw;
            pl.gl = gl;
            pl.x = c * cell_size;
            pl.y = r * cell_size;
            pl.z = current_z;
            pl.length = rot.length;
            pl.width = rot.width;
            pl.height = rot.height;
            pl.weight = products[i].weight;

            current_placements.push_back(pl);

            backtrack_2d(
                current_grid, current_placements, products, inventory, 
                lower_grid, required_support_ratio, cell_size, current_z, 
                layer_base_height, height_tolerance, unique_id_counter, state
            );

            // Backtrack: restore state
            current_placements.pop_back();
            inventory[i]++;
            unstamp_on_grid(current_grid, c, r, gw, gl);
        }
    }

    // 4. Branch on skipping: if we couldn't place any box at this empty coordinate, 
    // mark it as "wasted" (-1) so we can proceed to pack other locations.
    if (!placed_any) {
        current_grid[r][c] = -1;
        backtrack_2d(
            current_grid, current_placements, products, inventory, 
            lower_grid, required_support_ratio, cell_size, current_z, 
            layer_base_height, height_tolerance, unique_id_counter, state
        );
        current_grid[r][c] = 0; // Restore
    }
}

// Wrapper function to initiate search
Layer solve_layer_packing(
    int grid_width, int grid_height,
    std::vector<Product> products,
    std::vector<int> quantities,
    const std::vector<std::vector<int>>& lower_grid,
    float required_support_ratio,
    float cell_size,
    float current_z,
    float layer_base_height,
    float height_tolerance,
    int max_steps,
    int& unique_id_counter,
    const std::vector<std::vector<int>>& start_grid,
    const std::vector<Placement>& start_placements
) {
    std::vector<std::vector<int>> current_grid = start_grid.empty() ? 
        std::vector<std::vector<int>>(grid_height, std::vector<int>(grid_width, 0)) : start_grid;
    std::vector<Placement> current_placements = start_placements;
    
    SearchState state;
    state.max_steps = max_steps;

    backtrack_2d(
        current_grid, current_placements, products, quantities,
        lower_grid, required_support_ratio, cell_size, current_z,
        layer_base_height, height_tolerance, unique_id_counter, state
    );

    // Clean up skipped markers (-1) from the final grid before returning
    for (int r = 0; r < grid_height; ++r) {
        for (int c = 0; c < grid_width; ++c) {
            if (state.best_grid[r][c] == -1) {
                state.best_grid[r][c] = 0;
            }
        }
    }

    float max_pl_height = 0.0f;
    for (const auto& pl : state.best_placements) {
        if (pl.height > max_pl_height) {
            max_pl_height = pl.height;
        }
    }

    Layer result;
    result.z_start = current_z;
    result.height = max_pl_height;
    result.placements = state.best_placements;
    result.grid = state.best_grid;

    return result;
}
