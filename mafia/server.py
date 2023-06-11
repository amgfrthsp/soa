import enum
import random
import threading
import time
import utilities
import grpc
from concurrent import futures
import proto.server_pb2_grpc as server_pb2_grpc
import proto.server_pb2 as server_pb2

random.seed(time.time())

mutex = threading.Lock()

adj = ["Sunny", "Fluffy", "Old", "Pretty", "Cute", "Dull", "Smiley"]
name = ["Pug", "Doggy", "Kitty", "Lizzard", "Corgi", "Piggy"]

DISCONNECTED_TIMEOUT = 1.5
UPDATE_TIMER = 1


class GameState(enum.Enum):
    NOT_STARTED = 0
    FINISHED = 1
    DAY = 2
    VOTING = 3
    FINISH_DAY = 4
    NIGHT = 5
    MAFIA_NOTIFY = 6
    MAFIA_WAITING = 7
    SHERIFF_NOTIFY = 8
    SHERIFF_WAITING = 9


class UserStatus(enum.Enum):
    ALIVE = 1
    CANCELLED = 2
    KILLED = 3
    DISCONNECTED = 4


class User:

    def __init__(self, name, signiture, room):
        self.signiture = signiture
        self.name = name
        self.room = room
        self.role = None
        self.events = []
        self.last_ping = time.time()
        self.status = UserStatus.ALIVE

    def update_ping(self):
        self.last_ping = time.time()


