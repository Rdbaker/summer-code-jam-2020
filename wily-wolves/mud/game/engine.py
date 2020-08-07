from asgiref.sync import async_to_sync
from game.models import Player, Location


class Engine():
    def __init__(self, consumer):
        self.consumer = consumer

    @property
    def user(self):
        return self.consumer.user

    @property
    def player(self):
        return Player.objects.get(user=self.user)

    def gossip(self, gossip_content=None):
        if gossip_content is None:
            return "What do you want to gossip to the world?"

        async_to_sync(self.consumer.channel_layer.group_send)(
            self.consumer.room_group_name,
            {
                'type': 'global_message_login_required',
                'message': f"{self.user} gossips: {gossip_content}",
            }
        )

    def think(self, thought_content=None):
        if thought_content is None:
            return "What the hell are you thinking about?"

        async_to_sync(self.consumer.channel_layer.group_send)(
            self.consumer.room_group_name,
            {
                'type': 'message_to_self',
                'sender_channel_name': self.consumer.channel_name,
                'message': f"{self.user} thinks: {thought_content}",
            }
        )

    def where(self):
        return f"You are here: {self.player.location.description} ({self.player.location})"

    def start(self):
        if self.player.level == 0:
            start_location = Location.objects.get(x_coord=0, y_coord=0, z_coord=0)
            self.player.move_to(start_location)
            self.player.save()
            self.player.level_up()
            return "You are at the center of the world now!"
        else:
            return "This is no longer a valid command"

    def walk(self, direction):
        dest_x = self.player.location.x_coord
        dest_y = self.player.location.y_coord
        dest_z = self.player.location.z_coord

        direction = direction.lower()

        if direction in ('n', 'north'):
            direction_string = 'to the north'
            dest_y += 1

        elif direction in ('s', 'south'):
            direction_string = 'to the south'
            dest_y -= 1

        elif direction in ('e', 'east'):
            direction_string = 'to the east'
            dest_x += 1

        elif direction in ('w', 'west'):
            direction_string = 'to the west'
            dest_x -= 1

        elif direction in ('u', 'up'):
            direction_string = 'up'
            dest_z += 1

        elif direction in ('d', 'down'):
            direction_string = 'down'
            dest_z -= 1

        else:
            return "This is not a direction"

        dest_location = Location.objects.get(x_coord=dest_x, y_coord=dest_y, z_coord=dest_z)
        self.player.move_to(dest_location)
        self.player.save()

        return f"You move {direction_string}"

    # aslias commands
    move = walk

    def n(self):
        self.walk('n')

    def s(self):
        self.walk('s')

    def e(self):
        self.walk('e')

    def w(self):
        self.walk('w')

    def u(self):
        self.walk('u')

    def d(self):
        self.walk('d')

    def help(self):
        """If you use 'help' you can see a list of availlable commands.
        You can also use 'help <command>' to get a more specific guide."""

        methods_list = [
            func for func in dir(Engine)
            if (callable(getattr(Engine, func))
                and not func.startswith("__") and len(func) > 1)
        ]
        if len(self.command_line.split()) == 1:
            message = "This is the list of all commands available in this server:"
            for func in methods_list:
                message = message + f"\n{func!r}"
            return message
        elif len(self.command_line.split()) == 2:
            command_to_help = self.command_line.split(maxsplit=1)[1]
            if command_to_help in methods_list:
                help_text = eval('Engine.' + self.command_line.split(maxsplit=1)[1] + '.__doc__')
                return f"This is the 'help' for {command_to_help!r}: {help_text}"
            else:
                return f"{command_to_help!r} is not a valid command. We can't help you with that."
        else:
            return "Invalid input. You can either use 'help' or 'help <command>', but nothing more."