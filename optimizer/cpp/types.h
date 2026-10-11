#ifndef TYPES_H
#define TYPES_H

#include <string>
#include <vector>

struct OrientedSize {
    float length;       // along X
    float width;        // along Y
    float height;       // along Z

    bool operator<(const OrientedSize& other) const {
        if (length != other.length) return length < other.length;
        if (width != other.width) return width < other.width;
        return height < other.height;
    }
};

struct Product {
    int id;
    std::string sku;
    std::string name;
    float length;       // X-axis dimension (mm)
    float width;        // Y-axis dimension (mm)
    float height;       // Z-axis dimension (mm)
    float weight;       // kg
    bool fragile;
    bool stackable;
    float max_stack_weight;
    std::string allowed_rotations; // "XYZ", "XY", "Z"
};

struct PackedItem {
    int id;
    std::string sku;
    std::string name;
    float x;            // physical coordinate (mm)
    float y;            // physical coordinate (mm)
    float z;            // physical coordinate (mm)
    float length;       // oriented length (mm)
    float width;        // oriented width (mm)
    float height;       // oriented height (mm)
    float weight;       // kg
};

struct Placement {
    int id;
    std::string sku;
    std::string name;
    int gx, gy;         // 2D grid coordinates (column, row)
    int gw, gl;         // 2D grid dimensions (width cells, length cells)
    float x, y, z;      // physical coordinate (mm)
    float length, width, height; // physical dimensions when oriented (mm)
    float weight;       // kg
};

struct Layer {
    float z_start;
    float height;
    std::vector<Placement> placements;
    std::vector<std::vector<int>> grid; // occupancy matrix
};

#endif
