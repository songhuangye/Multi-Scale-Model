from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import regionToolset
import mesh
from material import createMaterialFromDataString

# ============================================ #
# use index to represent objects
# session.journalOptions.setValues(replayGeometry=INDEX,recoverGeometry=INDEX)

# use feature coordinate to represent objects
# session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
# ============================================ #

# import models for python, os for open directory and read .txt, numpy for array manipulate
# '''
import os
import numpy as np
import sys
import shutil



def read_map(path, csv_name):
    file = open(path + '\\' + csv_name, 'r')
    f = file.readlines()
    file.close()
    f = np.array(f)
    keys = f[0].split(';')[:-1]
    map = []
    para = []
    for i in f[1:]:
        if '#' not in i:
            # print(i)
            a = {}
            values = i.split(';')
            # print(values[0])
            a[keys[0]] = int(values[0])
            a[keys[1]] = int(values[1])
            c = values[2][1:-1].split(',')
            a[keys[2]] = [float(c[0]), float(c[1]), float(c[2])]
            lo = values[3][1:-1].split(',')
            a[keys[3]] = [int(lo[0]), int(lo[1]), int(lo[2])]
            a[keys[4]] = int(values[4])
            map.append(a)
        else:
            break
    map = np.array(map)
    for i in f:
        if i[0] == '#':
            a = {}
            key = i.split('=')[0].split()[-1]
            value = i.split('=')[-1].split()
            for v in range(len(value)):
                value[v] = float(value[v])
            a[key] = value
            para.append(a)
    return map, para


def create_small_cub(model_name, part_name, coordinate, element_size_in_xy, element_size_in_z):
    x = coordinate[0]
    y = coordinate[1]
    element_size_in_xy = element_size_in_xy+1e-5
    s1 = mdb.models[str(model_name)].ConstrainedSketch(name='__profile__', sheetSize=element_size_in_xy*100)
    g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
    s1.setPrimaryObject(option=STANDALONE)
    s1.rectangle(point1=(x - element_size_in_xy/2, y - element_size_in_xy/2),
                 point2=(x + element_size_in_xy/2, y + element_size_in_xy/2))
    p = mdb.models[str(model_name)].Part(name=str(part_name), dimensionality=THREE_D,
                                type=DEFORMABLE_BODY)
    p = mdb.models[str(model_name)].parts[str(part_name)]
    p.BaseSolidExtrude(sketch=s1, depth=element_size_in_z-1e-5)
    s1.unsetPrimaryObject()
    p = mdb.models[str(model_name)].parts[str(part_name)]
    # session.viewports['Viewport: 1'].setValues(displayedObject=p)
    del mdb.models[str(model_name)].sketches['__profile__']


def merge_cub(model_name, part_name_list, new_part_name):
    a = mdb.models[model_name].rootAssembly
    for i in range(0, len(part_name_list)):
        a = mdb.models[model_name].rootAssembly
        p = mdb.models[model_name].parts[part_name_list[i]]
        a.Instance(name=part_name_list[i] + '-1', part=p, dependent=ON)
    instance = tuple([a.instances['%s-1' % n] for n in part_name_list])
    a = mdb.models[model_name].rootAssembly
    a.InstanceFromBooleanMerge(name=new_part_name + '-1', instances=instance, originalInstances=DELETE, domain=GEOMETRY)
    for i in range(0, len(part_name_list)):
        del mdb.models[model_name].parts[part_name_list[i]]


def translate_instance(model_name, instance_name, aim_coor):
    a = mdb.models[model_name].rootAssembly
    a.translate(instanceList=(instance_name,), vector=(aim_coor[0], aim_coor[1], aim_coor[2]))


def create_and_cut_powder(model_name, powder_name, cutting_name, domain_size, element_size_in_z):
    width = domain_size[0]
    length = domain_size[1]
    s1 = mdb.models[str(model_name)].ConstrainedSketch(name='__profile__', sheetSize=width * 5)
    g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
    s1.setPrimaryObject(option=STANDALONE)
    s1.rectangle(point1=(width / 2, length / 2),
                 point2=(-width / 2, -length / 2))
    p = mdb.models[str(model_name)].Part(name=str(powder_name), dimensionality=THREE_D,
                                         type=DEFORMABLE_BODY)
    p = mdb.models[str(model_name)].parts[str(powder_name)]
    p.BaseSolidExtrude(sketch=s1, depth=element_size_in_z)
    s1.unsetPrimaryObject()
    p = mdb.models[str(model_name)].parts[str(powder_name)]
    # session.viewports['Viewport: 1'].setValues(displayedObject=p)
    del mdb.models[str(model_name)].sketches['__profile__']
    a = mdb.models[model_name].rootAssembly
    instance_name = powder_name + '-1'
    p = mdb.models[model_name].parts[powder_name]
    a.Instance(name=instance_name, part=p, dependent=ON)
    a = mdb.models[model_name].rootAssembly
    a.InstanceFromBooleanCut(name=instance_name, instanceToBeCut=mdb.models[model_name].rootAssembly.instances[instance_name], cuttingInstances=(a.instances[cutting_name + '-1-1'],), originalInstances=DELETE)
    del mdb.models[model_name].parts[powder_name]
    a = mdb.models[model_name].rootAssembly
    for i in a.instances.keys():
        del a.features[i]


