import time

from enum import Enum


class OrderType(Enum):
    LIMIT = 1
    MARKET = 2
    IOC = 3


class OrderSide(Enum):
    BUY = 1
    SELL = 2


class NonPositiveQuantity(Exception):
    pass


class NonPositivePrice(Exception):
    pass


class InvalidSide(Exception):
    pass


class UndefinedOrderType(Exception):
    pass


class UndefinedOrderSide(Exception):
    pass


class NewQuantityNotSmaller(Exception):
    pass


class UndefinedTraderAction(Exception):
    pass


class UndefinedResponse(Exception):
    pass


from abc import ABC


class Order(ABC):
    def __init__(self, id, symbol, quantity, side, time):
        self.id = id
        self.symbol = symbol
        if quantity > 0:
            self.quantity = quantity
        else:
            raise NonPositiveQuantity("Quantity Must Be Positive!")
        if side in [OrderSide.BUY, OrderSide.SELL]:
            self.side = side
        else:
            raise InvalidSide("Side Must Be Either \"Buy\" or \"OrderSide.SELL\"!")
        self.time = time


class LimitOrder(Order):
    def __init__(self, id, symbol, quantity, price, side, time):
        super().__init__(id, symbol, quantity, side, time)
        if price > 0:
            self.price = price
        else:
            raise NonPositivePrice("Price Must Be Positive!")
        self.type = OrderType.LIMIT


class MarketOrder(Order):
    def __init__(self, id, symbol, quantity, side, time):
        super().__init__(id, symbol, quantity, side, time)
        self.type = OrderType.MARKET


class IOCOrder(Order):
    def __init__(self, id, symbol, quantity, price, side, time):
        super().__init__(id, symbol, quantity, side, time)
        if price > 0:
            self.price = price
        else:
            raise NonPositivePrice("Price Must Be Positive!")
        self.type = OrderType.IOC


class FilledOrder(Order):
    def __init__(self, id, symbol, quantity, price, side, time, limit=False):
        super().__init__(id, symbol, quantity, side, time)
        self.price = price
        self.limit = limit


from collections import deque


