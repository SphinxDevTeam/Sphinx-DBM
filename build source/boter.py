import discord
from discord.ext import commands
from discord import app_commands
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.logging import RichHandler
from rich.markdown import Markdown
import logging
import yaml
import sys
import subprocess

console = Console()

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler()])
log = logging.getLogger("rich")

def load_config(filename="bot_config.yaml"):
    try:
        with open(filename, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        console.print("[red]Configuration file not found. Starting with an empty configuration.[/red]")
        return {}        

def install_requirements():
    """
    Install the required packages from requirements.txt.
    """
    console.print("[cyan]Checking and installing requirements...[/cyan]")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        console.print("[red]Failed to install requirements. Please check the requirements.txt file and try again.[/red]")
        sys.exit(1)
    console.print("[green]All requirements installed successfully![/green]")

def check_installation():
    """
    Check if the script has been run before and if the packages are installed.
    """
    flag_file = "installation_complete.flag"
    
    if os.path.exists(flag_file):
        console.print("[green]Requirements already installed. Skipping installation step.[/green]")
        return

    install_requirements()
    
    with open(flag_file, "w") as f:
        f.write("Installation complete.")

def import_libraries():
    """
    Import necessary libraries and handle import errors.
    """
    try:
        import discord
        from discord.ext import commands
        from discord import app_commands
        import yaml
    except ImportError as e:
        console.print(f"[red]Failed to import a required module: {e}. Please make sure all requirements are installed.[/red]")
        sys.exit(1)

def save_config(config, filename="bot_config.yaml"):
    try:
        with open(filename, "w") as f:
            yaml.dump(config, f)
            console.print("[green]Configuration saved successfully![/green]")
    except Exception as e:
        console.print(f"[red]Failed to save configuration: {e}[/red]")

def get_intents():
    intents = {
        "members": Confirm.ask("Enable Members Intent (required for some features)?"),
        "message_content": Confirm.ask("Enable Message Content Intent (required for reading message content)?")
    }
    return intents

def validate_token(token):
    if not token:
        console.print("[red]Invalid token. Please enter a non-empty bot token.[/red]")
        return False
    return True

def main_menu():
    console.print(Panel("[bold blue]Sphinx DBM V1[/bold blue]", expand=False))
    console.print(Panel(r"""
.oPYo.    .oPYo.    o    o   o   o    o    o    o  
8         8    8    8    8   8   8b   8    `b  d'  
`Yooo.   o8YooP'   o8oooo8   8   8`b  8     `bd'   
    `8    8         8    8   8   8 `b 8     .PY.   
     8    8         8    8   8   8  `b8    .P  Y.  
`YooP'    8         8    8   8   8   `8   .P    Y. 
:.....::::..::::::::..:::..::..::..:::..::..::::..:
:::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::
"""))
    options = ["Create Bot", "Edit Bot", "Run Bot", "Exit"]
    choice = Prompt.ask("Select an option", choices=options).lower()
    return choice

def create_bot():
    config = {}
    while True:
        config["token"] = Prompt.ask("Bot Token")
        if validate_token(config["token"]):
            break
    config["prefix"] = Prompt.ask("Command Prefix", default="!")
    config["status"] = Prompt.ask("Custom Status (leave empty for no status)", default="")
    config["intents"] = get_intents()
    config["commands"] = create_commands()
    save_config(config)

def create_commands():
    commands = []
    while True:
        command = {}
        command["name"] = Prompt.ask("Command Name")
        command["description"] = Prompt.ask("Description")
        command["response"] = Prompt.ask("Response")
        command["type"] = Prompt.ask("Command Type (slash/normal)", choices=["slash", "normal"], default="normal")
        command["permissions"] = Prompt.ask("Required Permissions (comma-separated, e.g., manage_messages, administrator)", default="").split(",")
        commands.append(command)
        if not Confirm.ask("Add another command?"):
            break
    return commands

def edit_bot():
    config = load_config()
    if not config:
        console.print("[red]No existing bot configuration found.[/red]")
        return

    edit_options = ["Token", "Prefix", "Status", "Intents", "Commands", "Back"]
    while True:
        console.print(Panel("[bold blue]Edit Bot Configuration[/bold blue]", expand=False))
        choice = Prompt.ask("What would you like to edit?", choices=edit_options).lower()
        if choice == "token":
            while True:
                config["token"] = Prompt.ask("New Bot Token", default=config.get("token", ""))
                if validate_token(config["token"]):
                    break
        elif choice == "prefix":
            config["prefix"] = Prompt.ask("New Command Prefix", default=config.get("prefix", "!"))
        elif choice == "status":
            config["status"] = Prompt.ask("New Custom Status (leave empty for no status)", default=config.get("status", ""))
        elif choice == "intents":
            config["intents"] = get_intents()
        elif choice == "commands":
            edit_commands(config)
        elif choice == "back":
            break

    save_config(config)

def edit_commands(config):
    while True:
        command_names = [cmd["name"] for cmd in config.get("commands", [])]
        command_names.append("Add New Command")
        command_names.append("Back")
        choice = Prompt.ask("Select a command to edit", choices=command_names).lower()
        
        if choice == "add new command":
            config["commands"].append(create_single_command())
        elif choice == "back":
            break
        else:
            command_to_edit = next((cmd for cmd in config["commands"] if cmd["name"].lower() == choice), None)
            if command_to_edit:
                edit_single_command(command_to_edit)
    
    save_config(config)

def create_single_command():
    command = {}
    command["name"] = Prompt.ask("Command Name")
    command["description"] = Prompt.ask("Description")
    command["response"] = Prompt.ask("Response")
    command["type"] = Prompt.ask("Command Type (slash/normal)", choices=["slash", "normal"], default="normal")
    command["permissions"] = Prompt.ask("Required Permissions (comma-separated, e.g., manage_messages, administrator)", default="").split(",")
    return command

def edit_single_command(command):
    edit_fields = ["Name", "Description", "Response", "Type", "Permissions", "Delete", "Back"]
    while True:
        console.print(Panel(f"[bold blue]Editing Command: {command['name']}[/bold blue]", expand=False))
        field = Prompt.ask("Select field to edit", choices=edit_fields).lower()
        if field == "name":
            command["name"] = Prompt.ask("New Command Name", default=command["name"])
        elif field == "description":
            command["description"] = Prompt.ask("New Description", default=command["description"])
        elif field == "response":
            command["response"] = Prompt.ask("New Response", default=command["response"])
        elif field == "type":
            command["type"] = Prompt.ask("New Command Type (slash/normal)", choices=["slash", "normal"], default=command["type"])
        elif field == "permissions":
            command["permissions"] = Prompt.ask("Required Permissions (comma-separated, e.g., manage_messages, administrator)", default="").split(",")
        elif field == "delete":
            config["commands"].remove(command)
            console.print("[red]Command deleted![/red]")
            break
        elif field == "back":
            break

class MyBot(commands.Bot):
    def __init__(self, config, intents):
        super().__init__(command_prefix=config["prefix"], intents=intents)
        self.config = config

    async def setup_hook(self):
        for cmd in self.config["commands"]:
            if cmd["type"] == "slash":
                slash_command = app_commands.Command(
                    name=cmd["name"],
                    description=cmd["description"],
                    callback=self.create_callback(cmd["response"])
                )
                self.tree.add_command(slash_command)
            else:
                command = commands.Command(
                    self.create_command_callback(cmd["response"]),
                    name=cmd["name"],
                    description=cmd["description"]
                )
                self.add_command(command)

    def create_callback(self, response):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_message(response)
        return callback

    def create_command_callback(self, response):
        async def command_callback(ctx):
            await ctx.send(response)
        return command_callback

    async def on_ready(self):
        if self.config["status"]:
            await self.change_presence(activity=discord.Game(name=self.config["status"]))
        await self.tree.sync()
        console.print(f"[green]Logged in as {self.user}![green]")

def run_bot():
    config = load_config()
    if not config:
        console.print("[red]No existing bot configuration found.[/red]")
        return

    intents = discord.Intents.default()
    intents.members = config["intents"].get("members", False)
    intents.message_content = config["intents"].get("message_content", False)

    with open("run_bot.py", "w") as f:
        f.write(f"""
import discord
from discord.ext import commands
from discord import app_commands

class MyBot(commands.Bot):
    def __init__(self, config, intents):
        super().__init__(command_prefix=config["prefix"], intents=intents)
        self.config = config

    async def setup_hook(self):
        for cmd in self.config["commands"]:
            if cmd["type"] == "slash":
                slash_command = app_commands.Command(
                    name=cmd["name"],
                    description=cmd["description"],
                    callback=self.create_callback(cmd["response"])
                )
                self.tree.add_command(slash_command)
            else:
                command = commands.Command(
                    self.create_command_callback(cmd["response"]),
                    name=cmd["name"],
                    description=cmd["description"]
                )
                self.add_command(command)

    def create_callback(self, response):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_message(response)
        return callback

    def create_command_callback(self, response):
        async def command_callback(ctx):
            await ctx.send(response)
        return command_callback

    async def on_ready(self):
        if self.config["status"]:
            await self.change_presence(activity=discord.Game(name=self.config["status"]))
        await self.tree.sync()
        print(f"Logged in as {{self.user}}")

config = {config}
intents = discord.Intents.default()
intents.members = {config['intents'].get('members', False)}
intents.message_content = {config['intents'].get('message_content', False)}

bot = MyBot(config, intents)

bot.run(config["token"])
""")
    subprocess.run(["python", "run_bot.py"])

def custom_terminal():
    commands = {
        "start": run_bot,
        "stop": lambda: console.print("[yellow]Stop bot functionality is not yet implemented. This feature will be available in V2. Check for the rewrite at https://sphinxnet.lol/labs or join our Discord server https://discord.gg/KGAfXd8syu.[/yellow]"),
        "restart": lambda: console.print("[yellow]Restart bot functionality is not yet implemented. This feature will be available in V2. Check for the rewrite at https://sphinxnet.lol/labs or join our Discord server https://discord.gg/KGAfXd8syu.[/yellow]"),
        "status": lambda: console.print("[yellow]Bot status functionality is not yet implemented. This feature will be available in V2. Check for the rewrite at https://sphinxnet.lol/labs or join our Discord server https://discord.gg/KGAfXd8syu.[/yellow]")
    }
    while True:
        command = Prompt.ask("Enter a command (start/stop/restart/status/exit)").lower()
        if command in commands:
            commands[command]()
        elif command == "exit":
            break
        else:
            console.print("[red]Invalid command.[/red]")

if __name__ == "__main__":
    try:
        while True:
            choice = main_menu()
            if choice == "create bot":
                create_bot()
            elif choice == "edit bot":
                edit_bot()
            elif choice == "run bot":
                custom_terminal()
            elif choice == "exit":
                break
    except Exception as e:
        log.exception("An error occurred: %s", e)
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        sys.exit(1)
