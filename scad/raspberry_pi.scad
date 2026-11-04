// A Raspberry Pi 4 Model B, approximate: the board, its mounting holes and
// blocks for the connectors that set clearances, from the published
// mechanical drawing (85 x 56, holes 58 x 49 on 3.5 from the corner).
// For laying out frames and checking clashes, not for fitting the connectors.
//
// Board coordinates: x along (0 the SD card end, 85 the USB / Ethernet end),
// y across (0 the power / HDMI edge, 56 the GPIO edge), z up from the board's
// underside.

pi_board = [85, 56, 1.4];
pi_corner_r = 3;
pi_hole_d = 2.7;
pi_holes = [[3.5, 3.5], [61.5, 3.5], [3.5, 52.5], [61.5, 52.5]];

// [x0, x1, y0, y1, z0, z1] in board coordinates; z from the underside
pi_parts = [
    [65.5, 87.1, 37.8, 53.7, 1.4, 14.9],   // Ethernet, 2.1 past the board's end
    [70.0, 87.1, 2.0, 15.0, 1.4, 17.4],    // USB 2 pair
    [70.0, 87.1, 20.5, 33.5, 1.4, 17.4],   // USB 3 pair
    [7.1, 57.9, 50.0, 55.0, 1.4, 9.9],     // GPIO header, 8.5 tall
    [6.7, 15.7, -1.2, 6.3, 1.4, 4.6],      // USB-C power, 1.2 past the edge
    [22.5, 29.5, -1.5, 6.0, 1.4, 4.4],     // micro HDMI 0
    [36.0, 43.0, -1.5, 6.0, 1.4, 4.4],     // micro HDMI 1
    [50.5, 57.5, -2.5, 12.5, 1.4, 7.4],    // audio jack
    [-2.5, 12.5, 20.5, 35.5, -1.5, 0],     // micro SD card under the board, 2.5 past its end
];

module pi_board_shape() difference() {
    hull() for (x = [pi_corner_r, pi_board[0] - pi_corner_r], y = [pi_corner_r, pi_board[1] - pi_corner_r])
        translate([x, y, 0]) cylinder(r = pi_corner_r, h = pi_board[2], $fn = 24);
    for (h = pi_holes) translate([h[0], h[1], -1]) cylinder(d = pi_hole_d, h = pi_board[2] + 2, $fn = 16);
}

module pi_parts() for (p = pi_parts) translate([p[0], p[2], p[4]]) cube([p[1] - p[0], p[3] - p[2], p[5] - p[4]]);

module raspberry_pi4() {
    color("#1f7a3a") pi_board_shape();
    color("#b8bcc2") pi_parts();
}