class Room:

    def __init__(self, number):
        self.number = number
        self.users = {}
        self.roles = ["Mafia", "Civilian", "Civilian", "Sheriff"]
        random.shuffle(self.roles)

        self.started = False
        self.finished = False

        self.game_state = GameState.NOT_STARTED
        self.votes = {}
        self.finished_day = []
        self.mafia_vote = None
        self.sheriff_vote = None

        self.day_one = True

    def is_available(self):
        return not self.started and len(self.users) < 4

    def add_user(self, new_user):
        self.users[new_user.name] = new_user
        new_user.role = self.roles.pop()

        for user in self.users.values():
            if user.name == new_user.name:
                continue
            event0 = server_pb2.Event()
            event0.user_joined.username = user.name
            new_user.events.append(event0)

            event = server_pb2.Event()
            event.user_joined.username = new_user.name
            user.events.append(event)

        print(
            f'User {new_user.name} registered. Room {self.number}, Role {new_user.role}')

    def process_user_left(self, disconnected_user):
        if disconnected_user in self.users:
            self.roles.append(self.users[disconnected_user].role)
            self.users.pop(disconnected_user)

            for user in self.users.values():
                event = server_pb2.Event()
                event.user_left.username = disconnected_user
                user.events.append(event)

        if self.finished or not self.started:
            return
        self.finish_game("Game is over.")

    def update(self):
        self.search_for_disconnected_users()

        if self.finished:
            return
        if len(self.users) == 4 and not self.started:
            self.started = True
            for user in self.users.values():
                game_started = server_pb2.GameStarted()
                event = server_pb2.Event()
                event.game_started.CopyFrom(game_started)
                user.events.append(event)
            self.game_state = GameState.DAY

        if not self.started:
            return

        match self.game_state:
            case GameState.DAY:
                self.should_finish()
                if self.finished:
                    return
                for user in self.users.values():
                    day_started = server_pb2.DayStarted()
                    event = server_pb2.Event()
                    event.day_started.CopyFrom(day_started)
                    user.events.append(event)
                self.game_state = self.next_game_state()
                if self.day_one:
                    self.day_one = False
                    self.game_state = self.next_game_state()
            case GameState.VOTING:
                if len(self.votes) < self.get_alive_users_cnt():
                    return
                self.game_state = self.next_game_state()
            case GameState.FINISH_DAY:
                if len(self.finished_day) < self.get_alive_users_cnt():
                    return
                cancelled_user = self.get_cancelled_user()
                for user in self.users.values():
                    event = server_pb2.Event()
                    event.user_cancelled.username = cancelled_user
                    if cancelled_user != "":
                        self.users[cancelled_user].status = UserStatus.CANCELLED
                    user.events.append(event)
                self.votes = {}
                self.game_state = self.next_game_state()
                self.should_finish()
                self.finished_day = []
            case GameState.NIGHT:
                for user in self.users.values():
                    night_started = server_pb2.NightStarted()
                    event = server_pb2.Event()
                    event.night_started.CopyFrom(night_started)
                    user.events.append(event)
                self.game_state = self.next_game_state()
            case GameState.MAFIA_NOTIFY:
                for user in self.users.values():
                    mafia_time = server_pb2.MafiaTime()
                    event = server_pb2.Event()
                    event.mafia_time.CopyFrom(mafia_time)
                    user.events.append(event)
                self.game_state = self.next_game_state()
            case GameState.MAFIA_WAITING:
                if self.mafia_vote == None:
                    return
                self.game_state = self.next_game_state()
            case GameState.SHERIFF_NOTIFY:
                for user in self.users.values():
                    sheriff_time = server_pb2.SheriffTime()
                    event = server_pb2.Event()
                    event.sheriff_time.CopyFrom(sheriff_time)
                    user.events.append(event)
                self.game_state = self.next_game_state()
            case GameState.SHERIFF_WAITING:
                sheriff = self.get_sheriff()
                if self.sheriff_vote == None and self.users[sheriff].status == UserStatus.ALIVE:
                    return
                for user in self.users.values():
                    sheriff_chose = server_pb2.SheriffChose()
                    event = server_pb2.Event()
                    event.sheriff_chose.CopyFrom(sheriff_chose)
                    user.events.append(event)
                self.sheriff_vote = None

                for user in self.users.values():
                    event = server_pb2.Event()
                    event.user_killed.username = self.mafia_vote
                    user.events.append(event)
                self.mafia_vote = None

                self.game_state = self.next_game_state()

    def next_game_state(self):
        next = GameState((self.game_state.value + 1) % len(GameState))
        if next.value < 2:
            next = GameState.DAY
        return next

    def process_finish_day(self, user):
        self.finished_day.append(user)

    def send_simple_message(self, user, text):
        msg = server_pb2.ServerMessage(msg=text)
        event = server_pb2.Event()
        event.server_msg.CopyFrom(msg)
        self.users[user].events.append(event)

    def vote(self, user_voted, victim):
        for user in self.users:
            self.send_simple_message(
                user, f'User {user_voted} voted for {victim}')
        self.votes[user_voted] = victim

    def register_mafia_kill(self, victim):
        for user in self.users:
            self.send_simple_message(
                user, f'Mafia made a decision.')
        self.mafia_vote = victim
        self.users[victim].status = UserStatus.KILLED

    def register_sheriff_vote(self, sheriff, victim):
        response = server_pb2.RevealRoleMessage(
            username=victim, role=self.users[victim].role, room=self.number)

        self.sheriff_vote = victim
        return response

    def should_finish(self):
        roles = []
        for user in self.users.values():
            if user.status == UserStatus.ALIVE:
                roles.append(user.role)
        if not 'Mafia' in roles:
            self.finish_game("Civilians won!")
        elif len(roles) <= 2:
            self.finish_game("Mafia won!")

    def get_alive_users_cnt(self):
        cnt = 0
        for user in self.users.values():
            if user.status == UserStatus.ALIVE:
                cnt += 1
        return cnt

    def finish_game(self, text):
        self.finished = True
        for user in self.users.values():
            game_finished = server_pb2.GameFinished(msg=text)
            event = server_pb2.Event()
            event.game_finished.CopyFrom(game_finished)
            user.events.append(event)

            for user1 in self.users.values():
                reveal = server_pb2.RevealRoleMessage(
                    username=user1.name, role=user1.role)
                event = server_pb2.Event()
                event.reveal_role.CopyFrom(reveal)
                user.events.append(event)

    def reveal_role(self, user, sheriff=False):
        for user1 in self.users.values():
            if sheriff:
                self.send_simple_message(
                    user1.name, "Sheriff has something to tell you")
            reveal = server_pb2.RevealRoleMessage(
                username=user, role=self.users[user].role)
            event = server_pb2.Event()
            event.reveal_role.CopyFrom(reveal)
            user1.events.append(event)
        return server_pb2.VoteResponse()

    def get_sheriff(self):
        for user in self.users.values():
            if user.role == "Sheriff":
                return user.name

    def get_cancelled_user(self):
        votes = {}
        for user in self.users:
            votes[user] = 0
        max_cnt = 0
        for user in self.votes:
            votes[self.votes[user]] += 1
            max_cnt = max(max_cnt, votes[self.votes[user]])
        cancelled_user = ""
        for user in self.users:
            if votes[user] == max_cnt:
                if cancelled_user != "":
                    return ""
                cancelled_user = user
        return cancelled_user

    def search_for_disconnected_users(self):
        disconnected = []
        for user in self.users:
            if time.time() - self.users[user].last_ping >= DISCONNECTED_TIMEOUT:
                disconnected.append(user)
        for user in disconnected:
            self.process_user_left(user)

    def generate_username(self):
        names = self.users.keys()
        for _ in range(50):
            username = random.choice(adj) + random.choice(name)
            if username not in names:
                return username
        return utilities.generate_random_string(10)


