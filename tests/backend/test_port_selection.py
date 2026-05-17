import unittest


class PortSelectionTests(unittest.TestCase):
    def test_select_first_free_port_from_range(self):
        from backend.app.port_selection import select_first_free_port

        port = select_first_free_port(
            start=3210,
            end=3212,
            is_port_available=lambda value: value == 3212,
        )

        self.assertEqual(port, 3212)


if __name__ == "__main__":
    unittest.main()
