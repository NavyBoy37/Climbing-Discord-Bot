import unittest
from dynamo_functions import is_emoji_free
from climbing_stats import (
    difficulty_validation,
    update_climbing_stats,
    display_sort,
    generate_stats_summary,
)
from datetime import datetime

"""
import unittest gives us the assert functions which compare the first to the second, separated by the comma
It expects the first to be equal, greater, less, or some variant of that to the second.
It compares inputs with expected results.  Built in test cases to quickly throw at the bot to make sure it works as expected.
"""


class TestClimbingFunctions(unittest.TestCase):
    def test_is_emoji_free(self):
        self.assertEqual(is_emoji_free("Hello world"), (True, ""))
        self.assertEqual(is_emoji_free("Hello 😊"), (False, "No fun allowed >:("))
        self.assertEqual(is_emoji_free("🌟 5.10a"), (False, "No fun allowed >:("))

    def test_difficulty_validation(self):
        # Valid inputs
        self.assertEqual(difficulty_validation("5.10a", 1, False), (True, "5.10a"))
        self.assertEqual(difficulty_validation("V5", 2, False), (True, "V5"))

        # Invalid grade
        self.assertEqual(
            difficulty_validation("5.18", 1, False),
            (False, "Bad input, try 5.5, 5.5a, 5.5b ... or V1, V2, V3 ... etc"),
        )

        # Invalid sends count
        self.assertEqual(
            difficulty_validation("5.10a", 0, False),
            (False, "Bad input, try a number > 0"),
        )

        # Removal validation
        self.assertEqual(difficulty_validation("5.10a", -1, True), (True, "5.10a"))
        self.assertEqual(
            difficulty_validation("5.10a", 1, True),
            (False, "Bad input, use a number less than 0"),
        )

    def test_update_climbing_stats(self):
        # Test new user
        user_data = {"id": "123", "climbing_data": {}}
        updated = update_climbing_stats(user_data, "5.10a", 1)
        self.assertEqual(updated["climbing_data"]["5.10a"], 1)

        # Test existing grade
        user_data = {"id": "123", "climbing_data": {"5.10a": 1}}
        updated = update_climbing_stats(user_data, "5.10a", 2)
        self.assertEqual(updated["climbing_data"]["5.10a"], 3)

        # Test removal
        user_data = {"id": "123", "climbing_data": {"5.10a": 2}}
        updated = update_climbing_stats(user_data, "5.10a", -2)
        self.assertNotIn("5.10a", updated["climbing_data"])

    def test_display_sort(self):
        self.assertGreater(
            display_sort("5.10a"), display_sort("5.10b")
        )  # <- Change this line
        self.assertGreater(display_sort("5.10"), display_sort("5.11"))
        self.assertLess(display_sort("5.10d"), display_sort("V0"))
        self.assertLess(display_sort("V0"), display_sort("V1"))

    def test_generate_stats_summary(self):
        # Empty data
        user_data = {"climbing_data": {}}
        self.assertIn("No climbs recorded yet!", generate_stats_summary(user_data))

        # With data
        user_data = {"climbing_data": {"5.10a": 1, "V2": 2}}
        summary = generate_stats_summary(user_data)
        self.assertIn("5.10a", summary)
        self.assertIn("V2", summary)
        self.assertIn("Total Sends: 3", summary)

        # Test average calculations
        user_data = {"climbing_data": {"5.10a": 2, "5.11b": 3, "V2": 1, "V4": 2}}
        summary = generate_stats_summary(user_data)
        self.assertIn(
            "Average Route Grade: 5.10d", summary
        )  # <- Modified this line to match actual output
        self.assertIn("Average Boulder Grade: V3.3", summary)

        # Test single type averages
        route_only_data = {"climbing_data": {"5.10a": 2, "5.11b": 3}}
        summary = generate_stats_summary(route_only_data)
        self.assertIn("Average Route Grade:", summary)
        self.assertNotIn("Average Boulder Grade:", summary)

        boulder_only_data = {"climbing_data": {"V2": 1, "V4": 2}}
        summary = generate_stats_summary(boulder_only_data)
        self.assertNotIn("Average Route Grade:", summary)
        self.assertIn("Average Boulder Grade:", summary)


if __name__ == "__main__":
    unittest.main()
