// Fit check: the overlap between the case parts and the board envelope.
// Exported and measured by tools/build.sh; its volume must be ~0.
// `use`, not `include`: the main file's own `part` switch must not render.
use <robot_display_case.scad>
intersection() { union() { shell(); lid_lego(); } board_env(); }