class Server(server_pb2_grpc.ServerServicer):

    def __init__(self, *args, **kwargs):
        self.rooms = []
        self.users = 0
        self.next_room_number = 0
        self.last_updated = 0

    def Register(self, request, context):
        mutex.acquire()
        room = self.get_next_room_number()

        if request.username == "":
            username = self.rooms[room].generate_username()
        else:
            username = request.username

        if username in self.rooms[room].users:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            mutex.release()
        else:
            user = User(username, request.signiture, room)
            auto_mode = True
            if self.rooms[room].get_alive_users_cnt() == 0:
                auto_mode = False
            self.rooms[room].add_user(user)

            mutex.release()
            return server_pb2.RegisterResponse(username=username, room=room, role=user.role, auto=auto_mode)

    def GetUpdates(self, request, context):
        mutex.acquire()
        if time.time() - self.last_updated >= UPDATE_TIMER:
            self.update()

        username = request.username
        signiture = request.signiture
        room = request.room
        if not username in self.rooms[room].users or self.rooms[room].users[username].signiture != signiture:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            mutex.release()
        else:
            user = self.rooms[room].users[username]
            user.update_ping()
            response = server_pb2.Updates()
            for event in user.events:
                response.events.append(event)
            user.events = []
            mutex.release()
            return response

    def AcceptVote(self, request, context):
        room = request.room
        user = request.username
        victim = request.victim
        self.rooms[room].vote(user, victim)
        return server_pb2.VoteResponse()

    def Ping(self, request, context):
        auto = (self.users % 4 != 0)
        self.users += 1
        return server_pb2.PingResponse(auto=auto)

    def FinishDay(self, request, context):
        room = request.room
        user = request.username
        self.rooms[room].process_finish_day(user)
        return server_pb2.VoteResponse()

    def AcceptMafiaVote(self, request, context):
        room = request.room
        victim = request.victim
        self.rooms[room].register_mafia_kill(victim)
        return server_pb2.VoteResponse()

    def AcceptSheriffVote(self, request, context):
        room = request.room
        victim = request.victim
        sheriff = request.username
        return self.rooms[room].register_sheriff_vote(sheriff, victim)

    def RevealMafia(self, request, context):
        room = request.room
        user = request.username
        return self.rooms[room].reveal_role(user, True)

    def update(self):
        self.last_updated = time.time()

        for room in self.rooms:
            room.update()

    def get_next_room_number(self):
        if len(self.rooms) == 0 or not self.rooms[-1].is_available():
            self.rooms.append(Room(self.next_room_number))
            self.next_room_number += 1
        return self.rooms[-1].number


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_pb2_grpc.add_ServerServicer_to_server(Server(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    request = server_pb2.DayStarted()
    print('okay')
    serve()
