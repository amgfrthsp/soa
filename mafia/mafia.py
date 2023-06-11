import enum
import random
import sys
import arcade
import arcade.gui
import threading
import time
import grpc
import proto.server_pb2_grpc as server_pb2_grpc
import proto.server_pb2 as server_pb2
import utilities
import pika

mutex = threading.Lock()

random.seed(time.time())

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
SCREEN_WIDTH /= 2.4
SCREEN_HEIGHT /= 2.4
DEFAULT_FONT_SIZE = SCREEN_HEIGHT / 40


class GameState(enum.Enum):
    NOT_STARTED = 1
    VOTING = 2
    VOTED = 3
    MAFIA = 4
    SHERIFF = 5
    OVER = 6
    NIGHT = 7
    FINISH = 8


class User:
    def __init__(self, username):
        self.name = username
        self.status = "ALIVE"
        self.role = "???"
        self.display_box = None
        self.number = -1


class Mafia(arcade.Window):
    def __init__(self, port):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Mafia")

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        arcade.set_background_color(arcade.color.WHITE)

        self.auto = False

        self.username = ""
        self.room = None
        self.role = None
        self.signiture = None
        self.status = "ALIVE"

        self.pinged = False

        self.registered = False
        self.joined = False
        self.last_updated = 0.0
        self.state = GameState.NOT_STARTED

        self.channel = None

        self.users = {}
        self.users_order = []
        self.mafia = None
        self.published = False

        self.first_day = True

        self.host = 'localhost'
        self.server_port = 50051
        port = self.server_port
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, port))
        self.stub = server_pb2_grpc.ServerStub(self.channel)

        self.h_box = arcade.gui.UIBoxLayout(
            vertical=False, align="top")

        # *************** LEFT BOX *************************************

        self.left_box = arcade.gui.UIBoxLayout(vertical=True, align="top")

        self.other_users_box = arcade.gui.UIBoxLayout(align="top",
                                                      vertical=True, space_between=-5)

        self.other_users_box.add(arcade.gui.UITextArea(text=f"Players:",
                                                       font_size=DEFAULT_FONT_SIZE * 1.5,
                                                       text_color=arcade.color.BLACK,
                                                       width=SCREEN_WIDTH / 3))

        self.commands_box = arcade.gui.UIBoxLayout(align="top",
                                                   vertical=True, space_between=-5)

        self.commands = {
            'register': arcade.gui.UITextArea(text="/register {name} --- Register as name",
                                              font_size=DEFAULT_FONT_SIZE,
                                              text_color=arcade.color.BLACK,
                                              width=SCREEN_WIDTH / 3),
            'vote': arcade.gui.UITextArea(text="/vote {player 1-4} --- Vote to cancel player",
                                          font_size=DEFAULT_FONT_SIZE,
                                          text_color=arcade.color.BLACK,
                                          width=SCREEN_WIDTH / 3),
            'finish': arcade.gui.UITextArea(text="/finish --- Finish current day",
                                            font_size=DEFAULT_FONT_SIZE,
                                            text_color=arcade.color.BLACK,
                                            width=SCREEN_WIDTH / 3),
            'kill': arcade.gui.UITextArea(text="/kill {player 1-4} --- Kill player",
                                          font_size=DEFAULT_FONT_SIZE,
                                          text_color=arcade.color.BLACK,
                                          width=SCREEN_WIDTH / 3),
            'check': arcade.gui.UITextArea(text="/check {player 1-4} --- Check player's role",
                                           font_size=DEFAULT_FONT_SIZE,
                                           text_color=arcade.color.BLACK,
                                           width=SCREEN_WIDTH / 3),
            'publish': arcade.gui.UITextArea(text="/publish --- tell everyone who is mafia",
                                             font_size=DEFAULT_FONT_SIZE,
                                             text_color=arcade.color.BLACK,
                                             width=SCREEN_WIDTH / 3),
        }

        self.commands_box.add(self.commands['register'])

        self.left_box.add(self.other_users_box.with_space_around(
            left=5).with_border(2))

        self.left_box.add(self.commands_box.with_space_around(
            left=5).with_border(2))

        # *************** CENTER BOX *************************************

        self.center_box = arcade.gui.UIBoxLayout(vertical=True, align="top")

        self.events_text = arcade.gui.UITextArea(
            width=SCREEN_WIDTH * 2 / 3.2,
            height=SCREEN_HEIGHT * 0.8,
            text="",
            font_size=DEFAULT_FONT_SIZE * 1.2,
            text_color=arcade.color.BLACK)

        bg_tex = arcade.load_texture(
            "src/texture.png")

        self.events = arcade.gui.widgets.UITexturePane(
            self.events_text,
            tex=bg_tex,
            padding=(10, 10, 10, 10)
        )

        self.input = ">"
        self.input_box = arcade.gui.UITextArea(
            width=SCREEN_WIDTH * 2 / 3,
            height=SCREEN_HEIGHT * 0.2,
            text=self.input,
            font_size=DEFAULT_FONT_SIZE * 1.2,
            text_color=arcade.color.BLACK)

        self.center_box.add(self.events.with_space_around(left=10,
                                                          right=10).with_border(2))

        self.center_box.add(self.input_box)

        # ***************************************************************

        self.h_box.add(self.left_box)
        self.h_box.add(self.center_box)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="left",
                anchor_y="top",
                child=self.h_box)
        )

    def on_update(self, delta_time):
        if self.state != GameState.NOT_STARTED:
            connection.process_data_events()
        if not self.pinged:
            self.ping()
            return
        if self.auto and not self.registered:
            self.register()

        if self.registered and time.time() - self.last_updated >= 1.0:
            self.last_updated = time.time()
            request = server_pb2.GetUpdateRequest(
                username=self.username, signiture=self.signiture, room=self.room)
            response = self.stub.GetUpdates(request)
            for event in response.events:
                if event.HasField("user_joined"):
                    self.process_user_joined(event.user_joined.username)
                elif event.HasField("user_left"):
                    self.process_user_left(event.user_left.username)
                elif event.HasField("game_started"):
                    self.process_game_started()
                elif event.HasField("game_finished"):
                    self.process_game_finished(event.game_finished.msg)
                elif event.HasField("day_started"):
                    self.process_day_started()
                elif event.HasField("user_cancelled"):
                    self.process_user_cancelled(event.user_cancelled.username)
                elif event.HasField("server_msg"):
                    self.display_game_event(
                        event.server_msg.msg, arcade.color.BLACK)
                elif event.HasField("night_started"):
                    self.process_night_started()
                elif event.HasField("mafia_time"):
                    self.process_mafia_time()
                elif event.HasField("user_killed"):
                    self.process_user_killed(event.user_killed.username)
                elif event.HasField("sheriff_time"):
                    self.process_sheriff_time()
                elif event.HasField("sheriff_chose"):
                    self.process_sheriff_chose()
                elif event.HasField("reveal_role"):
                    self.process_reveal_role(
                        event.reveal_role.username, event.reveal_role.role)

        for i in range(len(self.users_order)):
            user = self.users[self.users_order[i]]
            user.number = i
            user.display_box.text = f'{user.number + 1}) {user.name}:\n {user.role}  {user.status}'

        self.input_box.text = self.input

        if self.registered and not self.joined:
            self.joined = True
            self.process_user_joined(self.username)

        self.input_box.text = self.input

    def ping(self,):
        request = server_pb2.PingRequest()
        response = self.stub.Ping(request)
        self.auto = response.auto
        self.pinged = True
        if self.auto:
            self.commands_box.clear()

    def vote(self, victim):
        request = server_pb2.Vote(
            username=self.username, signiture=self.signiture, victim=victim, room=self.room)
        self.stub.AcceptVote(request)

    def mafia_vote(self, victim):
        request = server_pb2.Vote(
            username=self.username, signiture=self.signiture, victim=victim, room=self.room)
        self.display_game_event(f"You have killed {victim}")
        self.stub.AcceptMafiaVote(request)
        self.state = GameState.NIGHT

    def sheriff_vote(self, victim):
        request = server_pb2.Vote(
            username=self.username, signiture=self.signiture, victim=victim, room=self.room)
        response = self.stub.AcceptSheriffVote(request)
        self.users[victim].role = response.role

        self.display_game_event(
            f"User {victim} is {response.role}.\n Other players do not know it.")

        if response.role == "Mafia":
            self.mafia = victim
        self.state = GameState.NIGHT

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_key_press(self, key, key_modifiers):
        if self.status != "ALIVE" and self.registered:
            return
        if key == arcade.key.BACKSPACE:
            if len(self.input) > 1:
                self.input = self.input[:-1]
        elif key == arcade.key.ENTER:
            self.handle_input()
        else:
            self.input += chr(key)

    def handle_input(self):
        command = self.input[1:]
        self.input = ">"

        if self.status != "ALIVE":
            return

        if self.auto and not command.startswith('/'):
            self.send_message(f'{self.username}: {command}')
            return

        if command.startswith('/register'):
            tokens = command.split(' ')
            if not self.registered and len(tokens) <= 2:
                self.username = ""
                if len(tokens) > 1:
                    self.username = tokens[1]
                if not self.username in self.users_order:
                    self.register()
                    self.commands_box.clear()
            else:
                self.display_game_event(
                    "Invalid input")
        if command.startswith('/vote'):
            if self.state != GameState.VOTING:
                self.display_game_event(
                    "You are not allowed to vote now")
                return
            if self.validate_input(command):
                user = self.get_user_by_input(command)
                self.vote(user)
                self.state = GameState.FINISH
                self.commands_box.clear()
                self.commands_box.add(self.commands['finish'])
                if self.role == "Sheriff" and not self.published:
                    self.commands_box.add(self.commands['publish'])
            else:
                self.display_game_event(
                    "Invalid input")
        elif command.startswith('/kill'):
            if self.state != GameState.MAFIA:
                self.display_game_event(
                    "You are not allowed to kill")
                return
            if self.validate_input(command):
                user = self.get_user_by_input(command)
                self.mafia_vote(user)
                self.state = GameState.VOTED
                return
            self.display_game_event(
                "Invalid input")
        elif command.startswith('/check'):
            if self.state != GameState.SHERIFF:
                self.display_game_event(
                    "You are not allowed to check")
                return
            if self.validate_input(command):
                user = self.get_user_by_input(command)
                self.sheriff_vote(user)
                self.state = GameState.VOTED
            else:
                self.display_game_event(
                    "Invalid input")
        elif command.strip() == '/publish':
            if (self.state == GameState.VOTING or self.state == GameState.VOTED) and not self.published:
                self.publish_mafia()
                self.commands_box.clear()
                self.commands_box.add(self.commands['vote'])
            else:
                self.display_game_event(
                    "Invalid input")
        elif command.strip() == '/finish':
            if self.state == GameState.FINISH:
                self.finish_day()
            else:
                self.display_game_event(
                    "Invalid input")
        else:
            msg = f'{self.username}: {command}'
            if self.state == GameState.MAFIA or self.state == GameState.SHERIFF:
                self.channel.basic_publish(
                    exchange='', routing_key=self.get_queue_name(self.username), body=msg)
            elif self.state == GameState.NIGHT:
                self.display_game_event("You can't chat at night")
            else:
                self.send_message(msg)

    def validate_input(self, input):
        if len(input.split(' ')) < 2:
            return False
        vote = input.split(' ')[1]
        if not vote.isdigit() or not (1 <= int(vote) and int(vote) <= 4):
            return False
        user = self.users[self.users_order[int(vote) - 1]]
        if user.status != "ALIVE":
            return False
        return True

    def get_user_by_input(self, input):
        vote = input.split(' ')[1]
        return self.users_order[int(vote) - 1]

    def register(self):

        try:
            self.signiture = self.generateSigniture()
            request = server_pb2.RegisterRequest(
                username=self.username, signiture=self.signiture)
            response = self.stub.Register(request)

            self.username = response.username
            self.room = response.room
            self.role = response.role

            self.users[self.username] = User(self.username)

            if self.auto:
                self.display_game_event("YOU ARE PLAYING IN AUTO MODE")

            self.registered = True

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                print("Username already registered.\
                     Try a different name or let the system choose for you by not specifying a username")
            else:
                print(f"Error: {e}")
            arcade.finish_render()

    def process_user_joined(self, new_username):
        self.users_order.append(new_username)
        new_user = User(new_username)
        new_user.number = len(self.users_order) - 1
        self.number = len(self.users_order) - 1
        color = arcade.color.BLACK
        if new_username == self.username:
            color = arcade.color.VIVID_VIOLET
        user_display = arcade.gui.UITextArea(text=f'{new_user.number + 1}) {new_username}: {new_user.role}  {new_user.status}',
                                             font_size=DEFAULT_FONT_SIZE,
                                             text_color=color,
                                             width=SCREEN_WIDTH / 4)
        new_user.display_box = user_display
        self.users[new_username] = new_user

        self.other_users_box.add(user_display)
        self.display_game_event(f'User {new_username} joined the game')

    def finish_day(self):
        request = server_pb2.FinishDayMessage(
            room=self.room, username=self.username)
        self.stub.FinishDay(request)
        self.commands_box.clear()
        self.display_game_event("Wait for other players to finish the day")

    def process_user_left(self, user):
        self.users_order.remove(user)
        self.other_users_box.remove(self.users[user].display_box)
        self.users.pop(user)
        self.display_game_event(f'User {user} left the game', arcade.color.RED)

    def process_reveal_role(self, user, role):
        self.users[user].role = role
        self.display_game_event(f'User {user} is {role}!')

    def process_game_started(self):
        queue_name = self.get_queue_name(self.username)

        self.channel = connection.channel()
        self.channel.queue_declare(queue=queue_name)
        self.channel.basic_consume(queue=queue_name,
                                   on_message_callback=self.process_chat_message,
                                   auto_ack=True)

        self.users[self.username].role = self.role

        self.display_game_event(f'Game started!', arcade.color.GREEN)

    def get_queue_name(self, user):
        return f'chat_{self.room}_{user}'

    def process_chat_message(self, channel, method, properties, body):
        self.display_game_event(body.decode())

    def send_message(self, msg):
        for user in self.users:
            queue_name = self.get_queue_name(user)
            self.channel.basic_publish(
                exchange='', routing_key=queue_name, body=msg)

    def process_game_finished(self, msg):
        self.display_game_event(msg, arcade.color.BLACK)

    def process_day_started(self):
        self.display_game_event(
            f'************ Day has started ************', arcade.color.BLACK)
        self.state = GameState.VOTING
        self.commands_box.clear()
        if self.first_day:
            self.commands_box.add(self.commands['finish'])
            self.state = GameState.FINISH
            if self.auto:
                self.input = ">/finish"
                self.handle_input()
            self.first_day = False
            return
        self.commands_box.add(self.commands['vote'])
        if self.role == "Sheriff" and self.mafia is not None:
            self.commands_box.add(self.commands['publish'])
            if self.auto:
                if random.randint(0, 1) == 0:
                    self.input = "> /publish"
                    self.handle_input()
        if self.auto:
            while True:
                a = random.randint(1, 4)
                command = f"/vote {a}"
                if a - 1 != self.number and self.validate_input(command):
                    self.input = ">" + command
                    self.handle_input()
                    break
            self.input = ">/finish"
            self.handle_input()

    def publish_mafia(self):
        request = server_pb2.RevealRoleMessage(room=self.room)
        self.stub.RevealMafia(request)
        self.published = True

    def process_night_started(self):
        self.display_game_event(
            f'************ Night has started ************', arcade.color.BLACK)
        self.commands_box.clear()
        self.state = GameState.NIGHT

    def process_user_cancelled(self, user):
        if user == self.username:
            self.display_game_event(
                f'You were cancelled by the majority. Now you can only watch the game.\n', arcade.color.BLACK)
            self.status = 'CANCELLED'
            self.users[user].status = 'CANCELLED'
            self.users[user].display_box.text_color = arcade.color.RED
            self.state = GameState.OVER
        elif user == "":
            self.display_game_event(
                f'No one was cancelled today.\n', arcade.color.BLACK)
        else:
            self.display_game_event(
                f'{user} was cancelled by the majority.\n', arcade.color.BLACK)
            self.users[user].display_box.text_color = arcade.color.RED
            self.users[user].status = 'CANCELLED'

    def process_mafia_time(self):
        self.commands_box.clear()
        if self.role != 'Mafia':
            self.display_game_event(
                f'Mafia is working...', arcade.color.BLACK)
        else:
            self.commands_box.add(self.commands['kill'])
            self.display_game_event(
                f'You have to decide on your victim', arcade.color.BLACK)
            self.state = GameState.MAFIA
            if self.auto:
                while True:
                    a = random.randint(1, 4)
                    command = f"/kill {a}"
                    if a - 1 != self.number and self.validate_input(command):
                        self.input = ">" + command
                        self.handle_input()
                        break

    def process_user_killed(self, user):
        if user == self.username:
            self.display_game_event(
                f'You were killed by mafia. Now you can only watch the game.\n', arcade.color.BLACK)
            self.status = 'KILLED'
            self.users[user].status = 'KILLED'
            self.users[user].display_box.text_color = arcade.color.RED
            self.state = GameState.OVER
        else:
            self.display_game_event(
                f'{user} was killed by mafia.\n', arcade.color.BLACK)
            self.users[user].status = 'KILLED'
            self.users[user].display_box.text_color = arcade.color.RED

    def process_sheriff_time(self):
        self.commands_box.clear()
        if self.role != 'Sheriff':
            self.display_game_event(
                f'Sheriff is working...', arcade.color.BLACK)
        else:
            self.commands_box.add(self.commands['check'])
            self.display_game_event(
                f'You have to decide who to check.', arcade.color.BLACK)
            self.state = GameState.SHERIFF
            if self.auto:
                while True:
                    a = random.randint(1, 4)
                    command = f"/check {a}"
                    if a - 1 != self.number and self.validate_input(command):
                        self.input = ">" + command
                        self.handle_input()
                        break

    def process_sheriff_chose(self):
        if self.role != "Sheriff":
            self.display_game_event("Sheriff made a check\n")

    def display_game_event(self, text, color=arcade.color.BLACK):
        self.events_text.text = text + "\n" + self.events_text.text

    def generateSigniture(self):
        return utilities.generate_random_string(15)


def main():
    port = 50051
    if len(sys.argv) > 1:
        port = sys.argv[1]
    Mafia(port)
    try:
        arcade.run()
    except:
        arcade.run()


if __name__ == "__main__":
    main()
