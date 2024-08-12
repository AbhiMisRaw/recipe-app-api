from .calc import add, substract

from django.test import SimpleTestCase


class CalcTests(SimpleTestCase):
    """
    Test for calc module
    Mocking : Change behaviour of dependecies
    use-case : while testing like sending email when a user register for a service

    how to use mock code : unittest.mock
    ---------------------------------------------------------------------------------
    testClient : APIC lient()

    """

    def test_add_numbers(self):
        res = add(5, 6)
        self.assertEqual(res, 11)

    def test_subs_number(self):
        res = substract(10, 3)
        self.assertEqual(res, 7)
