"""ion lamp - look-dev v3 (saturated centre glow, satin plates, front camera) (broad volume glow, underglow strip, edge rims, clean plates) (procedural, no CAD).
Run:  blender -b --factory-startup --python build_ion_look.py -- [--out renders/look_test_v1.png] [--samples 128] [--no-render]
All dimensions in mm (scene unit = 1 mm scaled to metres via S). Placeholder only: shapes/size are guesses, not CAD.
"""
import bpy, bmesh, sys, os, math, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default
OUT = arg("--out", os.path.join(HERE, "renders", "look_test_v3.png"))
SAMPLES = int(arg("--samples", 128))
RES = (1600, 1000)

# ---- parameters (mm) ----
P = dict(
    plate_w=52, plate_h=140, plate_t=4, plate_r=3,     # aluminum plates
    gap=15,                                            # plate-to-plate clear gap (GOAL.md)
    glass_w=38, glass_h=124, glass_t=11, glass_r=5,    # clear glass core
    base_w=62, base_d=74, base_t=6, base_r=7,          # aluminum base
    foot=3.0,                                          # base lift for underglow
    glow_rgb=(1.0, 0.40, 0.07),                        # warm core
)
S = 0.001
def mm(v): return v * S

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
clear()
scene = bpy.context.scene

def rounded_slab(name, w, h, t, r, bevel_segments=6, edge_r=None):
    """Rounded-rect outline (w along Y, h along Z) extruded t along X; small clean edge bevel."""
    o = rounded_base(name, w, h, t, r, edge=edge_r if edge_r else 0.5)
    o.rotation_euler = (math.pi / 2, 0, math.pi / 2); bpy.ops.object.transform_apply(rotation=True)
    return o

def rounded_base(name, w, d, t, r, edge=1.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    pts = []
    for cx, cy, a0 in ((w/2-r, d/2-r, 0), (-w/2+r, d/2-r, 90), (-w/2+r, -d/2+r, 180), (w/2-r, -d/2+r, 270)):
        for i in range(13):
            a = math.radians(a0 + i * 90 / 12)
            pts.append((mm(cx + r * math.cos(a)), mm(cy + r * math.sin(a))))
    bot = [bm.verts.new((x, y, -mm(t) / 2)) for x, y in pts]
    bm.faces.new(bot)
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    vs = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, mm(t)), verts=vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    m = o.modifiers.new("edge", 'BEVEL'); m.width = mm(edge); m.segments = 4; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(60); m.harden_normals = False
    for p in me.polygons: p.use_smooth = True
    return o

# ---- materials ----
def mat_aluminum(name, rough=0.42, streak=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.40, 0.41, 0.43, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Anisotropic"].default_value = 0.45
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (350, 350, 4)  # long streaks along Z
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08 * streak; bump.inputs["Distance"].default_value = 0.002
    rr = n.new("ShaderNodeMath"); rr.operation = 'MULTIPLY_ADD'; rr.inputs[1].default_value = 0.10; rr.inputs[2].default_value = rough - 0.05
    l.new(tc.outputs["Object"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], nz.inputs["Vector"])
    l.new(nz.outputs["Fac"], bump.inputs["Height"]); l.new(bump.outputs["Normal"], b.inputs["Normal"])
    l.new(nz.outputs["Fac"], rr.inputs[0]); l.new(rr.outputs["Value"], b.inputs["Roughness"])
    return m

def mat_glass():
    m = bpy.data.materials.new("ClearGlass"); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    for x in list(n): n.remove(x)
    out = n.new("ShaderNodeOutputMaterial")
    g = n.new("ShaderNodeBsdfGlass"); g.inputs["IOR"].default_value = 1.50; g.inputs["Roughness"].default_value = 0.0
    g.inputs["Color"].default_value = (0.96, 0.99, 0.98, 1)
    tr = n.new("ShaderNodeBsdfTransparent")
    lp = n.new("ShaderNodeLightPath")
    mix = n.new("ShaderNodeMixShader")   # shadow rays pass through so inner lights can wash the plates
    l.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    l.new(g.outputs["BSDF"], mix.inputs[1]); l.new(tr.outputs["BSDF"], mix.inputs[2])
    l.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m

def mat_emissive_core(rgb, strength):
    """Broad diffused warm volume: emission density falls off smoothly from the centre (object space)."""
    m = bpy.data.materials.new("WarmCore"); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    for x in list(n): n.remove(x)
    out = n.new("ShaderNodeOutputMaterial")
    tc = n.new("ShaderNodeTexCoord")
    ln = n.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
    ramp = n.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'EASE'
    e0, e1 = ramp.color_ramp.elements
    e0.position = 0.0; e0.color = (1, 1, 1, 1); e1.position = 1.0; e1.color = (0, 0, 0, 1)
    mid = ramp.color_ramp.elements.new(0.35); mid.color = (0.30, 0.30, 0.30, 1)
    e1.position = 0.78
    mul = n.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength
    em = n.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1)
    sc = n.new("ShaderNodeVolumeScatter"); sc.inputs["Density"].default_value = 0.0; sc.inputs["Color"].default_value = (1, 0.93, 0.85, 1)
    add = n.new("ShaderNodeAddShader")
    l.new(tc.outputs["Object"], ln.inputs[0]); l.new(ln.outputs["Value"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], mul.inputs[0]); l.new(mul.outputs["Value"], em.inputs["Strength"])
    l.new(em.outputs["Emission"], add.inputs[0]); l.new(sc.outputs["Volume"], add.inputs[1])
    l.new(add.outputs["Shader"], out.inputs["Volume"])
    return m

