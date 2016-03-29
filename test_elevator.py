"""
So You Think You Can Program An Elevator

Many of us ride elevators every day. We feel like we understand how they work, how they decide where to go. If you were asked to put it into words, you might say that an elevator goes wherever it's told, and in doing so goes as far in one direction as it can before turning around. Sounds simple, right? Can you put it into code?

In this challenge, you are asked to implement the business logic for a simplified elevator model in Python. We'll ignore a lot of what goes into a real world elevator, like physics, maintenance overrides, and optimizations for traffic patterns. All you are asked to do is to decide whether the elevator should go up, go down, or stop.

How does the challenge work? The simulator and test harness are laid out in this document, followed by several examples. All of this can be run in an actual Python interpreter using Python's built-in `doctest` functionality, which extracts the code in this document and runs it.

A naive implementation of the business logic is provided in the `elevator.py` file in this project. If you run `doctest` using the provided implementation, several examples fail to produce the expected output. Your challenge is to fix that implementation until all of the examples pass.

Open a pull request with your solution. Good luck! Have fun!

## Test Harness

Like all elevators, ours can go up and down. We define constants for these. The elevator also happens to be in a building with six floors.
"""
from functools import wraps

from unittest import TestCase
from unittest.case import expectedFailure


UP = 1
DOWN = 2
FLOOR_COUNT = 6

"""
We will make an `Elevator` class that simulates an elevator. It will delegate to another class which contains the elevator business logic, i.e. deciding what the elevator should do. Your challenge is to implement this business logic class.

### User actions

A user can interact with the elevator in two ways. She can call the elevator by pressing the up or down  button on any floor, and she can select a destination floor by pressing the button for that floor on the panel in the elevator. Both of these actions are passed straight through to the logic delegate.
"""

class Elevator(object):
    def call(self, floor, direction):
        self._logic_delegate.on_called(floor, direction)

    def select_floor(self, floor):
        self._logic_delegate.on_floor_selected(floor)

"""
### Elevator actions

The logic delegate can respond by setting the elevator to move up, move down, or stop. It can also read the current floor and movement direction of the elevator. These actions are accessed through `Callbacks`, a mediator provided by the `Elevator` class to the logic delegate.
"""


class Elevator(Elevator):
    def __init__(self, logic_delegate, starting_floor=1):
        self._visited_floors = []
        self._current_floor = starting_floor
        # print "%s..." % starting_floor,
        self._visited_floors.append(starting_floor)
        self._motor_direction = None
        self._logic_delegate = logic_delegate
        self._logic_delegate.callbacks = self.Callbacks(self)

    class Callbacks(object):
        def __init__(self, outer):
            self._outer = outer

        @property
        def current_floor(self):
            return self._outer._current_floor

        @property
        def motor_direction(self):
            return self._outer._motor_direction

        @motor_direction.setter
        def motor_direction(self, direction):
            f = lambda d: {UP: 'UP', DOWN: 'DOWN'}.get(d, d)
            # print 'XXX motor_direction', f(self._outer._motor_direction), '->', f(direction)
            self._outer._motor_direction = direction

"""
### Simulation

The simulation runs in steps. Each time step consists of the elevator moving a single floor, or pausing at a floor. Either way, the business logic delegate gets notified. Along the way, we print out the movements of the elevator so that we can keep track of it. We also define a few helper methods that advance the simulation to points of interest, for ease of testing.
"""


class Elevator(Elevator):
    def step(self):
       delta = 0
       if self._motor_direction == UP: delta = 1
       elif self._motor_direction == DOWN: delta = -1

       if delta:
           self._current_floor = self._current_floor + delta
           # print "%s..." % self._current_floor,
           self._visited_floors.append(self._current_floor)
           self._logic_delegate.on_floor_changed()
       else:
           self._logic_delegate.on_ready()

       assert self._current_floor >= 1
       assert self._current_floor <= FLOOR_COUNT

    def run_until_stopped(self):
        self.step()
        while self._motor_direction is not None: self.step()

    def run_until_floor(self, floor):
        for i in range(100):
            self.step()
            if self._current_floor == floor: break
        else: assert False

