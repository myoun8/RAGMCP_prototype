import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from model_catalog import MODEL_CATALOG, discover_models, provider_for_model


class ModelCatalogTests(unittest.TestCase):
    def response(self, entries):
        return io.BytesIO(json.dumps({"data": entries}).encode())

    def test_discovery_filters_embeddings_and_duplicates(self):
        entries = [{"id": "Muse-New"}, {"id": "embeddinggemma-300m"},
                   {"id": "Muse-New"}, {"id": "Muse-Spark"}, {"id": None}, "bad"]
        with patch("model_catalog.urlopen", return_value=self.response(entries)) as fetch:
            catalog, live = discover_models(" user-key ")
        self.assertTrue(live)
        self.assertEqual(catalog["rchat"], ["Muse-New", "Muse-Spark"])
        request = fetch.call_args.args[0]
        self.assertEqual(request.full_url, "https://rchat.nist.gov/api/v1/models")
        self.assertEqual(request.get_header("Authorization"), "Bearer user-key")
        self.assertEqual(fetch.call_args.kwargs["timeout"], 10)

    def test_no_key_uses_fallback_without_network(self):
        with patch("model_catalog.urlopen") as fetch:
            catalog, live = discover_models()
        fetch.assert_not_called()
        self.assertFalse(live)
        self.assertEqual(catalog, MODEL_CATALOG)

    def test_auth_failure_uses_fallback(self):
        with patch("model_catalog.urlopen", side_effect=HTTPError("url", 401, "Unauthorized", {}, None)):
            catalog, live = discover_models("invalid-key")
        self.assertFalse(live)
        self.assertEqual(catalog, MODEL_CATALOG)

    def test_malformed_and_empty_catalogs_use_fallback(self):
        for payload in [b"not json", b"null", b'{"data":null}', b'{"data":[]}',
                        b'{"data":[{"id":"embeddinggemma-300m"}]}']:
            with self.subTest(payload=payload):
                with patch("model_catalog.urlopen", return_value=io.BytesIO(payload)):
                    catalog, live = discover_models("key")
                self.assertFalse(live)
                self.assertEqual(catalog, MODEL_CATALOG)

    def test_user_catalogs_do_not_change_global_fallback(self):
        with patch("model_catalog.urlopen", return_value=self.response([{"id": "Private-model"}])):
            first, _ = discover_models("first-user-key")
        second, _ = discover_models()
        self.assertNotIn("Private-model", second["rchat"])
        first["openai"].clear()
        self.assertEqual(MODEL_CATALOG["openai"], ["gpt-4o"])

    def test_explicit_provider_routes_new_and_vendor_named_rchat_models(self):
        self.assertEqual(provider_for_model("Muse-New", "rchat"), "rchat")
        self.assertEqual(provider_for_model("gpt-hosted-in-rchat", "rchat"), "rchat")
        with self.assertRaises(ValueError):
            provider_for_model("Muse-New", "unknown")

    def test_legacy_requests_still_route_current_and_vendor_models(self):
        self.assertEqual(provider_for_model("Muse-Glimmer-30B"), "rchat")
        self.assertEqual(provider_for_model("gpt-4o"), "openai")
        self.assertEqual(provider_for_model("claude-new"), "anthropic")
        with self.assertRaises(ValueError):
            provider_for_model("unknown")


if __name__ == "__main__":
    unittest.main()