class MatchingEngine():
    def __init__(self):
        self.bid_book = []
        self.ask_book = []
        # These are the order books you are given and expected to use for matching the orders below

    # Note: As you implement the following functions keep in mind that these enums are available:
    #     class OrderType(Enum):
    #         LIMIT = 1
    #         MARKET = 2
    #         IOC = 3

    #     class OrderSide(Enum):
    #         BUY = 1
    #         SELL = 2
    def remove(self, order):
        if order.side == OrderSide.BUY:
            self.bid_book.remove(order)
        elif order.side == OrderSide.sell:
            self.ask_book.remove(order)

    def handle_order(self, order):
        if order.type == OrderType.LIMIT:
            self.handle_limit_order(order)
            print('limit order handled')
        elif order.type == OrderType.MARKET:
            self.handle_market_order(order)
        elif order.type == OrderType.IOC:
            self.handle_ioc_order(order)
        else:
            # Implement this function
            # In this function you need to call different functions from the matching engine
            # depending on the type of order you are given

            # You need to raise the following error if the type of order is ambiguous
            raise UndefinedOrderType("Undefined Order Type!")

    def handle_limit_order(self, order):
        filled_orders = []
        # The orders that are filled from the market order need to be inserted into the above list
        if order.side == OrderSide.BUY:
            consumed_asks = []
            for item in self.ask_book:
                if order.price < item.price or order.quantity == 0:
                    break
                else:
                    if order.quantity == item.quantity:
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        consumed_asks.append(item)
                        order.quantity = 0

                    elif order.quantity < item.quantity:
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                   item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        order.quantity = 0
                        break

                    else:
                        order.quantity -= item.quantity
                        fulfilled_order = FilledOrder(order.id, order.symbol, item.quantity, order.price, order.side,
                                                     order.time)
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(fulfilled_order)
                        consumed_asks.append(item)

            for item2 in consumed_asks:
                self.remove(item2)
            if order.quantity != 0:
                self.insert_limit_order(order)

        elif order.side == OrderSide.SELL:
            consumed_bids = []
            for item in self.bid_book:
                if order.price > item.price or order.quantity == 0:
                    break
                else:
                    if order.quantity == item.quantity:
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        consumed_bids.append(item)
                        order.quantity = 0
                    elif order.quantity < item.quantity:
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                   item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                   order.time))
                        order.quantity = 0
                        break
                    else:
                        order.quantity -= item.quantity
                        fulfilled_order = FilledOrder(order.id, order.symbol, item.quantity, order.price, order.side,
                                                   order.time)
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(fulfilled_order)
                        consumed_bids.append(item)

            for item2 in consumed_bids:
                self.remove(item2)

            if order.quantity != 0:
                self.insert_limit_order(order)

        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
        else:
            # You need to raise the following error if the side the order is for is ambiguous
            raise UndefinedOrderSide("Undefined Order Side!")
        # The filled orders are expected to be the return variable (list)
        return filled_orders

    def handle_market_order(self, order):
        # Implement this function
        filled_orders = []
        # The orders that are filled from the market order need to be inserted into the above list
        if order.side == OrderSide.BUY:
            consumed_asks = []
            for item in self.ask_book:  # should really use while loop here for true functionality
                if order.quantity == 0:
                    break
                if order.quantity == item.quantity:
                    filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                     item.time))
                    filled_orders.append(LimitOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                    order.time))
                    consumed_asks.append(item)
                    order.quantity = 0
                    break
                elif order.quantity < item.quantity:
                    partial_order = LimitOrder(item.id, item.symbol, order.quantity, item.price, item.side, item.time)
                    item.quantity -= order.quantity
                    filled_orders.append(partial_order)
                    filled_orders.append(LimitOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                    order.time))
                    order.quantity = 0
                    break
                else:
                    order.quantity -= item.quantity
                    fulfilled_order = LimitOrder(order.id, order.symbol, item.quantity, order.price, order.side,
                                                 order.time)
                    filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                     item.time))
                    filled_orders.append(fulfilled_order)
                    consumed_asks.append(item)

            for item2 in consumed_asks:
                self.remove(item2)

            if order.quantity != 0:
                self.insert_market_order(order)

        elif order.side == OrderSide.SELL:
            consumed_bids = []
            for item in self.bid_book:
                if order.quantity == 0:
                    break
                if order.quantity == item.quantity:
                    filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                     item.time))
                    filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                     order.time))
                    consumed_bids.append(item)
                    order.quantity = 0
                    break
                elif order.quantity < item.quantity:

                    partial_order = LimitOrder(item.id, item.symbol, order.quantity, item.price, item.side, item.time)
                    item.quantity -= order.quantity
                    filled_orders.append(partial_order)
                    filled_orders.append(
                        LimitOrder(order.id, order.symbol, order.quantity, item.price, order.side, order.time))
                    order.quantity = 0
                    break
                else:
                    order.quantity -= item.quantity
                    fulfilled_order = FilledOrder(order.id, order.symbol, item.quantity, item.price, order.side,
                                                  order.time)
                    filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                     item.time))
                    filled_orders.append(fulfilled_order)
                    consumed_bids.append(item)
            for item2 in consumed_bids:
                self.remove(item2)

            if order.quantity != 0:
                self.insert_market_order(order)
                # should create new insert_market_order functionality, which takes in the price as well
        else:
            raise UndefinedOrderSide("Undefined Order Side!")
        # The filled orders are expected to be the return variable (list)
        return filled_orders

    def handle_ioc_order(self, order):
        filled_orders = []
        if order.side == OrderSide.BUY:
            consumed_asks = []
            for item in self.ask_book:
                if order.price < item.price or order.quantity == 0:
                    break
                else:
                    if order.quantity == item.quantity:
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(LimitOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        consumed_asks.append(item)
                        order.quantity = 0
                        # order gets filled, pop from ask book
                        # self.bid_book.pop(key = lambda x: x.id == order.id)
                    elif order.quantity < item.quantity:
                        # filled_orders.append(item)
                        # item.quantity -= order.quantity
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                   item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        order.quantity = 0
                        break
                        # order gets filled, pop from ask book
                        # self.bid_book.pop(key = lambda x: x.id == order.id)
                    else:
                        order.quantity -= item.quantity
                        fulfilled_order = FilledOrder(order.id, order.symbol, item.quantity, order.price, order.side,
                                                     order.time)
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(fulfilled_order)
                        consumed_asks.append(item)
            for item2 in consumed_asks:
                self.remove(item2)

            # if order.quantity != 0:
            #     self.insert_limit_order(order)

        elif order.side == OrderSide.SELL:
            consumed_bids = []
            for item in self.bid_book:
                if order.price > item.price or order.quantity == 0:
                    break
                else:
                    if order.quantity == item.quantity:
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        consumed_bids.append(item)
                        order.quantity = 0
                        break
                        # order gets filled, pop from bid book
                        # self.bid_book.pop(key = lambda x: x.id == order.id)
                    elif order.quantity < item.quantity:
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                   item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                                        order.time))
                        order.quantity = 0
                        break
                        # order gets filled, pop from ask book
                        # self.bid_book.pop(key = lambda x: x.id == order.id)
                    else:
                        order.quantity -= item.quantity
                        fulfilled_order = FilledOrder(order.id, order.symbol, item.quantity, order.price, order.side,
                                                     order.time)
                        filled_orders.append(FilledOrder(item.id, item.symbol, item.quantity, item.price, item.side,
                                                        item.time))
                        filled_orders.append(fulfilled_order)
                        consumed_bids.append(item)
            for item2 in consumed_bids:
                self.remove(item2)
            return filled_orders

    def insert_limit_order(self, order):
        assert order.type == OrderType.LIMIT
        if order.side == OrderSide.BUY:
            self.bid_book.append(order)
            self.bid_book.sort(key=lambda x: x.price, reverse=True)
        elif order.side == OrderSide.SELL:
            self.ask_book.append(order)
            self.ask_book.sort(key=lambda x: x.price)
        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
        else:
            # You need to raise the following error if the side the order is for is ambiguous
            raise UndefinedOrderSide("Undefined Order Side!")

        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
    def insert_market_order(self, order):
        # assert order.type == OrderType.MARKET
        if order.side == OrderSide.BUY:
            self.bid_book.append(order)
            self.bid_book.sort(key=lambda x: x.price, reverse=True)
        elif order.side == OrderSide.SELL:
            self.ask_book.append(order)
            # self.ask_book.sort(key=lambda x: x.price)
        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
        else:
            # You need to raise the following error if the side the order is for is ambiguous
            raise UndefinedOrderSide("Undefined Order Side!")


    def amend_quantity(self, id, quantity):
        # Implement this function
        # Hint: Remember that there are two order books, one on the bid side and one on the ask side
        switch = 0
        for item in self.ask_book:
            if item.id == id:
                if item.quantity > quantity:
                    item.quantity = quantity
                    switch = 1
                    break
                else:
                    raise NewQuantityNotSmaller("Amendment Must Reduce Quantity!")
        if switch == 0:
            for item in self.bid_book:
                if item.id == id:
                    if item.quantity > quantity:
                        item.quantity = quantity
                        break
                    else:
                        raise NewQuantityNotSmaller("Amendment Must Reduce Quantity!")
        # You need to raise the following error if the user attempts to modify an order
        # with a quantity that's greater than given in the existing order
        return False

    def cancel_order(self, id):
        # Implement this function
        # Think about the changes you need to make in the order book based on the parameters given
        switch = 0

        for item in self.ask_book:
            if item.id == id:
                cancelled_order = item
                switch = 1
                break
        if switch == 0:
            for item in self.bid_book:
                if item.id == id:
                    cancelled_order = item
                    break
        self.remove(cancelled_order)


        # You need to raise the following error if the user attempts to modify an order
        # with a quantity that's greater than given in the existing order
        return False