"""
That's it for the framework.

## Business Logic

As for the business logic, an example implementation is provided in the `elevator.py` file in this project.
"""

from elevator import ElevatorLogic

"""
As provided, it doesn't pass the tests in this document. Your challenge is to fix it so that it does. To run the tests, run this in your shell:

    python -m doctest -v README.md

With the correct business logic, here's how the elevator should behave:

### Basic usage

Make an elevator. It starts at the first floor.
"""


class BaseElevatorTest(TestCase):

    def setUp(self):
        self.e = Elevator(ElevatorLogic())
        self._assertVisited([1])

    def tearDown(self):
        if hasattr(self, 'e'):
            # Should be no unchecked visits
            self._assertVisited([])
            self.assertVisits([])

    def _assertVisited(self, floors):
        self.assertEqual(floors, self.e._visited_floors)
        del self.e._visited_floors[:]

    def assertVisits(self, floors):
        """
        The elevator visits the given floors when run until stopped.
        """
        self.e.run_until_stopped()
        self._assertVisited(floors)


def _clearElevator(f):
    """
    BaseElevatorTest method decorator to clear the elevator on exit and ignore the cleanup checks.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
            assert isinstance(self, BaseElevatorTest), self
            return f(self, *args, **kwargs)
        finally:
            del self.e
    return wrapper


class BasicUsageTest(BaseElevatorTest):

    def test_down_from_fifth(self):
        e = self.e

        # Somebody on the fifth floor wants to go down.
        self.e.call(5, DOWN)

        # Keep in mind that the simulation won't actually advance until we call `step` or one of the `run_until_*` methods.
        self.assertVisits([2, 3, 4, 5])

        # The elevator went up to the fifth floor. A passenger boards and wants to go to the first floor.
        e.select_floor(1)

        # Also, somebody on the third floor wants to go down.
        e.call(3, DOWN)

        # Even though the first floor was selected first, the elevator services the call at the third floor...
        self.assertVisits([4, 3])

        # ...before going to the first floor.
        self.assertVisits([2, 1])


"""
### Directionality

"""

class DirectionalityTest(BaseElevatorTest):

    def test_same_direction(self):
        e = self.e

        # Elevators want to keep going in the same direction. An elevator will serve as many
        # requests in one direction as it can before going the other way.
        # For example, if an elevator is going up, it won't stop to pick up passengers
        # who want to go down until it's done with everything that requires it to go up.

        e.call(2, DOWN)
        e.select_floor(5)

        # Even though the elevator was called at the second floor first,
        # it will service the fifth floor...

        self.assertVisits([2, 3, 4, 5])

        # ...before coming back down for the second floor.

        self.assertVisits([4, 3, 2])

    def test_direction_override(self):
        e = self.e

        # In fact, if a passenger tries to select a floor that contradicts the current
        # direction of the elevator, that selection is ignored entirely.
        # You've probably seen this before.
        # You call the elevator to go down.
        # The elevator shows up, and you board, not realizing that it's still going up.
        # You select a lower floor. The elevator ignores you.
        e.select_floor(3)
        e.select_floor(5)
        self.assertVisits([2, 3])
        e.select_floor(2)

        # At this point the elevator is at the third floor.
        # It's not finished going up because it's wanted at the fifth floor.
        # Therefore, selecting the second floor goes against the current direction,
        # so that request is ignored.

        self.assertVisits([4, 5])
        self.assertVisits([])  # nothing happens, because e.select_floor(2) was ignored

        # Now it's done going up, so you can select the second floor.

        e.select_floor(2)
        self.assertVisits([4, 3, 2])

"""
### Changing direction

