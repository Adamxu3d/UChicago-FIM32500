from collections import deque
import time
import random
from abc import ABC
from enum import Enum
import threading


class OrderType(Enum):
    LIMIT = 1
    MARKET = 2
    IOC = 3


class OrderSide(Enum):
    BUY = 1
    SELL = 2

class ActionType(Enum):
    PLACE_ORDER = 1
    AMEND_ORDER = 2
    CANCEL_ORDER = 3
    RETURN_POSITION = 4


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

# 1 thread for exchange,
# and 100 threads for the traders
trader_to_exchange = deque()
exchange_to_trader = [deque() for _ in range(100)]


# Above you are given two deques where the orders submitted to the exchange and back to the trader
# are expected to be populated by the trading exchange simulator
# The first is trader_to_exchange, a deque of orders to be populated for the exchange to execute
# The second is a list of 100 deques exchange_to_trader, which are acknowledgements from the exchange
# to each of the 100 traders for trades executed on their behalf

# Below you have an implementation of a simulated thread to be used where each trader is a separate thread
class MyThread:
    list_of_threads = []

    def __init__(self, id='NoID'):
        MyThread.list_of_threads.append(self)
        self.is_started = False
        self.id = id

    def start(self):
        self.is_started = True

    def join(self):
        print('Trader ' + str(self.id) + ' will be waited')