def create_powder(model_name, powder_name, domain_size, element_size_in_z):
    width = domain_size[0]
    length = domain_size[1]
    s1 = mdb.models[str(model_name)].ConstrainedSketch(name='__profile__', sheetSize=width * 5)
    g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
    s1.setPrimaryObject(option=STANDALONE)
    s1.rectangle(point1=(width / 2, length / 2),
                 point2=(-width / 2, -length / 2))
    p = mdb.models[str(model_name)].Part(name=str(powder_name), dimensionality=THREE_D,
                                         type=DEFORMABLE_BODY)
    p = mdb.models[str(model_name)].parts[str(powder_name)]
    p.BaseSolidExtrude(sketch=s1, depth=element_size_in_z)
    s1.unsetPrimaryObject()
    p = mdb.models[str(model_name)].parts[str(powder_name)]
    # session.viewports['Viewport: 1'].setValues(displayedObject=p)
    del mdb.models[str(model_name)].sketches['__profile__']
    a = mdb.models[model_name].rootAssembly
    instance_name = powder_name + '-1'
    p = mdb.models[model_name].parts[powder_name]
    a.Instance(name=instance_name, part=p, dependent=ON)
    a = mdb.models[model_name].rootAssembly
    for i in a.instances.keys():
        del a.features[i]


