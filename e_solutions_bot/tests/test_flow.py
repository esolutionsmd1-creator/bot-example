"""
Teste automate pentru fluxul de stoc și comenzi (cerința #25).
Rulare: python tests/test_flow.py
Nu necesită Telegram/aiogram - testează direct logica de business,
pe o bază de date SQLite temporară.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

import database
from services import product_service, cart_service, order_service


class StockFlowTests(unittest.TestCase):
    def setUp(self):
        # bază de date nouă, izolată, pentru fiecare test
        config.DB_PATH = os.path.join(tempfile.mkdtemp(), "test_shop.db")
        database.init_db()
        self.hoodie = next(p for p in product_service.get_all_products() if p["name"] == "Nike Hoodie")
        self.user_id = 111111

    def tearDown(self):
        cart_service.clear_cart(self.user_id)

    def test_1_stock_scade_dupa_comanda(self):
        # stock 5 -> comandă 2 -> stock 3
        cart_service.add_to_cart(self.user_id, self.hoodie["id"], 2)
        ok, order = order_service.create_order(self.user_id, "Ion Popescu", "060000000", "Chișinău")
        self.assertTrue(ok, order)
        self.assertEqual(product_service.get_product(self.hoodie["id"])["stock"], 3)

    def test_2_refuz_daca_stock_insuficient(self):
        product_service.update_stock(self.hoodie["id"], 2)
        ok, msg = cart_service.add_to_cart(self.user_id, self.hoodie["id"], 3)
        self.assertFalse(ok)
        self.assertEqual(product_service.get_product(self.hoodie["id"])["stock"], 2)

    def test_3_fara_oversell_doi_clienti(self):
        product_service.update_stock(self.hoodie["id"], 1)
        user_a, user_b = 222222, 333333
        cart_service.add_to_cart(user_a, self.hoodie["id"], 1)
        cart_service.add_to_cart(user_b, self.hoodie["id"], 1)

        ok_a, _ = order_service.create_order(user_a, "Client A", "060000001", "Chișinău")
        ok_b, _ = order_service.create_order(user_b, "Client B", "060000002", "Chișinău")

        self.assertNotEqual(ok_a, ok_b)  # doar UNA din comenzi reușește
        self.assertEqual(product_service.get_product(self.hoodie["id"])["stock"], 0)
        cart_service.clear_cart(user_a)
        cart_service.clear_cart(user_b)

    def test_4_anulare_nu_schimba_stock(self):
        initial_stock = product_service.get_product(self.hoodie["id"])["stock"]
        cart_service.add_to_cart(self.user_id, self.hoodie["id"], 1)
        cart_service.clear_cart(self.user_id)  # echivalent cu "Anulează" înainte de confirmare
        self.assertEqual(product_service.get_product(self.hoodie["id"])["stock"], initial_stock)

    def test_5_cos_gol_dupa_comanda_confirmata(self):
        cart_service.add_to_cart(self.user_id, self.hoodie["id"], 1)
        ok, order = order_service.create_order(self.user_id, "Ion Popescu", "060000000", "Chișinău")
        self.assertTrue(ok, order)
        self.assertEqual(cart_service.get_cart_items(self.user_id), [])

    def test_6_admin_schimba_stock_vizibil_pentru_client(self):
        product_service.update_stock(self.hoodie["id"], 42)
        self.assertEqual(product_service.get_product(self.hoodie["id"])["stock"], 42)

    def test_7_produs_inactiv_nu_poate_fi_comandat(self):
        product_service.toggle_active(self.hoodie["id"])
        ok, msg = cart_service.add_to_cart(self.user_id, self.hoodie["id"], 1)
        self.assertFalse(ok)
        product_service.toggle_active(self.hoodie["id"])  # revert


if __name__ == "__main__":
    unittest.main(verbosity=2)