# Paste in your implementation for the matching engine below
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
        elif order.side == OrderSide.SELL:
            self.ask_book.remove(order)
        else:
            raise UndefinedOrderSide("Undefined Order Side!")

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
                        filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, order.price,
                                                         order.side, order.time))
                        consumed_asks.append(item)
                        order.quantity = 0

                    elif order.quantity < item.quantity:
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                    item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
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
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
                                        order.time))
                        consumed_bids.append(item)
                        order.quantity = 0
                    elif order.quantity < item.quantity:
                        partial_order = FilledOrder(item.id, item.symbol, order.quantity, item.price, item.side,
                                                    item.time)
                        item.quantity -= order.quantity
                        filled_orders.append(partial_order)
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
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
                    filled_orders.append(LimitOrder(order.id, order.symbol, order.quantity, item.price, order.side,
                                                    order.time))
                    consumed_asks.append(item)
                    order.quantity = 0
                    break
                elif order.quantity < item.quantity:
                    partial_order = LimitOrder(item.id, item.symbol, order.quantity, item.price, item.side, item.time)
                    item.quantity -= order.quantity
                    filled_orders.append(partial_order)
                    filled_orders.append(LimitOrder(order.id, order.symbol, order.quantity, item.price, order.side,
                                                    order.time))
                    order.quantity = 0
                    break
                else:
                    order.quantity -= item.quantity
                    fulfilled_order = LimitOrder(order.id, order.symbol, item.quantity, item.price, order.side,
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
                    filled_orders.append(FilledOrder(order.id, order.symbol, order.quantity, item.price, order.side,
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

    def insert_limit_order(self, order):
        assert order.type == OrderType.LIMIT
        if order.side == OrderSide.BUY:
            self.bid_book.append(order)
            # self.bid_book.sort(key=lambda x: x.time)
            self.bid_book.sort(key=lambda x: x.price, reverse=True)
        elif order.side == OrderSide.SELL:
            self.ask_book.append(order)
            # self.ask_book.sort(key=lambda x: x.time)
            self.ask_book.sort(key=lambda x: x.price)
        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
        else:
            # You need to raise the following error if the side the order is for is ambiguous
            raise UndefinedOrderSide("Undefined Order Side!")

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
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
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
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
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
                        filled_orders.append(
                            FilledOrder(order.id, order.symbol, order.quantity, order.price, order.side,
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
            # self.bid_book.sort(key=lambda x: x.price, reverse=True)
        elif order.side == OrderSide.SELL:
            self.ask_book.append(order)
            # self.ask_book.sort(key=lambda x: x.price)
        # Implement this function
        # this function's sole puporse is to place limit orders in the book that are guaranteed
        # to not immediately fill
        else:
            # You need to raise the following error if the side the order is for is ambiguous
            raise UndefinedOrderSide("Undefined Order Side!")

    def amend_quantity(self, id, quantity): # modified to return True or False
        # Implement this function
        # Hint: Remember that there are two order books, one on the bid side and one on the ask side
        switch = 0
        for item in self.ask_book:
            if item.id == id:
                if item.quantity > quantity:
                    item.quantity = quantity
                    switch = 1
                    return True
                else:
                    raise NewQuantityNotSmaller("Amendment Must Reduce Quantity!")
        if switch == 0:
            for item in self.bid_book:
                if item.id == id:
                    if item.quantity > quantity:
                        item.quantity = quantity
                        return True
                    else:
                        raise NewQuantityNotSmaller("Amendment Must Reduce Quantity!")
        # You need to raise the following error if the user attempts to modify an order
        # with a quantity that's greater than given in the existing order
        return False

    def cancel_order(self, id): # modified to return true or false
        # Implement this function
        # Think about the changes you need to make in the order book based on the parameters given
        switch = 0
        cancelled_order = None
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
        if cancelled_order == None:
            return False
        else:
            return True
        # You need to raise the following error if the user attempts to modify an order
        # with a quantity that's greater than given in the existing order


# ----------------------------------------------------------
# PASTE MATCHING ENGINE FROM Q2 HERE
# -----------------------------------------------------------

# Each trader can take a separate action chosen from the list below:

# Actions:
# 1 - Place New Order/Order Filled
# 2 - Amend Quantity Of An Existing Order
# 3 - Cancel An Existing Order
# 4 - Return Balance And Position

# request - (Action #, Trader ID, Additional Arguments) -  this should be appended to trader_to_exchange
# result - (Action #, Action Return) - this should be appended to exchange_to_trader

# WE ASSUME 'AAPL' IS THE ONLY TRADED STOCK.


# the Trader class is inherited from thread class
class Trader(MyThread):
    loop_count = 0
    def __init__(self, id):
        super().__init__(id)
        self.book_position = 0 #position of each trader (should be opposite to that of the exchange)
        # the position records the number of shares owned by the trader
        # self.balance_track = [1000000]
        self.balance_track = 1000000
        self.limit_counter = 0
        # the traders each start with a balance of 1,000,000 and nothing on the books
        # each trader is a thread

    def place_limit_order(self, quantity=None, price=None, side=None):
        # Make sure the limit order given has the parameters necessary to construct the order
        # It's your choice how to implement the orders that do not have enough information
        quantity = 100
        price = 10000
        # side = OrderSide(1)
        side = OrderSide(random.randint(1,2))
        self.limit_counter += quantity
        # The 'order' returned must be of type LimitOrder
        myorder = LimitOrder(self.id, 'AAPL', quantity, price, side, time.time())

        # print('id: ', self.id)

        # trader_to_exchange.append(myorder)
        # appending the request to the trader_to_exchange
        # Make sure you modify the book position after the trade
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader, and the order to be executed)
        return ActionType.PLACE_ORDER.value, self.id, myorder

    def place_market_order(self, quantity=None, side=None):
        # Make sure the market order given has the parameters necessary to construct the order
        # It's your choice how to implement the orders that do not have enough information
        quantity = 100
        price = 10000
        # The 'order' returned must be of type MarketOrder
        myorder = MarketOrder(self.id, 'AAPL', quantity, side, time.time())
        # trader_to_exchange.append(myorder)
        # Make sure you modify the book position after the trade
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader, and the order to be executed)
        return ActionType.PLACE_ORDER.value, self.id, myorder

    def place_ioc_order(self, quantity=None, price=None, side=None):
        # Make sure the ioc order given has the parameters necessary to construct the order
        # It's your choice how to implement the orders that do not have enough information
        quantity = 100
        price = 10000
        # side = OrderSide(random.randint(1, 2))
        side = OrderSide(random.randint(1,2))
        # The 'order' returned must be of type IOCOrder
        myorder = IOCOrder(self.id, 'AAPL', quantity, price, side, time.time())
        # trader_to_exchange.append(myorder)
        # Make sure you modify the book position after the trade
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader, and the order to be executed)
        return ActionType.PLACE_ORDER.value, self.id, myorder

    def amend_quantity(self, quantity=None):
        # It's your choice how to implement the 'Amend' action where quantity is not given
        quantity = 50
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader, and quantity to change the order by)
        return ActionType.AMEND_ORDER.value, self.id, quantity

    def cancel_order(self):
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader)
        return ActionType.CANCEL_ORDER.value, self.id

    def balance_and_position(self):
        # You must return a tuple of the following:
        # (the action type enum, the id of the trader)
        return ActionType.RETURN_POSITION.value, self.id


    # unsure about this function
    def process_response(self, response):
        # if response from the market is filled order, then update the book_position and balance
        # Implement this function
        # You need to process each order according to the type (by enum) given by the 'response' variable
        # 4 different types of responses
        # --filled order, use filled order's quantity to update

        if response[0] == 1:
            filled_limit_order = response[1]
            self.limit_counter -= filled_limit_order.quantity
            if filled_limit_order.side == OrderSide.BUY:
                self.book_position += filled_limit_order.quantity
                self.balance_track -= filled_limit_order.quantity * filled_limit_order.price
            elif filled_limit_order.side == OrderSide.SELL:
                self.book_position -= filled_limit_order.quantity
                self.balance_track += filled_limit_order.quantity * filled_limit_order.price
            else:
                raise UndefinedOrderSide("Undefined Order Side!")
        elif response[0] == 2:
            if response[1]:
                self.limit_counter -= 50
            # not finished with this function
        elif response[0] == 3:
            if response[1]:
                self.limit_counter = 0
        elif response[0] == 4:
            print('balance: ', response[1][0], ' position: ', response[1][1])

        # --Amend quantity, need to use balance and position to check, then update the numbers
        # --Cancel order, revert the counter for limit order to 0
        # --balance and position
        # If the action taken by the trader is ambiguous you need to raise the following error
        else:
            raise UndefinedResponse("Undefined Response Received!")

    def random_action(self):
        # if self.limit_counter == 0:
        #     action = random.randint(1,4)
        # else:
        #     action = random.randint(2,4)
        #
        action = 1
        # print(action)

        if action == 1:
            action_request = self.place_limit_order()
            self.limit_counter += 100
        elif action == 2:
            action_request = self.amend_quantity()
        elif action == 3:
            action_request = self.cancel_order()
        elif action == 4:
            action_request = self.balance_and_position()
        else:
            raise UndefinedResponse("Undefined request to be added!")
        return action_request

    # Implement this function
    # According to the status of whether you have a position on the book and the action chosen
    # the trader needs to be able to take a separate action

    # The action taken can be random or deterministic, your choice

    def run_infinite_loop(self):
        # print('loop -1')
        if self.balance_track >= 0:
            if Trader.loop_count > 99:
                # print('first id:', self.id)
                try:
                    response = exchange_to_trader[self.id].popleft()
                    print('id:', self.id, response)
                    self.process_response(response)
                except IndexError:
                    pass
                # firstly update and process the response from trader class
                # however this should only run during the first cycle
            print('loop 1: ',Trader.loop_count)
            Trader.loop_count += 1
            action_request = self.random_action()
            trader_to_exchange.append(action_request)



