import unittest
from unittest.mock import patch, Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from snapshot import get_wayback_snapshot
from main import determine_status

class TestCore(unittest.TestCase):
    
    @patch('snapshot.requests.get')
    def test_staleness_logic(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "url": "http://web.archive.org/web/20220101120000/https://example.com",
                    "timestamp": "20220101120000"
                }
            }
        }
        mock_get.return_value = mock_response
        
        insertion_date = "2020-01-01T12:00:00Z"
        result = get_wayback_snapshot("https://example.com", insertion_date)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['is_stale'])
        self.assertGreater(result['gap_days'], 365)
        
    def test_determine_status(self):
        self.assertEqual(determine_status({'error': True}), "API ERROR")
        
        self.assertEqual(
            determine_status({'archived_supports_claim': True, 'live_supports_claim': True}), 
            "VERIFIED"
        )
        self.assertEqual(
            determine_status({'archived_supports_claim': True, 'live_supports_claim': False}), 
            "DRIFT DETECTED"
        )
        self.assertEqual(
            determine_status({'archived_supports_claim': False, 'live_supports_claim': False}), 
            "ORIGINALLY INVALID"
        )
        self.assertEqual(
            determine_status({'archived_supports_claim': False, 'live_supports_claim': True}), 
            "NEWLY SUPPORTED"
        )

if __name__ == '__main__':
    unittest.main()
