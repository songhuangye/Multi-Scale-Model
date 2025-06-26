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


def read_para(path, name):
    file = open(path + '\\' + name, 'r')
    f = file.readlines()
    file.close()
    f = np.array(f)
    data = []
    if f is not None:
        for i in f:
            if i.split():
                if i.split()[0][0] != '#' and i.split()[0][0] != '[':
                    data.append(i.split())
    else:
        print('Error: check the aim directory and file name')
    key_list = []
    value_list = []
    for i in data:
        key_list.append(i[0])
        value_list.append(float(i[-1]))

    dict_set = dict(zip(key_list, value_list))
    return dict_set


def write_inp_all(workdir, layer, tracks, width, length, scan_width_0, scan_length_0, hatch, depth_substrate, depth, step_time,
                  state, mesh_size_on_edge_P):
    # track parallel to the y-axis: x1 = (scan_width/2-tracks*hatch)+0.2, x2 = (scan_width/2-tracks*hatch)-0.2, y = +- length/2
    # track parallel to the x-axis: x = +- width/2, y1 = (scan_length/2-tracks*hatch)+0.2, y2 = (scan_length/2-tracks*hatch)-0.2
    if layer % 2 == 0:
        scan_width = scan_width_0
        scan_length = scan_length_0 + 0.4
        focus = scan_width / 2 - hatch * tracks
    else:
        scan_width = scan_width_0 + 0.4
        scan_length = scan_length_0
        focus = scan_length / 2 - hatch * tracks

    # create model
    if state == 'Spreading':
        model_name = 'Model-L' + str(layer - 1).zfill(3) + '-to-' + str(layer).zfill(3)
    else:
        model_name = 'Model-L' + str(layer).zfill(3) + '-T' + str(tracks).zfill(3)

    # model_Template = 'Model-L' + str(layer).zfill(3) + '-Template'
    # mdb.Model(name=model_name, objectToCopy=mdb.models[model_Template])

    # Model-Template contains only material from the library, need to create all things
    # mdb.Model(name=model_name, objectToCopy=mdb.models['Model-Template'])
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

    '''
    focus = 0
    if layer % 2 == 0:
        focus = scan_width / 2 - hatch * tracks
    else:
        focus = scan_length / 2 - hatch * tracks
    '''
    # ============================================================================== #
    #                                  begin [Part]

    # just use 'Part-1' as part name
    # p = mdb.models[model_name].parts['Part-1']

    s1 = mdb.models[model_name].ConstrainedSketch(name='__profile__',
                                                  sheetSize=(length + width))
    g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
    s1.setPrimaryObject(option=STANDALONE)
    s1.rectangle(point1=(-width / 2, -length / 2), point2=(width / 2, length / 2))
    p = mdb.models[model_name].Part(name='Part-1', dimensionality=THREE_D,
                                    type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts['Part-1']
    p.BaseSolidExtrude(sketch=s1, depth=depth)
    s1.unsetPrimaryObject()
    p = mdb.models[model_name].parts['Part-1']
    del mdb.models[model_name].sketches['__profile__']

    # create 'Set-All'
    p = mdb.models[model_name].parts['Part-1']
    c = p.cells
    cells = c[0:len(c)]
    p.Set(cells=cells, name='Set-All')

    # create datum points
    p = mdb.models[model_name].parts['Part-1']
    v = p.vertices

    if state == 'Spreading':
        # Create x-y direction layers
        # Create new layer
        if layer >= 6:
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - 3 * depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - 5 * depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, 0)),
                                 vector=(0.0, 0.0, depth_substrate))
        else:
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - depth_layer))
            if layer == 1:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))
            elif layer == 2:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 2 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 4 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 6 * depth_layer))
            elif layer == 3:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))
            elif layer == 4:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 2 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 4 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 6 * depth_layer))
            elif layer == 5:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))  # edge of substrate
        # Create limited scanning area
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, length / 2, depth)),
                             vector=((width - scan_width) / 2, 0.0, 0.0))
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, length / 2, depth)),
                             vector=(0.0, -(length - scan_length) / 2, 0.0))
        p.DatumPointByOffset(point=v.findAt(coordinates=(width / 2, -length / 2, depth)),
                             vector=(-(width - scan_width) / 2, 0.0, 0.0))
        p.DatumPointByOffset(point=v.findAt(coordinates=(width / 2, -length / 2, depth)),
                             vector=(0.0, (length - scan_length) / 2, 0.0))
    else:
        # Create x-y direction layers
        # Create new layer
        if layer >= 6:
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - 3 * depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - 5 * depth_layer))
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, 0)),
                                 vector=(0.0, 0.0, depth_substrate))
        else:
            p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                 vector=(0.0, 0.0, - depth_layer))
            if layer == 1:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))
            elif layer == 2:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 2 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 4 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 6 * depth_layer))
            elif layer == 3:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))
            elif layer == 4:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 2 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 4 * depth_layer))  # edge of substrate
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 6 * depth_layer))
            elif layer == 5:
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 3 * depth_layer))
                p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                                     vector=(0.0, 0.0, - 5 * depth_layer))  # edge of substrate
        '''
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                             vector=(0.0, 0.0, - depth_layer))
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                             vector=(0.0, 0.0, - 3 * depth_layer))
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
                             vector=(0.0, 0.0, - 6 * depth_layer))
        # p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
        #                      vector=(0.0, 0.0, - 9 * depth_layer))
        # p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)),
        #                     vector=(0.0, 0.0, - 11 * depth_layer))
        p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, 0)),
                             vector=(0.0, 0.0, depth_substrate - 0.7))
        '''
    # p.DatumPointByOffset(point=v.findAt(coordinates=(-width / 2, -length / 2, depth)), vector=(0.0, 0.0, -depth_layer))

    if state != 'Spreading':
        if layer % 2 == 0:
            begin_point = (width / 2, length / 2, depth)
            vector_focus1 = ((- width / 2 + (scan_width / 2 - tracks * hatch)) - 0.2, 0, 0)
            vector_focus2 = ((- width / 2 + (scan_width / 2 - tracks * hatch)) + 0.2, 0, 0)
            vector_trans1 = ((- width / 2 + (scan_width / 2 - tracks * hatch)) - 0.6, 0, 0)
            vector_trans2 = ((- width / 2 + (scan_width / 2 - tracks * hatch)) + 0.6, 0, 0)
            vector_limit1 = (0.0, -(length - scan_length) / 2, 0.0)
            vector_limit2 = (0.0, -(length - scan_length) / 2 - scan_length, 0.0)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_focus1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_focus2)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_trans1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_trans2)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_limit1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_limit2)
            if focus < scan_width / 2 - 0.6:
                vector_side1 = (-width / 2 + scan_width / 2, 0, 0)
                p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_side1)
            if focus > -scan_width / 2 + 0.6:
                vector_end = (-(width - scan_width) / 2 - scan_width, 0.0, 0.0)
                p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_end)
        else:
            begin_point = (-width / 2, length / 2, depth)
            vector_focus1 = (0, -(length / 2 - (scan_length / 2 - tracks * hatch)) - 0.2, 0)
            vector_focus2 = (0, -(length / 2 - (scan_length / 2 - tracks * hatch)) + 0.2, 0)
            vector_trans1 = (0, -(length / 2 - (scan_length / 2 - tracks * hatch)) - 0.6, 0)
            vector_trans2 = (0, -(length / 2 - (scan_length / 2 - tracks * hatch)) + 0.6, 0)
            vector_limit1 = ((width - scan_width) / 2, 0.0, 0.0)
            vector_limit2 = ((width - scan_width) / 2 + scan_width, 0.0, 0.0)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_focus1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_focus2)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_trans1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_trans2)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_limit1)
            p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_limit2)
            if focus < scan_length / 2 - 0.6:
                p.DatumPointByOffset(point=v.findAt(coordinates=begin_point),
                                     vector=(0, -width / 2 + scan_width / 2, 0))
            if focus > -scan_length / 2 + 0.6:
                vector_end = (0.0, -(length - scan_length) / 2 - scan_length, 0.0)
                p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector_end)

    begin_point = (width / 2, length / 2, depth)
    # vector = ((- width/2 + (scan_width/2 - tracks * hatch)), 0, 0)
    # p.DatumPointByOffset(point=v.findAt(coordinates=begin_point), vector=vector)

    # record datum points and cut the part
    p = mdb.models[model_name].parts['Part-1']
    d = p.datums

    datum_z = []
    datum_xy = []
    # point_side = []

    for i in d.items():
        if d[i[0]].pointOn[0] == -width / 2 and d[i[0]].pointOn[1] == -length / 2:
            datum_xy.append(d[i[0]])
        else:
            datum_z.append(d[i[0]])

    for t in datum_xy:
        c = p.cells
        pickedCells = c[0:len(c)]
        e = p.edges
        normal = ()
        for i in e:
            if i.pointOn[0][0] == width / 2 and i.pointOn[0][1] == length / 2:
                normal = i
        p.PartitionCellByPlanePointNormal(point=t, normal=normal, cells=pickedCells)

    for t in datum_z:
        c = p.cells
        pickedCells = c[0:len(c)]
        e = p.edges
        normal = ()
        if state != 'Spreading':
            if layer % 2 == 0:
                if t.pointOn[1] == length / 2:
                    for i in e:
                        if i.pointOn[0][1] == length / 2 or i.pointOn[0][1] == -length / 2:
                            if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                                normal = i
                                break
                else:
                    for i in e:
                        if i.pointOn[0][0] == width / 2 or i.pointOn[0][0] == -width / 2:
                            if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                                normal = i
                                break
            else:
                if t.pointOn[0] == -width / 2:
                    for i in e:
                        if i.pointOn[0][0] == width / 2 or i.pointOn[0][0] == -width / 2:
                            if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                                normal = i
                                break
                else:
                    for i in e:
                        if i.pointOn[0][1] == length / 2 or i.pointOn[0][1] == -length / 2:
                            if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                                normal = i
                                break
        elif state == 'Spreading':
            if t.pointOn[1] == length / 2 or t.pointOn[1] == -length / 2:
                for i in e:
                    if i.pointOn[0][1] == length / 2 or i.pointOn[0][1] == -length / 2:
                        if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                            normal = i
                            break
            elif t.pointOn[0] == -width / 2 or t.pointOn[0] == width / 2:
                for i in e:
                    if i.pointOn[0][0] == width / 2 or i.pointOn[0][0] == -width / 2:
                        if i.pointOn[0][-1] == depth or i.pointOn[0][-1] == 0:
                            normal = i
                            break
        p.PartitionCellByPlanePointNormal(point=t, normal=normal, cells=pickedCells)

        # p.PartitionCellByPlanePointNormal(point=t, normal=normal, cells=pickedCells)

    # update Set-All
    c = p.cells
    cells = c[0:len(c)]
    p.Set(cells=cells, name='Set-All')

    set_powder_layer = []
    set_substrate = []
    for i in c:
        if i.pointOn[0][-1] < depth_substrate:
            if set_substrate:
                set_substrate += c[int(i.index):int(i.index) + 1]
            else:
                set_substrate = c[int(i.index):int(i.index) + 1]
        else:
            if set_powder_layer:
                set_powder_layer += c[int(i.index):int(i.index) + 1]
            else:
                set_powder_layer = c[int(i.index):int(i.index) + 1]

    p.Set(cells=set_substrate, name='Set-substrate')
    p.Set(cells=set_powder_layer, name='Set-powder_layer')

    # redefine edges

    # important points
    # four corners: x = +- width/2, y = +- length
    # two sides of focused zone:
    # track parallel to the y-axis: x1 = (scan_width/2-tracks*hatch)+0.2, x2 = (scan_width/2-tracks*hatch)-0.2, y = +- length/2
    # track parallel to the x-axis: x = +- width/2, y1 = (scan_length/2-tracks*hatch)+0.2, y2 = (scan_length/2-tracks*hatch)-0.2
    p = mdb.models[model_name].parts['Part-1']
    e = p.edges
    v = p.vertices
    # p for parallel, v for vertical
    e_z = []  # edges parallel to the z-direction
    e_z_top = []
    e_p = []  # edges parallel to the scanning track in xy-plane
    e_p_a = []
    e_p_b = []
    e_v_out1 = []  # edges vertical to the scanning track in xy-plane but outside the focus zone
    e_v_out2 = []  # edges vertical to the scanning track in xy-plane but outside the focus zone
    e_v_side = []
    e_v_side1 = []
    e_v_side2 = []
    e_v_focus = []  # edges vertical to the scanning track in xy-plane but in the focus zone
    e_v_trans1 = []
    e_v_trans2 = []
    e_sp_l = []
    e_sp_r = []
    e_sp_t = []
    e_sp_d = []
    e_sp_m = []

    if state == 'Scanning':
        for i in e:
            v1_index = i.getVertices()[0]
            v2_index = i.getVertices()[1]
            v1 = v[v1_index]
            v2 = v[v2_index]
            xv1 = v1.pointOn[0][0]
            yv1 = v1.pointOn[0][1]
            zv1 = v1.pointOn[0][2]
            xv2 = v2.pointOn[0][0]
            yv2 = v2.pointOn[0][1]
            zv2 = v2.pointOn[0][2]
            vertex = [xv2 - xv1, yv2 - yv1, zv2 - zv1]
            middle = [(xv1 + xv2) / 2, (yv1 + yv2) / 2, (zv1 + zv2) / 2]
            if layer % 2 == 0:
                if vertex[0] == 0 and vertex[1] == 0 and vertex[2] != 0:
                    e_z.append(e.findAt(i.pointOn))
                elif vertex[0] == 0 and vertex[1] != 0 and vertex[2] == 0:
                    if -scan_length / 2 < middle[1] < scan_length / 2:
                        e_p.append(e.findAt(i.pointOn))
                    elif scan_length / 2 < middle[1] < length / 2:
                        e_p_a.append(e.findAt(i.pointOn))
                    elif - length / 2 < middle[1] < -scan_length / 2:
                        e_p_b.append(e.findAt(i.pointOn))
                elif vertex[0] != 0 and vertex[1] == 0 and vertex[2] == 0:
                    if focus > scan_width / 2 - 0.6:
                        # situation_1: when scanning track too close to the +scan_width/2,
                        # left side is limited by -scan_width/2 but no limit on the right side
                        if -width / 2 < middle[0] < -scan_width / 2:
                            e_v_side.append(e.findAt(i.pointOn))
                        elif -scan_width / 2 < middle[0] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[0] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[0] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[0] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[0] < width / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                    elif focus < -scan_width / 2 + 0.6:
                        # situation_2: when scanning track too close to the -scan_width/2,
                        # right side is limited by +scan_width/2 but no limit on the left side
                        if -width / 2 < middle[0] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[0] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[0] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[0] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[0] < scan_width / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                        elif scan_width / 2 < middle[0] < width / 2:
                            e_v_side.append(e.findAt(i.pointOn))
                    else:
                        # situation_3: scanning track is in the middle, both side +-scan_width/2 are limited
                        if -width / 2 < middle[0] < -scan_width / 2:
                            e_v_side1.append(e.findAt(i.pointOn))
                        elif -scan_width / 2 < middle[0] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[0] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[0] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[0] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[0] < scan_width / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                        elif scan_width / 2 < middle[0] < width / 2:
                            e_v_side2.append(e.findAt(i.pointOn))
            else:
                if vertex[0] == 0 and vertex[1] == 0 and vertex[2] != 0:
                    e_z.append(e.findAt(i.pointOn))
                elif vertex[0] != 0 and vertex[1] == 0 and vertex[2] == 0:
                    if -scan_width / 2 < middle[0] < scan_width / 2:
                        e_p.append(e.findAt(i.pointOn))
                    elif -width / 2 < middle[0] < -scan_width / 2:
                        e_p_a.append(e.findAt(i.pointOn))
                    elif scan_width / 2 < middle[0] < width / 2:
                        e_p_b.append(e.findAt(i.pointOn))
                elif vertex[0] == 0 and vertex[1] != 0 and vertex[2] == 0:
                    if focus > scan_length / 2 - 0.6:
                        if -length / 2 < middle[1] < -scan_length / 2:
                            e_v_side.append(e.findAt(i.pointOn))
                        elif -scan_length / 2 < middle[1] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[1] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[1] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[1] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[1] < length / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                    elif focus < -scan_length / 2 + 0.6:
                        if -length / 2 < middle[1] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[1] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[1] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[1] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[1] < scan_length / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                        elif scan_length / 2 < middle[1] < length / 2:
                            e_v_side.append(e.findAt(i.pointOn))
                    else:
                        if -length / 2 < middle[1] < -scan_length / 2:
                            e_v_side1.append(e.findAt(i.pointOn))
                        elif -scan_length / 2 < middle[1] < focus - 0.6:
                            e_v_out1.append(e.findAt(i.pointOn))
                        elif focus - 0.6 < middle[1] < focus - 0.2:
                            e_v_trans1.append(e.findAt(i.pointOn))
                        elif focus - 0.2 < middle[1] < focus + 0.2:
                            e_v_focus.append(e.findAt(i.pointOn))
                        elif focus + 0.2 < middle[1] < focus + 0.6:
                            e_v_trans2.append(e.findAt(i.pointOn))
                        elif focus + 0.6 < middle[1] < scan_length / 2:
                            e_v_out2.append(e.findAt(i.pointOn))
                        elif scan_length / 2 < middle[1] < length / 2:
                            e_v_side2.append(e.findAt(i.pointOn))
    elif state == 'Spreading':
        for i in e:
            v1_index = i.getVertices()[0]
            v2_index = i.getVertices()[1]
            v1 = v[v1_index]
            v2 = v[v2_index]
            xv1 = v1.pointOn[0][0]
            yv1 = v1.pointOn[0][1]
            zv1 = v1.pointOn[0][2]
            xv2 = v2.pointOn[0][0]
            yv2 = v2.pointOn[0][1]
            zv2 = v2.pointOn[0][2]
            vertex = [xv2 - xv1, yv2 - yv1, zv2 - zv1]
            middle = [(xv1 + xv2) / 2, (yv1 + yv2) / 2, (zv1 + zv2) / 2]
            if vertex[0] == 0 and vertex[1] == 0 and vertex[2] != 0:
                e_z.append(e.findAt(i.pointOn))
            elif vertex[0] != 0 and vertex[1] == 0 and vertex[2] == 0:
                if -width / 2 < middle[0] < -scan_width / 2:
                    e_sp_l.append(e.findAt(i.pointOn))
                elif -scan_width / 2 < middle[0] < scan_width / 2:
                    e_sp_m.append(e.findAt(i.pointOn))
                elif scan_width / 2 < middle[0] < width / 2:
                    e_sp_r.append(e.findAt(i.pointOn))
            elif vertex[0] == 0 and vertex[1] != 0 and vertex[2] == 0:
                if -length / 2 < middle[1] < -scan_length / 2:
                    e_sp_d.append(e.findAt(i.pointOn))
                elif -scan_length / 2 < middle[1] < scan_length / 2:
                    e_sp_m.append(e.findAt(i.pointOn))
                elif scan_length / 2 < middle[1] < length / 2:
                    e_sp_t.append(e.findAt(i.pointOn))

    # create set for edges
    if e_z:
        p.Set(edges=e_z, name='Set-e_z')

    if e_p:
        p.Set(edges=e_p, name='Set-e_p')

    if e_p_a:
        p.Set(edges=e_p_a, name='Set-e_p_a')

    if e_p_b:
        p.Set(edges=e_p_b, name='Set-e_p_b')

    if e_v_out1:
        p.Set(edges=e_v_out1, name='Set-e_v_out1')

    if e_v_out2:
        p.Set(edges=e_v_out2, name='Set-e_v_out2')

    if e_v_trans1:
        p.Set(edges=e_v_trans1, name='Set-e_v_trans1')

    if e_v_trans2:
        p.Set(edges=e_v_trans2, name='Set-e_v_trans2')

    if e_v_focus:
        p.Set(edges=e_v_focus, name='Set-e_focus')

    if e_v_side:
        p.Set(edges=e_v_side, name='Set-e_side')

    if e_v_side1:
        p.Set(edges=e_v_side1, name='Set-e_side1')

    if e_v_side2:
        p.Set(edges=e_v_side2, name='Set-e_side2')

    if e_sp_m:
        p.Set(edges=e_sp_m, name='Set-e_sp_m')

    if e_sp_l:
        p.Set(edges=e_sp_l, name='Set-e_sp_l')

    if e_sp_r:
        p.Set(edges=e_sp_r, name='Set-e_sp_r')

    if e_sp_t:
        p.Set(edges=e_sp_t, name='Set-e_sp_t')

    if e_sp_d:
        p.Set(edges=e_sp_d, name='Set-e_sp_d')

    #                                  end [Part]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [Property]

    # material data is already imported in the model-Template

    # create section-1
    p = mdb.models[model_name].parts['Part-1']
    mdb.models[model_name].HomogeneousSolidSection(name='Section-P', material='SS316L-Powder', thickness=None)

    p = mdb.models[model_name].parts['Part-1']
    mdb.models[model_name].HomogeneousSolidSection(name='Section-S', material='SS316L-Solid-AsBuilt', thickness=None)

    region_p = p.sets['Set-powder_layer']
    p.SectionAssignment(region=region_p, sectionName='Section-P', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)
    region = p.sets['Set-substrate']
    p.SectionAssignment(region=region, sectionName='Section-S', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)

    # Assign section-1 on 'Set-All'
    # region = p.sets['Set-All']
    # p.SectionAssignment(region=region, sectionName='Section-1', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
    #                    thicknessAssignment=FROM_SECTION)

    #                                  end [Property]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [Assembly]

    a = mdb.models[model_name].rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    p = mdb.models[model_name].parts['Part-1']
    a.Instance(name='Part-1-1', part=p, dependent=ON)

    # set surfaces
    f = a.instances['Part-1-1'].faces
    faces_top = []
    faces_bottom = []
    faces_side = []
    for i in f:
        if depth-0.005 < i.pointOn[0][-1] < depth+0.005:
            faces_top.append(f.findAt(i.pointOn))
        elif i.pointOn[0][-1] == 0:
            faces_bottom.append(f.findAt(i.pointOn))
        elif i.pointOn[0][0] == width / 2 or i.pointOn[0][0] == -width / 2 or \
                i.pointOn[0][1] == length / 2 or i.pointOn[0][1] == -length / 2:
            faces_side.append(f.findAt(i.pointOn))

    a.Surface(side1Faces=faces_top, name='Surf-Top')
    a.Surface(side1Faces=faces_bottom, name='Surf-Bottom')
    a.Surface(side1Faces=faces_side, name='Surf-Side')

    # update Set-All
    c = p.cells
    cells = c[0:len(c)]
    p.Set(cells=cells, name='Set-All')

    #                                  end [Assembly]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [Step]

    if state == 'Cooling':
        mdb.models[model_name].HeatTransferStep(name='Step-2', previous='Step-1', timePeriod=2, maxNumInc=1000000,
                                                initialInc=0.05, minInc=1e-11, maxInc=0.1, deltmx=1000000.0)
        mdb.models[model_name].steps['Step-2'].control.setValues(allowPropagation=OFF, resetDefaultValues=OFF,
                                                                 timeIncrementation=(4.0, 8.0, 9.0, 16.0, 10.0, 4.0,
                                                                                     12.0, 20.0, 6.0, 3.0, 50.0))
    else:
        mdb.models[model_name].HeatTransferStep(name='Step-1', previous='Initial', timePeriod=step_time, maxNumInc=1000000,
                                                initialInc=1e-6, minInc=1e-11, maxInc=0.0004, deltmx=1000000.0)
        mdb.models[model_name].steps['Step-1'].control.setValues(allowPropagation=OFF, resetDefaultValues=OFF,
                                                                 timeIncrementation=(
                                                                     4.0, 8.0, 9.0, 16.0, 10.0, 4.0, 12.0,
                                                                     20.0, 6.0, 3.0, 50.0))

    mdb.models[model_name].fieldOutputRequests['F-Output-1'].setValues(variables=('NT', 'HFL', 'SDV'))

    #                                  end [Step]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [Interaction]

    # create surface condition
    a = mdb.models[model_name].rootAssembly
    region = a.surfaces['Surf-Top']
    mdb.models[model_name].FilmCondition(name='Int-Surf-Top', createStepName='Step-1',
                                         surface=region, definition=EMBEDDED_COEFF, filmCoeff=10.6,
                                         filmCoeffAmplitude='', sinkTemperature=200.0, sinkAmplitude='',
                                         sinkDistributionType=UNIFORM, sinkFieldName='')

    # a = mdb.models[model_name].rootAssembly
    # region = a.surfaces['Surf-Side']
    # mdb.models[model_name].FilmCondition(name='Int-Surf-Side', createStepName='Step-1',
    #                                     surface=region, definition=EMBEDDED_COEFF, filmCoeff=10.6,
    #                                     filmCoeffAmplitude='', sinkTemperature=200.0, sinkAmplitude='',
    #                                      sinkDistributionType=UNIFORM, sinkFieldName='')

    # create predefined field initial temperature
    if layer == 1 and tracks == 0:
        a = mdb.models[model_name].rootAssembly
        region = a.instances['Part-1-1'].sets['Set-All']
        mdb.models[model_name].Temperature(name='Initial_Temperature',
                                           createStepName='Initial', region=region, distributionType=UNIFORM,
                                           crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(200.0,))

    #                                  end [Interaction]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [load]

    # create surface heat flux using subroutine
    if state != 'Spreading':
        a = mdb.models[model_name].rootAssembly
        region = a.surfaces['Surf-Top']
        mdb.models[model_name].SurfaceHeatFlux(name='Load-1', createStepName='Step-1',
                                               region=region, magnitude=1.0, distributionType=USER_DEFINED)

    # create bottom temperature as boundary condition == 200
    p = mdb.models[model_name].parts['Part-1']
    f = p.faces
    faces = []
    for i in f:
        if i.pointOn[0][-1] == 0:
            faces.append(f.findAt(i.pointOn))

    p.Set(faces=faces, name='Set-Bottom')
    a = mdb.models[model_name].rootAssembly
    region = a.instances['Part-1-1'].sets['Set-Bottom']
    mdb.models[model_name].TemperatureBC(name='BC-1',
                                         createStepName='Step-1', region=region, fixed=OFF,
                                         distributionType=UNIFORM, fieldName='', magnitude=200.0, amplitude=UNSET)
    #                                  end [load]
    # ============================================================================== #

    # ============================================================================== #
    #                                  begin [Mesh]

    # redefine edges

    # seeds spreading
    p = mdb.models[model_name].parts['Part-1']
    e = p.edges
    if e_z:
        for i in e_z:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if e_p:
        for i in e_p:
            pickedEdges = i
            p.seedEdgeBySize(edges=pickedEdges, size=mesh_size_on_edge_P, constraint=FINER)

    if e_p_a:
        for i in e_p_a:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if e_p_b:
        for i in e_p_b:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if e_v_focus:
        for i in e_v_focus:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=8, constraint=FIXED)

    if e_v_trans1:
        for i in e_v_trans1:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=3, constraint=FIXED)

    if e_v_trans2:
        for i in e_v_trans2:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=3, constraint=FIXED)

    if e_v_side:
        for i in e_v_side:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if e_v_side1:
        for i in e_v_side1:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if e_v_side2:
        for i in e_v_side2:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=1, constraint=FIXED)

    if layer % 2 == 0:
        l_out1 = (scan_width / 2 - tracks * hatch) + width / 2
        l_out2 = width / 2 - (scan_width / 2 - tracks * hatch)
    else:
        l_out2 = (scan_length / 2 - tracks * hatch) + length / 2
        l_out1 = length / 2 - (scan_length / 2 - tracks * hatch)

    ele_out1 = 2
    ele_out2 = 3
    '''if ele_out1 < 2:
        ele_out1 = 2
        ele_out2 = 3
    elif ele_out2 < 2:
        ele_out2 = 2
        ele_out1 = 3'''
    if e_v_out1:
        for i in e_v_out1:
            pickedEdges = i
            # p.seedEdgeByNumber(edges=pickedEdges, number=ele_out1, constraint=FINER)
            p.seedEdgeByNumber(edges=pickedEdges, number=ele_out1, constraint=FINER)

    if e_v_out2:
        for i in e_v_out2:
            pickedEdges = i
            # p.seedEdgeByNumber(edges=pickedEdges, number=ele_out2, constraint=FINER)
            p.seedEdgeByNumber(edges=pickedEdges, number=ele_out2, constraint=FINER)

    # mesh for the spreading state
    if e_sp_m:
        for i in e_sp_m:
            pickedEdges = i
            size = ((width - scan_width) / 2 + (length - scan_length) / 2) / 4
            p.seedEdgeBySize(edges=pickedEdges, size=size/2, constraint=FINER)

    if e_sp_l:
        for i in e_sp_l:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=4, constraint=FIXED)

    if e_sp_r:
        for i in e_sp_r:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=4, constraint=FIXED)

    if e_sp_t:
        for i in e_sp_t:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=4, constraint=FIXED)

    if e_sp_d:
        for i in e_sp_d:
            pickedEdges = i
            p.seedEdgeByNumber(edges=pickedEdges, number=4, constraint=FIXED)

    p.generateMesh()

    # set element type
    elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
    elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
    elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
    p = mdb.models[model_name].parts['Part-1']
    c = p.cells

    cells = c[0:len(c)]
    # p.Set(cells=cells, name='Set-All')

    # pickedCells = c[0:len(c)]

    # cells = c.findAt(dict_cells['C_Substrate'])
    pickedRegions = (cells,)
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))

    # create job ann input
    os.chdir(workdir)
    if state == 'Spreading':
        job_name = 'Job-L' + str(layer - 1).zfill(3) + '-to-L' + str(layer).zfill(3)
    else:
        job_name = 'Job-L' + str(layer).zfill(3) + '-T' + str(tracks).zfill(3)
    mdb.Job(name=job_name, model=model_name, description='', type=ANALYSIS,
            atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
            memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
            explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
            modelPrint=OFF, contactPrint=OFF, historyPrint=OFF,
            # X:\1_Simulation\ABAQUS_SIM\11_TCR-Model\ABA\Meso-scale-Model\Model-5X5-30Layer\Subroutines
            userSubroutine='X:\\1_Simulation\ABAQUS_SIM\\11_TCR-Model\\ABA\\Meso-scale-Model\\Model-5X5-30Layer\\Subroutines\\Sub-' + str(layer) + '-T' + str(tracks) + '.for',
            scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=4, numDomains=4, numGPUs=0)
    mdb.jobs[job_name].writeInput(consistencyChecking=OFF)

    # delate model
    # del mdb.models[model_name]

    #: The job input file has been written to "Job-L0-T0.inp".

    inputdir = workdir + '\\Input'

    inp_name = job_name + '.inp'
    inp_txt = job_name + '.txt'
    inp_0 = r'aaa.txt'

    shutil.copyfile(inp_name, inputdir + '\\' + inp_name)

    os.chdir(inputdir)
    os.renames(inp_name, inp_txt)

    file = open(inp_txt, 'r')
    data = file.readlines()
    file.close()

    counter = 0
    for i in range(len(data)):
        if '*Restart, write, frequency=0\n' in data[i]:
            data[i] = '*Restart, write, frequency=50\n'
        if '*Output, history, frequency=0' in data[i]:
            data[i] = '*Output, history, frequency=5\n'
        if '** -' in data[i] and inp_name != 'Job-L001-T000.inp':
            if counter == 0:
                data.insert(i + 1, '*MAP SOLUTION\n')
                counter += 1
            else:
                continue

    f = open(inp_0, 'w')
    for i in data:
        f.write(i)

    f.close()

    os.renames(inp_0, inp_name)
    os.remove(inp_txt)

    os.chdir(workdir)
    os.remove(inp_name)

    print('\n\n# ======================= Create input ' + model_name + ' ======================= #\n\n')

    # del mdb.models[model_name]

