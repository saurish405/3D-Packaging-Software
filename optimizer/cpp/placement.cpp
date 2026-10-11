#include <vector>

// Stamps a unique integer ID onto the grid cells occupied by a product
void stamp_on_grid(std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl, int val) {
    for (int r = gy; r < gy + gl; ++r) {
        for (int c = gx; c < gx + gw; ++c) {
            grid[r][c] = val;
        }
    }
}

// Unstamps (clears) grid cells occupied by a product (setting them to 0)
void unstamp_on_grid(std::vector<std::vector<int>>& grid, int gx, int gy, int gw, int gl) {
    for (int r = gy; r < gy + gl; ++r) {
        for (int c = gx; c < gx + gw; ++c) {
            grid[r][c] = 0;
        }
    }
}
