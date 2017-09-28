from pelican_html import PelicanParser
from pelican_html import load_settings
import unittest

class TestTest(unittest.TestCase):
    def test_test(self):
        parser = PelicanParser('hurricanes.html')
        parser.read_html()
        parser.to_md()
        
if __name__ == '__main__':
    x = load_settings('C:/Users/vince/Documents/GitHub/pelican-html/tests')
    unittest.main()