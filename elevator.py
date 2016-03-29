from __future__ import print_function

UP = 1
DOWN = 2
FLOOR_COUNT = 6


f = lambda d: {UP: 'UP', DOWN: 'DOWN', None: 'NONE'}.get(d)


class ElevatorLogic(object):
    """
    An incorrect implementation. Can you make it pass all the tests?

    Fix the methods below to implement the correct logic for elevators.
    The tests are integrated into `README.md`. To run the tests:
    $ python -m doctest -v README.md

    To learn when each method is called, read its docstring.
    To interact with the world, you can get the current floor from the
    `current_floor` property of the `callbacks` object, and you can move the
    elevator by setting the `motor_direction` property. See below for how this is done.
    """

    DEBUG = False

    def debug(self, *args):
        if self.DEBUG:
            print('XXX:', *args)

    def __init__(self):
        # Feel free to add any instance variables you want.
        self.callbacks = None

        self.requested_destinations = set()  # Floors selected as destinations
        self.requests_going_up = set()  # Requests to go up
        self.requests_going_down = set()  # Requests to go down

        self.directionality = None  # Direction bias

    def on_called(self, floor, direction):
        """
        This is called when somebody presses the up or down button to call the elevator.
        This could happen at any time, whether or not the elevator is moving.
        The elevator could be requested at any floor at any time, going in either direction.

        floor: the floor that the elevator is being called to
        direction: the direction the caller wants to go, up or down
        """
        self.debug('on_called(): floor', floor, 'wants to go', f(direction))

        if direction == UP:
            self.requests_going_up.add(floor)
        elif direction == DOWN:
            self.requests_going_down.add(floor)
        else:
            raise ValueError(direction)

    def on_floor_selected(self, floor):
        """
        This is called when somebody on the elevator chooses a floor.
        This could happen at any time, whether or not the elevator is moving.
        Any floor could be requested at any time.

        floor: the floor that was requested
        """
        if self.directionality is not None and self.directionality != self._direction_to(floor):
            self.debug('on_floor_selected() ignoring', floor)
        else:
            self.debug('on_floor_selected() accepting', floor)
            self.requested_destinations.add(floor)

    def on_floor_changed(self):
        """
        This lets you know that the elevator has moved one floor up or down.
        You should decide whether or not you want to stop the elevator.
        """
        current_floor = self.callbacks.current_floor

        destination = self._current_destination()
        assert destination is not None, destination
        if current_floor == destination:
            self.debug('on_floor_changed() stopping at', current_floor)
            self.callbacks.motor_direction = None

            for floors in [self.requested_destinations, self.requests_going_down,
                           self.requests_going_up]:
                floors.discard(current_floor)

            if self._current_destination() is None:
                self.debug('on_floor_changed() forgetting direction, no more stops going', f(self.directionality))
                self.directionality = None
            else:
                self.debug('on_floor_changed() planning to continue going', f(self.directionality), 'to', self._current_destination())
        else:
            self.debug('on_floor_changed() heading', f(self.directionality), 'to', destination)

    def on_ready(self):
        """
        This is called when the elevator is ready to go.
        Maybe passengers have embarked and disembarked. The doors are closed,
        time to actually move, if necessary.
        """
        if self._current_destination() is None and self.directionality is not None:
            self.debug('on_ready() forgetting direction, no further stops', f(self.directionality))
            self.directionality = None
            # Does this give us a new destination?
            new_destination = self._current_destination()
            if new_destination is not None:
                self.directionality = self._direction_to(new_destination)

        destination = self._current_destination()
        if destination is not None:
            if self.directionality is not None:
                self.debug('on_ready() continuing', f(self.directionality), 'to', destination)
                self.callbacks.motor_direction = self.directionality
            else:
                self.debug('on_ready() going', f(self._direction_to(destination)), 'to', destination)
                self.directionality = self.callbacks.motor_direction = self._direction_to(destination)
        else:
            self.debug('on_ready() doing nothing, no destination')
            self.directionality = None

    def _current_destination(self):
        current_floor = self.callbacks.current_floor

        def floors_up(floors):
            return {f for f in floors if current_floor <= f}

        def floors_down(floors):
            return {f for f in floors if f <= current_floor}

        def floor_distance(floor):
            return abs(current_floor - floor)

        if self.directionality is None:
            stops = self.requested_destinations | self.requests_going_up | self.requests_going_down
            destination = min(stops, key=floor_distance) if stops else None
        elif self.directionality == UP:
            stops_up = floors_up(self.requested_destinations | self.requests_going_up)
            returns_down = floors_up(self.requests_going_down)
            destination = (min(stops_up) if stops_up else
                           max(returns_down) if returns_down else
                           None)
        elif self.directionality == DOWN:
            stops_down = floors_down(self.requested_destinations | self.requests_going_down)
            returns_up = floors_down(self.requests_going_up)
            destination = (max(stops_down) if stops_down else
                           min(returns_up) if returns_up else
                           None)
        else:
            raise ValueError(self.directionality)
        self.debug('current destination:', f(self.directionality), 'to', destination)
        return destination

    def _direction_to(self, floor):
        """
        Direction from the current floor to the given floor.
        """
        current_floor = self.callbacks.current_floor
        return (UP if current_floor < floor else
                DOWN if floor < current_floor else
                None)