workdir = r'X:\1_Simulation\ABAQUS_SIM\11_TCR-Model\ABA\Meso-scale-Model\Model-5X5-30Layer'
paradir = workdir + '\\' + 'Parameters'
subdir = workdir + '\\' + 'Subroutines'
inpdir = workdir + '\\' + 'Input'
# inpdir = workdir + '\\' + 'Input-2'
pydir = workdir + '\\' + 'Py_Script'
fordir = workdir + '\\' + 'For_Script'

os.chdir(workdir)

dict_set = read_para(paradir, 'Setting.txt')

width = dict_set['Plane_width']
length = dict_set['Plane_length']
scan_width = dict_set['Quader_width']
scan_length = dict_set['Quader_length']
hatch = dict_set['Hatch_Distance']
depth_sub = dict_set['Depth_substrate']
depth_layer = dict_set['Depth_layer']

mesh_size_on_edge_P = 0.11

file = open(paradir + '\\' + 'Scan_Tracks.txt', 'r')
tracks_data = file.readlines()
file.close()
tracks_data = np.array(tracks_data)

# print(tracks_data)
last_track = 0
last_layer = 0
for i in tracks_data:
    if '#' not in i:
        lines = i.split('/')
        # print(lines)
        if '[Spreading]' in lines[0]:
            layer = last_layer + 1
            track = 0
            state = 'Spreading'
            step_time = 1.0
            depth = depth_sub + depth_layer * layer
            write_inp_all(workdir, layer, track, width, length, scan_width, scan_length, hatch, depth_sub, depth,
                          step_time, state, mesh_size_on_edge_P)
        else:
            layer = int(lines[0].split(',')[0][1:])
            track = int(lines[0].split(',')[-1][:-2])
            step_time = float(lines[3].split('=')[-1])
            #state = lines[-1]
            state = 'Scanning'
            depth = depth_sub + depth_layer * layer
            write_inp_all(workdir, layer, track, width, length, scan_width, scan_length, hatch, depth_sub, depth,
                          step_time, state, mesh_size_on_edge_P)
            last_layer = layer
            last_track = track