import unittest


class TestOrderBook(unittest.TestCase):

    def test_handle_limit_order2(self):
        # implement this unittest and three more
        matching_engine = MatchingEngine()
        order = LimitOrder(1, "S", 10, 10, OrderSide.BUY, time.time())
        matching_engine.insert_limit_order(order)

        order_1 = LimitOrder(2, "S", 5, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(3, "S", 10, 15, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        self.assertEqual(matching_engine.bid_book[0].price, 15)
        self.assertEqual(matching_engine.bid_book[1].quantity, 10)

        order_sell = LimitOrder(4, "S", 14, 8, OrderSide.SELL, time.time())
        filled_orders = matching_engine.handle_limit_order(order_sell)

        self.assertEqual(matching_engine.bid_book[0].quantity, 6)
        self.assertEqual(filled_orders[0].id, 3)
        self.assertEqual(filled_orders[0].price, 15)
        self.assertEqual(filled_orders[2].id, 1)
        self.assertEqual(filled_orders[2].quantity, 4)
        self.assertEqual(filled_orders[2].price, 10)


    def test_insert_limit_order(self):
        matching_engine = MatchingEngine()
        order = LimitOrder(1, "S", 10, 10, OrderSide.BUY, time.time())
        matching_engine.insert_limit_order(order)

        self.assertEqual(matching_engine.bid_book[0].quantity, 10)
        self.assertEqual(matching_engine.bid_book[0].price, 10)

    def test_handle_limit_order(self):
        matching_engine = MatchingEngine()
        order = LimitOrder(1, "S", 10, 10, OrderSide.BUY, time.time())
        matching_engine.insert_limit_order(order)

        order_1 = LimitOrder(2, "S", 5, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(3, "S", 10, 15, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        self.assertEqual(matching_engine.bid_book[0].price, 15)
        self.assertEqual(matching_engine.bid_book[1].quantity, 10)

        order_sell = LimitOrder(4, "S", 14, 8, OrderSide.SELL, time.time())
        filled_orders = matching_engine.handle_limit_order(order_sell)

        self.assertEqual(matching_engine.bid_book[0].quantity, 6)
        self.assertEqual(filled_orders[0].id, 3)
        self.assertEqual(filled_orders[0].price, 15)
        self.assertEqual(filled_orders[2].id, 1)
        self.assertEqual(filled_orders[2].quantity, 4)
        self.assertEqual(filled_orders[2].price, 10)



    def test_handle_market_order(self):
        matching_engine = MatchingEngine()
        order_1 = LimitOrder(1, "S", 6, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(2, "S", 5, 10, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        order = MarketOrder(5, "S", 5, OrderSide.SELL, time.time())
        filled_orders = matching_engine.handle_market_order(order)
        self.assertEqual(matching_engine.bid_book[0].quantity, 1)
        self.assertEqual(filled_orders[0].price, 10)

    def test_handle_ioc_order(self):
        matching_engine = MatchingEngine()
        order_1 = LimitOrder(1, "S", 1, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(2, "S", 5, 10, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        order = IOCOrder(6, "S", 5, 12, OrderSide.SELL, time.time())
        filled_orders = matching_engine.handle_ioc_order(order)
        self.assertEqual(matching_engine.bid_book[0].quantity, 1)
        self.assertEqual(len(filled_orders), 0)

    def test_amend_quantity(self):
        matching_engine = MatchingEngine()
        order_1 = LimitOrder(1, "S", 5, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(2, "S", 10, 15, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        matching_engine.amend_quantity(2, 8)
        self.assertEqual(matching_engine.bid_book[0].quantity, 8)

    def test_cancel_order(self):
        matching_engine = MatchingEngine()
        order_1 = LimitOrder(1, "S", 5, 10, OrderSide.BUY, time.time())
        order_2 = LimitOrder(2, "S", 10, 15, OrderSide.BUY, time.time())
        matching_engine.handle_limit_order(order_1)
        matching_engine.handle_limit_order(order_2)

        matching_engine.cancel_order(1)
        self.assertEqual(matching_engine.bid_book[0].id, 2)
        self.assertEqual(len(matching_engine.bid_book), 1)

import io
import __main__

suite = unittest.TestLoader().loadTestsFromModule(__main__)
buf = io.StringIO()
unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
buf = buf.getvalue().split("\n")
for test in buf:
    if test.startswith("test"):
        print(test)