"""


class ChangingDirectionTest(BaseElevatorTest):

    def test_switching_direction(self):
        e = self.e

        # The process of switching directions is a bit tricky.
        # Normally, if an elevator going up stops at a floor and there are no more requests
        # at higher floors, the elevator is free to switch directions right away.
        # However, if the elevator was called to that floor by a user indicating that
        # she wants to go up, the elevator is bound to consider itself going up.

        e.call(2, DOWN)
        e.call(4, UP)
        self.assertVisits([2, 3, 4])

        e.select_floor(5)
        self.assertVisits([5])
        self.assertVisits([4, 3, 2])

    def test_no_further(self):
        e = self.e

        # If nobody wants to go further up though, the elevator can turn around.

        e.call(2, DOWN)
        e.call(4, UP)
        self.assertVisits([2, 3, 4])
        self.assertVisits([3, 2])

    @_clearElevator
    @expectedFailure  # Questionable logic?
    def test_both_directions(self):
        e = self.e

        # If the elevator is called in both directions at that floor,
        # it must wait once for each direction.
        # You may have seen this too. Some elevators will close their doors and reopen them
        # to indicate that they have changed direction.

        e.select_floor(5)
        e.call(5, UP)
        e.call(5, DOWN)
        self.assertVisits([2, 3, 4, 5])

        # Here, the elevator considers itself to be going up,
        # as it favors continuing in the direction it came from.

        e.select_floor(4)  # ignored
        self.assertVisits([])

        # Since nothing caused the elevator to move further up,
        #  it now waits for requests that cause it to move down.

        e.select_floor(6)  # ignored
        self.assertVisits([])

        # Since nothing caused the elevator to move down, the elevator now considers itself idle.
        #  It can move in either direction.

        e.select_floor(6)
        self.assertVisits([6])


class EnPassantTest(BaseElevatorTest):

    def test_en_passant(self):
        e = self.e

        # Keep in mind that a user could call the elevator or select a floor at any time.
        # The elevator need not be stopped. If the elevator is called or a floor is selected
        # before it has reached the floor in question, then the request should be serviced.

        e.select_floor(6)
        e.run_until_floor(2)  # elevator is not stopped
        self._assertVisited([2])

        e.select_floor(3)
        self.assertVisits([3])  # stops for above

        e.run_until_floor(4)
        self._assertVisited([4])

        e.call(5, UP)
        self.assertVisits([5])  # stops for above

        # XXX: Extra check for final stop at 6
        self.assertVisits([6])

    def test_missed_call(self):
        e = self.e

        # On the other hand, if the elevator is already at, or has passed the floor in question,
        # then the request should be treated like a request in the wrong direction.
        # That is to say, a call is serviced later, and a floor selection is ignored.

        e.select_floor(5)
        e.run_until_floor(2)
        self._assertVisited([2])
        e.call(2, UP)  # missed the boat, come back later
        e.step()  # doesn't stop
        self._assertVisited([3])
        e.select_floor(3)  # missed the boat, ignored
        e.step()  # doesn't stop
        self._assertVisited([4])

        self.assertVisits([5])  # service e.select_floor(5)
        self.assertVisits([4, 3, 2])  # service e.call(2, UP)

class FuzzTestingTest(BaseElevatorTest):

    def test_random_moves(self):

        # No amount of legal moves should compel the elevator to enter an illegal state.
        # Here, we run a bunch of random requests against the simulator to make sure that
        # no asserts are triggered.

        import random
        e = self.e
        e.DEBUG = False  # XXX

        for i in range(100000):
            r = random.randrange(6)
            if r == 0:
                e.call(
                    random.randrange(FLOOR_COUNT) + 1,
                    random.choice((UP, DOWN)))
            elif r == 1:
                e.select_floor(random.randrange(FLOOR_COUNT) + 1)
            else:
                e.step()

        # Ignore whatever was visited.
        del self.e._visited_floors[:]



class MoreExamplesTest(BaseElevatorTest):
    """
    The rest of these examples may be useful for catching bugs. They are meant to be run via doctest, so they may not be very interesting to read through.
    """

    def test_no_board(self):
        e = self.e
        # An elevator is called but nobody boards. It goes idle.

        e.call(5, UP)
        self.assertVisits([2, 3, 4, 5])
        e.run_until_stopped()
        e.run_until_stopped()

    def test_called_two_floors(self):
        """
        The elevator is called at two different floors.
        """
        e = self.e

        e.call(3, UP)
        e.call(5, UP)
        self.assertVisits([2, 3])
        self.assertVisits([4, 5])

    def test_called_two_floors_reverse_order(self):
        """
        Like above, but called in reverse order.
        """
        e = self.e

        e.call(5, UP)
        e.call(3, UP)
        self.assertVisits([2, 3])
        self.assertVisits([4, 5])

    def test_called_two_floors_other_direction(self):
        """
        The elevator is called at two different floors, but going the other direction.
        """
        e = self.e

        e.call(3, DOWN)
        e.call(5, DOWN)
        self.assertVisits([2, 3, 4, 5])
        self.assertVisits([4, 3])

    def test_called_two_floors_opposite_directions(self):
        """
        The elevator is called at two different floors, going in opposite directions.
        """
        e = self.e

        e.call(3, UP)
        e.call(5, DOWN)
        self.assertVisits([2, 3])
        self.assertVisits([4, 5])

    def test_called_two_floors_opposite_directions_reversed(self):
        """
        Like above, but with directions reversed.
        """
        e = self.e

        e.call(3, DOWN)
        e.call(5, UP)
        self.assertVisits([2, 3, 4, 5])
        self.assertVisits([4, 3])

    def test_called_two_floors_above_below(self):
        """
        The elevator is called at two different floors, one above the current floor and one below.
        It first goes to the floor where it was called first.
        """
        e = self.e = Elevator(ElevatorLogic(), 3)
        self._assertVisited([3])

        e.call(2, UP)
        e.call(4, UP)
        self.assertVisits([2])
        self.assertVisits([3, 4])

    @_clearElevator
    @expectedFailure  # Priority ordering
    def test_called_two_floors_above_below_reverse_order(self):
        """
        Like above, but called in reverse order.
        """
        e = self.e = Elevator(ElevatorLogic(), 3)
        self._assertVisited([3])

        e.call(4, UP)
        e.call(2, UP)
        self.assertVisits([4])
        self.assertVisits([3, 2])

    def test_called_while_moving(self):
        """
        The elevator is called while it's already moving.
        """
        e = self.e

        e.call(5, UP)
        e.run_until_floor(2)
        self._assertVisited([2])
        e.call(3, UP)
        self.assertVisits([3])
        self.assertVisits([4, 5])

    def test_comes_back(self):
        """
        If the elevator is already at, or has passed the floor where it was called,
        it comes back later.
        """
        e = self.e

        e.call(5, UP)
        e.run_until_floor(3)
        self._assertVisited([2, 3])
        e.call(3, UP)
        self.assertVisits([4, 5])
        self.assertVisits([4, 3])

    def test_two_floors_selected(self):
        """
        Two floors are selected.
        """
        e = self.e

        e.select_floor(3)
        e.select_floor(5)
        self.assertVisits([2, 3])
        self.assertVisits([4, 5])

    def test_two_floors_selected_reverse_order(self):
        """
        Like above, but selected in reverse order.
        """
        e = self.e

        e.select_floor(5)
        e.select_floor(3)
        self.assertVisits([2, 3])
        self.assertVisits([4, 5])

    @_clearElevator
    @expectedFailure  # Very questionable
    def test_two_floors_selected_above_below(self):
        """
        Two floors are selected, one above the current floor and one below.
        The first selection sets the direction, so the second one is completely ignored.
        """
        e = self.e = Elevator(ElevatorLogic(), 3)
        self._assertVisited([3])

        e.select_floor(2)
        e.select_floor(4)
        self.assertVisits([2])
        self.assertVisits([])

    @_clearElevator
    @expectedFailure  # Very questionable
    def test_two_floors_selected_above_below_reverse_order(self):
        """
        Like above, but selected in reverse order.
        """
        e = self.e = Elevator(ElevatorLogic(), 3)
        self._assertVisited([3])

        e.select_floor(4)
        e.select_floor(2)
        self.assertVisits([4])
        self.assertVisits([])

    @_clearElevator
    @expectedFailure  # Very questionable
    def test_going_up_ignores_request_down(self):
        """
        If the elevator is called to a floor going up, it should ignore a request to go down.
        """
        e = self.e

        e.call(5, UP)
        self.assertVisits([2, 3, 4, 5])
        e.select_floor(6)
        e.select_floor(4)
        self.assertVisits([6])
        self.assertVisits([])

    @_clearElevator
    @expectedFailure  # Very questionable
    def test_going_down_ignores_request_up(self):
        """
        Like above, but going in other direction.
        """
        e = self.e

        e.call(5, DOWN)
        self.assertVisits([2, 3, 4, 5])
        e.select_floor(6)
        e.select_floor(4)
        self.assertVisits([4])
        self.assertVisits([])

    def test_called_selected_same_floor(self):
        """
        Elevator is called to a floor and a passenger also selects the same floor.
        The elevator should not go back to that floor twice.
        """
        e = self.e

        e.call(5, DOWN)
        e.select_floor(5)
        self.assertVisits([2, 3, 4, 5])
        e.select_floor(4)
        self.assertVisits([4])
        self.assertVisits([])

    @_clearElevator
    @expectedFailure
    def test_called_at_stopped_floor(self):
        """
        Similarly, if the elevator is called at a floor where it is stopped, it should not go back later.
        """
        e = self.e

        e.call(3, UP)
        self.assertVisits([2, 3])
        e.call(3, UP)
        e.call(5, DOWN)
        self.assertVisits([4, 5])
        self.assertVisits([])

    def test_call_continues_same_direction(self):
        """
        Elevator is ready to change direction, new call causes it to keep going in same direction.
        """
        e = self.e

        e.call(2, DOWN)
        e.call(4, UP)
        self.assertVisits([2, 3, 4])
        e.call(5, DOWN)  # It's not too late.
        self.assertVisits([5])
        self.assertVisits([4, 3, 2])

    def test_changing_directions_waits_one_stop(self):
        """
        When changing directions, wait one step to clear current direction.
        """
        e = self.e

        e.select_floor(5)
        e.call(5, UP)
        e.call(5, DOWN)
        self.assertVisits([2, 3, 4, 5])
        e.select_floor(4)  # ignored
        e.run_until_stopped()
        e.select_floor(6)  # ignored
        e.select_floor(4)
        self.assertVisits([4])
        self.assertVisits([])

    def test_changing_directions_waits_one_stop_other_direction(self):
        """
        Like above, but going in other direction.
        """
        e = self.e = Elevator(ElevatorLogic(), 6)
        self._assertVisited([6])

        e.select_floor(2)
        e.call(2, UP)
        e.call(2, DOWN)
        self.assertVisits([5, 4, 3, 2])
        e.select_floor(3)  # ignored
        e.run_until_stopped()
        e.select_floor(1)  # ignored
        e.select_floor(3)
        self.assertVisits([3])
        self.assertVisits([])

    @expectedFailure  # Questionable?
    def test_coming_back_to_other_direction(self):
        """
        If other direction is not cleared, come back.
        """
        e = self.e

        e.select_floor(5)
        e.call(5, UP)
        e.call(5, DOWN)
        self.assertVisits([2, 3, 4, 5])
        e.select_floor(6)
        self.assertVisits([6])
        self.assertVisits([5])
        e.select_floor(6)  # ignored
        e.select_floor(4)
        self.assertVisits([4])