def create_powder_1(model_name, powder_name, domain_size, size_in, depth):
    width = domain_size[0]
    length = domain_size[1]
    x_min = size_in[0]
    x_max = size_in[1]
    y_min = size_in[2]
    y_max = size_in[3]
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__',
                                                 sheetSize=length * 10)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(width / 2, length / 2), point2=(-width / 2, -length / 2))
    s.rectangle(point1=(x_min, y_min), point2=(x_max, y_max))
    p = mdb.models[model_name].Part(name=powder_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[powder_name]
    p.BaseSolidExtrude(sketch=s, depth=depth)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']


def get_heat_flux(lump, power, abs, scan_area, speed, hatch_dis):
    heat_f = lump * power * abs * scan_area / (speed * hatch_dis)
    return heat_f


def get_step_time(scan_area, speed, hatch_dis, lump, pause_per_l):
    scan_time = scan_area / (speed * hatch_dis) * lump
    pause_time = lump * pause_per_l
    step_time = scan_time + pause_time
    return [step_time, scan_time, pause_time]


def create_solid(a, b, depth, name):
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__',
                                                 sheetSize=a * 5)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(a / 2, b / 2), point2=(-a / 2, -b / 2))
    p = mdb.models[model_name].Part(name=name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[name]
    p.BaseSolidExtrude(sketch=s, depth=depth)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']


def create_solid_1(x_min, x_max, y_min, y_max, depth, name):
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__',
                                                 sheetSize=
                                                 (x_max + y_max) * 5)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(x_min, y_min), point2=(x_max, y_max))
    p = mdb.models[model_name].Part(name=name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[name]
    p.BaseSolidExtrude(sketch=s, depth=depth)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']

"""
def create_powder(width_out, length_out, width_in, length_in, depth, name):
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__',
                                                 sheetSize=width_out * 5)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(width_out / 2, length_out / 2), point2=(-width_out / 2, -length_out / 2))
    s.rectangle(point1=(width_in / 2, length_in / 2), point2=(-width_in / 2, -length_in / 2))
    p = mdb.models[model_name].Part(name=name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[name]
    p.BaseSolidExtrude(sketch=s, depth=depth)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']


def translate_instance(model_name, instance_name, aim_coor):
    a = mdb.models[model_name].rootAssembly
    a.translate(instanceList=(instance_name,), vector=(aim_coor[0], aim_coor[1], aim_coor[2]))
"""


work_dir = r'X:\1_Simulation\ABAQUS_SIM\11_TCR-Model\ABA\Lumped-layer-Model\Extern-Model\Temsile_model'
os.chdir(work_dir)
map_path = work_dir + r'\Extern-Model'
map_name = r'CFFFP_Tensile.csv'
model_name = 'Tensile_0point3layer-Rec'
# mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)

domain_map, paras = read_map(map_path, map_name)
"""
what's in paras
[{'X_min': [-5.925]}, 
{'X_max': [5.925]}, 
{'Y_min': [-19.925]}, 
{'Y_max': [19.925]}, 
{'Z_min': [0.1]}, 
{'Z_max': [11.2]}, 
{'Domain_shape': [38.0, 31.0, 101.0]}, 
{'E_size_xy': [0.4]}
{'Z_list': [0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9,......, 9.4, 9.7, 10.0, 10.3, 10.6, 10.9, 11.2]}]
"""
x_min = paras[0]['X_min'][0]
x_max = paras[1]['X_max'][0]
y_min = paras[2]['Y_min'][0]
y_max = paras[3]['Y_max'][0]
z_min = paras[4]['Z_min'][0]
z_max = paras[5]['Z_max'][0]
domain_shape = paras[6]['Domain_shape']
for d in range(len(domain_shape)):
    domain_shape[d] = int(domain_shape[d])

e_size_xy = paras[7]['E_size_xy'][0]
z_list = paras[8]['Z_list']

domain_width = x_max - x_min +4  # mm
domain_length = y_max - y_min +4 # mm
domain_height = z_max  # mm
element_size_in_xy = e_size_xy  # mm
element_size_in_z = 0.15
melt_pool_width = 0.2  # mm
layer_amount = domain_shape[0]


# change it !!!
layers = domain_shape[0]
# layers = 3

pre_Temp = 200
PS_Conductance = 10000

# domain_map = read_map(map_path, map_name)
domain_map = domain_map.reshape(domain_shape)

sub_or_not = True
# Width and length of substrate = max/min of x and y
sub_depth = 2
sub_mesh_size = 0.5

film_coef = 0.015

beam_power = 1.6E5
scanning_speed = 900
hatch = 0.05
absorp= 0.6

lumped_num = 5

# heat_flux = lumped_num * beam_power * absorp * ((scan_width / hatch) * scan_length) / scanning_speed
pause_per_layer = 1
# scan_time = ((scan_width / hatch) * scan_length) / scanning_speed
# heat_step_time = (pause_time + scan_time) * lumped_num


# heat_step_time = 15
# initInc = heat_step_time / 50
# maxInc = heat_step_time / 20
minInc = 1e-12


# Create Model
mdb.Model(name=model_name, absoluteZero=-273, modelType=STANDARD_EXPLICIT)
from material import createMaterialFromDataString
createMaterialFromDataString(model_name, 'SS316L-Powder', '2020',
    """{'description': '', 'density': {'temperatureDependency': ON, 'table': ((4.1593e-09, 100.0), (4.1379e-09, 200.0), (4.1165e-09, 300.0), (4.0952e-09, 400.0), (4.0738e-09, 500.0)), 'dependencies': 0, 'fieldName': '', 'distributionType': UNIFORM}, 'specificHeat': {'temperatureDependency': ON, 'table': ((438300000.0, 100.0), (484800000.0, 200.0), (527600000.0, 300.0), (559000000.0, 400.0), (640800000.0, 500.0)), 'dependencies': 0, 'law': CONSTANTVOLUME}, 'materialIdentifier': '', 'conductivity': {'temperatureDependency': ON, 'table': ((0.174827732, 100.0), (0.21244111, 200.0), (0.184825746, 300.0), (0.209005494, 400.0), (0.23311685, 500.0)), 'dependencies': 0, 'type': ISOTROPIC}, 'name': 'SS316L-Powder'}""")
#: Material 'SS316L-Powder' has been copied to the current model.
from material import createMaterialFromDataString
createMaterialFromDataString(model_name, 'SS316L-Solid-AsBuilt', '2020',
    """{'description': '', 'density': {'temperatureDependency': ON, 'table': ((7.5549e-09, 100.0), (7.5128e-09, 200.0), (7.4708e-09, 300.0), (7.4287e-09, 400.0), (7.3866e-09, 500.0)), 'dependencies': 0, 'fieldName': '', 'distributionType': UNIFORM}, 'specificHeat': {'temperatureDependency': ON, 'table': ((452000000.0, 100.0), (517000000.0, 200.0), (557000000.0, 300.0), (593000000.0, 400.0), (615500000.0, 500.0)), 'dependencies': 0, 'law': CONSTANTVOLUME}, 'materialIdentifier': '', 'conductivity': {'temperatureDependency': ON, 'table': ((12.17722958, 100.0), (14.29355277, 200.0), (16.07069189, 300.0), (17.10106055, 400.0), (17.46746974, 500.0)), 'dependencies': 0, 'type': ISOTROPIC}, 'name': 'SS316L-Solid-AsBuilt'}""")
#: Material 'SS316L-Solid-AsBuilt' has been copied to the current model.
mdb.models[model_name].setValues(absoluteZero=-273)

# Create Substrate

create_solid(domain_width, domain_length, sub_depth, 'Part-Sub')
step_length = []
heat_in_layer = []

for l in range(layers):  # np.shape(domain_map)[0]):
    part_name_in_layer_list = []
    part_name_cut_in_layer_list = []
    part_new_name = 'Part-L' + str(l) + '-S'
    part_new_name_cut = 'S-L' + str(l) + '_Cut'
    powder_new_name = 'Part-L' + str(l) + '-P'
    e_in_layer_list = domain_map[l]
    e_in_layer_list = e_in_layer_list.reshape(-1)
    z_co = e_in_layer_list[0]['Coordinate'][-1]
    if l == 0:
        h = z_list[l]
    else:
        h = abs(z_list[l] - z_list[l - 1])
    counter = 0
    e_x, e_y = [], []
    for e in e_in_layer_list:
        if e['State'] == 1:
            counter += 1
            # e_part_name = 'P-' + str(e['Ele_Number'])
            # e_part_name_cut = 'P-' + str(e['Ele_Number']) + '_Cut'
            # part_name_in_layer_list.append(e_part_name)
            # part_name_cut_in_layer_list.append(e_part_name_cut)
            e_coordinate = e['Coordinate']
            e_x.append(e_coordinate[0])
            e_y.append(e_coordinate[1])
            # create_small_cub(model_name, e_part_name, e_coordinate, element_size_in_xy, h)
            # create_small_cub(model_name, e_part_name_cut, e_coordinate, element_size_in_xy, h + 0.1)
        else:
            continue
    create_solid_1(x_min=min(e_x), x_max=max(e_x), y_min=min(e_y), y_max=max(e_y), name=part_new_name, depth=h)
    area_in_layer = counter * element_size_in_xy * element_size_in_xy
    step_length.append(get_step_time(area_in_layer, scanning_speed, hatch, lumped_num, pause_per_layer))
    # heat_in_layer.append(get_heat_flux(lumped_num, beam_power, absorp, area_in_layer, scanning_speed, hatch))
    heat_in_layer.append(96000.0)
    if len(part_name_in_layer_list) >= 2:
        merge_cub(model_name, part_name_in_layer_list, part_new_name)
        merge_cub(model_name, part_name_cut_in_layer_list, part_new_name_cut)
        create_and_cut_powder(model_name, powder_new_name, part_new_name_cut, [domain_width, domain_length], h)
    else:
        # create_powder(model_name, powder_new_name, [domain_width, domain_length], h)
        size_in_powder = [min(e_x), max(e_x), min(e_y), max(e_y)]
        create_powder_1(model_name, powder_name=powder_new_name, domain_size=[domain_width, domain_length], size_in=size_in_powder, depth=h)
    print('# Part - Layer ', l, ' Created.\n\n')
    if l % 10 == 1:
        mdb.save()

p_keys = mdb.models[model_name].parts.keys()
for p_k in p_keys:
    if 'Cut' in p_k:
        del mdb.models[model_name].parts[p_k]
    else:
        if 'Sub' not in p_k:
            new_p_key = p_k.split('-')[0] + '-' + p_k.split('-')[1] + '-' + p_k.split('-')[2]
            mdb.models[model_name].parts.changeKey(fromName=p_k, toName=new_p_key)

# Create sections
mdb.models[model_name].HomogeneousSolidSection(name='Section-S', material='SS316L-Solid-AsBuilt', thickness=None)
mdb.models[model_name].HomogeneousSolidSection(name='Section-P', material='SS316L-Powder', thickness=None)
# Assign sections to part
p_keys = mdb.models[model_name].parts.keys()
for p in p_keys:
    part = mdb.models[model_name].parts[p]
    c = part.cells
    cells = c
    region = regionToolset.Region(cells=cells)
    part = mdb.models[model_name].parts[p]
    if p[-1] == 'P':
        part.SectionAssignment(region=region, sectionName='Section-P', offset=0.0,
                            offsetType=MIDDLE_SURFACE, offsetField='',
                            thicknessAssignment=FROM_SECTION)
    elif p[-1] == 'S':
        part.SectionAssignment(region=region, sectionName='Section-S', offset=0.0,
                            offsetType=MIDDLE_SURFACE, offsetField='',
                            thicknessAssignment=FROM_SECTION)
    elif 'Sub' in p:
        part.SectionAssignment(region=region, sectionName='Section-S', offset=0.0,
                               offsetType=MIDDLE_SURFACE, offsetField='',
                               thicknessAssignment=FROM_SECTION)

# Assembly

p_keys = mdb.models[model_name].parts.keys()
a = mdb.models[model_name].rootAssembly
for p_k in p_keys:
    p = mdb.models[model_name].parts[p_k]
    a.Instance(name=p_k, part=p, dependent=ON)
# Translate sub to -sub_depth
# a.translate(instanceList=('Part-Sub', ), vector=(0.0, 0.0, -sub_depth))

a = mdb.models[model_name].rootAssembly
inst_list = a.instances.keys()
for inst in inst_list:
    if 'Sub' in inst:
        translate_instance(model_name, inst, [0.0, 0.0, -sub_depth])
    else:
        if 'Cut' not in inst:
            layer = int(inst.split('-')[1][1:])
            if layer == 0:
                continue
            else:
                translate_instance(model_name, inst, [0.0, 0.0, z_list[layer-1]])
                print('Instance ', inst, ' translated.\n\n')


a = mdb.models[model_name].rootAssembly
c_keys = a.instances.keys()
cells_P = []
cells_S = []
cells_Sub = []
for c_name in c_keys:
    if 'Sub' in c_name:
        c1 = a.instances[c_name].cells
        cells_Sub.append(c1)
    else:
        if c_name[-1] == 'S':
            c1 = a.instances[c_name].cells
            cells_S.append(c1)
        elif c_name[-1] == 'P':
            c1 = a.instances[c_name].cells
            cells_P.append(c1)

a.Set(cells=cells_S, name='Set-S')
a.Set(cells=cells_P, name='Set-P')
a.Set(cells=cells_Sub, name='Set-Sub')

for c_nr in range(layers):
    c_list = []
    for c_name in c_keys:
        if c_name.split('-')[1][1:] == str(c_nr):  # c_name.split('L')[-1] == str(c_nr):
            c1 = a.instances[c_name].cells
            c_list.append(c1)
    if len(c_list) > 0:
        a.Set(cells=c_list, name='Set-L' + str(c_nr))


# Define all useful faces
a = mdb.models[model_name].rootAssembly
c_keys = a.instances.keys()
for c_name in c_keys:
    c1 = a.instances[c_name]
    f1 = c1.faces
    x_list, y_list, z_list = [], [], []
    for f in f1:
        f_co = f.pointOn[0]
        x_list.append(f_co[0])
        y_list.append(f_co[1])
        z_list.append(f_co[2])
    P_face_in, S_face_out, S_face_top, S_face_bottom = [], [], [], []
    for f in f1:
        f_co = f.pointOn[0]
        if f_co[-1] == max(z_list):
            S_face_top.append(f1[f.index: f.index+1])
            # a = mdb.models[model_name].rootAssembly
            # s1 = c1.faces
            # side1Faces1 = s1.findAt((f_co,))
            # a.Surface(side1Faces=side1Faces1, name=c_name + '-TopFace')
        elif f_co[-1] == min(z_list):
            S_face_bottom.append(f1[f.index: f.index+1])
            # a = mdb.models[model_name].rootAssembly
            # s1 = c1.faces
            # side1Faces1 = s1.findAt((f_co,))
            # a.Surface(side1Faces=side1Faces1, name=c_name + '-BottomFace')
        else:
            if c_name[-1] == 'P':
                if f_co[0] != max(x_list) and f_co[0] != min(x_list) and \
                   f_co[1] != max(y_list) and f_co[1] != min(x_list):
                    P_face_in.append(f1[f.index: f.index+1])
            elif c_name[-1] == 'S':
                S_face_out.append(f1[f.index: f.index+1])
    if len(P_face_in) != 0:
        a.Surface(side1Faces=P_face_in, name=c_name + '-face-in')
    if len(S_face_out) != 0:
        a.Surface(side1Faces=S_face_out, name=c_name + '-face-out')
    if len(S_face_top) != 0:
        a.Surface(side1Faces=S_face_top, name=c_name + '-TopFace')
    if len(S_face_bottom) != 0:
        a.Surface(side1Faces=S_face_bottom, name=c_name + '-BottomFace')
    print('Faces for instance ', c_name, ' created.\n\n')

# Create Amplitude
amp_name_list = []
for s in range(len(step_length)):
    amp_name = 'Amp-Heat-L' + str(s)
    amp_name_list.append(amp_name)
    mdb.models[model_name].TabularAmplitude(name=amp_name,
        timeSpan=STEP, smooth=SOLVER_DEFAULT, data=((0.0, 1.0), (step_length[s][1], 1.0),
        (step_length[s][1] + 1e-5, 0.0), (step_length[s][0], 0.0)))
mdb.save()

# Set steps
# Step-killAll. Kill all Sets in layers
mdb.models[model_name].HeatTransferStep(name='Step-killAll', previous='Initial',
    timePeriod=1e-10, maxNumInc=100000, initialInc=1e-10, minInc=1e-15,
    maxInc=1e-10, deltmx=2000.0)
a = mdb.models[model_name].rootAssembly
i_keys = a.instances.keys()
for i in i_keys:
    if 'Sub' not in i:
        c1 = a.instances[i].cells
        cells1 = c1  # [0:1]
        region = regionToolset.Region(cells=cells1)
        mdb.models[model_name].ModelChange(name='DeAct-Inst_' + i, createStepName='Step-killAll',
                                       region=region, activeInStep=False, includeStrain=False)

mdb.models[model_name].HeatTransferStep(name='Step-Act-L0', previous='Step-killAll',
                                        timePeriod=step_length[0][0], maxNumInc=100000, initialInc=step_length[0][0]/50, minInc=minInc,
                                        maxInc=step_length[0][0]/30, deltmx=10000.0)
mdb.models[model_name].steps['Step-Act-L0'].control.setValues(allowPropagation=OFF, resetDefaultValues=OFF,
                                                                 timeIncrementation=(
                                                                     4.0, 8.0, 9.0, 16.0, 10.0, 4.0, 12.0,
                                                                     20.0, 6.0, 3.0, 50.0))
a = mdb.models[model_name].rootAssembly
inst_name = 'Part-L0-P'
c1 = a.instances[inst_name].cells
cells1 = c1  # [0:1]
region = regionToolset.Region(cells=cells1)
mdb.models[model_name].ModelChange(name='Act-Inst_' + inst_name, createStepName='Step-Act-L0',
                                   region=region, activeInStep=True, includeStrain=False)
a = mdb.models[model_name].rootAssembly
inst_name = 'Part-L0-S'
c1 = a.instances[inst_name].cells
cells1 = c1  # [0:1]
region = regionToolset.Region(cells=cells1)
mdb.models[model_name].ModelChange(name='Act-Inst_' + inst_name, createStepName='Step-Act-L0',
                                   region=region, activeInStep=True, includeStrain=False)
mdb.models[model_name].BodyHeatFlux(name='Load-' + inst_name, createStepName='Step-Act-L0',
                                    region=region, magnitude=heat_in_layer[0], amplitude=amp_name_list[0])
# mdb.models[model_name].loads['Load-' + inst_name].deactivate('Step-Act-L1')
for l in range(1, layers):
    # create new step
    mdb.models[model_name].HeatTransferStep(name='Step-Act-L' + str(l), previous='Step-Act-L' + str(l-1),
                                            timePeriod=step_length[l][0], maxNumInc=100000, initialInc=step_length[l][0]/200, minInc=minInc,
                                            maxInc=step_length[l][0]/50, deltmx=10000.0)
    mdb.models[model_name].steps['Step-Act-L' + str(l)].control.setValues(allowPropagation=OFF, resetDefaultValues=OFF,
                                                                  timeIncrementation=(
                                                                      4.0, 8.0, 9.0, 16.0, 10.0, 4.0, 12.0,
                                                                      20.0, 6.0, 3.0, 50.0))
    inst_name = 'Part-L' + str(l) + '-P'
    c1 = a.instances[inst_name].cells
    cells1 = c1  # [0:1]
    region = regionToolset.Region(cells=cells1)
    mdb.models[model_name].ModelChange(name='Act-Inst_' + inst_name, createStepName='Step-Act-L' + str(l),
                                       region=region, activeInStep=True, includeStrain=False)
    inst_name = 'Part-L' + str(l) + '-S'
    if inst_name in a.instances.keys():
        c1 = a.instances[inst_name].cells
        cells1 = c1  # [0:1]
        region = regionToolset.Region(cells=cells1)
        mdb.models[model_name].ModelChange(name='Act-Inst_' + inst_name, createStepName='Step-Act-L' + str(l),
                                           region=region, activeInStep=True, includeStrain=False)
        mdb.models[model_name].BodyHeatFlux(name='Load-' + inst_name, createStepName='Step-Act-L' + str(l),
                                            region=region, magnitude=heat_in_layer[l], amplitude=amp_name_list[l])
        # mdb.models[model_name].loads['Load-' + inst_name].deactivate('Step-Act-L' + str(l - 1))
    # if 'Step-Act-L' + str(l+1) in mdb.models[model_name].steps.keys():
    #     mdb.models[model_name].loads['Load-' + inst_name].deactivate('Step-Act-L' + str(l+1))
    # else:
    #     continue


for l in range(1, layers):
    if 'Load-Part-L' + str(l-1) + '-S' in mdb.models[model_name].loads.keys():
        mdb.models[model_name].loads['Load-Part-L' + str(l - 1) + '-S'].deactivate('Step-Act-L' + str(l))
mdb.save()

# Set initial temperature
a = mdb.models[model_name].rootAssembly
region = a.sets['Set-S']
mdb.models[model_name].Temperature(name='PreField-S',
                                   createStepName='Initial', region=region, distributionType=UNIFORM,
                                   crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(pre_Temp, ))
region = a.sets['Set-P']
mdb.models[model_name].Temperature(name='PreField-P',
                                   createStepName='Initial', region=region, distributionType=UNIFORM,
                                   crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(pre_Temp, ))
region = a.sets['Set-Sub']
mdb.models[model_name].Temperature(name='PreField-Sub',
                                   createStepName='Initial', region=region, distributionType=UNIFORM,
                                   crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(pre_Temp,))


# Create interaction property of Thermal conductance between powder and solid
mdb.models[model_name].ContactProperty('P-S-Contact')
mdb.models[model_name].interactionProperties['P-S-Contact'].ThermalConductance(
    definition=TABULAR, clearanceDependency=ON, pressureDependency=OFF,
    temperatureDependencyC=OFF, massFlowRateDependencyC=OFF, dependenciesC=0,
    clearanceDepTable=((PS_Conductance, 0.0), (0.0, 0.001)))
mdb.models[model_name].ContactProperty('Perfect-Contact')
mdb.models[model_name].interactionProperties['Perfect-Contact'].ThermalConductance(
    definition=TABULAR, clearanceDependency=ON, pressureDependency=OFF,
    temperatureDependencyC=OFF, massFlowRateDependencyC=OFF, dependenciesC=0,
    clearanceDepTable=((1e+10, 0.0), (0.0, 0.1)))


a = mdb.models[model_name].rootAssembly
region1 = a.surfaces['Part-L0-S-BottomFace']
region2 = a.surfaces['Part-Sub-TopFace']
mdb.models[model_name].SurfaceToSurfaceContactStd(
    name='Constraint-S-Sub', createStepName='Step-Act-L0', master=region1,
    slave=region2, sliding=FINITE, thickness=ON,
    interactionProperty='Perfect-Contact', adjustMethod=NONE,
    initialClearance=OMIT, datumAxis=None, clearanceRegion=None)
region1 = a.surfaces['Part-L0-P-BottomFace']
mdb.models[model_name].SurfaceToSurfaceContactStd(
    name='Constraint-P-Sub', createStepName='Step-Act-L0', master=region1,
    slave=region2, sliding=FINITE, thickness=ON,
    interactionProperty='Perfect-Contact', adjustMethod=NONE,
    initialClearance=OMIT, datumAxis=None, clearanceRegion=None)


# Set thermal conductance between powder and solid
for l in range(0, layers-1):
    a = mdb.models[model_name].rootAssembly
    if 'Part-L' + str(l) + '-P-TopFace' in a.surfaces.keys():
        region = a.surfaces['Part-L' + str(l) + '-P-TopFace']
        mdb.models[model_name].FilmCondition(name='FilmCondi_P-L' + str(l) + '-TopFace',
                                                        createStepName='Step-Act-L' + str(l), surface=region,
                                                        definition=EMBEDDED_COEFF,
                                                        filmCoeff=film_coef, filmCoeffAmplitude='', sinkTemperature=pre_Temp,
                                                        sinkAmplitude='', sinkDistributionType=UNIFORM,
                                                        sinkFieldName='')
        mdb.models[model_name].interactions['FilmCondi_P-L' + str(l) + '-TopFace'].deactivate('Step-Act-L' + str(l+1))
        region = a.surfaces['Part-L' + str(l) + '-S-TopFace']
        mdb.models[model_name].FilmCondition(name='FilmCondi_S-L' + str(l) + '-TopFace',
                                             createStepName='Step-Act-L' + str(l), surface=region,
                                             definition=EMBEDDED_COEFF,
                                             filmCoeff=film_coef, filmCoeffAmplitude='', sinkTemperature=pre_Temp,
                                             sinkAmplitude='', sinkDistributionType=UNIFORM,
                                             sinkFieldName='')
        mdb.models[model_name].interactions['FilmCondi_S-L' + str(l) + '-TopFace'].deactivate('Step-Act-L' + str(l + 1))
    if 'Part-L' + str(l) + '-S-face-out' in a.surfaces.keys() and 'Part-L' + str(l) + '-P-face-in' in a.surfaces.keys():
        region1 = a.surfaces['Part-L' + str(l) + '-S-face-out']
        region2 = a.surfaces['Part-L' + str(l) + '-P-face-in']
        mdb.models[model_name].SurfaceToSurfaceContactStd(name='Int-P-S-L' + str(l),
                                                          # createStepName='Step-Act-L' + str(l), master=region1,
                                                          createStepName='Step-Act-L' + str(l), master=region1,
                                                          slave=region2,
                                                          sliding=FINITE, thickness=ON,
                                                          interactionProperty='P-S-Contact',
                                                          adjustMethod=NONE, initialClearance=OMIT, datumAxis=None,
                                                          clearanceRegion=None)
        mdb.models[model_name].interactions['Int-P-S-L' + str(l)].setValues(
            initialClearance=OMIT, surfaceSmoothing=AUTOMATIC, adjustMethod=NONE,
            sliding=FINITE, enforcement=SURFACE_TO_SURFACE, thickness=ON,
            contactTracking=TWO_CONFIG, bondingSet=None)
        # mdb.models[model_name].interactions['Int-P-S-L' + str(l)].deactivate('Step-Act-L' + str(l + 1))
        if l >= 1:
            if 'Part-L' + str(l) + '-S' in a.instances.keys():
                a = mdb.models[model_name].rootAssembly
                region1 = a.surfaces['Part-L' + str(l) + '-S-BottomFace']
                region2 = a.surfaces['Part-L' + str(l-1) + '-S-TopFace']
                mdb.models[model_name].SurfaceToSurfaceContactStd(name='Constraint-S-L' + str(l) + '/L' + str(l - 1),
                                                                  # createStepName='Step-Act-L' + str(l), master=region1,
                                                                  createStepName='Step-Act-L' + str(l), master=region1,
                                                                  slave=region2,
                                                                  sliding=FINITE, thickness=ON,
                                                                  interactionProperty='Perfect-Contact',
                                                                  adjustMethod=NONE, initialClearance=OMIT,
                                                                  datumAxis=None,
                                                                  clearanceRegion=None)
                mdb.models[model_name].interactions['Constraint-S-L' + str(l) + '/L' + str(l - 1)].setValues(
                    initialClearance=OMIT, surfaceSmoothing=AUTOMATIC, adjustMethod=NONE,
                    sliding=FINITE, enforcement=SURFACE_TO_SURFACE, thickness=ON,
                    contactTracking=TWO_CONFIG, bondingSet=None)
            if 'Part-L' + str(l) + '-P' in a.instances.keys():
                a = mdb.models[model_name].rootAssembly
                region1 = a.surfaces['Part-L' + str(l) + '-P-BottomFace']
                region2 = a.surfaces['Part-L' + str(l-1) + '-P-TopFace']
                mdb.models[model_name].SurfaceToSurfaceContactStd(name='Constraint-P-L' + str(l) + '/L' + str(l - 1),
                                                                  # createStepName='Step-Act-L' + str(l), master=region1,
                                                                  createStepName='Step-Act-L' + str(l), master=region1,
                                                                  slave=region2,
                                                                  sliding=FINITE, thickness=ON,
                                                                  interactionProperty='Perfect-Contact',
                                                                  adjustMethod=NONE, initialClearance=OMIT,
                                                                  datumAxis=None,
                                                                  clearanceRegion=None)
                mdb.models[model_name].interactions['Constraint-P-L' + str(l) + '/L' + str(l - 1)].setValues(
                    initialClearance=OMIT, surfaceSmoothing=AUTOMATIC, adjustMethod=NONE,
                    sliding=FINITE, enforcement=SURFACE_TO_SURFACE, thickness=ON,
                    contactTracking=TWO_CONFIG, bondingSet=None)

mdb.save()

# Mesh
for p_name in mdb.models[model_name].parts.keys():
    if p_name[0] == 'P':
        p = mdb.models[model_name].parts[p_name]
        edges = p.edges
        edge_x_min = edges[0].pointOn[0][0]
        edge_x_max = edges[0].pointOn[0][0]
        edge_y_min = edges[0].pointOn[0][1]
        edge_y_max = edges[0].pointOn[0][1]
        for e in edges:
            if e.pointOn[0][0] <= edge_x_min:
                edge_x_min = e.pointOn[0][0]
            if e.pointOn[0][0] >= edge_x_max:
                edge_x_max = e.pointOn[0][0]
            if e.pointOn[0][1] <= edge_y_min:
                edge_y_min = e.pointOn[0][1]
            if e.pointOn[0][1] >= edge_y_max:
                edge_y_max = e.pointOn[0][1]
        for e in edges:
            e_x = e.pointOn[0][0]
            e_y = e.pointOn[0][1]
            e_z = e.pointOn[0][2]
            if e_x == edge_x_min or e_x == edge_x_max or e_y == edge_y_min or e_y == edge_y_max:
                pickedEdges = edges.findAt(((e_x, e_y, e_z),))
                p.seedEdgeBySize(edges=pickedEdges, size=element_size_in_xy*3, deviationFactor=0.1,
                                 minSizeFactor=0.1, constraint=FINER)
            else:
                pickedEdges = edges.findAt(((e_x, e_y, e_z),))
                p.seedEdgeBySize(edges=pickedEdges,
                                 size=element_size_in_xy*2,
                                 deviationFactor=0.1,
                                 minSizeFactor=0.1,
                                 constraint=FINER)
        p = mdb.models[model_name].parts[p_name]
        p.generateMesh()
        elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
        elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
        p = mdb.models[model_name].parts[p_name]
        cells = p.cells
        for c_num in range(len(cells)):
            c = cells[c_num:c_num+1]
            pickedRegions = (c,)
            p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
        '''
        p = mdb.models[model_name].parts[p_name]
        p.seedPart(size=element_size_in_z, deviationFactor=0.1, minSizeFactor=0.1)
        p = mdb.models[model_name].parts[p_name]
        p.generateMesh()
        elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
        elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
        p = mdb.models[model_name].parts[p_name]
        c = p.cells
        cells = c[0:1]
        pickedRegions = (cells,)
        p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
        '''
    elif p_name[0] == 'S':
        p = mdb.models[model_name].parts[p_name]
        p.seedPart(size=element_size_in_xy*0.8, deviationFactor=0.1, minSizeFactor=element_size_in_xy*0.2)
        p = mdb.models[model_name].parts[p_name]
        p.generateMesh()
        elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
        elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
        p = mdb.models[model_name].parts[p_name]
        cells = p.cells
        for c_num in range(len(cells)):
            c = cells[c_num:c_num + 1]
            pickedRegions = (c,)
            p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))

mdb.save()