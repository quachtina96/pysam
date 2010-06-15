#!/usr/bin/env python
'''unit testing code for pysam.

Execute in the :file:`tests` directory as it requires the Makefile
and data files located there.
'''

import sys, os, shutil, gzip
import pysam
import unittest
import itertools
import subprocess

def checkBinaryEqual( filename1, filename2 ):
    '''return true if the two files are binary equal.'''
    if os.path.getsize( filename1 ) !=  os.path.getsize( filename2 ):
        return False

    infile1 = open(filename1, "rb")
    infile2 = open(filename2, "rb")

    def chariter( infile ):
        while 1:
            c = infile.read(1)
            if c == "": break
            yield c

    found = False
    for c1,c2 in itertools.izip( chariter( infile1), chariter( infile2) ):
        if c1 != c2: break
    else:
        found = True

    infile1.close()
    infile2.close()
    return found

class TestIndexing(unittest.TestCase):
    filename = "example.gtf.gz" 
    filename_idx = "example.gtf.gz.tbi" 

    def setUp( self ):
        
        self.tmpfilename = "tmp_%i.gtf.gz" % id(self)
        shutil.copyfile( self.filename, self.tmpfilename )

    def testIndexPreset( self ):
        '''test indexing via preset.'''

        pysam.tabix_index( self.tmpfilename, preset = "gff" )
        checkBinaryEqual( self.tmpfilename + ".tbi", self.filename_idx )

    def tearDown( self ):
        os.unlink( self.tmpfilename )
        os.unlink( self.tmpfilename + ".tbi" )

class TestIteration( unittest.TestCase ):

    filename = "example.gtf.gz" 

    def setUp( self ):

        self.tabix = pysam.Tabixfile( self.filename )
        lines = gzip.open(self.filename).readlines()
        # creates index of contig, start, end, adds content without newline.
        self.compare = [ 
            (x[0][0], int(x[0][3]), int(x[0][4]),x[1]) 
            for x in [ (y.split("\t"), y[:-1]) for y in lines ] ]
                         
    def getSubset( self, contig = None, start = None, end = None):
        
        if contig == None:
            # all lines
            subset = [ x[3] for x in self.compare ]
        else:
            if start != None and end == None:
                # until end of contig
                subset = [ x[3] for x in self.compare if x[0] == contig and x[2] > start ]
            elif start == None and end != None:
                # from start of contig
                subset = [ x[3] for x in self.compare if x[0] == contig and x[1] <= end ]
            else:
                # all within contig
                subset = [ x[3] for x in self.compare if x[0] == contig ]
            
        return subset

    def checkPairwise( self, result, ref ):

        self.assertEqual( len(result), len(ref),
                          "unexpected number of results: %i, expected %i" % (len(result), len(ref) ) )

        for x, d in enumerate( zip( result, ref )):
            
            self.assertEqual( d[0], d[1],
                              "unexpected results in pair %i: '%s', expected '%s'" % \
                                  (x, 
                                   d[0], 
                                   d[1]) )


    def testAll( self ):
        result = list(self.tabix.fetch())
        ref = self.getSubset( )
        self.checkPairwise( result, ref )

    def testPerContig( self ):
        for contig in ("chr1", "chr2", "chr1", "chr2" ):
            result = list(self.tabix.fetch( contig ))
            ref = self.getSubset( contig )
            self.checkPairwise( result, ref )

    def testPerContigToEnd( self ):
        
        for contig in ("chr1", "chr2", "chr1", "chr2" ):
            for start in range( 0, 200000, 1000):
                result = list(self.tabix.fetch( contig, start ))
                ref = self.getSubset( contig, start )
                self.checkPairwise( result, ref )
                
# tabixfile = 

# print "##########"
# for l in tabixfile.fetch("chr2", 28814, 28900):
#     print l

# print "##########"

# for l in tabixfile.fetch():
#     print l

if __name__ == "__main__":
    unittest.main()


