#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 13:54:27 2020

@author: emilio
"""

from scipy.io import loadmat as tradLoadmat
import h5py
import numpy as np
from pathlib import Path

def LoadHdf5Mat(matfilePath):
    # def LookAheadDeref(hdf5File, reference):
        
    def UnpackHdf5(hdf5Matfile, hdf5Group):
        out = {}
        if type(hdf5Group) is h5py._hl.group.Group:
            for key in hdf5Group:
                out[key] = hdf5Group[key]
                if type(out[key]) is h5py._hl.group.Group:
                    out[key] = UnpackHdf5(hdf5Matfile,out[key])
                elif type(out[key]) is h5py._hl.dataset.Dataset:
                    out[key] = UnpackHdf5(hdf5Matfile,out[key])
                elif type(out[key]) is h5py.h5r.Reference:
                    out[key] = UnpackHdf5(hdf5Matfile,out[key])
                        
        elif type(hdf5Group) is h5py._hl.dataset.Dataset:
            out = np.ndarray(hdf5Group.shape, dtype=object)
            
            if hdf5Group.dtype == np.dtype('object'):
                
                with np.nditer([out, hdf5Group], ['refs_ok'], [['writeonly'], ['readonly']]) as iterRef:
                    for valOut, valIn in iterRef:
                        if type(valIn[()]) is h5py._hl.group.Group:
                            valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                        elif type(valIn[()]) is h5py._hl.dataset.Dataset:
                            valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                        elif type(valIn[()]) is h5py.h5r.Reference:
                            valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                        else:
                            valOut[()] = valIn[()]
                            
                      
                   
                    out = iterRef.operands[0]
                    out = out.T # undo Matlab's weird transpose when saving...
            else:
                # apparently type dataset can also store arrays like type
                # reference and I just give up
                #
                # but I'm also renaming this variable to parallel what was done
                # for the reference and perhaps someday I'll make it its own
                # function
                deref = hdf5Group
                if 'MATLAB_empty' in deref.attrs.keys(): # deal with empty arrays
                    # print('empty array')
                    # print(deref[()])
                    if 'MATLAB_class' in deref.attrs.keys():
                        pass
                        # print(deref.attrs['MATLAB_class'])
                    out = np.ndarray(0)
                    return out.T
                
                if 'MATLAB_int_decode' in deref.attrs.keys():
                    if 'MATLAB_class' in deref.attrs.keys():
                        if deref.attrs['MATLAB_class'] == b'char':
                            out = "".join([chr(ch) for ch in deref[()]])
                            return out
                        elif deref.attrs['MATLAB_class'] == b'logical':
                            pass # uint8, the default, is a fine type for logicals
                        else:
                            # print(deref.attrs['MATLAB_class'])
                            print('int decode but class not char...')
                    else:
                        print('int decode but no class?')
                
                out = deref[()]
                out = out.T # for some reason Matlab transposes when saving...
        elif type(hdf5Group) is h5py.h5r.Reference:
            deref = hdf5Matfile[hdf5Group]
            
            if type(deref) is h5py._hl.group.Group:
                out = UnpackHdf5(hdf5Matfile, deref)
            elif deref.dtype == np.dtype('object'):
                try:
                    out = np.ndarray(deref.shape, dtype=object)
                except (AttributeError) as err:
                    raise RuntimeError('problem with forming iterator of a non-group a')
                        
                else:
                    with np.nditer([out, deref], ['refs_ok'], [['writeonly'], ['readonly']]) as iterRef:
                        for valOut, valIn in iterRef:
                            if type(valIn[()]) is h5py._hl.group.Group:
                                valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                            elif type(valIn[()]) is h5py._hl.dataset.Dataset:
                                valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                            elif type(valIn[()]) is h5py.h5r.Reference:
                                valOut[()] = UnpackHdf5(hdf5Matfile, valIn[()])
                            else:
                                # print('non-hdf5 object')
                                if 'MATLAB_empty' in deref.attrs.keys(): # deal with empty arrays
                                    valOut[()] = np.ndarray(0)
                                else:
                                    valOut[()] = valIn[()]
                        out = iterRef.operands[0]
                        out = out.T # undo Matlab's weird transpose when saving...
            else:
                if 'MATLAB_empty' in deref.attrs.keys(): # deal with empty arrays
                    # print('empty array')
                    # print(deref[()])
                    if 'MATLAB_class' in deref.attrs.keys():
                        # print(deref.attrs['MATLAB_class'])
                        pass
                    out = np.ndarray(0)
                    return out.T
                
                if 'MATLAB_int_decode' in deref.attrs.keys():
                    if 'MATLAB_class' in deref.attrs.keys():
                        if deref.attrs['MATLAB_class'] == b'char':
                            out = "".join([chr(ch) for ch in deref[()]])
                            return out
                        elif deref.attrs['MATLAB_class'] == b'logical':
                            pass # uint8, the default, is a fine type for logicals
                        else:
                            # print(deref.attrs['MATLAB_class'])
                            print('int decode but class not char...')
                    else:
                        print('int decode but no class?')
                
                out = deref[()]
                out = out.T # for some reason Matlab transposes when saving...
        
        return out
    
    hdf5Matfile = h5py.File(matfilePath, 'r')
    
    out = {}

    # this loop looks very similar to that in unpacking the group, but it
    # specifically ignores the #refs# key... I'm also not sure its terminal
    # condition is quite right, as I don't know if a non-structure variable
    # is saved as a Dataset at the top of the hierarchy--I assume so?
    for key in hdf5Matfile:
        if key == '#refs#':
            pass
        
        elif type(hdf5Matfile[key]) is h5py._hl.group.Group:
            out[key] = UnpackHdf5(hdf5Matfile, hdf5Matfile[key])
        elif type(hdf5Matfile[key]) is h5py._hl.dataset.Dataset:
            out[key] = UnpackHdf5(hdf5Matfile, hdf5Matfile[key])
            
    return out
 
    

def LoadMatFile(matfilePath):
    
    try:
        annots = tradLoadmat(matfilePath)
    except NotImplementedError:
        annots = LoadHdf5Mat(matfilePath)
        
    return annots