def mat_matte(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m

al = mat_aluminum("BrushedAluminum")
al_base = mat_aluminum("AluminumBase", rough=0.22, streak=0.6)
glass = mat_glass()

# ---- geometry ----
zb = P["foot"]                                     # underside of base
base = rounded_base("Base", P["base_w"], P["base_d"], P["base_t"], P["base_r"])
base.location = (0, 0, mm(zb + P["base_t"] / 2)); base.data.materials.append(al_base)

zt = zb + P["base_t"]                              # top of base
off = (P["gap"] + P["plate_t"]) / 2                # plate centre offset from midplane
for sgn, nm in ((-1, "PlateLeft"), (1, "PlateRight")):
    p = rounded_slab(nm, P["plate_w"], P["plate_h"], P["plate_t"], P["plate_r"], edge_r=0.5)
    p.location = (mm(sgn * off), 0, mm(zt + P["plate_h"] / 2 - 2))   # 2 mm tenon into base (hidden)
    p.data.materials.append(al)

gl = rounded_slab("GlassCore", P["glass_w"], P["glass_h"], P["glass_t"], P["glass_r"], bevel_segments=8, edge_r=1.8)
gl.location = (0, 0, mm(zt + P["glass_h"] / 2 + 0.5)); gl.data.materials.append(glass)

# warm core: soft ellipsoid inside glass, brightest low-mid
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
core = bpy.context.object; core.name = "WarmCore"
core.scale = (mm(P["glass_t"] * 0.42), mm(P["glass_w"] * 0.48), mm(P["glass_h"] * 0.49))
core.location = (0, 0, mm(zt + P["glass_h"] * 0.47)); bpy.ops.object.shade_smooth()
core.data.materials.append(mat_emissive_core(P["glow_rgb"], 650.0))
core.visible_shadow = False

# lights that sell the glow (shadow rays pass through glass)
def add_light(kind, name, loc, energy, rgb, size=None, rot=None, shape='RECTANGLE', size_y=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = rgb
    if kind == 'AREA':
        d.shape = shape; d.size = size; d.size_y = size_y or size
    elif kind == 'POINT':
        d.shadow_soft_size = size
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.location = loc
    if name.startswith('Rim'): o.visible_camera = False
    if name.startswith('CoreGlow'): o.visible_camera = o.visible_glossy = o.visible_transmission = o.visible_diffuse = o.visible_volume_scatter = False
    if rot: o.rotation_euler = [math.radians(a) for a in rot]
    return o
glow = tuple(P["glow_rgb"])
add_light('POINT', "CoreGlowLow", (0, 0, mm(zt + 45)), 0.35, glow, size=mm(8))
add_light('POINT', "CoreGlowMid", (0, 0, mm(zt + 85)), 0.2, glow, size=mm(8))
# underglow: area light under base, pointing down onto desk, sits inside the raised base
add_light('AREA', "Underglow", (0, 0, mm(zb - 1.4)), 6.0, glow, size=mm(P["base_w"] - 6), size_y=mm(P["base_d"] - 6), rot=(180, 0, 0))

ug = rounded_base("UnderglowStrip", P["base_w"] - 8, P["base_d"] - 8, 1.0, P["base_r"] - 3, edge=0.3)
ug.location = (0, 0, mm(P["foot"] - 0.6))
ugm = bpy.data.materials.new("UnderglowMat"); ugm.use_nodes = True
un = ugm.node_tree.nodes; [un.remove(x) for x in list(un)]
ue = un.new("ShaderNodeEmission"); ue.inputs["Color"].default_value = (*P["glow_rgb"], 1); ue.inputs["Strength"].default_value = 8.0
uo = un.new("ShaderNodeOutputMaterial"); ugm.node_tree.links.new(ue.outputs[0], uo.inputs["Surface"])
ug.data.materials.append(ugm)

# ---- backdrop: curved cyclorama, minimal light grey ----
bd = bpy.data.meshes.new("Backdrop"); bm = bmesh.new()
W, Lf, Lb, Hh, R = 3.0, 1.5, 0.9, 1.4, 0.35
prof = [(-Lf, 0.0), (Lb - R, 0.0)] + [(Lb - R + R * math.sin(a), R - R * math.cos(a)) for a in [i * (math.pi / 2) / 16 for i in range(1, 17)]] + [(Lb, R + Hh)]
rows = []
for (y, z) in prof:
    rows.append([bm.verts.new((-W / 2, y, z)), bm.verts.new((W / 2, y, z))])
for a, b in zip(rows[:-1], rows[1:]):
    bm.faces.new((a[0], a[1], b[1], b[0]))
bm.to_mesh(bd); bm.free()
bdo = bpy.data.objects.new("Backdrop", bd); scene.collection.objects.link(bdo)
for p in bd.polygons: p.use_smooth = True
bdo.data.materials.append(mat_matte("BackdropMat", (0.78, 0.78, 0.79), 0.95))

# ---- lighting: soft studio ----
add_light('AREA', "KeyBox", (-0.30, -0.40, 0.55), 6.0, (1.0, 0.98, 0.96), size=0.9, size_y=0.9, rot=(58, 0, -38))
add_light('AREA', "FillBox", (0.55, -0.30, 0.22), 3.0, (0.92, 0.96, 1.0), size=0.5, size_y=0.5, rot=(70, 0, 62))
add_light('AREA', "RimStrip", (0.32, 0.30, 0.30), 9.0, (1.0, 1.0, 1.0), size=0.05, size_y=0.6, rot=(-120, 0, 15))
add_light('AREA', "RimStripL", (-0.32, 0.30, 0.30), 9.0, (1.0, 1.0, 1.0), size=0.05, size_y=0.6, rot=(-120, 0, -15))
add_light('AREA', "TopSoft", (0, 0.1, 0.9), 5.0, (1.0, 1.0, 1.0), size=1.6, size_y=1.6)
for o in scene.objects:
    if o.type == 'LIGHT' and o.name in ("KeyBox", "FillBox", "RimStrip", "RimStripL", "TopSoft"):
        t = o.constraints.new('TRACK_TO'); t.target = base; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'

world = bpy.data.worlds.new("World"); world.use_nodes = True; scene.world = world
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.78, 0.79, 0.81, 1); bg.inputs["Strength"].default_value = 0.28

# ---- camera ----
cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 85; cam_d.sensor_width = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 16
cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam)
cam.location = (-0.13, -0.66, 0.30)
tgt = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(tgt); tgt.location = (0, 0, mm(78))
t = cam.constraints.new('TRACK_TO'); t.target = tgt; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
cam_d.dof.focus_object = tgt
scene.camera = cam

# ---- render settings ----
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'; cy.samples = SAMPLES; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 12; cy.glossy_bounces = 6; cy.transmission_bounces = 12; cy.transparent_max_bounces = 16; cy.volume_bounces = 1; cy.volume_step_rate = 0.5
cy.sample_clamp_indirect = 10; cy.caustics_reflective = False; cy.caustics_refractive = False
scene.render.threads_mode = 'AUTO'
scene.render.resolution_x, scene.render.resolution_y = RES; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] else 'None'
scene.view_settings.exposure = 0.0

blend_path = os.path.join(HERE, "ion_look_v3.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("saved", blend_path)

if "--no-render" not in argv:
    scene.render.filepath = OUT
    t0 = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDER_SECONDS %.1f -> %s" % (time.time() - t0, OUT))
