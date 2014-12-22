#!/usr/bin/env python

"""
Run from the directory above with: 'nosetests tests' or 'nosetests
tests/test_umfile.py'
"""

import os
import shutil
import numpy as np

import umfile

class TestUMFile():

    def __init__(self):
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.restart_dump = os.path.join(self.my_path, 'inputs',
                                         'restart_dump.astart')

    def test_dump_exists(self):
        """
        Check that the dump file needed for testing exists.
        """

        assert(os.path.exists(self.restart_dump))


    def test_open(self):
        """
        Open file and check a field.
        """

        f = umfile.UMFile(self.restart_dump)
        assert(len(f.fields) > 0)
        assert(f.fields[2].__str__() == 'U COMPNT OF WIND AFTER TIMESTEP')


    def test_array_read(self):
        """
        Read data using array syntax.
        """

        f = umfile.UMFile(self.restart_dump)

        u_wnd = f.fields[2][:]
        assert(u_wnd.shape == (145, 192))
        assert(np.mean(u_wnd) > -0.1 and np.mean(u_wnd) < 0)


    def test_array_write(self):
        """
        Write data using array syntax.
        """

        f = umfile.UMFile(self.restart_dump)

        assert(np.sum(f.fields[2][:]) != 0)
        f.fields[2][:] = 0
        assert(np.sum(f.fields[2][:]) == 0)


    def test_close(self):
        """
        Modify data and check that changes are written out. 
        """

        # First make a copy of the test file. 

        restart_dump_copy = self.restart_dump + '.copy'
        shutil.copyfile(self.restart_dump, restart_dump_copy) 

        f = umfile.UMFile(restart_dump_copy, 'r+')

        assert(np.sum(f.fields[2][:]) != 0)
        f.fields[2][:] = 0
        assert(np.sum(f.fields[2][:]) == 0)

        f.close()

        f = umfile.UMFile(restart_dump_copy)
        assert(np.sum(f.fields[2][:]) == 0)

        os.remove(restart_dump_copy)


