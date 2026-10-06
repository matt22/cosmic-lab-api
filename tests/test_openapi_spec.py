import json
import re
import unittest
from pathlib import Path

from src import airports_api, books_api, cities_api, incidents_api, movies_api
from src import offshore_oil_fields_api

SRC = Path(__file__).resolve().parent.parent / "src"

# Each path's (module, loader, query function) so the spec can be checked
# against real responses without the Workers runtime.
ENDPOINTS = {
    "/api/v1/airports": (airports_api, airports_api.load_airports, airports_api.query_airports),
    "/api/v1/cities": (cities_api, cities_api.load_cities, cities_api.query_cities),
    "/api/v1/books": (books_api, books_api.load_books, books_api.query_books),
    "/api/v1/movies": (movies_api, movies_api.load_movies, movies_api.query_movies),
    "/api/v1/incidents": (incidents_api, incidents_api.load_incidents, incidents_api.query_incidents),
    "/api/v1/offshore-oil-fields": (
        offshore_oil_fields_api,
        offshore_oil_fields_api.load_offshore_oil_fields,
        offshore_oil_fields_api.query_offshore_oil_fields,
    ),
}

JSON_TYPES = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "null": (type(None),),
}


class OpenApiSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((SRC / "openapi.json").read_text(encoding="utf-8"))

    def resolve(self, schema):
        while "$ref" in schema:
            node = self.spec
            for part in schema["$ref"].removeprefix("#/").split("/"):
                node = node[part]
            schema = {**node, **{k: v for k, v in schema.items() if k != "$ref"}}
        return schema

    def assert_matches(self, value, schema, where):
        """Check value against the subset of JSON Schema the spec uses."""
        schema = self.resolve(schema)
        for part in schema.get("allOf", []):
            self.assert_matches(value, part, where)
        types = schema.get("type")
        if types:
            types = [types] if isinstance(types, str) else types
            python_types = tuple(t for name in types for t in JSON_TYPES[name])
            self.assertIsInstance(value, python_types, where)
            self.assertFalse(isinstance(value, bool), where)
        if "enum" in schema:
            self.assertIn(value, schema["enum"], where)
        if isinstance(value, dict):
            for key in schema.get("required", []):
                self.assertIn(key, value, f"{where}: missing {key}")
            properties = schema.get("properties", {})
            if properties and "required" in schema:
                self.assertEqual(set(value), set(properties), f"{where}: undocumented keys")
            for key, sub in properties.items():
                if key in value:
                    self.assert_matches(value[key], sub, f"{where}.{key}")
        if isinstance(value, list) and "items" in schema:
            for index, item in enumerate(value):
                self.assert_matches(item, schema["items"], f"{where}[{index}]")

    def test_every_ref_resolves(self):
        refs = re.findall(r'"\$ref": "([^"]+)"', json.dumps(self.spec))
        self.assertTrue(refs)
        for ref in refs:
            self.resolve({"$ref": ref})

    def test_spec_paths_match_worker_routes(self):
        worker_source = (SRC / "worker.py").read_text(encoding="utf-8")
        routes = set(re.findall(r'"(/api/v1/[\w-]+)"', worker_source))
        self.assertEqual(set(self.spec["paths"]), routes)
        self.assertEqual(set(ENDPOINTS), routes)

    def test_documented_parameters_match_validation(self):
        for path, (module, _, _) in ENDPOINTS.items():
            parameters = [self.resolve(p) for p in self.spec["paths"][path]["get"]["parameters"]]
            required = [p for p in parameters if p["required"]]
            self.assertEqual(len(required), 1, path)
            name, example = required[0]["name"], required[0]["example"]
            self.assertEqual({p["name"] for p in parameters}, {name, "page"}, path)

            self.assertEqual(module.parse_query({name: [example]})[1], 1, path)
            with self.assertRaises(ValueError, msg=path):
                module.parse_query({})
            with self.assertRaises(ValueError, msg=path):
                module.parse_query({name: [example], "page": ["0"]})
            with self.assertRaises(ValueError, msg=path):
                module.parse_query({name: [example], "extra": ["1"]})

    def test_example_responses_match_schemas(self):
        for path, (module, load, query) in ENDPOINTS.items():
            operation = self.spec["paths"][path]["get"]
            required = next(self.resolve(p) for p in operation["parameters"] if p.get("required"))
            value, page = module.parse_query({required["name"]: [required["example"]]})
            response = query(load(), value, page)
            self.assertTrue(response["data"], f"{path} example returns no records")
            schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
            self.assert_matches(response, schema, path)

    def test_every_record_matches_its_schema(self):
        # Catches nullable or odd values that the example page might not contain.
        for path, (module, load, query) in ENDPOINTS.items():
            schema = self.resolve(self.spec["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"])
            item_schema = schema["allOf"][1]["properties"]["data"]["items"]
            records = load()
            if module in (airports_api, cities_api):
                serialize = getattr(module, "serialize_airport", None) or module.serialize_city
                records = [serialize(record) for record in records]
            for record in records:
                self.assert_matches(record, item_schema, f"{path} id={record['id']}")


if __name__ == "__main__":
    unittest.main()
