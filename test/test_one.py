import unittest

def add(arg1,arg2):
		return arg1+arg2
		
class India(unittest.TestCase):
    
    def test_add(self):
        self.assertEqual(5,add(2,3))

