"""
Test for TES API v2.0.0 support in seed_terminology_db.py
"""
import json
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add the refiner directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "refiner"))

from scripts.seed_terminology_db import TESDataLoader, CodeableConcept


class TestTESDataLoaderV2(unittest.TestCase):
    """Test TES Data Loader v2.0.0 functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'TES_API_URL': 'https://test-api.example.com',
            'TES_API_KEY': 'test-key',
            'API_SLEEP_INTERVAL': '0.1'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test fixtures"""
        Path(self.test_db.name).unlink(missing_ok=True)
        self.env_patcher.stop()

    def test_v1_filtering_logic(self):
        """Test that v1.0.0 filtering logic still works"""
        loader = TESDataLoader(self.test_db.name, api_version="1.0.0")
        
        # v1.0.0 resource with rs-grouper prefix
        v1_resource = {
            "id": "rs-grouper-66071002",
            "compose": {"include": []},
            "title": "Hepatitis B"
        }
        
        # v1.0.0 resource without rs-grouper prefix
        non_grouper = {
            "id": "some-other-valueset",
            "compose": {"include": []},
            "title": "Not a grouper"
        }
        
        self.assertTrue(loader.is_relevant_grouper(v1_resource))
        self.assertFalse(loader.is_relevant_grouper(non_grouper))
        
        # Test condition extraction
        condition = loader.extract_condition_from_resource(v1_resource)
        self.assertEqual(condition, "66071002")

    def test_v2_filtering_logic(self):
        """Test v2.0.0 filtering logic with useContext"""
        loader = TESDataLoader(self.test_db.name, api_version="2.0.0")
        
        # v2.0.0 main grouper
        v2_main_grouper = {
            "id": "1995",
            "compose": {"include": []},
            "title": "Hepatitis B Main Grouper",
            "useContext": [
                {
                    "code": {"code": "focus"},
                    "valueCodeableConcept": {
                        "coding": [{"system": "http://snomed.info/sct", "code": "66071002"}]
                    }
                },
                {
                    "code": {"code": "task"},
                    "valueCodeableConcept": {
                        "coding": [{"code": "condition-grouper"}]
                    }
                }
            ]
        }
        
        # v2.0.0 additional context grouper
        v2_additional_grouper = {
            "id": "1996",
            "compose": {"include": []},
            "title": "Hepatitis_B_Additional_Context_Lab_Codes",
            "useContext": [
                {
                    "code": {"code": "focus"},
                    "valueCodeableConcept": {
                        "coding": [{"system": "http://snomed.info/sct", "code": "66071002"}]
                    }
                },
                {
                    "code": {"code": "task"},
                    "valueCodeableConcept": {
                        "coding": [{"code": "additional-context-grouper"}]
                    }
                }
            ]
        }
        
        # Non-relevant resource
        non_grouper = {
            "id": "2000",
            "compose": {"include": []},
            "title": "Some other ValueSet",
            "useContext": [
                {
                    "code": {"code": "task"},
                    "valueCodeableConcept": {
                        "coding": [{"code": "some-other-purpose"}]
                    }
                }
            ]
        }
        
        self.assertTrue(loader.is_relevant_grouper(v2_main_grouper))
        self.assertTrue(loader.is_relevant_grouper(v2_additional_grouper))
        self.assertFalse(loader.is_relevant_grouper(non_grouper))
        
        # Test condition extraction
        condition1 = loader.extract_condition_from_resource(v2_main_grouper)
        condition2 = loader.extract_condition_from_resource(v2_additional_grouper)
        self.assertEqual(condition1, "66071002")
        self.assertEqual(condition2, "66071002")

    def test_extract_codes_v2_with_valueset_references(self):
        """Test code extraction with ValueSet references (v2.0.0 main groupers)"""
        loader = TESDataLoader(self.test_db.name, api_version="2.0.0")
        
        resource_with_valuesets = {
            "compose": {
                "include": [
                    {
                        "valueSet": [
                            "https://example.com/ValueSet/hepatitis-b-loinc-codes",
                            "https://example.com/ValueSet/hepatitis-b-snomed-codes"
                        ]
                    }
                ]
            }
        }
        
        # Should return empty codes but not crash
        codes = loader.extract_codes(resource_with_valuesets)
        self.assertEqual(codes["loinc"], [])
        self.assertEqual(codes["snomed"], [])

    def test_extract_codes_v2_with_direct_concepts(self):
        """Test code extraction with direct concepts (v2.0.0 additional context groupers)"""
        loader = TESDataLoader(self.test_db.name, api_version="2.0.0")
        
        resource_with_concepts = {
            "compose": {
                "include": [
                    {
                        "system": "http://loinc.org",
                        "concept": [
                            {"code": "5195-3", "display": "Hepatitis B virus surface antigen"},
                            {"code": "16933-4", "display": "Hepatitis B virus DNA"}
                        ]
                    },
                    {
                        "system": "http://snomed.info/sct",
                        "concept": [
                            {"code": "66071002", "display": "Viral hepatitis type B"}
                        ]
                    }
                ]
            }
        }
        
        codes = loader.extract_codes(resource_with_concepts)
        
        self.assertEqual(len(codes["loinc"]), 2)
        self.assertEqual(len(codes["snomed"]), 1)
        self.assertEqual(codes["loinc"][0].code, "5195-3")
        self.assertEqual(codes["snomed"][0].code, "66071002")

    @patch('scripts.seed_terminology_db.requests.get')
    def test_api_version_parameter_in_requests(self, mock_get):
        """Test that version parameter is added to API requests for v2.0.0+"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"entry": []}
        mock_get.return_value = mock_response
        
        loader = TESDataLoader(self.test_db.name, api_version="2.0.0")
        loader.make_tes_request("ValueSet", {"status": "active"})
        
        # Check that version parameter was added
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['version'], "2.0.0")
        self.assertEqual(params['status'], "active")

    @patch('scripts.seed_terminology_db.requests.get')
    def test_v1_no_version_parameter(self, mock_get):
        """Test that no version parameter is added for v1.0.0"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"entry": []}
        mock_get.return_value = mock_response
        
        loader = TESDataLoader(self.test_db.name, api_version="1.0.0")
        loader.make_tes_request("ValueSet", {"status": "active"})
        
        # Check that version parameter was NOT added
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertNotIn('version', params)
        self.assertEqual(params['status'], "active")


if __name__ == '__main__':
    unittest.main()