# The trader needs to continue to take actions until the book balance falls to 0
# While the trader can take actions, it chooses from a random_action and uploads the action
# to the exchange

# The trader then takes any received responses from the exchange and processes it
# trader_to_exchange = deque()
# exchange_to_trader = [deque() for _ in range(100)]
# the exchange class is inherited from thread class
class Exchange(MyThread):
    requests_no = 0
    def __init__(self):
        super().__init__()
        self.balance = [1000000 for _ in range(100)]
        # an array of 1000000 of size 100 representing the balance of each trader
        self.position = [0 for _ in range(100)]
        # an array of 0 of size 100 representing the position of exchange relative to each trader
        self.matching_engine = MatchingEngine()
        # The exchange keeps track of the traders' balances
        # The exchange uses the matching engine you built previously

    def place_new_order(self, order):
        # The exchange must use the matching engine to handle orders given
        filled_order = self.matching_engine.handle_limit_order(order)
        # adding the filled order to the info to be sent to trader
        # exchange_to_trader[order.id].append(filled_order)
        # exchange to trader information
        # order id, limit order enum, order itself
        results = []
        for item in filled_order:
            # append the filled orders to results
            results.append((item.id, (ActionType.PLACE_ORDER.value, item)))
            # update the book position and balance based on sell or buy
            if item.side == OrderSide.BUY:
                self.position[item.id] -= item.quantity
                self.balance[item.id] -= item.quantity*item.price
            elif item.side == OrderSide.SELL:
                self.position[item.id] += item.quantity
                self.balance[item.id] += item.quantity * item.price
            else:
                raise UndefinedOrderSide("Undefined Order Side!")

        for requests in results:
            print('request id: ',self.id, 'length request: ', Exchange.requests_no)
            # Exchange.requests_no+=1
            exchange_to_trader[requests[0]].append(requests[1])

        # The list of results is expected to contain a tuple of the follow form:
        # (Trader id that processed the order, (action type enum, order))
        # The exchange must update the balance of positions of each trader involved in the trade (if any)
        return 0

    def amend_quantity(self, id, quantity):
        # The matching engine must be able to process the 'amend' action based on the given parameters
        try:
            amend_bool = self.matching_engine.amend_quantity(id, quantity)
            return ActionType.AMEND_ORDER.value, amend_bool
        except NewQuantityNotSmaller:
            return ActionType.AMEND_ORDER.value, False

        # Keep in mind of any exceptions that may be thrown by the matching engine while handling orders
        # The return must be in the form (action type enum, logical based on if order processed)

    def cancel_order(self, id):
        # The matching engine must be able to process the 'cancel' action based on the given parameters
        cancel_bool = self.matching_engine.cancel_order(self, id)
        return ActionType.CANCEL_ORDER.value, cancel_bool

        # Keep in mind of any exceptions that may be thrown by the matching engine while handling orders
        # The return must be in the form (action type enum, logical based on if order processed)

    def balance_and_position(self, id):
        # The matching engine must be able to process the 'balance' action based on the given parameters
        # The return must be in the form (action type enum, (trader balance, trader positions))
        result = (ActionType.RETURN_POSITION.value, (self.balance[id], self.position[id]))
        return result

    # class ActionType(Enum):
    #     PLACE_ORDER = 1
    #     AMEND_ORDER = 2
    #     CANCEL_ORDER = 3
    #     RETURN_POSITION = 4

    def handle_request(self, request):
        # The exchange must be able to process different types of requests based on the action
        # type given using the functions implemented above
        # catagorize on different responses, update the book and balance
        action = request[0]
        if action == 1:
            # the results contains a list of filled orders
            self.place_new_order(request[2])
        elif action == 2:
            exchange_to_trader[request[1]].append(self.amend_quantity(request[1], request[2]))
        elif action == 3:
            exchange_to_trader[request[1]].append(self.cancel_order(request[1]))
        elif action == 4:
            exchange_to_trader[request[1]].append(self.balance_and_position(request[1]))
        # You must raise the following exception if the action given is ambiguous
        else:
            raise UndefinedTraderAction("Undefined Trader Action!")

    def run_infinite_loop(self):
        #         # if trader's balance becomes 0 then stop the trading
        # from trader id0 to trader id99, process their requests
        for i in range(100):
            try:
                request = trader_to_exchange.popleft()
                self.handle_request(request)
            except IndexError:
                pass



        # print('askbook: ',self.matching_engine.ask_book)
        # print('bidbook: ',self.matching_engine.bid_book)



