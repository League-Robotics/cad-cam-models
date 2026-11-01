// Headless driver for Part Designer: loads the compiled app.js into a sandbox and exports STLs.
// Usage: node pd.js <out.stl> <partString>      or require('./pd.js')
const fs = require('fs'), vm = require('vm'), path = require('path');
const PD = process.env.PARTDESIGNER || '/Users/eric/proj/league-projects/infrastructure/partdesigner';
const fakeEl = () => new Proxy(function () {}, { get: (t, k) => k === Symbol.toPrimitive ? () => '' : (k in t ? t[k] : fakeEl()), set: () => true, apply: () => fakeEl() });
const ctx = { window: {}, document: { getElementById: () => fakeEl(), querySelector: () => fakeEl(), createElement: () => fakeEl() }, console, Math, Blob: class {}, URL };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(PD, 'app.js'), 'utf8'), ctx);
vm.runInContext(`
  this.toSTL = (s) => Buffer.from(STLExporter.createBuffer(Part.fromString(s), new Measurements()));
  this.encode = (blocks) => { // blocks: [[x,y,z,'x'|'y'|'z',type,rounded]]
    const p = new Part();
    for (const [x,y,z,o,t,r] of blocks) p.blocks.set(new Vector3(x,y,z), new Block(ORIENTATION[o], t, r !== false));
    return p.toString();
  };
  this.BT = BlockType;`, Object.assign(ctx, { Buffer }));
module.exports = ctx;
if (require.main === module) fs.writeFileSync(process.argv[2], ctx.toSTL(process.argv[3]));
