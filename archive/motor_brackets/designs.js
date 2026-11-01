// Motor brackets designed with Part Designer (headless, via pd.js).
//
// Everything is laid out in the motor STL's own frame (motor_envelope_holes.stl), in millimeters on the
// 8 mm Technic grid. A cell is named by its minimum corner and holds one 8x8x8 block with a hole along
// one STL axis. Motor facts used below:
//   body      X[-16,56] Y[-16,8] Z[0,24]   head (rotates) X[32,56] Y[-16,8] Z[24,32]
//   axle      vertical (Z) at X=44 Y=-4, open on the head top and on the bottom face
//   side pin holes (Y axis, both faces)   (X,Z) = (4,20) (36,4) (36,20) (52,4) (52,20)
//   bottom pin holes (Z axis, Z=0 face)   (X,Y) = (36,-4) (52,-4) (44,-12) (44,4)
//   head top pin holes (Z axis, rotating) same X,Y as the bottom ones
const fs = require('fs');
const pd = require('./pd.js');
const { BT } = pd;

// STL axis -> Part Designer orientation. The STL exporter writes internal (x,y,z) as STL (Y,Z,X).
const ORIENT = { X: 'z', Y: 'x', Z: 'y' };
const FWD = { X: [0, 0, 1], Y: [1, 0, 0], Z: [0, 1, 0] };

class Design {
	constructor(name, description) {
		this.name = name;
		this.description = description;
		this.cells = new Map();
	}

	cell(X, Y, Z, axis, type = BT.PinHole) {
		this.cells.set([X, Y, Z].join(), { X, Y, Z, axis, type });
		return this;
	}

	// Fills a box of cells (min corner inclusive, max corner exclusive, in mm) with one hole axis.
	box([x0, y0, z0], [x1, y1, z1], axis, type = BT.PinHole) {
		for (let X = x0; X < x1; X += 8) for (let Y = y0; Y < y1; Y += 8) for (let Z = z0; Z < z1; Z += 8) {
			this.cell(X, Y, Z, axis, type);
		}
		return this;
	}

	blocks() {
		let result = [];
		for (let { X, Y, Z, axis, type } of this.cells.values()) {
			let p = [Y / 4, Z / 4, X / 4];
			let f = FWD[axis];
			// An 8 mm cell is two 4 mm Part Designer blocks stacked along the hole axis.
			result.push([...p, ORIENT[axis], type]);
			result.push([p[0] + f[0], p[1] + f[1], p[2] + f[2], ORIENT[axis], type]);
		}
		return result;
	}

	// Where the exported STL's origin sits in the motor frame (Part Designer normalizes to the min corner).
	origin() {
		let c = [...this.cells.values()];
		return ['X', 'Y', 'Z'].map(a => Math.min(...c.map(v => v[a])));
	}
}

const designs = [];
const add = (d) => (designs.push(d), d);


// 2. L-bracket: side plate plus a 9x2 foot that sticks out sideways at the bottom with vertical holes,
//    so the motor stands upright (axle vertical) on a beam or plate and is pinned down through the foot.
add(new Design('l_bracket', 'Side plate + outward 9x2 foot with vertical holes (motor upright, axle vertical)'))
	.box([-16, -24, 0], [56, -16, 24], 'Y')
	.box([-16, -40, -8], [56, -16, 0], 'Z');

// 3. Cradle: both side plates joined by a floor under the whole motor. Uses all 10 side holes and the
//    4 bottom holes; the hole under the axle is a plain pin hole so the axle passes through and spins.
add(new Design('cradle', 'U-cradle: both side plates + 9x5 floor; 14 pins into the motor, axle passes through the floor'))
	.box([-16, -24, 0], [56, -16, 24], 'Y')
	.box([-16, 8, 0], [56, 16, 24], 'Y')
	.box([-16, -24, -8], [56, 16, 0], 'Z');


// Every bracket below sits flush against the motor (Part Designer's 0.2 mm margins leave 0.4 mm of
// clearance) and wraps at least one edge, so it hugs the motor and offers holes in more than one direction.

// 4. End L: a floor under the head (4 pins into the bottom face, axle passes through) that turns up the
//    end face. Holes point down (Z) and out the end (X).
add(new Design('end_l', 'Floor under the head + wall up the end face; 4 bottom pins, Z and X holes'))
	.box([32, -16, -8], [56, 8, 0], 'Z')
	.box([56, -16, -8], [64, 8, 24], 'X');

// 5. Head cage: wraps the head end on three sides and underneath. 8 side pins + 4 bottom pins, with
//    holes facing Y on both sides, X off the end and Z underneath. The head itself stays free above.
add(new Design('head_cage', 'Wraps both sides, the end and the floor of the head end; 12 pins, holes in X, Y and Z'))
	.box([32, -24, 0], [56, -16, 24], 'Y')
	.box([32, 8, 0], [56, 16, 24], 'Y')
	.box([56, -24, -8], [64, 16, 24], 'X')
	.box([32, -24, -8], [56, 16, 0], 'Z');

// 6. Tail boot: wraps the back end on both sides, the end and the floor. Pins into the body side hole on
//    each face. Pair it with the head cage for a full frame that leaves the middle of the motor open.
add(new Design('tail_boot', 'Wraps sides, back end and floor of the tail; 2 side pins, holes in X, Y and Z'))
	.box([-16, -24, 0], [8, -16, 24], 'Y')
	.box([-16, 8, 0], [8, 16, 24], 'Y')
	.box([-24, -24, -8], [-16, 16, 24], 'X')
	.box([-16, -24, -8], [8, 16, 0], 'Z');

// 7. Top hanger: the full side plate with a lip that wraps over the top edge of the body, so the motor
//    hangs from a beam above it or mounts sideways. The lip stops beside the head so it can still turn.
add(new Design('top_hanger', 'Side plate + lip over the top edge of the body; 5 side pins, Y and Z holes'))
	.box([-16, -24, 0], [56, -16, 24], 'Y')
	.box([-16, -24, 24], [56, -16, 32], 'Z')
	.box([-16, -16, 24], [32, -8, 32], 'Z');

module.exports = { designs, Design };

if (require.main === module) {
	fs.mkdirSync('stl', { recursive: true });
	let manifest = [];
	for (let d of designs) {
		let s = pd.encode(d.blocks());
		fs.writeFileSync(`stl/${d.name}.stl`, pd.toSTL(s));
		manifest.push({ name: d.name, description: d.description, origin: d.origin(), part: s,
			url: 'https://lego3d.jointheleague.org/?part=' + s });
		console.log(d.name.padEnd(18), d.origin().join(','), s.length, 'chars');
	}
	fs.writeFileSync('designs.json', JSON.stringify(manifest, null, 2));
}