# The exchange must continue handling orders as orders are issued by the traders
# A way to do this is check if there are any orders waiting to be processed in the deque

# If there are, handle the request using the functions built above and using the
# corresponding trader's deque, return an acknowledgement based on the response

if __name__ == "__main__":

    # the trader initiated the thread with numbers so they have ids
    trader = [Trader(i) for i in range(100)]
    # creating an array of traders, each i represents the thread number

    # the exchange also initiated a thread with 'NoID' as its ID as it had default constructor
    exchange = Exchange()

    # creating a single thread for the exchange
    exchange.start()
    # start of the exchange thread

    for t in trader:
        # start all of the trader threads
        t.start()


    # do not execute the following process unless all the threads are finished
    exchange.join()
    for t in trader:
        t.join()



    sum_exch = 0
    for t in MyThread.list_of_threads:
        # if it does not have any id, it should be the exchange book
        if t.id == "NoID":
            for b in t.balance:
                sum_exch += b

    # for item in MyThread.list_of_threads:
    #     print(item.id)


    print("Total Money Amount for All Traders before Trading Session: " + str(sum_exch))

    a = time.time()

    for i in range(10):
        thread_active = False
        for t in MyThread.list_of_threads:
            # for each of the cycles the run_infinite loop needs to update the balance in list_of_threads
            if t.is_started:
                t.run_infinite_loop()
                thread_active = True
        if not thread_active:
            break

    sum_exch = 0
    for t in MyThread.list_of_threads:
        # if it does not have any id, it should be the exchange book
        if t.id == "NoID":
            for b in t.balance:
                sum_exch += b
    print(len(MyThread.list_of_threads))
    print('time taken: ', time.time()-a)
    print("Total Money Amount for All Traders after Trading Session: ", str(int(sum_exch)))
